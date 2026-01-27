from datetime import datetime, timedelta, timezone
import os
import uuid
import traceback
from fastapi.responses import JSONResponse
from sqlmodel import select
import jwt
from fastapi import APIRouter, HTTPException

from app.core.database import SessionDep
from app.core.bcrypt_encrypter import hash_text, verify_text
from app.models.user import UserRole, User
from app.schemas.user import UserLogin, UserRegistration

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
        print("[signup_jwt - signup_session] HTTPException:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
    except TypeError as e:
        print("[signup_jwt - signup_session] TypeError:", str(e))
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
    except Exception as e:
        print("[signup_jwt - signup_session] Error:", str(e))
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
    except (Exception, HTTPException) as e:
        print("[jwt_auth - login] Error:", e)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
