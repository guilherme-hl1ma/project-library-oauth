from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command

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

from app.api import dcr, authentication

app.include_router(dcr.router)
app.include_router(authentication.router)
