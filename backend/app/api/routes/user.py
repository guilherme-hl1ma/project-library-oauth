from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_user_required
from app.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(path="/me")
def me(
    current_user: Annotated[User, Depends(get_user_required)],
):
    try:
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authorize client error: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
