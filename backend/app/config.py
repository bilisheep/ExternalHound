"""
应用程序配置管理

使用Pydantic Settings管理环境变量和配置。
"""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import tomllib
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


CONFIG_ENV_VAR = "EXTERNALHOUND_CONFIG"
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "config.toml"
DEFAULT_ENV_FILES = (
    str(BASE_DIR.parent / ".env"),
    str(BASE_DIR / ".env"),
)


def _resolve_config_path() -> Path:
    config_path = os.environ.get(CONFIG_ENV_VAR)
    if config_path:
        return Path(config_path).expanduser()
    return DEFAULT_CONFIG_PATH


class TomlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    Settings source that loads values from a TOML config file.
    """

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls)
        self.config_path = _resolve_config_path()

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        return None, "", False

    def __call__(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            return {}
        with self.config_path.open("rb") as config_file:
            data = tomllib.load(config_file)
        if not isinstance(data, dict):
            return {}
        return data

    def __repr__(self) -> str:
        return f"TomlConfigSettingsSource(config_path={self.config_path!s})"


class Settings(BaseSettings):
    """
    应用程序配置类

    所有配置项都可以通过环境变量覆盖。
    环境变量名称与字段名称相同（大小写敏感）。
    """

    # 应用配置
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    API_V1_PREFIX: str

    # PostgreSQL 配置
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SSLMODE: str | None = None

    # Neo4j 配置
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Redis 配置
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int

    # JWT 配置（后续版本使用）
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # 文件上传配置
    UPLOAD_DIR: str
    MAX_UPLOAD_SIZE: int

    # CORS配置
    CORS_ORIGINS: list[str]
    CORS_ALLOW_CREDENTIALS: bool
    CORS_ALLOW_METHODS: list[str]
    CORS_ALLOW_HEADERS: list[str]

    model_config = SettingsConfigDict(
        env_file=list(DEFAULT_ENV_FILES),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略未定义的环境变量
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    @property
    def POSTGRES_URL(self) -> str:
        """
        构建PostgreSQL连接URL

        Returns:
            异步PostgreSQL连接字符串
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_SYNC_URL(self) -> str:
        """
        构建同步PostgreSQL连接URL（用于Alembic迁移）

        Returns:
            同步PostgreSQL连接字符串
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_CONNECT_ARGS(self) -> dict[str, object]:
        sslmode = self._resolve_postgres_sslmode()
        if not sslmode:
            return {}
        sslmode = sslmode.lower()
        if sslmode == "disable":
            return {"ssl": False}
        if sslmode in {"require", "verify-ca", "verify-full"}:
            return {"ssl": True}
        return {}

    def _resolve_postgres_sslmode(self) -> str | None:
        if self.POSTGRES_SSLMODE:
            return self.POSTGRES_SSLMODE
        if self.POSTGRES_HOST in {"localhost", "127.0.0.1", "::1"}:
            return "disable"
        return None


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用lru_cache确保配置只被加载一次。

    Returns:
        Settings实例
    """
    return Settings()


# 全局配置实例
settings = get_settings()
