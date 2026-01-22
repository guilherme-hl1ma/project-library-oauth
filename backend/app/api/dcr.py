from typing import Annotated
from fastapi import Depends
from fastapi.routing import APIRouter

from app.api.dependencies.auth import get_user_jwt_auth
from app.models.user import User


router = APIRouter(prefix="/dcr", tags=["Dynamic Client Registration"])


@router.post("/register")
def register_client(current_user: Annotated[User, Depends(get_user_jwt_auth)]):
    return "teste"
