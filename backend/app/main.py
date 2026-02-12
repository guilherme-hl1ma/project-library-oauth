from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command

from app.api.handlers import (
    application_error_handler,
    domain_error_handler,
    unexpected_error_handler,
    forbidden_error_handler,
)
from app.domain.oauth_client.exceptions import DomainError
from app.services.exceptions import (
    ApplicationError,
    ForbiddenError,
    InternalServerError,
)

log = logging.getLogger("uvicorn")


load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    log.info("Starting up...")
    log.info("Run alembic upgrade head...")
    run_migrations()
    yield
    log.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import dcr, authentication, auth_code_grant, user, project

app.include_router(dcr.router)
app.include_router(authentication.router)
app.include_router(auth_code_grant.router)
app.include_router(user.router)
app.include_router(project.router)

app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(InternalServerError, unexpected_error_handler)
app.add_exception_handler(ForbiddenError, forbidden_error_handler)
