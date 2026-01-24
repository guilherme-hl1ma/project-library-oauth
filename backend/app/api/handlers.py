from fastapi import Request
from fastapi.responses import JSONResponse


async def domain_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
        },
    )


async def application_error_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=409,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
        },
    )


async def unexpected_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
