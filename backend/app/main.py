from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

app = FastAPI()

from app.api import dcr, authentication

app.include_router(dcr.router)
app.include_router(authentication.router)
