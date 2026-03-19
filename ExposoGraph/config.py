"""Runtime configuration helpers for app deployment modes."""

from __future__ import annotations

import os
from enum import Enum
from typing import Mapping


class AppMode(str, Enum):
    STATELESS = "stateless"
    LOCAL = "local"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"


def normalize_app_mode(value: str | None) -> AppMode:
    """Normalize environment/config values into a supported app mode."""
    if value is None:
        return AppMode.STATELESS

    cleaned = value.strip().lower()
    aliases = {
        "stateless": AppMode.STATELESS,
        "public": AppMode.STATELESS,
        "web": AppMode.STATELESS,
        "local": AppMode.LOCAL,
        "curation": AppMode.LOCAL,
        "persistent": AppMode.LOCAL,
    }
    return aliases.get(cleaned, AppMode.STATELESS)


def get_app_mode(env: Mapping[str, str] | None = None) -> AppMode:
    """Resolve the current app mode from the environment."""
    source = env if env is not None else os.environ
    return normalize_app_mode(source.get("ExposoGraph_MODE"))


def persistence_enabled(mode: AppMode | str) -> bool:
    """Whether server-side persistence features are allowed."""
    normalized = mode if isinstance(mode, AppMode) else normalize_app_mode(mode)
    return normalized == AppMode.LOCAL
