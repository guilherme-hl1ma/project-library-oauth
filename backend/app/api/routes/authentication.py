import os
import secrets
import traceback
from typing import Annotated
from fastapi.responses import JSONResponse
from sqlmodel import select
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import SessionDep
from app.core.bcrypt_encrypter import hash_text, verify_text
from app.core.redis_instance import RedisSingleton
from app.dependencies.auth import (
    get_user_required,
    get_user_from_access_token,
)
from app.models.user import UserRole, User
from app.schemas.user.user import UserLogin, UserRegistration
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

redis_client = RedisSingleton().getInstance()

SESSION_TTL = 60 * 60 * 24  # 24 hours


def _create_session(user: User) -> str:
    """Create a session in Redis and return the session ID."""
    session_id = secrets.token_urlsafe(32)
    session_data = f"{user.id}"
    redis_client.set(
        name=f"session:{session_id}",
        value=session_data,
        ex=SESSION_TTL,
    )
    return session_id


@router.post("/signup")
def signup_jwt(user: UserRegistration, session: SessionDep):
    try:
        user_db: User | None = session.exec(
            select(User).where(User.email == user.email)
        ).first()
        if user_db:
            raise HTTPException(
                status_code=409,
                detail="E-mail already exists. Try again using another one.",
            )

        user_id = str(uuid.uuid4())
        new_user: User = User(
            id=user_id,
            email=user.email,
            password=hash_text(user.password),
            role=UserRole.USER,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        session_id = _create_session(new_user)

        response = JSONResponse(
            status_code=200,
            content={"message": "User created successfully"},
        )
        response.set_cookie(
            key="token",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=SESSION_TTL,
        )

        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except TypeError as e:
        print("[signup - session] TypeError:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
    except Exception as e:
        print("[signup - session] Error:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.post("/login")
def login(user: UserLogin, session: SessionDep):
    try:
        user_db: User | None = session.exec(
            select(User).where(User.email == user.email)
        ).first()

        if user_db is None:
            raise HTTPException(
                status_code=404,
                detail="Invalid user. Try again.",
            )

        is_pwd_correct = verify_text(
            plain_text=user.password, hashed_text=user_db.password
        )

        if is_pwd_correct != True:
            raise HTTPException(
                status_code=404,
                detail="Invalid user. Try again.",
            )

        session_id = _create_session(user_db)

        response = JSONResponse(
            status_code=200,
            content={"message": "Login successful"},
        )
        response.set_cookie(
            key="token",
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=SESSION_TTL,
        )

        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        print("[auth - login] Error:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.get("/me")
def me(
    current_user: Annotated[User, Depends(get_user_required)],
):
    """
    Auth Server session endpoint.
    Uses the 'token' cookie (opaque session ID in Redis) to identify the user.
    This is for the Auth Server's own use (e.g., consent screen, auth-frontend).
    """
    try:
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth me error: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.get("/userinfo")
def userinfo(
    current_user: Annotated[User, Depends(get_user_from_access_token)],
):
    """
    OAuth2/OIDC UserInfo endpoint.
    Uses the 'access_token' (OAuth token) to return user information.
    """
    try:
        return {
            "sub": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Userinfo error: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.post("/logout")
def logout(request=None):
    response = JSONResponse(
        status_code=200, content={"message": "Logged out successfully"}
    )

    # Invalidate the session in Redis
    if request:
        session_id = request.cookies.get("token")
        if session_id:
            redis_client.delete(f"session:{session_id}")

    response.delete_cookie(key="token", samesite="lax")

    return response


@router.post("/forgot-password")
def forgot_password(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    print(f"Password reset requested for: {email}")
    return {"message": "If this email is registered, a reset link has been sent."}
