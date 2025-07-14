"""
Real-time sync client for PRSNL CodeMirror CLI.

Provides WebSocket-based real-time synchronization with the PRSNL backend.
"""

import asyncio
import json
import logging
import platform
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from urllib.parse import urlparse, urlunparse

import aiohttp
from aiohttp import ClientWebSocketResponse
from rich.console import Console

logger = logging.getLogger(__name__)


class RealtimeSyncClient:
    """
    Real-time sync client for CLI to Web synchronization.
    
    Features:
    - WebSocket connection management
    - Automatic reconnection with exponential backoff
    - Progress streaming
    - Bi-directional communication
    - Event queuing during disconnection
    """
    
    def __init__(self, config, console: Console):
        self.config = config
        self.console = console
        self.websocket: Optional[ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.machine_id = self._get_machine_id()
        self.connected = False
        self.reconnect_attempts = 0
        self.event_queue: List[Dict[str, Any]] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._heartbeat_task = None
        self._receive_task = None
        
    def _get_machine_id(self) -> str:
        """Generate a stable machine ID."""
        # Try to get from config first
        if hasattr(self.config, 'machine_id') and self.config.machine_id:
            return self.config.machine_id
        
        # Generate based on platform info
        machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        machine_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_info))
        
        # Save to config for future use
        self.config.machine_id = machine_id
        self.config.save()
        
        return machine_id
    
    def _get_websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL."""
        parsed = urlparse(self.config.prsnl_url)
        
        # Convert scheme
        if parsed.scheme == 'https':
            ws_scheme = 'wss'
        else:
            ws_scheme = 'ws'
        
        # Build WebSocket URL
        ws_url = urlunparse((
            ws_scheme,
            parsed.netloc,
            '/api/codemirror/ws/cli-sync',
            '',
            f'api_key={self.config.prsnl_token}&machine_id={self.machine_id}',
            ''
        ))
        
        return ws_url
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to PRSNL backend."""
        if self.connected:
            return True
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            ws_url = self._get_websocket_url()
            
            self.console.print("[cyan]Connecting to PRSNL real-time sync...[/cyan]")
            
            self.websocket = await self.session.ws_connect(
                ws_url,
                heartbeat=30,
                timeout=aiohttp.ClientTimeout(total=60)
            )
            
            # Wait for welcome message
            msg = await self.websocket.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get('type') == 'connected':
                    self.connected = True
                    self.reconnect_attempts = 0
                    self.console.print("[green]✅ Connected to PRSNL real-time sync[/green]")
                    
                    # Start background tasks
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    self._receive_task = asyncio.create_task(self._receive_loop())
                    
                    # Send queued events
                    await self._flush_event_queue()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.console.print(f"[red]Failed to connect to real-time sync: {e}[/red]")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        self.connected = False
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Close session
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep connection alive."""
        while self.connected:
            try:
                await asyncio.sleep(30)
                await self.send_event({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break
    
    async def _receive_loop(self):
        """Receive messages from WebSocket."""
        while self.connected:
            try:
                msg = await self.websocket.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                    
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    logger.warning("WebSocket closed or error")
                    break
                    
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break
        
        # Trigger reconnection
        self.connected = False
        asyncio.create_task(self._reconnect())
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        message_type = data.get('type')
        
        if message_type == 'heartbeat_ack':
            # Heartbeat acknowledged
            pass
            
        elif message_type == 'command':
            # Remote command execution (future feature)
            await self._handle_remote_command(data)
            
        else:
            # Trigger event handlers
            handlers = self.event_handlers.get(message_type, [])
            for handler in handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
    
    async def _handle_remote_command(self, data: Dict[str, Any]):
        """Handle remote command execution requests."""
        command = data.get('command')
        command_id = data.get('command_id')
        
        # Send acknowledgment
        await self.send_event({
            "type": "command_ack",
            "command_id": command_id,
            "status": "received"
        })
        
        # Future: Implement command execution with proper security
        logger.info(f"Received remote command: {command}")
    
    async def _reconnect(self):
        """Reconnect with exponential backoff."""
        self.reconnect_attempts += 1
        
        # Calculate backoff time (max 60 seconds)
        backoff = min(60, (2 ** self.reconnect_attempts) * 2)
        
        self.console.print(f"[yellow]Reconnecting in {backoff} seconds...[/yellow]")
        await asyncio.sleep(backoff)
        
        # Try to reconnect
        success = await self.connect()
        if not success and self.reconnect_attempts < 10:
            # Try again
            asyncio.create_task(self._reconnect())
    
    async def _flush_event_queue(self):
        """Send queued events after reconnection."""
        if not self.event_queue:
            return
        
        self.console.print(f"[cyan]Sending {len(self.event_queue)} queued events...[/cyan]")
        
        for event in self.event_queue[:]:  # Copy list to avoid modification during iteration
            try:
                await self._send_raw(event)
                self.event_queue.remove(event)
            except Exception as e:
                logger.error(f"Failed to send queued event: {e}")
                break
    
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to WebSocket or queue if disconnected."""
        if not self.connected:
            # Queue event for later
            self.event_queue.append(event)
            return False
        
        try:
            return await self._send_raw(event)
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
            self.event_queue.append(event)
            return False
    
    async def _send_raw(self, event: Dict[str, Any]) -> bool:
        """Send raw event to WebSocket."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send_json(event)
            return True
        return False
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def send_analysis_progress(self, analysis_id: str, progress: int, 
                                   stage: str, details: Dict[str, Any] = None):
        """Send analysis progress update."""
        event = {
            "type": "analysis_progress",
            "analysis_id": analysis_id,
            "progress": progress,
            "stage": stage,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_event(event)
    
    async def send_analysis_complete(self, analysis_id: str, results: Dict[str, Any]):
        """Send analysis completion notification."""
        event = {
            "type": "analysis_complete",
            "analysis_id": analysis_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_event(event)
    
    async def send_insight_detected(self, analysis_id: str, insight: Dict[str, Any]):
        """Send real-time insight detection."""
        event = {
            "type": "insight_detected",
            "analysis_id": analysis_id,
            "insight": insight,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_event(event)


class RealtimeProgressReporter:
    """
    Progress reporter that sends real-time updates via WebSocket.
    
    Integrates with the analysis pipeline to provide live updates.
    """
    
    def __init__(self, sync_client: RealtimeSyncClient, analysis_id: str):
        self.sync_client = sync_client
        self.analysis_id = analysis_id
        self.current_stage = "initializing"
        self.current_progress = 0
        
    async def update(self, progress: int, stage: str, details: Dict[str, Any] = None):
        """Update progress and send via WebSocket."""
        self.current_progress = progress
        self.current_stage = stage
        
        await self.sync_client.send_analysis_progress(
            self.analysis_id,
            progress,
            stage,
            details
        )
    
    async def stage_started(self, stage: str):
        """Mark stage as started."""
        await self.update(self.current_progress, stage, {"status": "started"})
    
    async def stage_completed(self, stage: str):
        """Mark stage as completed."""
        await self.update(self.current_progress, stage, {"status": "completed"})
    
    async def insight_found(self, insight: Dict[str, Any]):
        """Report insight found during analysis."""
        await self.sync_client.send_insight_detected(self.analysis_id, insight)
    
    async def complete(self, results: Dict[str, Any]):
        """Mark analysis as complete."""
        await self.sync_client.send_analysis_complete(self.analysis_id, results)