from sys import prefix
from fastapi.routing import APIRoute


router = APIRoute(prefix="/dcr", tags=["Dynamic Client Registration"])


@router.post("/register")
def register_client():
    pass
