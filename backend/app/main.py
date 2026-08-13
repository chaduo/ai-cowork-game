from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.config import Settings, get_settings
from app.errors import ApiError, handle_api_error, handle_unexpected_error, handle_validation_error
from app.api.projects import router as projects_router
from app.db import create_engine_for


SERVICE_NAME = "ai-cowork-game-api"
APPLICATION_VERSION = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="AI Cowork Game API", version=APPLICATION_VERSION)
    app.state.settings = settings
    app.state.engine = create_engine_for(settings)
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
    app.include_router(projects_router)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": APPLICATION_VERSION,
        }

    return app


app = create_app()
