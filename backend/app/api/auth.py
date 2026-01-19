from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.get(path="/authorize")
def authorize_client(response_type: str):
    pass
