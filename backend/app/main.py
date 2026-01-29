from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command

from app.api.handlers import (
    application_error_handler,
    domain_error_handler,
    unexpected_error_handler,
)
from app.domain.oauth_client.exceptions import DomainError
from app.services.exceptions import ApplicationError, InternalServerError

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

from app.api.routes import dcr, authentication, auth_code_grant

app.include_router(dcr.router)
app.include_router(authentication.router)
app.include_router(auth_code_grant.router)

app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(InternalServerError, unexpected_error_handler)
