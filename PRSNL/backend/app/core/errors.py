"""Standard error response formats and handlers"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ErrorCode:
    """Standard error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class ErrorDetail:
    """Error detail for field-specific errors"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

class StandardError(HTTPException):
    """Standard error with consistent format"""
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or []
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(status_code=status_code, detail=self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        error_dict = {
            "error": {
                "code": self.code,
                "message": self.message,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }
        
        if self.details:
            error_dict["error"]["details"] = [
                {"field": d.field, "message": d.message} 
                for d in self.details
            ]
        
        return error_dict

# Convenience error classes
class ValidationError(StandardError):
    """400 Validation Error"""
    def __init__(self, message: str = "Validation failed", details: Optional[List[ErrorDetail]] = None):
        super().__init__(
            status_code=400,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )

class NotFoundError(StandardError):
    """404 Not Found Error"""
    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            status_code=404,
            code=ErrorCode.NOT_FOUND,
            message=message
        )

class UnauthorizedError(StandardError):
    """401 Unauthorized Error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message=message
        )

class ForbiddenError(StandardError):
    """403 Forbidden Error"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=403,
            code=ErrorCode.FORBIDDEN,
            message=message
        )

class ConflictError(StandardError):
    """409 Conflict Error"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            status_code=409,
            code=ErrorCode.CONFLICT,
            message=message
        )

class RateLimitError(StandardError):
    """429 Rate Limited Error"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            code=ErrorCode.RATE_LIMITED,
            message=message
        )

class ServiceUnavailableError(StandardError):
    """503 Service Unavailable Error"""
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message
        )

async def standard_error_handler(request: Request, exc: StandardError) -> JSONResponse:
    """Handle StandardError exceptions"""
    # Get request ID from request state if available
    request_id = getattr(request.state, "request_id", exc.request_id)
    exc.request_id = request_id
    
    # Log the error
    logger.error(
        f"Error {exc.code}: {exc.message}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Log the error
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    # Don't expose internal errors in production
    message = "An internal error occurred"
    if hasattr(exc, "detail"):
        message = str(exc.detail)
    
    error = StandardError(
        status_code=500,
        code=ErrorCode.INTERNAL_ERROR,
        message=message,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error.to_dict()
    )

def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[List[Dict[str, str]]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standard error response"""
    error_details = []
    if details:
        error_details = [ErrorDetail(d["field"], d["message"]) for d in details]
    
    error = StandardError(
        status_code=status_code,
        code=code,
        message=message,
        details=error_details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error.to_dict()
    )