from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from backend.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from backend.api.routes import router
from backend.core.exception_hanlder import app_exception_handler, rate_limit_exception_handler
from backend.core.exception import AppException
from backend.core.config import get_settings
from backend.core.logging import configure_logging, get_logger
from backend.db.connection import engine

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    await engine.dispose() 
    logger.info("Application shutting down...")


app = FastAPI(
    title="Queryly API",
    version="1.0.0",
    description="An API for converting natural language queries into SQL queries.",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.include_router(router, prefix="/api")



