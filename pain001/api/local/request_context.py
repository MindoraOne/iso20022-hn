# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Request correlation (traceability) for the local API.

`REQUEST_ID_CTX` stores the request_id of the request in progress via
`ContextVar` (safe across concurrent asyncio requests, unlike a mutable
global). `RequestIdLogFilter` injects that value as a `request_id`
attribute on every `LogRecord` that passes through the logger the filter is
added to, so the logging format can include `%(request_id)s` on EVERY
line without having to pass it explicitly on every `logger.*` call.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

# Default "-" for log lines emitted outside a request (process startup,
# background tasks) — must never be left empty in the format.
NO_REQUEST_ID = "-"

# Standard correlation header: inbound (if the caller already brings its own)
# and outbound (always, on success and error) — see middleware in app_local.py.
REQUEST_ID_HEADER = "X-Request-Id"

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)


def set_request_id(request_id: str):
    """Sets the request_id of the current context. Returns the token for reset()."""
    return _request_id_ctx.set(request_id)


def reset_request_id(token) -> None:
    """Restores the previous context (always call in the middleware's `finally`)."""
    _request_id_ctx.reset(token)


def get_request_id() -> str:
    """Request_id of the current context, or `NO_REQUEST_ID` outside a request."""
    return _request_id_ctx.get()


class RequestIdLogFilter(logging.Filter):
    """Adds `record.request_id` so the `Formatter` includes it in the message."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
