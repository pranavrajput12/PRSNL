"""
CodeMirror WebSocket API

Enterprise-grade WebSocket endpoints for real-time synchronization
between CLI and Web interfaces.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.auth import get_current_user_ws, verify_token
from app.services.codemirror_realtime_service import realtime_service
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/codemirror/ws", tags=["codemirror-websocket"])

# Security for WebSocket connections
security = HTTPBearer(auto_error=False)


@router.websocket("/sync")
async def websocket_sync(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    analysis_id: Optional[str] = Query(None),
    source: str = Query("web")
):
    """
    WebSocket endpoint for real-time CodeMirror synchronization.
    
    Supports both token-based auth (for web) and API key auth (for CLI).
    
    Query parameters:
    - token: JWT token or API key for authentication
    - analysis_id: Optional specific analysis to subscribe to
    - source: Client source (web, cli, vscode, etc.)
    """
    user_id = None
    
    try:
        # Authenticate the connection
        if token:
            # Try JWT first (web clients)
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
            except:
                # Try API key (CLI clients)
                pool = await get_db_pool()
                async with pool.acquire() as db:
                    api_key_record = await db.fetchrow("""
                        SELECT user_id FROM api_keys 
                        WHERE key_hash = crypt($1, key_hash) 
                        AND is_active = true
                    """, token)
                    
                    if api_key_record:
                        user_id = str(api_key_record['user_id'])
        
        # For development - allow unauthenticated connections
        if not user_id:
            user_id = "anonymous-dev"  # Default user for development
            logger.warning("Allowing unauthenticated WebSocket connection for development")
        
        # Set up connection metadata
        metadata = {
            "source": source,
            "analysis_id": analysis_id,
            "capabilities": ["sync", "progress", "insights"]
        }
        
        # Handle the WebSocket connection
        await realtime_service.handle_websocket(websocket, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/analysis/{analysis_id}")
async def websocket_analysis_updates(
    websocket: WebSocket,
    analysis_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for subscribing to specific analysis updates.
    
    Provides real-time updates for:
    - Analysis progress
    - Detected patterns
    - Generated insights
    - Security findings
    - Completion status
    """
    user_id = None
    
    try:
        # Authenticate
        if token:
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
            except:
                await websocket.close(code=1008, reason="Authentication failed")
                return
        else:
            await websocket.close(code=1008, reason="Token required")
            return
        
        # Verify user has access to this analysis
        pool = await get_db_pool()
        async with pool.acquire() as db:
            has_access = await db.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM codemirror_analyses ca
                    JOIN github_repos gr ON ca.repo_id = gr.id
                    JOIN github_accounts ga ON gr.account_id = ga.id
                    WHERE ca.id = $1 AND ga.user_id = $2
                )
            """, UUID(analysis_id), UUID(user_id))
            
            if not has_access:
                await websocket.close(code=1008, reason="Access denied")
                return
        
        # Connect and subscribe to analysis channel
        await realtime_service.connection_manager.connect(websocket, user_id)
        await realtime_service.connection_manager.subscribe_to_channel(
            websocket, f"analysis:{analysis_id}"
        )
        
        # Send current analysis state
        analysis_state = await realtime_service.get_sync_state(analysis_id)
        if analysis_state:
            await websocket.send_json({
                "type": "current_state",
                "analysis_id": analysis_id,
                "state": analysis_state
            })
        
        # Keep connection alive
        while True:
            # Wait for messages (heartbeat, etc.)
            data = await websocket.receive_json()
            
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
                
    except WebSocketDisconnect:
        logger.info(f"Analysis WebSocket disconnected for {analysis_id}")
    except Exception as e:
        logger.error(f"Analysis WebSocket error: {e}")
    finally:
        realtime_service.connection_manager.disconnect(websocket)


@router.websocket("/cli-sync")
async def websocket_cli_sync(
    websocket: WebSocket,
    api_key: str = Query(...),
    machine_id: Optional[str] = Query(None)
):
    """
    Dedicated WebSocket endpoint for CLI real-time sync.
    
    Features:
    - Bi-directional sync between CLI and web
    - Progress streaming from CLI to web
    - Command execution from web to CLI
    - Automatic reconnection support
    """
    user_id = None
    
    try:
        # Authenticate with API key
        pool = await get_db_pool()
        async with pool.acquire() as db:
            api_key_record = await db.fetchrow("""
                SELECT user_id, name FROM api_keys 
                WHERE key_hash = crypt($1, key_hash) 
                AND is_active = true
            """, api_key)
            
            if not api_key_record:
                await websocket.close(code=1008, reason="Invalid API key")
                return
            
            user_id = str(api_key_record['user_id'])
            
            # Log CLI connection
            await db.execute("""
                INSERT INTO codemirror_cli_connections (
                    user_id, machine_id, api_key_name, connected_at
                ) VALUES ($1, $2, $3, NOW())
            """, api_key_record['user_id'], machine_id, api_key_record['name'])
        
        # Set up CLI-specific metadata
        metadata = {
            "source": "cli",
            "machine_id": machine_id,
            "capabilities": ["sync", "analysis", "upload", "command"]
        }
        
        await realtime_service.connection_manager.connect(websocket, user_id, metadata)
        
        # Subscribe to user's command channel
        await realtime_service.connection_manager.subscribe_to_channel(
            websocket, f"cli_commands:{user_id}"
        )
        
        # Send welcome message with capabilities
        await websocket.send_json({
            "type": "connected",
            "message": "CLI connected to PRSNL real-time sync",
            "capabilities": {
                "real_time_progress": True,
                "bi_directional_sync": True,
                "remote_commands": True,
                "auto_reconnect": True
            }
        })
        
        # Handle CLI messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "analysis_progress":
                # Forward progress to web clients
                await realtime_service.notify_analysis_progress(
                    user_id=user_id,
                    analysis_id=data.get("analysis_id"),
                    progress=data.get("progress", 0),
                    stage=data.get("stage", "unknown"),
                    details=data.get("details", {})
                )
                
            elif message_type == "analysis_complete":
                # Handle analysis completion
                await _handle_cli_analysis_complete(user_id, data)
                
            elif message_type == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
                
    except WebSocketDisconnect:
        logger.info(f"CLI WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"CLI WebSocket error: {e}")
    finally:
        realtime_service.connection_manager.disconnect(websocket)
        
        # Log disconnection
        if user_id and machine_id:
            try:
                pool = await get_db_pool()
                async with pool.acquire() as db:
                    await db.execute("""
                        UPDATE codemirror_cli_connections 
                        SET disconnected_at = NOW() 
                        WHERE user_id = $1 AND machine_id = $2 
                        AND disconnected_at IS NULL
                    """, UUID(user_id), machine_id)
            except:
                pass


async def _handle_cli_analysis_complete(user_id: str, data: Dict[str, Any]):
    """Handle analysis completion from CLI."""
    analysis_id = data.get("analysis_id")
    results = data.get("results", {})
    
    if not analysis_id:
        return
    
    try:
        # Update analysis in database
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE codemirror_analyses
                SET 
                    results = results || $2,
                    analysis_completed_at = NOW()
                WHERE id = $1
            """, UUID(analysis_id), results)
        
        # Notify all connected clients
        event = {
            "event_type": "analysis_completed",
            "source": "cli",
            "user_id": user_id,
            "analysis_id": analysis_id,
            "data": {
                "status": "completed",
                "summary": results.get("summary", {}),
                "insights_count": len(results.get("insights", [])),
                "patterns_count": len(results.get("patterns", []))
            }
        }
        
        await realtime_service.publish_event(event)
        
    except Exception as e:
        logger.error(f"Error handling CLI analysis completion: {e}")