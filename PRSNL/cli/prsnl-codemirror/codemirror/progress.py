"""
Progress Tracking for CodeMirror CLI

Provides real-time progress updates to the web interface via Celery task progress.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProgressUpdate:
    """Represents a progress update"""
    task_id: str
    progress_type: str
    current_value: int
    total_value: Optional[int] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class ProgressTracker:
    """
    Thread-safe progress tracker for CodeMirror CLI operations.
    
    Integrates with Celery tasks to provide real-time progress updates.
    """
    
    def __init__(self, task_id: str, sync_client: Optional[object] = None):
        self.task_id = task_id
        self.sync_client = sync_client
        self.progress_history = []
        self.current_progress = {}
        self.callbacks = []
        
    def add_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Add a callback to be called on progress updates"""
        self.callbacks.append(callback)
    
    def update_progress(
        self,
        progress_type: str,
        current_value: int,
        total_value: Optional[int] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update progress for a specific operation type"""
        
        update = ProgressUpdate(
            task_id=self.task_id,
            progress_type=progress_type,
            current_value=current_value,
            total_value=total_value,
            message=message,
            metadata=metadata,
            timestamp=datetime.utcnow()
        )
        
        # Store in history
        self.progress_history.append(update)
        
        # Update current progress
        self.current_progress[progress_type] = update
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
        
        # Send to web interface if sync client available
        if self.sync_client:
            try:
                asyncio.create_task(self._send_progress_update(update))
            except Exception as e:
                logger.error(f"Failed to send progress update: {e}")
    
    async def _send_progress_update(self, update: ProgressUpdate):
        """Send progress update to web interface"""
        if not self.sync_client:
            return
            
        try:
            progress_data = {
                'task_id': update.task_id,
                'progress_type': update.progress_type,
                'current_value': update.current_value,
                'total_value': update.total_value,
                'message': update.message,
                'metadata': update.metadata,
                'timestamp': update.timestamp.isoformat() if update.timestamp else None
            }
            
            # Send via sync client
            await self.sync_client.send_progress_update(progress_data)
            
        except Exception as e:
            logger.error(f"Failed to send progress update to web: {e}")
    
    def get_overall_progress(self) -> Dict[str, Any]:
        """Calculate overall progress across all operations"""
        
        if not self.current_progress:
            return {"percentage": 0, "status": "not_started"}
        
        # Calculate weighted average if we have total values
        total_weight = 0
        weighted_sum = 0
        
        for progress_type, update in self.current_progress.items():
            if update.total_value and update.total_value > 0:
                weight = update.total_value
                progress = (update.current_value / update.total_value) * 100
                weighted_sum += progress * weight
                total_weight += weight
        
        if total_weight > 0:
            overall_percentage = weighted_sum / total_weight
        else:
            # Fall back to simple average
            percentages = []
            for update in self.current_progress.values():
                if update.total_value and update.total_value > 0:
                    percentages.append((update.current_value / update.total_value) * 100)
            
            overall_percentage = sum(percentages) / len(percentages) if percentages else 0
        
        # Determine status
        if overall_percentage == 0:
            status = "not_started"
        elif overall_percentage < 100:
            status = "in_progress"
        else:
            status = "completed"
        
        return {
            "percentage": round(overall_percentage, 2),
            "status": status,
            "active_operations": list(self.current_progress.keys()),
            "last_update": max(
                (update.timestamp for update in self.current_progress.values()),
                default=datetime.utcnow()
            ).isoformat()
        }
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of all progress updates"""
        
        summary = {
            "task_id": self.task_id,
            "total_updates": len(self.progress_history),
            "active_operations": len(self.current_progress),
            "overall_progress": self.get_overall_progress(),
            "operations": {}
        }
        
        # Add details for each operation type
        for progress_type, update in self.current_progress.items():
            summary["operations"][progress_type] = {
                "current_value": update.current_value,
                "total_value": update.total_value,
                "percentage": (update.current_value / update.total_value * 100) if update.total_value else None,
                "message": update.message,
                "last_update": update.timestamp.isoformat() if update.timestamp else None
            }
        
        return summary

class FileAnalysisProgress:
    """Specialized progress tracker for file analysis operations"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        self.files_processed = 0
        self.total_files = 0
        self.current_file = None
        
    def set_total_files(self, total: int):
        """Set the total number of files to process"""
        self.total_files = total
        self.tracker.update_progress(
            progress_type="file_analysis",
            current_value=0,
            total_value=total,
            message=f"Starting analysis of {total} files"
        )
    
    def start_file(self, file_path: str):
        """Mark the start of processing a file"""
        self.current_file = file_path
        self.tracker.update_progress(
            progress_type="file_analysis",
            current_value=self.files_processed,
            total_value=self.total_files,
            message=f"Analyzing {file_path}",
            metadata={"current_file": file_path}
        )
    
    def complete_file(self, file_path: str, analysis_result: Optional[Dict[str, Any]] = None):
        """Mark the completion of processing a file"""
        self.files_processed += 1
        self.current_file = None
        
        metadata = {"completed_file": file_path}
        if analysis_result:
            metadata["analysis_result"] = analysis_result
        
        self.tracker.update_progress(
            progress_type="file_analysis",
            current_value=self.files_processed,
            total_value=self.total_files,
            message=f"Completed {file_path} ({self.files_processed}/{self.total_files})",
            metadata=metadata
        )
    
    def add_error(self, file_path: str, error_message: str):
        """Add an error for a file"""
        self.tracker.update_progress(
            progress_type="file_analysis_errors",
            current_value=self.files_processed,
            total_value=self.total_files,
            message=f"Error processing {file_path}: {error_message}",
            metadata={"error_file": file_path, "error": error_message}
        )

class PatternDetectionProgress:
    """Specialized progress tracker for pattern detection operations"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        self.patterns_found = 0
        self.files_scanned = 0
        self.total_files = 0
        
    def set_total_files(self, total: int):
        """Set the total number of files to scan for patterns"""
        self.total_files = total
        self.tracker.update_progress(
            progress_type="pattern_detection",
            current_value=0,
            total_value=total,
            message=f"Starting pattern detection in {total} files"
        )
    
    def scan_file(self, file_path: str, patterns_found: int = 0):
        """Update progress for scanning a file"""
        self.files_scanned += 1
        self.patterns_found += patterns_found
        
        self.tracker.update_progress(
            progress_type="pattern_detection",
            current_value=self.files_scanned,
            total_value=self.total_files,
            message=f"Scanned {file_path} - {self.patterns_found} patterns found total",
            metadata={
                "current_file": file_path,
                "patterns_in_file": patterns_found,
                "total_patterns": self.patterns_found
            }
        )
    
    def complete_detection(self, total_patterns: int, unique_patterns: int):
        """Mark pattern detection as complete"""
        self.tracker.update_progress(
            progress_type="pattern_detection",
            current_value=self.total_files,
            total_value=self.total_files,
            message=f"Pattern detection complete - {total_patterns} patterns, {unique_patterns} unique",
            metadata={
                "total_patterns": total_patterns,
                "unique_patterns": unique_patterns,
                "files_scanned": self.files_scanned
            }
        )

class GitAnalysisProgress:
    """Specialized progress tracker for Git history analysis"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        self.commits_processed = 0
        self.total_commits = 0
        
    def set_total_commits(self, total: int):
        """Set the total number of commits to analyze"""
        self.total_commits = total
        self.tracker.update_progress(
            progress_type="git_analysis",
            current_value=0,
            total_value=total,
            message=f"Starting Git history analysis of {total} commits"
        )
    
    def process_commit(self, commit_hash: str, commit_message: str):
        """Update progress for processing a commit"""
        self.commits_processed += 1
        
        self.tracker.update_progress(
            progress_type="git_analysis",
            current_value=self.commits_processed,
            total_value=self.total_commits,
            message=f"Analyzed commit {commit_hash[:8]} - {commit_message[:50]}...",
            metadata={
                "commit_hash": commit_hash,
                "commit_message": commit_message
            }
        )
    
    def complete_analysis(self, analysis_summary: Dict[str, Any]):
        """Mark Git analysis as complete"""
        self.tracker.update_progress(
            progress_type="git_analysis",
            current_value=self.total_commits,
            total_value=self.total_commits,
            message=f"Git analysis complete - {self.commits_processed} commits analyzed",
            metadata=analysis_summary
        )

class SecurityScanProgress:
    """Specialized progress tracker for security scanning"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        self.files_scanned = 0
        self.total_files = 0
        self.vulnerabilities_found = 0
        
    def set_total_files(self, total: int):
        """Set the total number of files to scan"""
        self.total_files = total
        self.tracker.update_progress(
            progress_type="security_scan",
            current_value=0,
            total_value=total,
            message=f"Starting security scan of {total} files"
        )
    
    def scan_file(self, file_path: str, vulnerabilities: int = 0):
        """Update progress for scanning a file"""
        self.files_scanned += 1
        self.vulnerabilities_found += vulnerabilities
        
        self.tracker.update_progress(
            progress_type="security_scan",
            current_value=self.files_scanned,
            total_value=self.total_files,
            message=f"Scanned {file_path} - {self.vulnerabilities_found} vulnerabilities found",
            metadata={
                "current_file": file_path,
                "vulnerabilities_in_file": vulnerabilities,
                "total_vulnerabilities": self.vulnerabilities_found
            }
        )
    
    def complete_scan(self, scan_summary: Dict[str, Any]):
        """Mark security scan as complete"""
        self.tracker.update_progress(
            progress_type="security_scan",
            current_value=self.total_files,
            total_value=self.total_files,
            message=f"Security scan complete - {self.vulnerabilities_found} vulnerabilities found",
            metadata=scan_summary
        )

def create_progress_tracker(task_id: str, sync_client: Optional[object] = None) -> ProgressTracker:
    """Factory function to create a progress tracker"""
    return ProgressTracker(task_id, sync_client)

def create_file_analysis_progress(tracker: ProgressTracker) -> FileAnalysisProgress:
    """Factory function to create a file analysis progress tracker"""
    return FileAnalysisProgress(tracker)

def create_pattern_detection_progress(tracker: ProgressTracker) -> PatternDetectionProgress:
    """Factory function to create a pattern detection progress tracker"""
    return PatternDetectionProgress(tracker)

def create_git_analysis_progress(tracker: ProgressTracker) -> GitAnalysisProgress:
    """Factory function to create a Git analysis progress tracker"""
    return GitAnalysisProgress(tracker)

def create_security_scan_progress(tracker: ProgressTracker) -> SecurityScanProgress:
    """Factory function to create a security scan progress tracker"""
    return SecurityScanProgress(tracker)