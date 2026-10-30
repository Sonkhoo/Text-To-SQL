import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

from backend.db.connection import engine, get_db
from backend.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    await engine.dispose() 
    logger.info("Application shutting down...")


app = FastAPI(
    title="My FastAPI Application",
    version="1.0.0",
    description="A simple FastAPI application",
    lifespan=lifespan
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.include_router(router, prefix="/api")





