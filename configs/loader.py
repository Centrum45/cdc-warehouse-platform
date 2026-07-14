from __future__ import annotations

"""
Configuration loader for environment-specific app config.

Load order:
    1. configs/app-{env}.yaml     (default: dev)
    2. environment variables inside ${VAR_NAME} or ${VAR_NAME:-default}

Environment selection:
    Set ENVIRONMENT env var to "dev", "staging", or "prod".
    Defaults to "dev" when unset.

Secrets:
    Values containing ${VAR_NAME} or ${VAR_NAME:-default} are resolved
    from environment variables automatically.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml

_CONFIG_ROOT = Path(__file__).resolve().parent
_ENV_RE = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${VAR} and ${VAR:-default} patterns in config values."""
    if isinstance(value, str):
        def _replacer(m: re.Match) -> str:
            var_name = m.group(1)
            default = m.group(2)
            return os.environ.get(var_name, default if default is not None else m.group(0))
        return _ENV_RE.sub(_replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def load_config(env: str | None = None) -> dict[str, Any]:
    """Load one environment config file and resolve env vars.

    Args:
        env: Environment name. Defaults to ENVIRONMENT env var or 'dev'.
    """
    environment = env or os.environ.get("ENVIRONMENT", "dev")

    env_path = _CONFIG_ROOT / f"app-{environment}.yaml"
    if not env_path.exists():
        raise FileNotFoundError(f"Environment config not found: {env_path}")
    with open(env_path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    config = _resolve_env_vars(config)

    return config


# Convenience: load config once at import time
_current_env = os.environ.get("ENVIRONMENT", "dev")
try:
    config = load_config(_current_env)
except FileNotFoundError:
    config = {}
