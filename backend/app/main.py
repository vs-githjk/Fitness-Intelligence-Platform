import json
import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.api import (
    assessments,
    auth,
    check_ins,
    coach,
    daily_scores,
    exercises,
    health,
    invites,
    trainee,
    training_assignments,
    training_programs,
    workout_sessions,
    workout_templates,
)
from app.config import settings
from app.database import engine

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
logger = logging.getLogger("fitness_intelligence.requests")
logging.basicConfig(level=getattr(logging, settings.log_level))
logger.setLevel(settings.log_level)

docs_url = "/docs" if settings.api_docs_enabled else None
openapi_url = "/openapi.json" if settings.api_docs_enabled else None
redoc_url = "/redoc" if settings.api_docs_enabled else None
app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Deterministic baseline and longitudinal fitness intelligence. Not medical diagnosis or treatment.",
    docs_url=docs_url,
    openapi_url=openapi_url,
    redoc_url=redoc_url,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)


def _request_id(request: Request) -> str:
    supplied = request.headers.get("X-Request-ID", "")
    return supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())


def _log_event(**values: object) -> None:
    logger.info(json.dumps(values, separators=(",", ":"), sort_keys=True))


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = _request_id(request)
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        logger.error(
            json.dumps(
                {
                    "duration_ms": duration_ms,
                    "environment": settings.app_env.value,
                    "error_type": type(exc).__name__,
                    "event": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": request_id,
                    "version": __version__,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            },
        )
    response.headers["X-Request-ID"] = request_id
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    _log_event(
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
        environment=settings.app_env.value,
        event="request_completed",
        method=request.method,
        path=path,
        request_id=request_id,
        status=response.status_code,
        version=__version__,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = {
        ".".join(str(part) for part in error["loc"][1:]): error["msg"] for error in exc.errors()
    }
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Please correct the highlighted fields",
                "fields": fields,
            }
        },
    )


def database_ready() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def live_payload() -> dict[str, str]:
    return {"status": "healthy", "version": __version__}


@app.get("/health", tags=["system"])
@app.get("/health/live", tags=["system"])
def healthcheck() -> dict[str, str]:
    return live_payload()


@app.get("/health/ready", tags=["system"])
def readinesscheck() -> JSONResponse:
    try:
        database_ready()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "version": __version__},
        )
    return JSONResponse(content={"status": "ready", "version": __version__})


for router in (
    auth.router,
    trainee.router,
    assessments.router,
    health.router,
    check_ins.router,
    daily_scores.router,
    coach.router,
    exercises.router,
    workout_templates.router,
    training_programs.router,
    training_assignments.router,
    workout_sessions.router,
    invites.router,
):
    app.include_router(router, prefix="/api/v1")
