from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import chat, health, leads, meetings, memory, security_routes, workflows
from application.bootstrap import bootstrap_manager
from application.context import app_context
from config.settings import settings
from infrastructure.database.session import db
from exceptions.base import AppError, InfrastructureError, NotFoundError, ValidationError
from middleware.correlation import CorrelationIDMiddleware
from middleware.identity import IdentityResolutionMiddleware
from middleware.rate_limiter import RateLimitMiddleware
from middleware.security import RequestValidationMiddleware, SecurityHeadersMiddleware
from monitoring.logger import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    try:
        await bootstrap_manager.bootstrap()
        logger.info("Application bootstrapped successfully")
    except Exception as e:
        logger.warning(f"Application bootstrap deferred: {e}")

    app.state.app_context = app_context
    app.state.db_session = db.session_factory

    yield

    logger.info("Shutting down")
    await bootstrap_manager.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Executive Assistant API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(IdentityResolutionMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)


async def _app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(f"{exc.__class__.__name__}: {exc.message}", extra={"status_code": exc.status_code, "detail": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.detail},
    )


app.add_exception_handler(AppError, _app_exception_handler)
app.add_exception_handler(ValidationError, _app_exception_handler)
app.add_exception_handler(NotFoundError, _app_exception_handler)
app.add_exception_handler(InfrastructureError, _app_exception_handler)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(meetings.router)
app.include_router(leads.router)
app.include_router(memory.router)
app.include_router(workflows.router)
app.include_router(security_routes.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
    }
