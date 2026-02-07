import os
from typing import Annotated
from fastapi import Depends, HTTPException, Request
import jwt

from app.core.database import SessionDep
from app.models.user import User

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


# =====================
# USER Session (token)
# Used by Auth Server internally during OAuth flow
# =====================

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


# =====================
# OAuth Access Token
# Used by Client applications to access protected resources
# =====================

def get_access_token_data(request: Request) -> dict | None:
    try:
        access_token = request.cookies.get("access_token")
        
        if not access_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.replace("Bearer ", "")
        
        if not access_token:
            return None

        token_data = jwt.decode(
            access_token,
            key=str(SECRET_JWT),
            algorithms=["HS256"],
            issuer=JWT_ISSUER
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
    return token_data


def get_access_token_required(
    token_data: Annotated[dict | None, Depends(get_access_token_data)],
) -> dict:
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def get_user_from_access_token(
    session: SessionDep,
    token_data: Annotated[dict, Depends(get_access_token_required)],
) -> User:
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
