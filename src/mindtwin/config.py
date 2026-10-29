"""Project settings.

Precedence (highest first): environment variables ``MINDTWIN_<FIELD>``, a TOML file
(``mindtwin.toml`` in the working directory, or the path in ``MINDTWIN_CONFIG``), then defaults.

    from mindtwin.config import get_settings
    settings = get_settings()
    settings.data_dir
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

ENV_PREFIX = "MINDTWIN_"
DEFAULT_CONFIG_FILE = "mindtwin.toml"


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    data_dir: Path = Field(Path("data/raw/cmapss"), description="Where C-MAPSS files live")
    results_dir: Path = Field(Path("experiments/results"), description="Experiment outputs")
    seed: int = Field(42, description="Default random seed")
    rul_cap: int = Field(125, gt=0, description="Piecewise-linear RUL cap")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


def _from_env() -> dict[str, Any]:
    values = {}
    for name in Settings.model_fields:
        key = ENV_PREFIX + name.upper()
        if key in os.environ:
            values[name] = os.environ[key]
    return values


def _from_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        env_path = os.environ.get(ENV_PREFIX + "CONFIG")
        path = Path(env_path) if env_path else Path(DEFAULT_CONFIG_FILE)
        if not path.exists():
            return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_settings(path: Path | None = None) -> Settings:
    """Build settings from defaults, a TOML file and the environment."""
    return Settings(**{**_from_file(path), **_from_env()})


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings for the current process."""
    return load_settings()
