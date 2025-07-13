import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Configure a logger for API response times
api_logger = logging.getLogger("api_response_time")
api_logger.setLevel(logging.INFO)

# Create a file handler for API response times
file_handler = logging.FileHandler("logs/api_response_times.log")
formatter = logging.Formatter("{'timestamp': '%(asctime)s', 'level': '%(levelname)s', 'message': '%(message)s'}")
file_handler.setFormatter(formatter)
api_logger.addHandler(file_handler)

class APIResponseTimeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        api_logger.info(
            f"{{'endpoint': '{request.url.path}', 'method': '{request.method}', 'status_code': {response.status_code}, 'response_time_ms': {process_time * 1000:.2f}}}"
        )
        return response
