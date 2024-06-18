from typing import Any

from fastapi import HTTPException, status


class BadRequestError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "Invalid request body"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class UnauthorizedError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "Invalid authentication credentials"
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class NotFoundError(HTTPException):
    def __init__(self, message: Any) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class ServerError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "The server encountered an error while processing the request."
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
