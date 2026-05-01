"""Configuration for edgar_analyst.

Loads required environment variables from .env at the project root and
validates them on first access. Constants that do not change at runtime
(API URLs, model name, paths) are also defined here so the rest of the
codebase has one place to look.

Usage:
    from edgar_analyst.config import get_settings, ANTHROPIC_MODEL

    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# Resolve the project root from this file's location rather than from the
# current working directory. This makes the package importable and runnable
# from anywhere (tests, scripts, notebooks) without breaking config loading.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Constants
#
# These do not vary by environment. Centralizing them here means one edit
# point if (for example) we change models or EDGAR moves an endpoint.
# ---------------------------------------------------------------------------

ANTHROPIC_MODEL = "claude-sonnet-4-6"
"""The Claude model used for the agent loop. Sonnet 4.6 balances cost and
capability for agentic, financial-analysis workloads."""

EDGAR_BASE_URL = "https://data.sec.gov"
"""Base URL for SEC EDGAR's structured data API (submissions, XBRL facts)."""

EDGAR_ARCHIVES_URL = "https://www.sec.gov/Archives"
"""Base URL for raw filing documents (HTML 10-Ks, 10-Qs, exhibits)."""

EDGAR_RATE_LIMIT_PER_SEC = 8
"""SEC publishes a 10 req/sec limit. We stay under it deliberately so a
burst of cache misses cannot trip the rate limiter."""

CACHE_DIR = _PROJECT_ROOT / "data" / "cache"
"""On-disk cache for EDGAR responses. Persistent across runs."""

OUTPUT_DIR = _PROJECT_ROOT / "out"
"""Directory where generated memos are written."""


# ---------------------------------------------------------------------------
# Runtime settings (validated environment variables)
# ---------------------------------------------------------------------------


class Settings(BaseModel):
    """Runtime settings loaded from environment variables.

    Validation runs at instantiation; missing or empty values raise
    a clear error before any tool or API call is attempted. Add new
    required env vars here as fields with `min_length=1` to enforce
    they are present and non-empty.
    """

    anthropic_api_key: str = Field(min_length=1)
    sec_user_agent: str = Field(min_length=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate runtime settings from environment.

    Lazy and cached: settings are read on first call (so importing this
    module in a test environment without a .env does not crash), and
    the same instance is returned on subsequent calls.

    Returns:
        Validated Settings instance.

    Raises:
        SystemExit: If any required environment variable is missing or
            empty. We fail fast with a human-readable message rather
            than letting downstream code error obscurely on a None value.
    """
    try:
        return Settings(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            sec_user_agent=os.getenv("SEC_USER_AGENT", ""),
        )
    except ValidationError as e:
        missing = [str(err["loc"][0]).upper() for err in e.errors()]
        raise SystemExit(
            f"Missing or empty required environment variables: {missing}.\n"
            f"Copy .env.example to .env and fill in the values."
        ) from e