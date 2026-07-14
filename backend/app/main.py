from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import assessments, auth, check_ins, coach, daily_scores, health, trainee
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Deterministic baseline and longitudinal fitness intelligence. Not medical diagnosis or treatment.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


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


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}


for router in (
    auth.router,
    trainee.router,
    assessments.router,
    health.router,
    check_ins.router,
    daily_scores.router,
    coach.router,
):
    app.include_router(router, prefix="/api/v1")
