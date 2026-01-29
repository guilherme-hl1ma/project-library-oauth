from enum import StrEnum
from pydantic import BaseModel


class GrantType(StrEnum):
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICT = "implict"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class TokenEndpointAuthMethod(StrEnum):
    NONE = "none"
    CLIENT_SECRETED_POST = "client_secret_post"
    CLIENT_SECRET_BASIC = "client_secret_basic"


class ClientMetadataRegister(BaseModel):
    client_name: str | None = None
    redirect_uris: list[str]
    grant_types: list[str]
    token_endpoint_auth_method: list[TokenEndpointAuthMethod]


class ClientMetadataResponse(BaseModel):
    client_id: str
    client_secret: str
    issued_at: int
    client_name: str | None
    redirect_uris: list[str]
