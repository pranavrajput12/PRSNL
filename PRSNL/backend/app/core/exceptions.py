from fastapi import HTTPException, status
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None

class ItemNotFound(HTTPException):
    def __init__(self, item_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
            headers={"X-Error-Code": "ITEM_NOT_FOUND"}
        )

class InvalidInput(HTTPException):
    def __init__(self, message: str = "Invalid input provided"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            headers={"X-Error-Code": "INVALID_INPUT"}
        )

class ServiceUnavailable(HTTPException):
    def __init__(self, service_name: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} is currently unavailable",
            headers={"X-Error-Code": "SERVICE_UNAVAILABLE"}
        )

class InternalServerError(HTTPException):
    def __init__(self, message: str = "An unexpected error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            headers={"X-Error-Code": "INTERNAL_SERVER_ERROR"}
        )
