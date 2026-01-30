from enum import StrEnum
from pydantic import BaseModel


class GrantType(StrEnum):
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICT = "implict"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class TokenEndpointAuthMethod(StrEnum):
    """
    OAuth 2.0 Token Endpoint Authentication Methods

    Defines how the client authenticates itself when requesting tokens at the /token endpoint.

    Methods:
    - none: No client authentication (for public clients like SPAs, mobile apps)
      * Cannot securely store secrets
      * Must use PKCE for security
      * Example: Single Page Applications, Mobile Apps

    - client_secret_post: Client credentials sent in the request body
      * For confidential clients (backend servers)
      * client_id and client_secret sent as form parameters
      * Example POST body:
        grant_type=authorization_code
        &client_id=my_client
        &client_secret=super_secret_123
        &code=AUTH_CODE

    - client_secret_basic: Client credentials sent via HTTP Basic Authentication
      * For confidential clients (backend servers)
      * Most common method
      * Example header:
        Authorization: Basic base64(client_id:client_secret)

    Usage in /token endpoint:
    The server validates that the client is using an authentication method
    it declared during registration (token_endpoint_auth_method field).

    Reference: RFC 6749 Section 2.3 (Client Authentication)
    """

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
