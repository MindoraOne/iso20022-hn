# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Per-environment configuration for the service (pattern recommended by FastAPI).

Uses `pydantic-settings` instead of scattered hardcoded constants: a single
point that reads `.env`, validates types, and exposes explicit defaults.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_temp_dir() -> str:
    """``tmp`` subfolder inside the process cwd (not the OS temp dir).

    `pain001.data.loader._load_from_file` anchors every data path to
    `os.getcwd()` (protection against path traversal, see
    `pain001/security/path_validator.py`: `base_dir=os.getcwd()`), so any
    `TEMP_DIR` outside the cwd (for example `tempfile.gettempdir()`,
    typically `/tmp`) makes `validate_path` reject the uploaded CSV with
    `SecurityError` even in a legitimate flow. That's why the default runs
    inside the cwd — it works with no extra configuration outside Docker —
    and inside the container it matches `/app/tmp` because `WORKDIR` is
    `/app` (the `Dockerfile` also explicitly sets `ENV TEMP_DIR=/app/tmp`).
    """
    return str(Path.cwd() / "tmp")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 8000
    host: str = "0.0.0.0"
    cors_origins: str = "*"
    max_body_size: int = 5 * 1024 * 1024
    rate_limit_health: str = "60/minute"
    rate_limit_templates: str = "30/minute"
    rate_limit_generate: str = "10/minute"
    log_level: str = "INFO"

    # Temp directory for uploaded CSVs (see validators.save_to_temp).
    temp_dir: str = Field(default_factory=_default_temp_dir)

    # Bank subfolder under templates/local/ that holds the active
    # Jinja2 templates (see LOCAL_TEMPLATE_ROOT in constants.py)
    local_template_bank: str = "bancatlan"

    @property
    def cors_origins_list(self) -> list[str]:
        """Comma-separated in `.env` -> list of origins for CORSMiddleware."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
