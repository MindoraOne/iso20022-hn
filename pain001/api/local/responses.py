# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""
The 'code' field is the i18n key that the consumer translates in its own
message dictionary into the end user's language. The 'message' field of
an error response is fixed text in ENGLISH (see CLIENT_MESSAGES): the
API's standard/technical language, not the one the user sees. It never
exposes internal details (namespaces, versions, raw exception text); those
details are only logged on the server.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CODES_PATH = Path(__file__).parent / "message-codes.json"
with _CODES_PATH.open(encoding="utf-8") as _f:
    MESSAGE_CODES: dict[str, Any] = json.load(_f)


def message_code(*path: str) -> str:
    """Accesses `MESSAGE_CODES` step by step, guarding against key typos.

    Walks `path` over `MESSAGE_CODES`, navigating one level per element. It
    is the only supported way to read a key from the JSON: a direct access
    like `MESSAGE_CODES["error"]["payment"]["TYPO"]` blows up with a
    cryptic `KeyError` (without indicating in which branch of the tree the
    key was missing); this function gives an actionable message instead.

    Args:
        *path: keys to walk in order, e.g. `("error", "payment", "CSV_INVALID")`.

    Returns:
        The code (string) at the leaf of the tree pointed to by `path`.

    Raises:
        KeyError: some intermediate key does not exist in `MESSAGE_CODES`.
        TypeError: `path` is valid but the leaf is not a string (code).
    """
    node: Any = MESSAGE_CODES
    visited: list[str] = []
    for key in path:
        visited.append(key)
        if not isinstance(node, dict) or key not in node:
            path_str = ".".join(visited)
            raise KeyError(
                f"Missing key '{key}' in message-codes.json (path: {path_str}). Add it before using it."
            )
        node = node[key]

    if not isinstance(node, str):
        path_str = ".".join(path)
        raise TypeError(
            f"Path '{path_str}' in message-codes.json does not point to a code (string); "
            f"it points to a {type(node).__name__}."
        )
    return node


# Fixed messages in ENGLISH (the API's standard language) that accompany `code`.
# Single place where this text lives: reused both by app_local.py (endpoints and
# exception handlers) and by validators.py, avoiding duplicating the
# code -> text mapping in every file that builds an envelope.
CLIENT_MESSAGES: dict[str, str] = {
    message_code("success", "payment", "XML_GENERATED"): "XML generated successfully.",
    message_code("success", "payment", "TEMPLATES_LISTED"): "Templates listed successfully.",
    message_code("success", "payment", "HEALTH_OK"): "Service is healthy.",
    message_code("error", "payment", "TEMPLATE_NOT_FOUND"): "The requested template was not found.",
    message_code("error", "payment", "GENERATION_FAILED"): "XML generation failed.",
    message_code("error", "payment", "XSD_INVALID"): "The generated XML does not comply with the ISO 20022 XSD schema.",
    message_code("error", "payment", "CSV_INVALID"): "Invalid or missing required fields in the payment data.",
    message_code("error", "payment", "INCONSISTENT_DEBTOR"): (
        "All transactions in a request must share the same debtor account. "
        "A single request maps to a single <PmtInf>, and its debtor block is "
        "taken from the first row only."
    ),
    message_code("error", "fields", "INVALID_FILE_TYPE"): "The uploaded file type is invalid.",
    message_code("error", "fields", "FILE_TOO_LARGE"): "File size exceeds the maximum allowed limit.",
    message_code("error", "fields", "FILE_READ_ERROR"): "The uploaded file could not be read.",
    message_code("error", "fields", "VALIDATION_FAILED"): "Request validation failed.",
    message_code("error", "fields", "MISSING_FIELD"): "This field is required.",
    message_code("error", "fields", "INVALID_FIELD"): "Invalid value for this field.",
    message_code("error", "fields", "UNKNOWN_FIELD"): "This field is not allowed.",
    message_code("error", "generic", "RATE_LIMIT_EXCEEDED"): "Too many requests. Please try again later.",
    message_code("error", "generic", "NOT_FOUND"): "Resource not found.",
    message_code("error", "generic", "METHOD_NOT_ALLOWED"): "Method not allowed.",
    message_code("error", "generic", "INTERNAL_ERROR"): "Internal service error.",
}


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
    """Build a standard error response envelope with the fixed English text from CLIENT_MESSAGES."""
    payload: dict[str, Any] = {
        "code": code,
        "message": CLIENT_MESSAGES.get(code, CLIENT_MESSAGES[message_code("error", "generic", "INTERNAL_ERROR")]),
    }
    if errors:
        payload["errors"] = {"details": errors}
    return payload
