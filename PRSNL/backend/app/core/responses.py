"""Standard response formats and utilities"""
from typing import Any, Optional, List, Dict, Union
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel

class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    data: Any = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class PaginatedResponse(StandardResponse):
    """Standard paginated response format"""
    data: List[Any] = []
    meta: Dict[str, Any] = {
        "total": 0,
        "page": 1,
        "per_page": 20,
        "total_pages": 0,
        "has_next": False,
        "has_prev": False
    }

class CursorPaginatedResponse(StandardResponse):
    """Standard cursor-based paginated response"""
    data: List[Any] = []
    meta: Dict[str, Any] = {
        "next_cursor": None,
        "has_more": False,
        "count": 0
    }

def create_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standard successful response"""
    response = StandardResponse(
        success=True,
        data=data,
        message=message,
        meta=meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.dict(exclude_none=True)
    )

def create_paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 20,
    message: Optional[str] = None
) -> JSONResponse:
    """Create a standard paginated response"""
    total_pages = (total + per_page - 1) // per_page
    
    response = PaginatedResponse(
        data=data,
        message=message,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    )
    
    return JSONResponse(
        status_code=200,
        content=response.dict(exclude_none=True)
    )

def create_cursor_paginated_response(
    data: List[Any],
    next_cursor: Optional[str] = None,
    has_more: bool = False,
    message: Optional[str] = None
) -> JSONResponse:
    """Create a standard cursor-based paginated response"""
    response = CursorPaginatedResponse(
        data=data,
        message=message,
        meta={
            "next_cursor": next_cursor,
            "has_more": has_more,
            "count": len(data)
        }
    )
    
    return JSONResponse(
        status_code=200,
        content=response.dict(exclude_none=True)
    )

# Response models for OpenAPI documentation
class SuccessResponse(BaseModel):
    """Standard success response model"""
    success: bool = True
    message: str
    timestamp: str

class CreatedResponse(SuccessResponse):
    """Resource created response"""
    id: str
    
class UpdatedResponse(SuccessResponse):
    """Resource updated response"""
    id: str

class DeletedResponse(SuccessResponse):
    """Resource deleted response"""
    id: str

# Common response messages
class ResponseMessage:
    """Common response messages"""
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    SUCCESS = "Operation completed successfully"
    FOUND = "Resource found"
    NOT_FOUND = "Resource not found"
    INVALID_REQUEST = "Invalid request"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Access forbidden"