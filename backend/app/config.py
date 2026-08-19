from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Small environment-backed configuration object for the platform API."""

    app_env: str = "local"
    database_url: str = "sqlite:///./data/app.db"
    log_level: str = "INFO"
    game_agent_provider: str = "fake"
    candidate_test_provider: str = "fake"
    game_design_provider: str = "fake"
    game_design_model: str = "kimi-k3"
    game_design_timeout_seconds: float = 90.0
    opengame_cli_js: str | None = None
    opengame_model: str = "kimi-k3"
    opengame_timeout_seconds: float = 300.0
    chrome_executable: str | None = None
    chrome_timeout_seconds: float = 30.0

    def __init__(
        self,
        app_env: str | None = None,
        database_url: str | None = None,
        log_level: str | None = None,
        game_agent_provider: str | None = None,
        candidate_test_provider: str | None = None,
        game_design_provider: str | None = None,
        game_design_model: str | None = None,
        game_design_timeout_seconds: float | None = None,
        opengame_cli_js: str | None = None,
        opengame_model: str | None = None,
        opengame_timeout_seconds: float | None = None,
        chrome_executable: str | None = None,
        chrome_timeout_seconds: float | None = None,
    ) -> None:
        object.__setattr__(self, "app_env", app_env or os.getenv("APP_ENV", "local"))
        object.__setattr__(
            self,
            "database_url",
            database_url or os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        )
        object.__setattr__(self, "log_level", log_level or os.getenv("LOG_LEVEL", "INFO"))
        # Direct Settings construction is the explicit isolated-test mode. The
        # production get_settings() below opts into real providers.
        object.__setattr__(self, "game_agent_provider", game_agent_provider or "fake")
        object.__setattr__(self, "candidate_test_provider", candidate_test_provider or "fake")
        object.__setattr__(self, "game_design_provider", game_design_provider or "fake")
        object.__setattr__(self, "game_design_model", game_design_model or os.getenv("GAME_DESIGN_MODEL", os.getenv("OPENAI_MODEL", "kimi-k3")))
        design_timeout = game_design_timeout_seconds
        if design_timeout is None and os.getenv("GAME_DESIGN_TIMEOUT_SECONDS"):
            design_timeout = float(os.environ["GAME_DESIGN_TIMEOUT_SECONDS"])
        object.__setattr__(self, "game_design_timeout_seconds", design_timeout or 90.0)
        object.__setattr__(self, "opengame_cli_js", opengame_cli_js or os.getenv("OPENGAME_CLI_JS"))
        object.__setattr__(self, "opengame_model", opengame_model or os.getenv("OPENAI_MODEL", "kimi-k3"))
        timeout = opengame_timeout_seconds
        if timeout is None and os.getenv("OPENGAME_TIMEOUT_SECONDS"):
            timeout = float(os.environ["OPENGAME_TIMEOUT_SECONDS"])
        object.__setattr__(self, "opengame_timeout_seconds", timeout or 300.0)
        object.__setattr__(self, "chrome_executable", chrome_executable or os.getenv("CHROME_EXECUTABLE"))
        chrome_timeout = chrome_timeout_seconds
        if chrome_timeout is None and os.getenv("CHROME_TIMEOUT_SECONDS"):
            chrome_timeout = float(os.environ["CHROME_TIMEOUT_SECONDS"])
        object.__setattr__(self, "chrome_timeout_seconds", chrome_timeout or 30.0)


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        game_agent_provider=os.getenv("GAME_AGENT_PROVIDER", "opengame"),
        candidate_test_provider=os.getenv("CANDIDATE_TEST_PROVIDER", "chrome"),
        game_design_provider=os.getenv("GAME_DESIGN_PROVIDER", "openai"),
        game_design_model=os.getenv("GAME_DESIGN_MODEL", os.getenv("OPENAI_MODEL", "kimi-k3")),
    )
