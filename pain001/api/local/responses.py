# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
The 'message' field is informational/debug only.
The 'code' field is what the frontend uses to look up text in its own i18n dict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CODES_PATH = Path(__file__).parent / "message-codes.json"
with _CODES_PATH.open(encoding="utf-8") as _f:
    MESSAGE_CODES: dict[str, Any] = json.load(_f)


def success_response(
    code: str,
    data: Any = None,
) -> dict[str, Any]:
    """Build a standard success response envelope."""
    payload: dict[str, Any] = {
        "code": code,
        "message": code,
    }
    if data is not None:
        payload["data"] = data
    return payload


def error_response(
    code: str,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a standard error response envelope."""
    payload: dict[str, Any] = {
        "code": code,
        "message": code,
    }
    if errors:
        payload["errors"] = {"details": errors}
    return payload