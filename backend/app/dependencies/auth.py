import os
from typing import Annotated
from fastapi import Depends, HTTPException, Request
import jwt

from app.core.database import SessionDep
from app.models.user import User

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


def get_current_user_or_none(session: SessionDep, request: Request) -> User | None:
    try:
        token = request.cookies.get("token") or request.headers.get("X-Token")
        if not token:
            return None

        token_decoded = jwt.decode(
            token, key=str(SECRET_JWT), algorithms=["HS256"], issuer=JWT_ISSUER
        )
        user_id = token_decoded.get("sub")
        return session.get(User, user_id)
    except Exception:
        return None


def get_user_required(
    user: Annotated[User | None, Depends(get_current_user_or_none)],
) -> User:
    if not user:
        raise HTTPException(
            status_code=401, detail="Authentication required for API access"
        )
    return user
