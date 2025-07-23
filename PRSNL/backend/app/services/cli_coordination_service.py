"""
CLI Coordination Service for PRSNL CodeMirror

DragonflyDB-based coordination layer for CLI-web communication,
shared state management, and real-time synchronization.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

import redis
from langfuse import observe

logger = logging.getLogger(__name__)


class CoordinationEventType(Enum):
    """Types of coordination events"""
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    FILE_CHANGE_DETECTED = "file_change_detected"
    CLI_TOOL_STARTED = "cli_tool_started"
    CLI_TOOL_COMPLETED = "cli_tool_completed"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"


@dataclass
class CoordinationEvent:
    """Coordination event data structure"""
    event_type: CoordinationEventType
    event_id: str
    repository_path: str
    analysis_id: Optional[str]
    timestamp: datetime
    payload: Dict[str, Any]
    source: str  # 'cli', 'web', 'worker'
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class AnalysisState:
    """Shared analysis state"""
    analysis_id: str
    repository_path: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: int  # 0-100
    current_phase: str
    cli_tools_running: List[str]
    cli_tools_completed: List[str]
    results: Dict[str, Any]
    error_message: Optional[str]
    started_at: datetime
    updated_at: datetime


class CLICoordinationService:
    """
    Service for coordinating CLI tools and web interface through DragonflyDB.
    
    Provides shared state management, event streaming, result synchronization,
    and conflict resolution for CLI-web integration.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.Redis] = None
        self.event_subscribers: Dict[str, List[Callable]] = {}
        self.is_listening = False
        self.listener_task: Optional[asyncio.Task] = None
        
        # Key prefixes for organization
        self.KEY_PREFIX = "prsnl:cli_coordination"
        self.ANALYSIS_STATE_PREFIX = f"{self.KEY_PREFIX}:analysis_state"
        self.EVENT_STREAM_PREFIX = f"{self.KEY_PREFIX}:events"
        self.LOCK_PREFIX = f"{self.KEY_PREFIX}:locks"
        self.SYNC_PREFIX = f"{self.KEY_PREFIX}:sync"
        
        # Configuration
        self.event_ttl = 3600  # Events expire after 1 hour
        self.state_ttl = 86400  # State expires after 24 hours
        self.lock_timeout = 300  # Locks timeout after 5 minutes
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Connect to DragonflyDB"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            
            # Create separate client for pub/sub
            self.pubsub_client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            
            logger.info("Connected to DragonflyDB for CLI coordination")
            
        except Exception as e:
            logger.error(f"Failed to connect to DragonflyDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from DragonflyDB"""
        try:
            if self.listener_task:
                self.listener_task.cancel()
                try:
                    await self.listener_task
                except asyncio.CancelledError:
                    pass
            
            if self.pubsub_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.pubsub_client.close
                )
            
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.close
                )
            
            logger.info("Disconnected from DragonflyDB")
            
        except Exception as e:
            logger.error(f"Error disconnecting from DragonflyDB: {e}")
    
    @observe(name="cli_coordination_publish_event")
    async def publish_event(self, event: CoordinationEvent):
        """Publish coordination event to DragonflyDB"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            # Serialize event
            event_data = {
                'event_type': event.event_type.value,
                'event_id': event.event_id,
                'repository_path': event.repository_path,
                'analysis_id': event.analysis_id,
                'timestamp': event.timestamp.isoformat(),
                'payload': event.payload,
                'source': event.source,
                'priority': event.priority
            }
            
            event_json = json.dumps(event_data)
            
            # Publish to channel
            channel = f"{self.EVENT_STREAM_PREFIX}:{event.repository_path}"
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.publish, channel, event_json
            )
            
            # Store event in stream for replay capability
            stream_key = f"{self.EVENT_STREAM_PREFIX}:history:{event.repository_path}"
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.xadd,
                stream_key, event_data, maxlen=1000  # Keep last 1000 events
            )
            
            # Set TTL on stream
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.expire, stream_key, self.event_ttl
            )
            
            logger.debug(f"Published coordination event: {event.event_type.value} for {event.repository_path}")
            
        except Exception as e:
            logger.error(f"Failed to publish coordination event: {e}")
            raise
    
    async def subscribe_to_events(
        self, 
        repository_path: str, 
        callback: Callable[[CoordinationEvent], None]
    ):
        """Subscribe to coordination events for a repository"""
        
        if not self.pubsub_client:
            await self.connect()
        
        try:
            channel = f"{self.EVENT_STREAM_PREFIX}:{repository_path}"
            
            # Add callback to subscribers
            if channel not in self.event_subscribers:
                self.event_subscribers[channel] = []
            self.event_subscribers[channel].append(callback)
            
            # Start listener if not already running
            if not self.is_listening:
                await self._start_event_listener()
            
            # Subscribe to channel
            pubsub = self.pubsub_client.pubsub()
            await asyncio.get_event_loop().run_in_executor(
                None, pubsub.subscribe, channel
            )
            
            logger.info(f"Subscribed to coordination events for {repository_path}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to coordination events: {e}")
            raise
    
    async def _start_event_listener(self):
        """Start background event listener"""
        
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listener_task = asyncio.create_task(self._event_listener_loop())
    
    async def _event_listener_loop(self):
        """Background loop for processing events"""
        
        try:
            pubsub = self.pubsub_client.pubsub()
            
            while self.is_listening:
                try:
                    # Get message with timeout
                    message = await asyncio.get_event_loop().run_in_executor(
                        None, pubsub.get_message, True, 1.0
                    )
                    
                    if message and message['type'] == 'message':
                        await self._process_event_message(message)
                        
                except Exception as e:
                    logger.error(f"Error in event listener loop: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Event listener loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Event listener loop failed: {e}")
        finally:
            self.is_listening = False
    
    async def _process_event_message(self, message: Dict[str, Any]):
        """Process incoming event message"""
        
        try:
            # Parse event data
            event_data = json.loads(message['data'])
            
            # Reconstruct event object
            event = CoordinationEvent(
                event_type=CoordinationEventType(event_data['event_type']),
                event_id=event_data['event_id'],
                repository_path=event_data['repository_path'],
                analysis_id=event_data.get('analysis_id'),
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                payload=event_data['payload'],
                source=event_data['source'],
                priority=event_data['priority']
            )
            
            # Call subscribers for this channel
            channel = message['channel']
            subscribers = self.event_subscribers.get(channel, [])
            
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to process event message: {e}")
    
    @observe(name="cli_coordination_update_analysis_state")
    async def update_analysis_state(self, state: AnalysisState):
        """Update shared analysis state"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            # Serialize state
            state_data = {
                'analysis_id': state.analysis_id,
                'repository_path': state.repository_path,
                'status': state.status,
                'progress': state.progress,
                'current_phase': state.current_phase,
                'cli_tools_running': state.cli_tools_running,
                'cli_tools_completed': state.cli_tools_completed,
                'results': state.results,
                'error_message': state.error_message,
                'started_at': state.started_at.isoformat(),
                'updated_at': state.updated_at.isoformat()
            }
            
            state_json = json.dumps(state_data)
            
            # Store state
            state_key = f"{self.ANALYSIS_STATE_PREFIX}:{state.analysis_id}"
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex,
                state_key, self.state_ttl, state_json
            )
            
            # Also store by repository path for lookup
            repo_key = f"{self.ANALYSIS_STATE_PREFIX}:repo:{state.repository_path}"
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex,
                repo_key, self.state_ttl, state.analysis_id
            )
            
            logger.debug(f"Updated analysis state: {state.analysis_id} - {state.status}")
            
        except Exception as e:
            logger.error(f"Failed to update analysis state: {e}")
            raise
    
    async def get_analysis_state(self, analysis_id: str) -> Optional[AnalysisState]:
        """Get shared analysis state"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            state_key = f"{self.ANALYSIS_STATE_PREFIX}:{analysis_id}"
            state_json = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, state_key
            )
            
            if not state_json:
                return None
            
            # Deserialize state
            state_data = json.loads(state_json)
            
            return AnalysisState(
                analysis_id=state_data['analysis_id'],
                repository_path=state_data['repository_path'],
                status=state_data['status'],
                progress=state_data['progress'],
                current_phase=state_data['current_phase'],
                cli_tools_running=state_data['cli_tools_running'],
                cli_tools_completed=state_data['cli_tools_completed'],
                results=state_data['results'],
                error_message=state_data.get('error_message'),
                started_at=datetime.fromisoformat(state_data['started_at']),
                updated_at=datetime.fromisoformat(state_data['updated_at'])
            )
            
        except Exception as e:
            logger.error(f"Failed to get analysis state: {e}")
            return None
    
    async def get_repository_analysis_state(self, repository_path: str) -> Optional[AnalysisState]:
        """Get current analysis state for a repository"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            repo_key = f"{self.ANALYSIS_STATE_PREFIX}:repo:{repository_path}"
            analysis_id = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, repo_key
            )
            
            if analysis_id:
                return await self.get_analysis_state(analysis_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get repository analysis state: {e}")
            return None
    
    async def acquire_lock(self, resource_name: str, timeout: int = None) -> bool:
        """Acquire distributed lock"""
        
        if not self.redis_client:
            await self.connect()
        
        timeout = timeout or self.lock_timeout
        lock_key = f"{self.LOCK_PREFIX}:{resource_name}"
        lock_value = f"{time.time()}:{hashlib.md5(str(asyncio.current_task()).encode()).hexdigest()}"
        
        try:
            # Try to acquire lock
            acquired = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.set,
                lock_key, lock_value, nx=True, ex=timeout
            )
            
            if acquired:
                logger.debug(f"Acquired lock: {resource_name}")
                return True
            else:
                logger.debug(f"Failed to acquire lock: {resource_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to acquire lock {resource_name}: {e}")
            return False
    
    async def release_lock(self, resource_name: str) -> bool:
        """Release distributed lock"""
        
        if not self.redis_client:
            await self.connect()
        
        lock_key = f"{self.LOCK_PREFIX}:{resource_name}"
        
        try:
            # Delete lock
            deleted = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.delete, lock_key
            )
            
            if deleted:
                logger.debug(f"Released lock: {resource_name}")
                return True
            else:
                logger.debug(f"Lock not found or already released: {resource_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to release lock {resource_name}: {e}")
            return False
    
    async def sync_cli_results(
        self, 
        analysis_id: str, 
        cli_results: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Synchronize CLI results with web interface"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            # Create sync request
            sync_id = f"sync_{analysis_id}_{int(time.time())}"
            sync_key = f"{self.SYNC_PREFIX}:{sync_id}"
            
            sync_request = {
                'sync_id': sync_id,
                'analysis_id': analysis_id,
                'cli_results': cli_results,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'pending'
            }
            
            # Store sync request
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex,
                sync_key, timeout, json.dumps(sync_request)
            )
            
            # Publish sync event
            sync_event = CoordinationEvent(
                event_type=CoordinationEventType.SYNC_REQUEST,
                event_id=sync_id,
                repository_path="",  # Will be filled by subscriber
                analysis_id=analysis_id,
                timestamp=datetime.utcnow(),
                payload={'sync_id': sync_id, 'cli_results_available': True},
                source='cli',
                priority=1
            )
            
            await self.publish_event(sync_event)
            
            # Wait for sync response
            response_key = f"{self.SYNC_PREFIX}:response:{sync_id}"
            
            for _ in range(timeout):
                response_json = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.get, response_key
                )
                
                if response_json:
                    response = json.loads(response_json)
                    return response
                
                await asyncio.sleep(1)
            
            # Timeout
            logger.warning(f"CLI sync timeout for analysis {analysis_id}")
            return {'status': 'timeout', 'message': 'Sync request timed out'}
            
        except Exception as e:
            logger.error(f"Failed to sync CLI results: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def respond_to_sync(
        self, 
        sync_id: str, 
        response_data: Dict[str, Any]
    ):
        """Respond to CLI sync request from web interface"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            response_key = f"{self.SYNC_PREFIX}:response:{sync_id}"
            
            response = {
                'sync_id': sync_id,
                'response_data': response_data,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
            
            # Store response
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex,
                response_key, 60, json.dumps(response)  # 1 minute TTL
            )
            
            logger.debug(f"Responded to sync request: {sync_id}")
            
        except Exception as e:
            logger.error(f"Failed to respond to sync: {e}")
            raise
    
    async def get_event_history(
        self, 
        repository_path: str, 
        limit: int = 100
    ) -> List[CoordinationEvent]:
        """Get event history for a repository"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            stream_key = f"{self.EVENT_STREAM_PREFIX}:history:{repository_path}"
            
            # Get events from stream
            events_data = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.xrevrange,
                stream_key, count=limit
            )
            
            events = []
            for event_id, fields in events_data:
                try:
                    event = CoordinationEvent(
                        event_type=CoordinationEventType(fields['event_type']),
                        event_id=fields['event_id'],
                        repository_path=fields['repository_path'],
                        analysis_id=fields.get('analysis_id'),
                        timestamp=datetime.fromisoformat(fields['timestamp']),
                        payload=json.loads(fields['payload']),
                        source=fields['source'],
                        priority=int(fields['priority'])
                    )
                    events.append(event)
                except Exception as e:
                    logger.error(f"Failed to parse event from history: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get event history: {e}")
            return []
    
    async def cleanup_expired_data(self):
        """Clean up expired coordination data"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            # Get all keys with our prefixes
            patterns = [
                f"{self.ANALYSIS_STATE_PREFIX}:*",
                f"{self.EVENT_STREAM_PREFIX}:*",
                f"{self.LOCK_PREFIX}:*",
                f"{self.SYNC_PREFIX}:*"
            ]
            
            for pattern in patterns:
                keys = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.keys, pattern
                )
                
                expired_keys = []
                for key in keys:
                    ttl = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.ttl, key
                    )
                    
                    # If TTL is -1 (no expiry) or -2 (key doesn't exist), skip
                    if ttl == -2:
                        expired_keys.append(key)
                
                # Delete expired keys
                if expired_keys:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, *expired_keys
                    )
                    logger.info(f"Cleaned up {len(expired_keys)} expired keys")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination service statistics"""
        
        if not self.redis_client:
            await self.connect()
        
        try:
            stats = {
                'connected': True,
                'active_analyses': 0,
                'event_streams': 0,
                'active_locks': 0,
                'pending_syncs': 0,
                'subscribers': len(self.event_subscribers),
                'listening': self.is_listening
            }
            
            # Count active analyses
            analysis_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, f"{self.ANALYSIS_STATE_PREFIX}:*"
            )
            stats['active_analyses'] = len([k for k in analysis_keys if not k.endswith(':repo:*')])
            
            # Count event streams
            stream_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, f"{self.EVENT_STREAM_PREFIX}:history:*"
            )
            stats['event_streams'] = len(stream_keys)
            
            # Count active locks
            lock_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, f"{self.LOCK_PREFIX}:*"
            )
            stats['active_locks'] = len(lock_keys)
            
            # Count pending syncs
            sync_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, f"{self.SYNC_PREFIX}:*"
            )
            stats['pending_syncs'] = len(sync_keys)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get coordination stats: {e}")
            return {
                'connected': False,
                'error': str(e)
            }


# Singleton instance
cli_coordination_service = CLICoordinationService()