"""
File Watch Service for PRSNL CodeMirror CLI Integration

Real-time file system monitoring using Watchdog for automatic analysis
triggers, incremental updates, and live repository intelligence.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
from collections import defaultdict, deque

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from langfuse import observe

logger = logging.getLogger(__name__)


class EventType(Enum):
    """File system event types"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class AnalysisTrigger(Enum):
    """Triggers for automated analysis"""
    IMMEDIATE = "immediate"  # Trigger analysis immediately
    BATCHED = "batched"      # Wait for batch of changes
    SCHEDULED = "scheduled"   # Trigger on schedule
    MANUAL = "manual"        # Only manual triggers


@dataclass
class FileChangeEvent:
    """Data class for file change events"""
    event_type: EventType
    file_path: str
    timestamp: datetime
    file_size: Optional[int]
    file_extension: str
    is_source_file: bool
    batch_id: Optional[str] = None


@dataclass
class WatchConfiguration:
    """Configuration for file watching"""
    repository_path: str
    watch_patterns: List[str]  # Patterns to watch (*.py, *.js, etc.)
    ignore_patterns: List[str]  # Patterns to ignore
    analysis_trigger: AnalysisTrigger
    batch_window_seconds: int  # Time to wait for batching events
    max_events_per_batch: int  # Maximum events before forcing analysis
    debounce_seconds: float   # Minimum time between events for same file
    enable_git_integration: bool  # Watch for git changes
    enable_security_monitoring: bool  # Monitor for security-relevant changes


@dataclass
class AnalysisRequest:
    """Request for automated analysis"""
    request_id: str
    repository_path: str
    trigger_events: List[FileChangeEvent]
    analysis_types: List[str]  # ['git', 'security', 'structural']
    priority: str  # 'low', 'medium', 'high'
    created_at: datetime


class FileSystemEventCollector(FileSystemEventHandler):
    """Collects and processes file system events"""
    
    def __init__(self, watch_service: 'FileWatchService', config: WatchConfiguration):
        super().__init__()
        self.watch_service = watch_service
        self.config = config
        self.last_event_time = {}  # Debouncing
        
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """Determine if event should be processed"""
        
        # Skip directories unless explicitly configured
        if event.is_directory and not self.config.enable_git_integration:
            return False
        
        file_path = event.src_path
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if self._matches_pattern(file_path, pattern):
                return False
        
        # Check if it matches watch patterns
        if self.config.watch_patterns:
            matches_pattern = any(
                self._matches_pattern(file_path, pattern) 
                for pattern in self.config.watch_patterns
            )
            if not matches_pattern:
                return False
        
        # Debounce check
        now = time.time()
        last_time = self.last_event_time.get(file_path, 0)
        if now - last_time < self.config.debounce_seconds:
            return False
        
        self.last_event_time[file_path] = now
        return True
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern)
    
    def _create_change_event(self, event: FileSystemEvent, event_type: EventType) -> FileChangeEvent:
        """Create FileChangeEvent from watchdog event"""
        
        file_path = event.src_path
        file_size = None
        
        # Get file size if file exists and is not directory
        if not event.is_directory and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                pass
        
        # Determine file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a source file
        source_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.php', '.rb'}
        is_source_file = file_extension in source_extensions
        
        return FileChangeEvent(
            event_type=event_type,
            file_path=file_path,
            timestamp=datetime.utcnow(),
            file_size=file_size,
            file_extension=file_extension,
            is_source_file=is_source_file
        )
    
    def on_created(self, event: FileSystemEvent):
        """Handle file/directory creation"""
        if self._should_process_event(event):
            change_event = self._create_change_event(event, EventType.CREATED)
            self.watch_service._handle_file_event(change_event)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file/directory modification"""
        if self._should_process_event(event):
            change_event = self._create_change_event(event, EventType.MODIFIED)
            self.watch_service._handle_file_event(change_event)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file/directory deletion"""
        if self._should_process_event(event):
            change_event = self._create_change_event(event, EventType.DELETED)
            self.watch_service._handle_file_event(change_event)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file/directory move/rename"""
        if self._should_process_event(event):
            change_event = self._create_change_event(event, EventType.MOVED)
            # For moves, we also store the destination path
            if hasattr(event, 'dest_path'):
                change_event.file_path = f"{event.src_path} -> {event.dest_path}"
            self.watch_service._handle_file_event(change_event)


class FileWatchService:
    """
    Service for real-time file system monitoring and analysis triggering.
    
    Monitors repository changes and triggers appropriate analysis based on
    file types, change patterns, and configured rules.
    """
    
    def __init__(self):
        self.observers: Dict[str, Observer] = {}  # repo_path -> observer
        self.configurations: Dict[str, WatchConfiguration] = {}
        self.event_queues: Dict[str, deque] = {}  # repo_path -> event queue
        self.batch_timers: Dict[str, threading.Timer] = {}
        self.analysis_callbacks: Dict[str, List[Callable]] = {}
        self.active_batches: Dict[str, str] = {}  # repo_path -> batch_id
        self.statistics: Dict[str, Dict[str, Any]] = {}
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Background thread for processing events
        self._processing_thread = None
        self._stop_processing = threading.Event()
        
    def __del__(self):
        """Cleanup when service is destroyed"""
        self.stop_all_watchers()
    
    @observe(name="file_watch_start")
    async def start_watching(
        self, 
        config: WatchConfiguration,
        analysis_callback: Optional[Callable[[AnalysisRequest], None]] = None
    ) -> bool:
        """
        Start watching a repository for file changes.
        
        Args:
            config: Watch configuration
            analysis_callback: Callback function for analysis requests
            
        Returns:
            bool: True if watching started successfully
        """
        logger.info(f"Starting file watch for repository: {config.repository_path}")
        
        try:
            # Validate repository path
            if not os.path.exists(config.repository_path):
                raise ValueError(f"Repository path does not exist: {config.repository_path}")
            
            repo_path = config.repository_path
            
            # Stop existing watcher if present
            if repo_path in self.observers:
                await self.stop_watching(repo_path)
            
            # Store configuration
            self.configurations[repo_path] = config
            self.event_queues[repo_path] = deque(maxlen=1000)  # Limit queue size
            self.statistics[repo_path] = {
                'events_processed': 0,
                'analyses_triggered': 0,
                'start_time': datetime.utcnow(),
                'last_event_time': None
            }
            
            # Register analysis callback
            if analysis_callback:
                if repo_path not in self.analysis_callbacks:
                    self.analysis_callbacks[repo_path] = []
                self.analysis_callbacks[repo_path].append(analysis_callback)
            
            # Create event handler
            event_handler = FileSystemEventCollector(self, config)
            
            # Create and start observer
            observer = Observer()
            observer.schedule(
                event_handler, 
                config.repository_path, 
                recursive=True
            )
            observer.start()
            
            self.observers[repo_path] = observer
            
            # Start processing thread if not already running
            if self._processing_thread is None or not self._processing_thread.is_alive():
                self._start_processing_thread()
            
            logger.info(f"File watching started successfully for {repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file watching for {config.repository_path}: {e}")
            return False
    
    async def stop_watching(self, repository_path: str) -> bool:
        """Stop watching a repository"""
        
        try:
            if repository_path in self.observers:
                observer = self.observers[repository_path]
                observer.stop()
                observer.join(timeout=5)  # Wait up to 5 seconds
                
                # Cleanup
                del self.observers[repository_path]
                del self.configurations[repository_path]
                if repository_path in self.event_queues:
                    del self.event_queues[repository_path]
                if repository_path in self.batch_timers:
                    timer = self.batch_timers[repository_path]
                    timer.cancel()
                    del self.batch_timers[repository_path]
                if repository_path in self.analysis_callbacks:
                    del self.analysis_callbacks[repository_path]
                if repository_path in self.statistics:
                    del self.statistics[repository_path]
                
                logger.info(f"Stopped file watching for {repository_path}")
                return True
            else:
                logger.warning(f"No active watcher found for {repository_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop file watching for {repository_path}: {e}")
            return False
    
    def stop_all_watchers(self):
        """Stop all active watchers"""
        repo_paths = list(self.observers.keys())
        
        for repo_path in repo_paths:
            try:
                asyncio.create_task(self.stop_watching(repo_path))
            except Exception as e:
                logger.error(f"Error stopping watcher for {repo_path}: {e}")
        
        # Stop processing thread
        if self._processing_thread and self._processing_thread.is_alive():
            self._stop_processing.set()
            self._processing_thread.join(timeout=5)
    
    def _start_processing_thread(self):
        """Start background thread for processing events"""
        self._stop_processing.clear()
        self._processing_thread = threading.Thread(
            target=self._process_events_background,
            daemon=True
        )
        self._processing_thread.start()
    
    def _process_events_background(self):
        """Background thread to process events"""
        while not self._stop_processing.is_set():
            try:
                # Process events for all repositories
                for repo_path in list(self.event_queues.keys()):
                    self._process_pending_events(repo_path)
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in background event processing: {e}")
                time.sleep(1)  # Wait longer on error
    
    def _handle_file_event(self, event: FileChangeEvent):
        """Handle incoming file system event"""
        
        # Find which repository this event belongs to
        repo_path = None
        for path in self.configurations.keys():
            if event.file_path.startswith(path):
                repo_path = path
                break
        
        if not repo_path:
            logger.debug(f"No matching repository found for event: {event.file_path}")
            return
        
        config = self.configurations[repo_path]
        
        with self._lock:
            # Add to event queue
            self.event_queues[repo_path].append(event)
            
            # Update statistics
            self.statistics[repo_path]['events_processed'] += 1
            self.statistics[repo_path]['last_event_time'] = event.timestamp
            
            # Handle based on trigger type
            if config.analysis_trigger == AnalysisTrigger.IMMEDIATE:
                self._trigger_immediate_analysis(repo_path, [event])
            elif config.analysis_trigger == AnalysisTrigger.BATCHED:
                self._handle_batched_event(repo_path, event, config)
    
    def _trigger_immediate_analysis(self, repo_path: str, events: List[FileChangeEvent]):
        """Trigger immediate analysis for events"""
        
        try:
            # Create analysis request
            request = AnalysisRequest(
                request_id=f"immediate_{int(time.time())}_{len(events)}",
                repository_path=repo_path,
                trigger_events=events,
                analysis_types=self._determine_analysis_types(events),
                priority="high",
                created_at=datetime.utcnow()
            )
            
            # Execute callbacks
            callbacks = self.analysis_callbacks.get(repo_path, [])
            for callback in callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Analysis callback failed: {e}")
            
            # Update statistics
            self.statistics[repo_path]['analyses_triggered'] += 1
            
            logger.info(f"Triggered immediate analysis for {len(events)} events in {repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to trigger immediate analysis: {e}")
    
    def _handle_batched_event(self, repo_path: str, event: FileChangeEvent, config: WatchConfiguration):
        """Handle event for batched analysis"""
        
        # Start or reset batch timer
        if repo_path in self.batch_timers:
            self.batch_timers[repo_path].cancel()
        
        # Create batch timer
        timer = threading.Timer(
            config.batch_window_seconds,
            self._process_batch,
            args=[repo_path]
        )
        timer.start()
        self.batch_timers[repo_path] = timer
        
        # Check if we should trigger early due to event count
        queue = self.event_queues[repo_path]
        if len(queue) >= config.max_events_per_batch:
            timer.cancel()
            self._process_batch(repo_path)
    
    def _process_batch(self, repo_path: str):
        """Process batch of events for analysis"""
        
        with self._lock:
            queue = self.event_queues[repo_path]
            if not queue:
                return
            
            # Get all events from queue
            events = list(queue)
            queue.clear()
            
            # Clean up timer
            if repo_path in self.batch_timers:
                del self.batch_timers[repo_path]
        
        try:
            # Create batch analysis request
            request = AnalysisRequest(
                request_id=f"batch_{int(time.time())}_{len(events)}",
                repository_path=repo_path,
                trigger_events=events,
                analysis_types=self._determine_analysis_types(events),
                priority="medium",
                created_at=datetime.utcnow()
            )
            
            # Execute callbacks
            callbacks = self.analysis_callbacks.get(repo_path, [])
            for callback in callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Batch analysis callback failed: {e}")
            
            # Update statistics
            self.statistics[repo_path]['analyses_triggered'] += 1
            
            logger.info(f"Triggered batch analysis for {len(events)} events in {repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to process batch: {e}")
    
    def _process_pending_events(self, repo_path: str):
        """Process any pending events (for scheduled triggers)"""
        
        config = self.configurations.get(repo_path)
        if not config or config.analysis_trigger != AnalysisTrigger.SCHEDULED:
            return
        
        with self._lock:
            queue = self.event_queues[repo_path]
            if not queue:
                return
            
            # Check if enough time has passed since last analysis
            stats = self.statistics[repo_path]
            last_analysis = stats.get('last_analysis_time')
            
            if last_analysis:
                time_since_last = datetime.utcnow() - last_analysis
                if time_since_last.total_seconds() < config.batch_window_seconds:
                    return
            
            # Get events and clear queue
            events = list(queue)
            queue.clear()
            
            # Update last analysis time
            stats['last_analysis_time'] = datetime.utcnow()
        
        # Trigger analysis
        self._trigger_scheduled_analysis(repo_path, events)
    
    def _trigger_scheduled_analysis(self, repo_path: str, events: List[FileChangeEvent]):
        """Trigger scheduled analysis"""
        
        try:
            request = AnalysisRequest(
                request_id=f"scheduled_{int(time.time())}_{len(events)}",
                repository_path=repo_path,
                trigger_events=events,
                analysis_types=self._determine_analysis_types(events),
                priority="low",
                created_at=datetime.utcnow()
            )
            
            # Execute callbacks
            callbacks = self.analysis_callbacks.get(repo_path, [])
            for callback in callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Scheduled analysis callback failed: {e}")
            
            # Update statistics
            self.statistics[repo_path]['analyses_triggered'] += 1
            
            logger.info(f"Triggered scheduled analysis for {len(events)} events in {repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to trigger scheduled analysis: {e}")
    
    def _determine_analysis_types(self, events: List[FileChangeEvent]) -> List[str]:
        """Determine which types of analysis to run based on events"""
        
        analysis_types = set()
        
        # Analyze event patterns
        has_source_changes = any(event.is_source_file for event in events)
        has_config_changes = any(
            event.file_extension in {'.json', '.yaml', '.yml', '.toml', '.ini', '.env'}
            for event in events
        )
        has_security_relevant = any(
            'password' in event.file_path.lower() or 
            'secret' in event.file_path.lower() or
            'key' in event.file_path.lower() or
            event.file_extension in {'.pem', '.key', '.crt'}
            for event in events
        )
        has_git_changes = any(
            '.git' in event.file_path or
            event.file_path.endswith('.gitignore') or
            event.file_path.endswith('.gitattributes')
            for event in events
        )
        
        # Determine analysis types
        if has_source_changes:
            analysis_types.add('structural')
            analysis_types.add('git')  # Source changes affect git analysis
        
        if has_security_relevant or has_config_changes:
            analysis_types.add('security')
        
        if has_git_changes:
            analysis_types.add('git')
        
        # Default to structural analysis if no specific triggers
        if not analysis_types:
            analysis_types.add('structural')
        
        return list(analysis_types)
    
    async def get_watch_status(self, repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Get status of file watching"""
        
        if repository_path:
            # Status for specific repository
            if repository_path not in self.observers:
                return {'error': f'No active watcher for {repository_path}'}
            
            observer = self.observers[repository_path]
            config = self.configurations[repository_path]
            stats = self.statistics[repository_path]
            queue = self.event_queues[repository_path]
            
            return {
                'repository_path': repository_path,
                'is_alive': observer.is_alive(),
                'configuration': asdict(config),
                'statistics': {
                    **stats,
                    'start_time': stats['start_time'].isoformat() if stats['start_time'] else None,
                    'last_event_time': stats['last_event_time'].isoformat() if stats['last_event_time'] else None
                },
                'pending_events': len(queue),
                'active_callbacks': len(self.analysis_callbacks.get(repository_path, []))
            }
        else:
            # Status for all repositories
            return {
                'total_watchers': len(self.observers),
                'active_repositories': list(self.observers.keys()),
                'processing_thread_active': self._processing_thread and self._processing_thread.is_alive(),
                'watchers': {
                    repo_path: {
                        'is_alive': observer.is_alive(),
                        'events_processed': self.statistics[repo_path]['events_processed'],
                        'analyses_triggered': self.statistics[repo_path]['analyses_triggered']
                    }
                    for repo_path, observer in self.observers.items()
                }
            }
    
    async def trigger_manual_analysis(
        self, 
        repository_path: str, 
        analysis_types: Optional[List[str]] = None
    ) -> bool:
        """Manually trigger analysis for a repository"""
        
        if repository_path not in self.configurations:
            logger.error(f"No watcher configured for {repository_path}")
            return False
        
        try:
            # Create manual analysis request
            request = AnalysisRequest(
                request_id=f"manual_{int(time.time())}",
                repository_path=repository_path,
                trigger_events=[],  # No specific triggering events
                analysis_types=analysis_types or ['git', 'security', 'structural'],
                priority="high",
                created_at=datetime.utcnow()
            )
            
            # Execute callbacks
            callbacks = self.analysis_callbacks.get(repository_path, [])
            if not callbacks:
                logger.warning(f"No analysis callbacks registered for {repository_path}")
                return False
            
            for callback in callbacks:
                try:
                    callback(request)
                except Exception as e:
                    logger.error(f"Manual analysis callback failed: {e}")
                    return False
            
            # Update statistics
            self.statistics[repository_path]['analyses_triggered'] += 1
            
            logger.info(f"Triggered manual analysis for {repository_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger manual analysis: {e}")
            return False
    
    def create_default_config(
        self, 
        repository_path: str,
        language_hint: Optional[str] = None
    ) -> WatchConfiguration:
        """Create a default watch configuration for a repository"""
        
        # Default patterns based on common file types
        default_watch_patterns = [
            '*.py', '*.js', '*.jsx', '*.ts', '*.tsx',
            '*.java', '*.go', '*.rs', '*.cpp', '*.c', '*.cs',
            '*.php', '*.rb', '*.swift', '*.kt', '*.scala',
            '*.json', '*.yaml', '*.yml', '*.toml', '*.ini',
            '*.md', '*.txt', '*.rst'
        ]
        
        # Language-specific adjustments
        if language_hint:
            if language_hint == 'python':
                default_watch_patterns.extend(['*.pyx', '*.pxd', 'requirements*.txt', 'setup.py', 'pyproject.toml'])
            elif language_hint in ['javascript', 'typescript']:
                default_watch_patterns.extend(['package.json', 'package-lock.json', '*.vue', '*.svelte'])
            elif language_hint == 'java':
                default_watch_patterns.extend(['*.xml', '*.gradle', 'build.gradle', 'pom.xml'])
        
        default_ignore_patterns = [
            '**/.git/**',
            '**/node_modules/**',
            '**/venv/**',
            '**/__pycache__/**',
            '**/build/**',
            '**/dist/**',
            '**/target/**',
            '**/.pytest_cache/**',
            '**/.coverage',
            '**/*.pyc',
            '**/*.pyo',
            '**/*.log',
            '**/tmp/**',
            '**/temp/**'
        ]
        
        return WatchConfiguration(
            repository_path=repository_path,
            watch_patterns=default_watch_patterns,
            ignore_patterns=default_ignore_patterns,
            analysis_trigger=AnalysisTrigger.BATCHED,
            batch_window_seconds=30,  # 30 second batching window
            max_events_per_batch=50,  # Max 50 events per batch
            debounce_seconds=2.0,     # 2 second debounce
            enable_git_integration=True,
            enable_security_monitoring=True
        )
    
    async def get_recent_events(
        self, 
        repository_path: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent file system events for a repository"""
        
        if repository_path not in self.event_queues:
            return []
        
        queue = self.event_queues[repository_path]
        recent_events = list(queue)[-limit:]  # Get last N events
        
        return [
            {
                'event_type': event.event_type.value,
                'file_path': event.file_path,
                'timestamp': event.timestamp.isoformat(),
                'file_size': event.file_size,
                'file_extension': event.file_extension,
                'is_source_file': event.is_source_file,
                'batch_id': event.batch_id
            }
            for event in recent_events
        ]


# Singleton instance
file_watch_service = FileWatchService()