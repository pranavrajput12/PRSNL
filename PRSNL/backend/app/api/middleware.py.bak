import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ..core.exceptions import ErrorResponse, InternalServerError

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request ID: {request.state.request_id} - Method: {request.method} - Path: {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "N/A")
            logger.exception(f"Unhandled exception for Request ID: {request_id}", exc_info=exc)
            # Return a generic 500 error for unhandled exceptions
            error_response = InternalServerError()
            return JSONResponse(
                status_code=error_response.status_code,
                content=ErrorResponse(detail=error_response.detail, code="INTERNAL_SERVER_ERROR").model_dump()
            )
