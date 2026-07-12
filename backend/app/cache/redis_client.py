from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import get_settings

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]


@lru_cache
def _client() -> Any | None:
    settings = get_settings()
    if redis is None or not settings.redis_url or len(settings.redis_url) < 8:
        return None
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def cache_get(key: str) -> Any | None:
    client = _client()
    if client is None:
        return None
    raw = client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def cache_set(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    client = _client()
    if client is None:
        return
    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
    client.setex(key, ttl, json.dumps(value, default=str))
