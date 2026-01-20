from datetime import datetime, timedelta, timezone
import os
from fastapi.responses import JSONResponse
from sqlmodel import select
import jwt
from fastapi import APIRouter, HTTPException

from backend.app.core.database import SessionDep
from backend.app.core.encrypt_pwd import hash_pwd
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["JWT Authentication"])

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


@router.post("/signup")
def signup_jwt(user: User, session: SessionDep):
    try:
        user_db = session.exec(select(User).where(User.email == user.email)).first()
        if user_db:
            raise HTTPException(
                status_code=409,
                detail="E-mail already exists. Try again using another one.",
            )

        email = user.email
        password = user.password
        hashed = hash_pwd(password)
        user.password = hashed

        issued_time = datetime.now(timezone.utc).timestamp()
        expiration_time = (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        payload = {
            "iss": JWT_ISSUER,
            "sub": email,
            "iat": issued_time,
            "exp": expiration_time,
        }

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

        session.add(user)
        session.commit()
        session.refresh(user)

        return response
    except (Exception, HTTPException) as e:
        print("[signup_jwt - signup_session] Error:", e)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
