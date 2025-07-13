import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        endpoint = request.url.path
        metrics_service.record_api_latency(endpoint, process_time)
        logger.debug(f"PerformanceMiddleware: {endpoint} took {process_time:.4f}s")
        
        return response
