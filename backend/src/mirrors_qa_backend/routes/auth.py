from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/authenticate")
def authenticate_user() -> Response:
    return JSONResponse(content={"token": "token"}, status_code=status.HTTP_200_OK)
