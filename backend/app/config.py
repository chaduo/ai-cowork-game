from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Small environment-backed configuration object for the platform API."""

    app_env: str = "local"
    database_url: str = "sqlite:///./data/app.db"
    log_level: str = "INFO"

    def __init__(
        self,
        app_env: str | None = None,
        database_url: str | None = None,
        log_level: str | None = None,
    ) -> None:
        object.__setattr__(self, "app_env", app_env or os.getenv("APP_ENV", "local"))
        object.__setattr__(
            self,
            "database_url",
            database_url or os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        )
        object.__setattr__(self, "log_level", log_level or os.getenv("LOG_LEVEL", "INFO"))


def get_settings() -> Settings:
    return Settings()
