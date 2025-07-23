"""
Real-time Progress Broadcasting Service for PRSNL
=================================================

Provides WebSocket-based real-time progress updates for long-running tasks.

Features:
- Task progress broadcasting to connected WebSocket clients
- Channel-based broadcasting for targeted updates
- Progress event structure with metadata
- Error handling and connection management
- Integration with all worker task types

This service resolves the TODO comments in worker tasks for WebSocket real-time progress updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict

from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class ProgressType(Enum):
    """Types of progress events"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    FILE_PROCESSING = "file_processing"
    MEDIA_PROCESSING = "media_processing"
    AI_PROCESSING = "ai_processing"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    CONVERSATION_INTELLIGENCE = "conversation_intelligence"
    CODEMIRROR_ANALYSIS = "codemirror_analysis"

@dataclass
class ProgressEvent:
    """Structured progress event for WebSocket broadcasting"""
    task_id: str
    progress_type: str
    current_value: int
    total_value: int
    message: str
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        
        # Set default channel based on task_id if not provided
        if self.channel is None:
            self.channel = f"task_{self.task_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string for WebSocket transmission"""
        return json.dumps(self.to_dict())

class RealtimeProgressService:
    """
    Service for broadcasting real-time progress updates via WebSocket.
    
    Integrates with the existing WebSocket manager to provide structured
    progress updates for all worker task types.
    """
    
    def __init__(self):
        self.websocket_manager = websocket_manager
        self.active_channels: Dict[str, Set[str]] = {}  # channel -> set of client_ids
        self.client_channels: Dict[str, Set[str]] = {}  # client_id -> set of channels
    
    async def subscribe_to_channel(self, client_id: str, channel: str):
        """Subscribe a client to a specific progress channel"""
        try:
            # Add client to channel
            if channel not in self.active_channels:
                self.active_channels[channel] = set()
            self.active_channels[channel].add(client_id)
            
            # Add channel to client's subscriptions
            if client_id not in self.client_channels:
                self.client_channels[client_id] = set()
            self.client_channels[client_id].add(channel)
            
            logger.debug(f"Client {client_id} subscribed to channel {channel}")
            
            # Send subscription confirmation
            await self.send_to_client(client_id, {
                "event_type": "channel_subscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to subscribe client {client_id} to channel {channel}: {e}")
    
    async def unsubscribe_from_channel(self, client_id: str, channel: str):
        """Unsubscribe a client from a specific channel"""
        try:
            # Remove client from channel
            if channel in self.active_channels:
                self.active_channels[channel].discard(client_id)
                if not self.active_channels[channel]:
                    del self.active_channels[channel]
            
            # Remove channel from client
            if client_id in self.client_channels:
                self.client_channels[client_id].discard(channel)
                if not self.client_channels[client_id]:
                    del self.client_channels[client_id]
            
            logger.debug(f"Client {client_id} unsubscribed from channel {channel}")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe client {client_id} from channel {channel}: {e}")
    
    async def client_disconnected(self, client_id: str):
        """Clean up when a client disconnects"""
        try:
            # Get all channels for this client
            channels = self.client_channels.get(client_id, set()).copy()
            
            # Unsubscribe from all channels
            for channel in channels:
                await self.unsubscribe_from_channel(client_id, channel)
            
            logger.debug(f"Cleaned up channels for disconnected client {client_id}")
            
        except Exception as e:
            logger.error(f"Failed to clean up channels for client {client_id}: {e}")
    
    async def send_progress_update(
        self,
        task_id: str,
        progress_type: str,
        current_value: int,
        total_value: int,
        message: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send a progress update via WebSocket to subscribed clients.
        
        This is the main function called by worker tasks to broadcast progress.
        """
        try:
            # Create progress event
            progress_event = ProgressEvent(
                task_id=task_id,
                progress_type=progress_type,
                current_value=current_value,
                total_value=total_value,
                message=message,
                entity_id=entity_id,
                user_id=user_id,
                channel=channel,
                metadata=metadata
            )
            
            # Calculate percentage
            percentage = (current_value / max(total_value, 1)) * 100
            
            # Enhance event with additional data
            enhanced_event = progress_event.to_dict()
            enhanced_event.update({
                "percentage": round(percentage, 2),
                "event_type": "progress_update",
                "is_complete": current_value >= total_value,
                "service": "realtime_progress"
            })
            
            # Send to specific channel if provided
            if progress_event.channel:
                await self.broadcast_to_channel(progress_event.channel, enhanced_event)
            
            # Also send to user-specific channel if user_id provided
            if user_id:
                user_channel = f"user_{user_id}"
                await self.broadcast_to_channel(user_channel, enhanced_event)
            
            # Log progress update
            logger.info(f"Progress update sent: {task_id} - {progress_type} - {current_value}/{total_value} ({percentage:.1f}%) - {message}")
            
        except Exception as e:
            logger.error(f"Failed to send progress update for task {task_id}: {e}")
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast a message to all clients subscribed to a channel"""
        try:
            if channel not in self.active_channels:
                logger.debug(f"No subscribers for channel {channel}")
                return
            
            clients = self.active_channels[channel].copy()
            message_json = json.dumps(message)
            
            # Send to all subscribed clients
            send_tasks = []
            for client_id in clients:
                send_tasks.append(self.send_to_client(client_id, message))
            
            # Execute all sends concurrently
            if send_tasks:
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                
                # Handle any failed sends
                failed_clients = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_client = list(clients)[i]
                        failed_clients.append(failed_client)
                        logger.warning(f"Failed to send to client {failed_client}: {result}")
                
                # Clean up failed clients
                for failed_client in failed_clients:
                    await self.client_disconnected(failed_client)
            
            logger.debug(f"Broadcasted to channel {channel}: {len(clients)} clients")
            
        except Exception as e:
            logger.error(f"Failed to broadcast to channel {channel}: {e}")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send a message to a specific client"""
        try:
            message_json = json.dumps(message)
            await self.websocket_manager.send_personal_message(message_json, client_id)
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            raise
    
    async def broadcast_task_started(
        self,
        task_id: str,
        task_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast that a task has started"""
        await self.send_progress_update(
            task_id=task_id,
            progress_type=ProgressType.TASK_STARTED.value,
            current_value=0,
            total_value=100,
            message=f"Started {task_type} task",
            entity_id=entity_id,
            user_id=user_id,
            metadata={**(metadata or {}), "task_type": task_type}
        )
    
    async def broadcast_task_completed(
        self,
        task_id: str,
        task_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast that a task has completed successfully"""
        await self.send_progress_update(
            task_id=task_id,
            progress_type=ProgressType.TASK_COMPLETED.value,
            current_value=100,
            total_value=100,
            message=f"Completed {task_type} task successfully",
            entity_id=entity_id,
            user_id=user_id,
            metadata={**(metadata or {}), "task_type": task_type}
        )
    
    async def broadcast_task_failed(
        self,
        task_id: str,
        task_type: str,
        error_message: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast that a task has failed"""
        await self.send_progress_update(
            task_id=task_id,
            progress_type=ProgressType.TASK_FAILED.value,
            current_value=0,
            total_value=100,
            message=f"Task {task_type} failed: {error_message}",
            entity_id=entity_id,
            user_id=user_id,
            metadata={**(metadata or {}), "task_type": task_type, "error": error_message}
        )
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get statistics about active channels and connections"""
        return {
            "active_channels": len(self.active_channels),
            "total_subscriptions": sum(len(clients) for clients in self.active_channels.values()),
            "unique_clients": len(self.client_channels),
            "channels": {
                channel: len(clients) 
                for channel, clients in self.active_channels.items()
            }
        }


# Create singleton instance
realtime_progress_service = RealtimeProgressService()


# Convenience functions for worker tasks
async def send_task_progress(
    task_id: str,
    progress_type: str,
    current_value: int,
    total_value: int,
    message: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Convenience function for worker tasks to send progress updates.
    
    This replaces the TODO comments in worker files.
    """
    await realtime_progress_service.send_progress_update(
        task_id=task_id,
        progress_type=progress_type,
        current_value=current_value,
        total_value=total_value,
        message=message,
        entity_id=entity_id,
        user_id=user_id,
        metadata=metadata
    )