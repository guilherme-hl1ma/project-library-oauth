import json
import secrets
from sys import exception
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.database import SessionDep
from app.core.redis_instance import RedisSingleton
from app.dependencies.auth import get_user_jwt_auth
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.schemas.auth_code_grant.auth_code_grant import (
    AuthorizationCodeError,
    AuthorizationRequest,
    AuthorizationResponse,
)

router = APIRouter(tags=["Authorization Code"])
redis_client = RedisSingleton().getInstance()


def build_error_url(base_url: str, error: str) -> str:
    return f"{base_url}?error={error}&state=auth_error"


@router.get(path="/authorize")
def authorize_client(
    request: Request,
    req_params: Annotated[AuthorizationRequest, Query()],
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_jwt_auth)],
):
    BASE_URL = None
    try:
        CLIENT_ID = None

        client_db = session.get(OAuthClient, req_params.client_id)
        if client_db is None:
            raise HTTPException(status_code=400, detail="Invalid client.")

        BASE_URL = client_db.redirect_uris[0]
        CLIENT_ID = client_db.client_id

        if req_params.redirect_uri is None:
            raise HTTPException(status_code=400, detail="Invalid redirect URI.")

        if req_params.redirect_uri not in client_db.redirect_uris:
            return RedirectResponse(
                f"{build_error_url(base_url=BASE_URL, error="invalid_request")}"
            )

        if CLIENT_ID is None:
            return RedirectResponse(
                f"{build_error_url(base_url=BASE_URL, error="unauthorized_client")}"
            )

        if req_params.response_type != "code":
            return RedirectResponse(
                f"{build_error_url(base_url=BASE_URL, error="unsupported_response_type")}"
            )

        code = secrets.token_urlsafe(32)

        auth_data = {
            "user_id": current_user.id,
            "client_id": client_db.client_id,
            "redirect_uri": req_params.redirect_uri,
            "scopes": req_params.scope,
        }

        redis_client.set(
            name=f"{current_user.id}:auth_code:{code}",
            value=json.dumps(auth_data),
            ex=600,  # RFC 6749 - "A maximum authorization code lifetime of 10 minutes is RECOMMENDED"
        )

        query = f"code={code}"
        if req_params.state:
            query += f"&state={req_params.state}"
        return RedirectResponse(url=f"{req_params.redirect_uri}?{query}")
    except Exception as e:
        if BASE_URL is not None:
            return RedirectResponse(
                f"{build_error_url(base_url=BASE_URL, error="server_error")}"
            )
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
