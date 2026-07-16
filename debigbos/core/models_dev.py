"""models.dev registry integration — dynamic model context windows.

Fetches https://models.dev/api.json (community-maintained, 4000+ models)
to resolve accurate context window sizes instead of hardcoded defaults.
Cache: in-memory (1h TTL) → disk (~/.debigbos/models_dev_cache.json).
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

MODELS_DEV_URL = "https://models.dev/api.json"
CACHE_TTL = 3600  # 1 hour
CACHE_DIR = Path.home() / ".debigbos"
CACHE_FILE = CACHE_DIR / "models_dev_cache.json"

# In-memory cache
_cache_data: dict[str, Any] = {}
_cache_time: float = 0.0

# deBigBos provider names → models.dev provider IDs
PROVIDER_MAP: dict[str, str] = {
    "opencode-zen": "opencode",
    "opencode-go": "opencode-go",
    "openai": "openai",
    "anthropic": "anthropic",
    "deepseek": "deepseek",
    "groq": "groq",
    "mistral": "mistral",
    "gemini": "google",
    "openrouter": "openrouter",
}


def _load_disk_cache() -> dict[str, Any]:
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_disk_cache(data: dict[str, Any]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    except Exception:
        pass


def _disk_cache_age() -> Optional[float]:
    try:
        if not CACHE_FILE.exists():
            return None
        return time.time() - CACHE_FILE.stat().st_mtime
    except Exception:
        return None


def fetch_models_dev(force: bool = False) -> dict[str, Any]:
    """Fetch models.dev registry with tiered cache."""
    global _cache_data, _cache_time

    if not force and _cache_data and (time.time() - _cache_time) < CACHE_TTL:
        return _cache_data

    if not force:
        age = _disk_cache_age()
        if age is not None and age < CACHE_TTL:
            disk = _load_disk_cache()
            if disk:
                _cache_data = disk
                _cache_time = time.time() - age
                return _cache_data

    try:
        response = httpx.get(MODELS_DEV_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data:
            _cache_data = data
            _cache_time = time.time()
            _save_disk_cache(data)
            return data
    except Exception:
        logger.debug("Failed to fetch models.dev", exc_info=True)

    # Fallback to any disk cache
    if not _cache_data:
        _cache_data = _load_disk_cache()
        if _cache_data:
            _cache_time = time.time() - CACHE_TTL + 300
    return _cache_data


def get_context_window(provider: str, model: str) -> Optional[int]:
    """Look up context window from models.dev. Returns None if not found."""
    mdev_id = PROVIDER_MAP.get(provider)
    if not mdev_id:
        return None

    data = fetch_models_dev()
    provider_data = data.get(mdev_id)
    if not isinstance(provider_data, dict):
        return None

    models = provider_data.get("models", {})
    if not isinstance(models, dict):
        return None

    entry = models.get(model)
    if not isinstance(entry, dict):
        # Case-insensitive fallback
        ml = model.lower()
        for mid, mdata in models.items():
            if isinstance(mdata, dict) and mid.lower() == ml:
                entry = mdata
                break

    if isinstance(entry, dict):
        limit = entry.get("limit")
        if isinstance(limit, dict):
            ctx = limit.get("context")
            if isinstance(ctx, (int, float)) and ctx > 0:
                return int(ctx)

    return None
