"""
HTTP Client Health API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.http_client_factory import http_client_factory, ClientType

router = APIRouter()


class ClientRefreshRequest(BaseModel):
    """Request model for client refresh"""
    client_type: str


@router.get("/health", response_model=Dict[str, Any])
async def http_client_health():
    """
    Get health status of all HTTP clients
    """
    try:
        health_status = await http_client_factory.health_check()
        return {
            "status": "success",
            "health": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def http_client_statistics():
    """
    Get connection statistics for all HTTP clients
    """
    try:
        stats = await http_client_factory.get_connection_stats()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics failed: {str(e)}")


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_http_client(request: ClientRefreshRequest):
    """
    Refresh a specific HTTP client
    
    Args:
        request: Client refresh configuration
        
    Returns:
        Refresh results
    """
    try:
        # Validate client type
        try:
            client_type = ClientType(request.client_type)
        except ValueError:
            valid_types = [ct.value for ct in ClientType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid client type '{request.client_type}'. Valid types: {valid_types}"
            )
        
        # Refresh the client
        await http_client_factory.refresh_client(client_type)
        
        return {
            "status": "success",
            "message": f"Client '{request.client_type}' refreshed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Client refresh failed: {str(e)}")


@router.post("/close/{client_type}", response_model=Dict[str, Any])
async def close_http_client(client_type: str):
    """
    Close a specific HTTP client
    
    Args:
        client_type: Type of client to close
        
    Returns:
        Close results
    """
    try:
        # Validate client type
        try:
            client_type_enum = ClientType(client_type)
        except ValueError:
            valid_types = [ct.value for ct in ClientType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid client type '{client_type}'. Valid types: {valid_types}"
            )
        
        # Close the client
        await http_client_factory.close_client(client_type_enum)
        
        return {
            "status": "success",
            "message": f"Client '{client_type}' closed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Client close failed: {str(e)}")


@router.get("/types", response_model=Dict[str, Any])
async def get_client_types():
    """
    Get available HTTP client types
    """
    try:
        client_types = [
            {
                "type": ct.value,
                "description": {
                    ClientType.GITHUB: "GitHub API client with authentication",
                    ClientType.AZURE_OPENAI: "Azure OpenAI client for AI operations",
                    ClientType.GENERAL: "General purpose HTTP client",
                    ClientType.MEDIA_DOWNLOAD: "Media download client for large files",
                    ClientType.CRAWL: "Web crawling client with browser headers"
                }.get(ct, "HTTP client")
            }
            for ct in ClientType
        ]
        
        return {
            "status": "success",
            "client_types": client_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get client types: {str(e)}")


# Add to main router
def include_http_client_health_routes(main_router):
    """Include HTTP client health routes in main router"""
    main_router.include_router(
        router,
        prefix="/api/http-client",
        tags=["http_client_health"]
    )