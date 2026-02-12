from datetime import datetime, timedelta, timezone
import os
import uuid
import traceback
from typing import Annotated
from fastapi.responses import JSONResponse
from sqlmodel import select
import jwt
from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.database import SessionDep
from app.core.bcrypt_encrypter import hash_text, verify_text
from app.dependencies.auth import (
    get_user_required,
    get_user_from_access_token,
)
from app.models.user import UserRole, User
from app.schemas.user.user import UserLogin, UserRegistration

router = APIRouter(prefix="/auth", tags=["JWT Authentication"])

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


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

        issued_time = datetime.now(timezone.utc).timestamp()
        expiration_time = (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()
        payload = {
            "iss": JWT_ISSUER,
            "sub": user_id,
            "iat": issued_time,
            "exp": expiration_time,
            "email": user.email,
            "role": UserRole.USER.value,
        }

        token = jwt.encode(
            payload=payload,
            algorithm="HS256",
            key=str(SECRET_JWT),
        )

        response = JSONResponse(status_code=200, content=token)
        response.set_cookie(
            key="token",
            value=str(token),
            httponly=True,
            # secure=True,
            samesite="lax",
            max_age=60 * 60 * 24,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except TypeError as e:
        print("[signup_jwt - signup_session] TypeError:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
    except Exception as e:
        print("[signup_jwt - signup_session] Error:", str(e))
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

        issued_time = datetime.now(timezone.utc).timestamp()
        expiration_time = (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        payload = {
            "iss": JWT_ISSUER,
            "sub": user_db.id,
            "iat": issued_time,
            "exp": expiration_time,
            "email": user.email,
            "role": UserRole.USER.value,
        }

        if SECRET_JWT is None:
            raise HTTPException(status_code=500, detail="Internal server error.")

        token = jwt.encode(
            payload=payload,
            algorithm="HS256",
            key=SECRET_JWT,
        )

        response = JSONResponse(status_code=200, content=token)
        response.set_cookie(
            key="token",
            value=str(token),
            httponly=True,
            # secure=True,
            samesite="lax",
            max_age=60 * 60 * 24,
        )

        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        print("[jwt_auth - login] Error:", e)
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
    Uses the 'token' cookie (auth server session) to identify the user.
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
    OAuth2 UserInfo endpoint.
    Uses the 'access_token' (OAuth token) to return user information.
    This is what the Client App should use instead of /auth/me.
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
        print(f"Userinfo error: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.post("/logout")
def logout():
    response = JSONResponse(
        status_code=200, content={"message": "Logged out successfully"}
    )

    response.delete_cookie(key="token", samesite="lax")

    return response


@router.post("/forgot-password")
def forgot_password(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    print(f"Password reset requested for: {email}")
    return {"message": "If this email is registered, a reset link has been sent."}
