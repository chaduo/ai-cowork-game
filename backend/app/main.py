from fastapi import FastAPI

from app.config import Settings, get_settings


SERVICE_NAME = "ai-cowork-game-api"
APPLICATION_VERSION = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="AI Cowork Game API", version=APPLICATION_VERSION)
    app.state.settings = settings

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": APPLICATION_VERSION,
        }

    return app


app = create_app()
