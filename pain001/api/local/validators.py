# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request, UploadFile, status

from pain001.api.local.constants import (
    LOCAL_TEMPLATE_ROOT,
    MAX_FILE_SIZE,
    MAX_FILE_SIZE_MB,
    TEMP_DIR,
    UPLOAD_CHUNK_SIZE,
)
from pain001.api.local.enums import (
    LOCAL_TEMPLATE_FILENAMES,
    ROW_TYPE_VALUES,
    LocalTemplateType,
)
from pain001.api.local.models import PaymentRow
from pain001.api.local.responses import error_response, message_code

# [HN] fields taken from data[0] only when building the shared <Dbtr>/<DbtrAcct>/
# <DbtrAgt> block of the single <PmtInf> — every row in the request MUST agree
# on these, otherwise the XML would silently drop the debtor of every row
# beyond the first one.
DEBTOR_KEY_FIELDS: tuple[str, ...] = (
    "debtor_account_IBAN",
    "debtor_name",
    "debtor_clearing_member_id",
)


def resolve_template_path(template_type: LocalTemplateType) -> Path:
    """Return the absolute path of the Jinja2 XML template.

    Raises:
        HTTPException 404: Template file not present in container image.
    """
    filename = LOCAL_TEMPLATE_FILENAMES[template_type]
    path = LOCAL_TEMPLATE_ROOT / "xml" / f"{filename}.xml"
    if not path.exists():
        code = message_code("error", "payment", "TEMPLATE_NOT_FOUND")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code, errors=[{
                "field": "template",
                "code": code,
                "message": f"File not found: {path.name}",
            }]),
        )
    return path


def assert_consistent_debtor(data: list[dict[str, Any]]) -> None:
    """All rows in a request must share the same debtor account.

    A single request maps to a single ISO 20022 <PmtInf>, whose <Dbtr>/
    <DbtrAcct>/<DbtrAgt> block is rendered once from `data[0]` — the
    template has no way to represent a different debtor per transaction.
    Rather than silently applying row 0's debtor to every transaction, this
    rejects the request explicitly so the caller can split it per debtor.

    Args:
        data: Loaded payment rows (already passed through `load_payment_data`).

    Raises:
        HTTPException 400: some row disagrees with row 0 on a DEBTOR_KEY_FIELDS value.
    """
    if len(data) < 2:
        return

    reference = {field: data[0].get(field, "") for field in DEBTOR_KEY_FIELDS}

    for index, row in enumerate(data[1:], start=1):
        for field in DEBTOR_KEY_FIELDS:
            row_value = row.get(field, "")
            if row_value != reference[field]:
                code = message_code("error", "payment", "INCONSISTENT_DEBTOR")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(code, errors=[{
                        "field": field,
                        "code": code,
                        "message": (
                            f"Row {index} has {field}={row_value!r}, but row 0 has "
                            f"{reference[field]!r}. All transactions in a request "
                            "must share the same debtor account."
                        ),
                    }]),
                )


def assert_valid_row_types(data: list[dict[str, Any]]) -> None:
    """Reject rows whose optional `type` is set but not a known transaction kind.

    `type` is only meaningful for the mixed template (per-row ach/
    between_accounts/odp); an unrecognized value would otherwise be silently
    ignored by the template's conditionals, generating a structurally wrong
    <CdtTrfTxInf> without any warning.

    Args:
        data: Loaded payment rows (already passed through `load_payment_data`).

    Raises:
        HTTPException 422: some row's `type` is set but not in ROW_TYPE_VALUES.
    """
    for index, row in enumerate(data):
        raw_type = row.get("type", row.get("local_instrument", ""))
        row_type = (raw_type or "").strip().lower()
        if row_type and row_type not in ROW_TYPE_VALUES:
            code = message_code("error", "fields", "INVALID_FIELD")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_response(code, errors=[{
                    "field": f"data[{index}].type",
                    "code": code,
                    "message": (
                        f"Invalid type {raw_type!r} in row {index}. "
                        f"Expected one of: {sorted(ROW_TYPE_VALUES)}."
                    ),
                }]),
            )


def uses_mixed_template(template: LocalTemplateType, data: list[dict[str, Any]]) -> bool:
    """Whether a request must be routed to the mixed template.

    True when the caller explicitly asked for `template=mixed`, or when any
    row carries a `type`/`local_instrument` — in that case the request is
    routed to the mixed template regardless of `template`, keeping the base
    templates (ach/between_accounts/odp) fully retro-compatible.
    """
    if template == LocalTemplateType.mixed:
        return True
    return any(
        (row.get("type") or row.get("local_instrument") or "").strip()
        for row in data
    )


def check_content_length(request: Request) -> None:
    """Reject oversized requests before reading the body.

    Reads the Content-Length header — if present and over the limit,
    rejects immediately without touching the file stream.
    FastAPI may still buffer small files, but this short-circuits
    large uploads early at the HTTP layer.

    Args:
        request: The incoming FastAPI request.

    Raises:
        HTTPException 400: Content-Length exceeds MAX_FILE_SIZE.
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        code = message_code("error", "fields", "FILE_TOO_LARGE")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code, errors=[{
                "field": "csv_file",
                "code": code,
                "message": f"File size exceeds the {MAX_FILE_SIZE_MB}MB limit",
            }]),
        )


def validate_upload(upload: UploadFile) -> bytes:
    """Read and validate the uploaded file.

    Checks extension (.csv) and size (MAX_FILE_SIZE).
    Reads in chunks to catch oversized files without loading
    the full content into memory first.

    Args:
        upload: The FastAPI UploadFile object.

    Returns:
        Raw bytes of the file content.

    Raises:
        HTTPException 400: Invalid file type, size, or read error.
    """
    filename = upload.filename or ""
    if not filename.lower().endswith(".csv"):
        code = message_code("error", "fields", "INVALID_FILE_TYPE")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code, errors=[{
                "field": "csv_file",
                "code": code,
                "message": f"Expected .csv file, got {Path(filename).suffix or 'unknown'}",
            }]),
        )

    chunks: list[bytes] = []
    total = 0
    size_code = message_code("error", "fields", "FILE_TOO_LARGE")
    read_code = message_code("error", "fields", "FILE_READ_ERROR")

    try:
        for chunk in iter(lambda: upload.file.read(UPLOAD_CHUNK_SIZE), b""):
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(size_code, errors=[{
                        "field": "csv_file",
                        "code": size_code,
                        "message": f"File size exceeds the {MAX_FILE_SIZE_MB}MB limit",
                    }]),
                )
            chunks.append(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(read_code),
        ) from exc

    return b"".join(chunks)


def save_to_temp(contents: bytes, suffix: str = ".csv") -> Path:
    """Write bytes to a temp file inside TEMP_DIR and return its path.

    The caller is responsible for cleanup (unlink in finally block).
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, mode="wb", dir=str(TEMP_DIR)
    )
    tmp.write(contents)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def rows_to_csv_text(rows: list[dict[str, Any]]) -> str:
    """Serialize already-normalized (snake_case) payment rows into CSV text.

    Column order follows `PaymentRow.model_fields` (the declared row
    contract), with any extra key found in the rows themselves — allowed by
    `PaymentRow`'s `extra="allow"` — appended afterwards in first-seen
    order, so the header stays stable across requests. Missing keys render
    as empty cells (`csv.DictWriter` fills gaps for fields absent from a
    given row, and the stdlib `csv` module writes `None` values as empty
    strings too), producing a CSV that can be fed straight back into
    `/local/hn/generate/csv`.
    """
    fieldnames = list(PaymentRow.model_fields.keys())
    known_fields = set(fieldnames)
    for row in rows:
        for key in row:
            if key not in known_fields:
                fieldnames.append(key)
                known_fields.add(key)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
