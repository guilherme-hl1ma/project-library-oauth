from fastapi import APIRouter

router = APIRouter(tags=["Authorization Code"])


@router.get(path="/authorize")
def authorize_client(
    response_type: str, client_id: str, redirect_url: str, scope: list[str], state: str
):
    pass
