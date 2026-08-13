from fastapi import FastAPI


SERVICE_NAME = "ai-cowork-game-api"
APPLICATION_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title="AI Cowork Game API", version=APPLICATION_VERSION)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": APPLICATION_VERSION,
        }

    return app


app = create_app()
