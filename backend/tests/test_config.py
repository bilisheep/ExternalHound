from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from app.config import CONFIG_ENV_VAR, Settings


SETTINGS_ENV_KEYS = [
    "APP_NAME",
    "APP_VERSION",
    "DEBUG",
    "API_V1_PREFIX",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_SSLMODE",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_PROJECTS",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_PASSWORD",
    "REDIS_DB",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "UPLOAD_DIR",
    "MAX_UPLOAD_SIZE",
    "CORS_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
    "CORS_ALLOW_METHODS",
    "CORS_ALLOW_HEADERS",
]


@pytest.fixture(autouse=True)
async def cleanup_test_data():
    yield


def _clear_settings_env(monkeypatch) -> None:
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _write_config(
    path: Path,
    app_name: str = "ExternalHound API",
    postgres_host: str = "localhost",
    cors_origins: list[str] | None = None,
) -> None:
    cors_origins = cors_origins or ["http://localhost:3000"]
    cors_lines = "\n".join(f'  "{origin}",' for origin in cors_origins)
    config_text = textwrap.dedent(
        f"""\
        APP_NAME = "{app_name}"
        APP_VERSION = "1.0.0"
        DEBUG = false
        API_V1_PREFIX = "/api/v1"

        POSTGRES_HOST = "{postgres_host}"
        POSTGRES_PORT = 5432
        POSTGRES_USER = "postgres"
        POSTGRES_PASSWORD = "externalhound_pg_pass"
        POSTGRES_DB = "externalhound"
        POSTGRES_SSLMODE = "disable"

        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "externalhound_neo4j_pass"

        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        REDIS_PASSWORD = "externalhound_redis_pass"
        REDIS_DB = 0

        SECRET_KEY = "your-secret-key-change-in-production"
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        REFRESH_TOKEN_EXPIRE_DAYS = 7

        UPLOAD_DIR = "/tmp/externalhound/uploads"
        MAX_UPLOAD_SIZE = 104857600

        CORS_ORIGINS = [
        {cors_lines}
        ]
        CORS_ALLOW_CREDENTIALS = true
        CORS_ALLOW_METHODS = ["GET", "POST"]
        CORS_ALLOW_HEADERS = ["*"]
        """
    )
    path.write_text(config_text, encoding="utf-8")


@pytest.mark.asyncio
async def test_settings_loads_toml_config(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    _write_config(
        config_path,
        app_name="ExternalHound TOML",
        postgres_host="toml-db",
        cors_origins=["http://example.test"],
    )
    monkeypatch.setenv(CONFIG_ENV_VAR, str(config_path))

    settings = Settings(_env_file=None)

    assert settings.APP_NAME == "ExternalHound TOML"
    assert settings.POSTGRES_HOST == "toml-db"
    assert settings.CORS_ORIGINS == ["http://example.test"]


@pytest.mark.asyncio
async def test_env_overrides_toml_config(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    _write_config(config_path, app_name="FromToml")
    monkeypatch.setenv(CONFIG_ENV_VAR, str(config_path))
    monkeypatch.setenv("APP_NAME", "FromEnv")

    settings = Settings(_env_file=None)

    assert settings.APP_NAME == "FromEnv"
    assert settings.APP_VERSION == "1.0.0"
