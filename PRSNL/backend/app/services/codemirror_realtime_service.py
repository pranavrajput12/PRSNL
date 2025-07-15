"""
CodeMirror Real-time Sync Service

Enterprise-grade real-time synchronization between CLI and Web interfaces
using WebSockets, DragonflyDB pub/sub, and event-driven architecture.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Callable
from uuid import UUID, uuid4
import hashlib

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.db.database import get_db_pool
from app.config import settings
from app.services.dragonflydb_service import dragonflydb_service
from app.services.http_client_factory import http_client_factory, ClientType

logger = logging.getLogger(__name__)


class SyncEvent(BaseModel):
    """Real-time sync event model."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str  # analysis_started, analysis_progress, analysis_completed, insight_added, pattern_detected
    source: str  # cli, web
    user_id: str
    repo_id: Optional[str] = None
    analysis_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]
    checksum: Optional[str] = None  # For data integrity
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for data integrity."""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


class ConnectionManager:
    """Manages WebSocket connections for real-time sync."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> set of connections
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.subscription_channels: Dict[str, Set[str]] = {}  # connection_id -> set of channels
        
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Dict[str, Any] = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc),
            "connection_id": str(uuid4()),
            **(metadata or {})
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            connection_id = metadata["connection_id"]
            
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Clean up subscriptions
            if connection_id in self.subscription_channels:
                del self.subscription_channels[connection_id]
            
            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a specific channel."""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            connection_id = metadata["connection_id"]
            if connection_id not in self.subscription_channels:
                self.subscription_channels[connection_id] = set()
            self.subscription_channels[connection_id].add(channel)
            
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast message to all connections subscribed to a channel."""
        for connection_id, channels in self.subscription_channels.items():
            if channel in channels:
                # Find websocket by connection_id
                for ws, metadata in self.connection_metadata.items():
                    if metadata["connection_id"] == connection_id:
                        try:
                            await ws.send_json(message)
                        except Exception as e:
                            logger.error(f"Error broadcasting to channel {channel}: {e}")


class CodeMirrorRealtimeService:
    """
    Enterprise-grade real-time synchronization service for CodeMirror.
    
    Features:
    - WebSocket-based real-time communication
    - DragonflyDB pub/sub for distributed events
    - Event sourcing for audit trail
    - Conflict resolution for concurrent updates
    - Automatic reconnection and state recovery
    """
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.sync_state_cache: Dict[str, Dict[str, Any]] = {}  # analysis_id -> latest state
        self._pubsub_task = None
        
    async def start(self):
        """Start the real-time service."""
        # Start DragonflyDB pub/sub listener
        self._pubsub_task = asyncio.create_task(self._pubsub_listener())
        logger.info("CodeMirror real-time service started")
        
    async def stop(self):
        """Stop the real-time service."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
        logger.info("CodeMirror real-time service stopped")
    
    async def _pubsub_listener(self):
        """Listen for events from DragonflyDB pub/sub."""
        channel = "codemirror:events"
        
        while True:
            try:
                # Subscribe to DragonflyDB channel
                async for message in dragonflydb_service.subscribe(channel):
                    try:
                        event_data = json.loads(message)
                        event = SyncEvent(**event_data)
                        await self._handle_pubsub_event(event)
                    except Exception as e:
                        logger.error(f"Error processing pub/sub message: {e}")
                        
            except Exception as e:
                logger.error(f"Pub/sub listener error: {e}")
                await asyncio.sleep(5)  # Reconnect after 5 seconds
    
    async def _handle_pubsub_event(self, event: SyncEvent):
        """Handle event received from pub/sub."""
        # Update local cache
        if event.analysis_id:
            if event.analysis_id not in self.sync_state_cache:
                self.sync_state_cache[event.analysis_id] = {}
            
            self.sync_state_cache[event.analysis_id].update({
                "last_event": event.event_type,
                "last_update": event.timestamp,
                "source": event.source,
                **event.data
            })
        
        # Broadcast to relevant WebSocket connections
        channel = f"analysis:{event.analysis_id}" if event.analysis_id else f"user:{event.user_id}"
        await self.connection_manager.broadcast_to_channel(channel, event.dict())
        
        # Trigger event handlers
        await self._trigger_event_handlers(event)
    
    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket connection for real-time sync."""
        await self.connection_manager.connect(websocket, user_id)
        
        try:
            # Send initial state
            await self._send_initial_state(websocket, user_id)
            
            while True:
                # Receive messages from client
                data = await websocket.receive_json()
                await self._handle_client_message(websocket, user_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connection_manager.disconnect(websocket)
    
    async def _send_initial_state(self, websocket: WebSocket, user_id: str):
        """Send initial sync state to newly connected client."""
        try:
            # Get active analyses for user
            pool = await get_db_pool()
            async with pool.acquire() as db:
                active_analyses = await db.fetch("""
                    SELECT 
                        ca.id,
                        ca.analysis_type,
                        ca.created_at,
                        pj.status,
                        pj.progress_percentage,
                        pj.current_stage
                    FROM codemirror_analyses ca
                    LEFT JOIN processing_jobs pj ON ca.job_id = pj.job_id
                    JOIN github_repos gr ON ca.repo_id = gr.id
                    JOIN github_accounts ga ON gr.account_id = ga.id
                    WHERE ga.user_id = $1 
                    AND pj.status IN ('pending', 'processing')
                    ORDER BY ca.created_at DESC
                    LIMIT 10
                """, UUID(user_id))
                
                initial_state = {
                    "type": "initial_state",
                    "analyses": [dict(a) for a in active_analyses],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await websocket.send_json(initial_state)
                
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
    
    async def _handle_client_message(self, websocket: WebSocket, user_id: str, data: Dict[str, Any]):
        """Handle messages from WebSocket clients."""
        message_type = data.get("type")
        
        if message_type == "subscribe":
            # Subscribe to specific channels
            channels = data.get("channels", [])
            for channel in channels:
                await self.connection_manager.subscribe_to_channel(websocket, channel)
                
        elif message_type == "sync_request":
            # Handle sync request from CLI
            await self._handle_sync_request(user_id, data)
            
        elif message_type == "heartbeat":
            # Respond to heartbeat
            await websocket.send_json({"type": "heartbeat_ack", "timestamp": datetime.now(timezone.utc).isoformat()})
    
    async def _handle_sync_request(self, user_id: str, data: Dict[str, Any]):
        """Handle sync request from CLI or web client."""
        sync_type = data.get("sync_type")
        
        if sync_type == "analysis_update":
            # Validate and process analysis update
            analysis_id = data.get("analysis_id")
            update_data = data.get("data", {})
            
            if analysis_id and update_data:
                event = SyncEvent(
                    event_type="analysis_progress",
                    source=data.get("source", "unknown"),
                    user_id=user_id,
                    analysis_id=analysis_id,
                    data=update_data
                )
                
                # Publish to DragonflyDB for distribution
                await self.publish_event(event)
    
    async def publish_event(self, event: SyncEvent):
        """Publish event to DragonflyDB for distribution."""
        # Calculate checksum for data integrity
        event.checksum = event.calculate_checksum()
        
        # Store event in database for audit trail
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                INSERT INTO codemirror_sync_events (
                    event_id, event_type, source, user_id,
                    repo_id, analysis_id, timestamp, data, checksum
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                UUID(event.event_id), event.event_type, event.source, UUID(event.user_id),
                UUID(event.repo_id) if event.repo_id else None,
                UUID(event.analysis_id) if event.analysis_id else None,
                event.timestamp, event.data, event.checksum
            )
        
        # Publish to DragonflyDB
        channel = "codemirror:events"
        await dragonflydb_service.publish(channel, event.json())
        
        # Also handle locally for immediate response
        await self._handle_pubsub_event(event)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _trigger_event_handlers(self, event: SyncEvent):
        """Trigger registered event handlers."""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
    
    async def notify_analysis_started(self, user_id: str, repo_id: str, analysis_id: str, 
                                     analysis_type: str = "web", metadata: Dict[str, Any] = None):
        """Notify all connected clients that an analysis has started."""
        event = SyncEvent(
            event_type="analysis_started",
            source=analysis_type,
            user_id=user_id,
            repo_id=repo_id,
            analysis_id=analysis_id,
            data={
                "status": "started",
                "metadata": metadata or {},
                "start_time": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await self.publish_event(event)
    
    async def notify_analysis_progress(self, user_id: str, analysis_id: str, 
                                      progress: int, stage: str, details: Dict[str, Any] = None):
        """Notify progress updates during analysis."""
        event = SyncEvent(
            event_type="analysis_progress",
            source="system",
            user_id=user_id,
            analysis_id=analysis_id,
            data={
                "progress": progress,
                "stage": stage,
                "details": details or {},
                "update_time": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await self.publish_event(event)
    
    async def notify_insight_detected(self, user_id: str, analysis_id: str, 
                                     insight: Dict[str, Any], source: str = "system"):
        """Notify when a new insight is detected."""
        event = SyncEvent(
            event_type="insight_added",
            source=source,
            user_id=user_id,
            analysis_id=analysis_id,
            data={
                "insight": insight,
                "detected_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await self.publish_event(event)
    
    async def get_sync_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get current sync state for an analysis."""
        return self.sync_state_cache.get(analysis_id)
    
    async def resolve_conflicts(self, analysis_id: str, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts when multiple sources update the same analysis.
        
        Uses timestamp-based last-write-wins strategy with checksum validation.
        """
        # Sort updates by timestamp
        sorted_updates = sorted(updates, key=lambda x: x.get("timestamp", ""))
        
        # Apply updates in order
        resolved_state = {}
        for update in sorted_updates:
            # Verify checksum if present
            if "checksum" in update:
                calculated = hashlib.sha256(
                    json.dumps(update.get("data", {}), sort_keys=True).encode()
                ).hexdigest()[:16]
                
                if calculated != update["checksum"]:
                    logger.warning(f"Checksum mismatch for update in analysis {analysis_id}")
                    continue
            
            # Apply update
            resolved_state.update(update.get("data", {}))
            resolved_state["last_update"] = update.get("timestamp")
            resolved_state["last_source"] = update.get("source")
        
        return resolved_state
    
    async def _make_http_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make HTTP request using centralized client factory"""
        try:
            async with http_client_factory.client_session(ClientType.GENERAL) as client:
                if method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                elif method.upper() == "PUT":
                    response = await client.put(url, **kwargs)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return response.json() if response.content else {}
                
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {"error": str(e)}


# Create singleton instance
realtime_service = CodeMirrorRealtimeService()