from functools import lru_cache
from urllib.parse import urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_supabase_url(url: str) -> str:
    """Accept either project root or accidental /rest/v1 suffix."""
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    if path.endswith("/rest/v1"):
        path = path[: -len("/rest/v1")]
    elif path == "/rest/v1":
        path = ""
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")).rstrip("/")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str
    supabase_publishable_key: str
    supabase_service_role_key: str | None = None
    supabase_db_password: str | None = None

    redis_url: str | None = None
    cache_ttl_seconds: int = 900  # 15 minutes

    cors_origins: str = "http://localhost:3000"

    default_gym_slug: str = "usc-gym"

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, value: str) -> str:
        return _normalize_supabase_url(value)

    @property
    def supabase_key(self) -> str:
        return self.supabase_service_role_key or self.supabase_publishable_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
