import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Header,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse, RedirectResponse
import jwt

from app.core.database import SessionDep
from app.core.redis_instance import RedisSingleton
from app.dependencies.auth import get_current_user_or_none, get_user_required
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.schemas.auth_code_grant.auth_code_grant import (
    AccessTokenRequest,
    AuthorizationRequest,
    RefreshTokenRequest,
)

router = APIRouter(tags=["Authorization Code"])
redis_client = RedisSingleton().getInstance()

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")


####################
# Utility Functions
####################


def format_url(base_url: str) -> str:
    if base_url[-1] == "/":
        base_url = base_url[:-1]
    return base_url


def build_error_url(base_url: str, error: str) -> str:
    return f"{base_url}?error={error}&state=auth_error"


def extract_client_credentials(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if authorization and authorization.startswith("Basic "):
        try:
            encoded = authorization.replace("Basic ", "")
            decoded = base64.b64decode(encoded).decode("utf-8")

            if ":" not in decoded:
                return {"client_id": None, "client_secret": None}

            client_id, client_secret = decoded.split(":", 1)
            return {"client_id": client_id, "client_secret": client_secret}
        except Exception:
            return {"client_id": None, "client_secret": None}

    return {"client_id": None, "client_secret": None}


#####################################
# Authorization Code Grant Endpoints
#####################################


@router.get(path="/authorize")
def authorize_client(
    request: Request,
    req_params: Annotated[AuthorizationRequest, Query()],
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user_or_none)],
):
    BASE_URL = None
    try:
        CLIENT_ID = None

        if not current_user:
            return RedirectResponse(url="http://localhost:4000/login")

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

        redirect_uri_formatted = format_url(base_url=req_params.redirect_uri)
        auth_data = {
            "user_id": current_user.id,
            "client_id": client_db.client_id,
            "redirect_uri": redirect_uri_formatted,
            "scopes": req_params.scope,
        }

        redis_client.set(
            name=f"{client_db.client_id}:auth_code:{code}",
            value=json.dumps(auth_data),
            ex=600,  # RFC 6749 - "A maximum authorization code lifetime of 10 minutes is RECOMMENDED"
        )

        query = f"code={code}"
        if req_params.state:
            query += f"&state={req_params.state}"
        return RedirectResponse(url=f"{req_params.redirect_uri}?{query}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authorize client error: {e}")
        if BASE_URL is not None:
            print(f"Redirecting to error URL: {BASE_URL}")
            error_url = build_error_url(base_url=BASE_URL, error="server_error")
            return RedirectResponse(url=error_url)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@router.post(path="/token")
def get_access_token(
    request: Request,
    req_params: Annotated[AccessTokenRequest, Body()],
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
):
    response_headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}

    try:
        if req_params.grant_type != "authorization_code":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "unsupported_grant_type",
                    "error_description": f"Grant type must be 'authorization_code', got '{req_params.grant_type}'",
                },
                headers=response_headers,
            )

        if not req_params.code:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_request",
                    "error_description": "Missing required parameter: code",
                },
                headers=response_headers,
            )

        if not req_params.redirect_uri:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_request",
                    "error_description": "Missing required parameter: redirect_uri",
                },
                headers=response_headers,
            )

        auth_credentials = extract_client_credentials(authorization)
        client_id = auth_credentials["client_id"] or req_params.client_id
        client_secret = auth_credentials["client_secret"]

        if not client_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client authentication required",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        client = session.get(OAuthClient, client_id)

        if not client:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client not found",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        if not client.is_active:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client is inactive",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        if client_secret and not client.verify_secret(client_secret):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Invalid client credentials",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        redis_key = f"{client.client_id}:auth_code:{req_params.code}"
        auth_code_data = redis_client.get(redis_key)

        if not auth_code_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Authorization code not found or has expired",
                },
                headers=response_headers,
            )

        try:
            auth_data = json.loads(str(auth_code_data))
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Invalid authorization code format",
                },
                headers=response_headers,
            )

        if auth_data.get("client_id") != client.client_id:
            redis_client.delete(redis_key)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Authorization code was issued to a different client",
                },
                headers=response_headers,
            )

        redirect_uri_formatted = format_url(base_url=req_params.redirect_uri)
        if auth_data.get("redirect_uri") != redirect_uri_formatted:
            redis_client.delete(redis_key)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Redirect URI does not match authorization request",
                },
                headers=response_headers,
            )

        redis_client.delete(redis_key)

        user_id = auth_data.get("user_id")
        scopes = auth_data.get("scopes", "")

        access_token_data = {
            "sub": str(user_id),
            "client_id": client.client_id,
            "scope": scopes,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": JWT_ISSUER,
            "token_type": "bearer",
        }

        refresh_token_data = {
            "sub": str(user_id),
            "client_id": client.client_id,
            "scope": scopes,
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
            "iss": JWT_ISSUER,
            "token_type": "bearer",
        }

        access_token = jwt.encode(access_token_data, str(SECRET_JWT), algorithm="HS256")
        refresh_token = jwt.encode(
            refresh_token_data, str(SECRET_JWT), algorithm="HS256"
        )

        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": refresh_token,
                "scope": scopes,
            },
            headers=response_headers,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=3600,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
        )

        return response

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": "invalid_request", "error_description": e.detail},
            headers=response_headers,
        )

    except Exception as e:
        print(f"Unexpected error in token endpoint: {e}")
        import traceback

        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "server_error",
                "error_description": "An unexpected error occurred",
            },
            headers=response_headers,
        )


@router.post(path="/token/refresh")
def refresh_access_token(
    request: Request,
    req_params: Annotated[RefreshTokenRequest, Body()],
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
):
    response_headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}

    try:
        if req_params.grant_type != "refresh_token":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "unsupported_grant_type",
                    "error_description": f"Grant type must be 'refresh_token', got '{req_params.grant_type}'",
                },
                headers=response_headers,
            )

        refresh_token = req_params.refresh_token or request.cookies.get("refresh_token")

        if not refresh_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_request",
                    "error_description": "Missing required parameter: refresh_token",
                },
                headers=response_headers,
            )

        try:
            refresh_token_data = jwt.decode(
                refresh_token,
                str(SECRET_JWT),
                algorithms=["HS256"],
                issuer=JWT_ISSUER,
            )
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Refresh token has expired",
                },
                headers=response_headers,
            )
        except jwt.InvalidTokenError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": f"Invalid refresh token: {str(e)}",
                },
                headers=response_headers,
            )

        user_id = refresh_token_data.get("sub")
        client_id = refresh_token_data.get("client_id")
        original_scopes = refresh_token_data.get("scope", "")

        if not user_id or not client_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_grant",
                    "error_description": "Refresh token is missing required claims",
                },
                headers=response_headers,
            )

        client = session.get(OAuthClient, client_id)

        if not client:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client not found",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        if not client.is_active:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_client",
                    "error_description": "Client is inactive",
                },
                headers={
                    **response_headers,
                    "WWW-Authenticate": 'Basic realm="OAuth2"',
                },
            )

        auth_credentials = extract_client_credentials(authorization)
        if auth_credentials["client_secret"]:
            if not client.verify_secret(auth_credentials["client_secret"]):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "invalid_client",
                        "error_description": "Invalid client credentials",
                    },
                    headers={
                        **response_headers,
                        "WWW-Authenticate": 'Basic realm="OAuth2"',
                    },
                )

        scopes = original_scopes
        if req_params.scope:
            requested_scopes = set(req_params.scope.split())
            original_scope_set = (
                set(original_scopes.split()) if original_scopes else set()
            )

            if not requested_scopes.issubset(original_scope_set):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_scope",
                        "error_description": "Requested scope exceeds original grant scope",
                    },
                    headers=response_headers,
                )
            scopes = req_params.scope

        new_access_token_data = {
            "sub": str(user_id),
            "client_id": client.client_id,
            "scope": scopes,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": JWT_ISSUER,
            "token_type": "bearer",
        }

        new_refresh_token_data = {
            "sub": str(user_id),
            "client_id": client.client_id,
            "scope": original_scopes,
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
            "iss": JWT_ISSUER,
            "token_type": "bearer",
        }

        new_access_token = jwt.encode(
            new_access_token_data, str(SECRET_JWT), algorithm="HS256"
        )
        new_refresh_token = jwt.encode(
            new_refresh_token_data, str(SECRET_JWT), algorithm="HS256"
        )

        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": new_refresh_token,
                "scope": scopes,
            },
            headers=response_headers,
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            samesite="lax",
            max_age=3600,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

        return response

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": "invalid_request", "error_description": e.detail},
            headers=response_headers,
        )

    except Exception as e:
        print(f"Unexpected error in refresh token endpoint: {e}")
        import traceback

        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "server_error",
                "error_description": "An unexpected error occurred",
            },
            headers=response_headers,
        )
