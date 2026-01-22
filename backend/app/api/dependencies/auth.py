import os
from fastapi import HTTPException, Request
import jwt

from app.core.database import SessionDep
from app.models.user import User

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


def get_user_jwt_auth(session: SessionDep, request: Request) -> User | None:
    try:
        token = request.cookies.get("token")

        if not token:
            raise HTTPException(status_code=401, detail="Invalid credential")

        token_decoded: dict = jwt.decode(
            jwt=token, key=SECRET_JWT, algorithms=["HS256"], issuer=JWT_ISSUER
        )

        user_id = token_decoded.get("sub", None)
        if user_id is None:
            print("[get_user_jwt_auth] Error: email cannot be None")
            raise HTTPException(status_code=401, detail="Invalid credential")
        current_user = session.get(User, user_id)
    except HTTPException:
        raise
    except (jwt.ExpiredSignatureError, jwt.InvalidIssuerError) as e:
        print("[get_user_jwt_auth] Error:", e)
        raise HTTPException(status_code=401, detail="Invalid credential")
    except Exception as e:
        print("[get_user_jwt_auth] Error:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return current_user
