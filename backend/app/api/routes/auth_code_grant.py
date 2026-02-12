import base64
import json
import os
import urllib.parse
import secrets
from datetime import datetime, timedelta, timezone
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
from app.dependencies.auth import (
    get_current_user_or_none,
    get_user_required,
    get_user_from_access_token,
)
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.schemas.auth_code_grant.auth_code_grant import (
    AuthorizationRequest,
    TokenRequest,
)

router = APIRouter(tags=["Authorization Code"])
redis_client = RedisSingleton().getInstance()

SECRET_JWT = os.getenv("SECRET_JWT")
JWT_ISSUER = os.getenv("JWT_ISSUER")

AUTH_FRONTEND_URL = os.getenv("AUTH_FRONTEND_URL", "http://localhost:3000")


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


def _generate_tokens(user_id: str, client_id: str, scopes: str) -> dict:
    """Generate access_token and refresh_token pair."""
    now = datetime.now(timezone.utc)

    access_token_data = {
        "sub": str(user_id),
        "client_id": client_id,
        "scope": scopes,
        "exp": now + timedelta(hours=1),
        "iat": now,
        "iss": JWT_ISSUER,
        "token_type": "bearer",
    }

    refresh_token_data = {
        "sub": str(user_id),
        "client_id": client_id,
        "scope": scopes,
        "exp": now + timedelta(days=30),
        "iat": now,
        "iss": JWT_ISSUER,
        "token_type": "bearer",
    }

    access_token = jwt.encode(access_token_data, str(SECRET_JWT), algorithm="HS256")
    refresh_token = jwt.encode(refresh_token_data, str(SECRET_JWT), algorithm="HS256")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "scopes": scopes,
    }


def _build_token_response(tokens: dict, response_headers: dict) -> JSONResponse:
    """Build the standard OAuth token response with cookies."""
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": tokens["access_token"],
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": tokens["refresh_token"],
            "scope": tokens["scopes"],
        },
        headers=response_headers,
    )

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        samesite="lax",
        max_age=3600,
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
    )

    return response


#####################################
# Authorization Code Grant Endpoints
#####################################


@router.get(path="/authorize")
def authorize_client(
    request: Request,
    req_params: Annotated[AuthorizationRequest, Query()],
    session: SessionDep,
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
):
    """
    RFC 6749 Section 4.1.1 - Authorization Request.

    Instead of issuing the code directly, this endpoint redirects the user
    to the Auth Server's consent screen. The consent screen is served by
    the auth-frontend and allows the user to approve or deny the request.
    """
    BASE_URL = None
    try:
        CLIENT_ID = None

        if not current_user:
            # Store the original authorization request in the query string
            # so after login, the user can be redirected back here.
            original_params = urllib.parse.quote(str(request.url.query), safe="")
            return RedirectResponse(
                url=f"{AUTH_FRONTEND_URL}/login?return_to=/authorize&oauth_params={original_params}"
            )

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

        scopes = req_params.scope
        if isinstance(scopes, list):
            scopes = " ".join(scopes)

        redirect_uri_formatted = format_url(base_url=req_params.redirect_uri)

        consent_key = f"consent_granted:{current_user.id}:{client_db.client_id}"
        existing_consent = redis_client.get(consent_key)

        if existing_consent:
            try:
                granted_scopes = set(json.loads(str(existing_consent)))
                requested_scopes = set((scopes or "").split())

                if requested_scopes.issubset(granted_scopes):
                    code = secrets.token_urlsafe(32)
                    auth_data = {
                        "user_id": current_user.id,
                        "client_id": client_db.client_id,
                        "redirect_uri": redirect_uri_formatted,
                        "scopes": scopes or "",
                    }
                    redis_client.set(
                        name=f"{client_db.client_id}:auth_code:{code}",
                        value=json.dumps(auth_data),
                        ex=600,
                    )
                    query = f"code={code}"
                    if req_params.state:
                        query += f"&state={req_params.state}"
                    return RedirectResponse(url=f"{req_params.redirect_uri}?{query}")
            except (json.JSONDecodeError, Exception):
                pass

        consent_id = secrets.token_urlsafe(32)
        consent_data = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "client_id": client_db.client_id,
            "client_name": client_db.client_name or client_db.client_id,
            "redirect_uri": redirect_uri_formatted,
            "scopes": scopes or "",
            "state": req_params.state or "",
        }

        redis_client.set(
            name=f"consent:{consent_id}",
            value=json.dumps(consent_data),
            ex=600,  # 10 minutes to complete the consent flow
        )

        return RedirectResponse(
            url=f"{AUTH_FRONTEND_URL}/consent?consent_id={consent_id}"
        )

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


@router.get(path="/authorize/consent-data")
def get_consent_data(
    consent_id: str = Query(...),
    current_user: User | None = Depends(get_current_user_or_none),
):
    """
    Returns the consent request data so the auth-frontend consent screen
    can display what the client is requesting.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    consent_data_raw = redis_client.get(f"consent:{consent_id}")
    if not consent_data_raw:
        raise HTTPException(
            status_code=404, detail="Consent request not found or expired"
        )

    consent_data = json.loads(str(consent_data_raw))

    if consent_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=403, detail="Consent request does not belong to this user"
        )

    return {
        "client_name": consent_data.get("client_name"),
        "scopes": consent_data.get("scopes", "").split(),
        "user_email": consent_data.get("user_email"),
    }


@router.post(path="/authorize/consent")
def handle_consent(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_user_required)],
    consent_id: str = Body(...),
    approved: bool = Body(...),
    approved_scopes: list[str] = Body(default=[]),
):
    consent_data_raw = redis_client.get(f"consent:{consent_id}")
    if not consent_data_raw:
        raise HTTPException(
            status_code=400, detail="Consent request not found or expired"
        )

    consent_data = json.loads(str(consent_data_raw))

    if consent_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=403, detail="Consent does not belong to this user"
        )

    redis_client.delete(f"consent:{consent_id}")

    redirect_uri = consent_data.get("redirect_uri")
    state = consent_data.get("state")

    if not approved:
        # User denied — redirect back with access_denied error
        error_url = f"{redirect_uri}?error=access_denied"
        if state:
            error_url += f"&state={state}"
        return JSONResponse(
            status_code=200,
            content={"redirect_url": error_url},
        )

    # User approved — generate authorization code
    # Use the approved scopes (which may be a subset of what was requested)
    final_scopes = (
        " ".join(approved_scopes) if approved_scopes else consent_data.get("scopes", "")
    )

    consent_key = f"consent_granted:{current_user.id}:{consent_data.get('client_id')}"
    redis_client.set(
        name=consent_key,
        value=json.dumps(final_scopes.split()),
        ex=60 * 60 * 24 * 30,  # 30 days
    )

    code = secrets.token_urlsafe(32)

    auth_data = {
        "user_id": current_user.id,
        "client_id": consent_data.get("client_id"),
        "redirect_uri": redirect_uri,
        "scopes": final_scopes,
    }

    redis_client.set(
        name=f"{consent_data.get('client_id')}:auth_code:{code}",
        value=json.dumps(auth_data),
        ex=600,  # RFC 6749 - max 10 minutes
    )

    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"

    return JSONResponse(
        status_code=200,
        content={"redirect_url": redirect_url},
    )


@router.post(path="/token")
def token_endpoint(
    request: Request,
    req_params: Annotated[TokenRequest, Body()],
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
):
    """
    RFC 6749 Section 4.1.3 & 6 - Unified Token Endpoint.

    Handles both grant types:
    - grant_type=authorization_code (exchange code for tokens)
    - grant_type=refresh_token (refresh an expired access token)
    """
    response_headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}

    try:
        if req_params.grant_type == "authorization_code":
            return _handle_authorization_code_grant(
                request, req_params, session, authorization, response_headers
            )
        elif req_params.grant_type == "refresh_token":
            return _handle_refresh_token_grant(
                request, req_params, session, authorization, response_headers
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "unsupported_grant_type",
                    "error_description": f"Supported grant types: 'authorization_code', 'refresh_token'. Got '{req_params.grant_type}'",
                },
                headers=response_headers,
            )

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


def _handle_authorization_code_grant(
    request: Request,
    req_params: TokenRequest,
    session: SessionDep,
    authorization: str | None,
    response_headers: dict,
) -> JSONResponse:
    """Handle grant_type=authorization_code."""

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

    client = _authenticate_client(
        req_params.client_id, authorization, session, response_headers
    )
    if isinstance(client, JSONResponse):
        return client

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

    tokens = _generate_tokens(user_id, client.client_id, scopes)
    return _build_token_response(tokens, response_headers)


def _handle_refresh_token_grant(
    request: Request,
    req_params: TokenRequest,
    session: SessionDep,
    authorization: str | None,
    response_headers: dict,
) -> JSONResponse:
    """Handle grant_type=refresh_token."""

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

    # RFC 6749 Section 6: scope MUST NOT include any scope not originally granted
    scopes = original_scopes
    if req_params.scope:
        requested_scopes = set(req_params.scope.split())
        original_scope_set = set(original_scopes.split()) if original_scopes else set()

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

    tokens = _generate_tokens(user_id, client.client_id, scopes)
    return _build_token_response(tokens, response_headers)


def _authenticate_client(
    client_id_param: str | None,
    authorization: str | None,
    session: SessionDep,
    response_headers: dict,
) -> OAuthClient | JSONResponse:
    """Authenticate the client via Basic Auth or client_id parameter."""

    auth_credentials = extract_client_credentials(authorization)
    client_id = auth_credentials["client_id"] or client_id_param
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

    return client


#####################################
# Token Revocation
#####################################


@router.post(path="/token/revoke")
def revoke_tokens():
    """
    Full logout — revokes ALL tokens:
    - access_token and refresh_token (OAuth tokens)
    - token (Auth Server session)

    The user will need to log in again on the Auth Server.
    """
    response = JSONResponse(
        status_code=200,
        content={"message": "All tokens revoked successfully"},
    )

    response.delete_cookie(key="access_token", samesite="lax")
    response.delete_cookie(key="refresh_token", samesite="lax")
    response.delete_cookie(key="token", samesite="lax")

    return response


@router.post(path="/token/revoke-consent")
def revoke_consent(
    current_user: Annotated[User, Depends(get_user_from_access_token)],
    request: Request,
):
    """
    Deauthorize — revokes OAuth tokens AND removes stored consent.
    The Auth Server session ('token' cookie) remains intact.

    Next time the user goes through the OAuth flow, the consent screen
    will appear again because the stored consent was cleared.
    """
    access_token = request.cookies.get("access_token")
    client_id = None
    if access_token:
        try:
            payload = jwt.decode(access_token, str(SECRET_JWT), algorithms=["HS256"])
            client_id = payload.get("client_id")
        except Exception:
            pass

    if client_id:
        consent_key = f"consent_granted:{current_user.id}:{client_id}"
        redis_client.delete(consent_key)

    response = JSONResponse(
        status_code=200,
        content={"message": "Consent revoked successfully"},
    )

    response.delete_cookie(key="access_token", samesite="lax")
    response.delete_cookie(key="refresh_token", samesite="lax")

    return response
