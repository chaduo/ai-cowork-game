from app.config import Settings


def test_settings_use_deterministic_local_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "local"
    assert settings.database_url == "sqlite:///./data/app.db"
    assert settings.log_level == "INFO"


def test_settings_read_documented_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/test.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.app_env == "test"
    assert settings.database_url == "sqlite:///./data/test.db"
    assert settings.log_level == "DEBUG"
