# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile, status

from pain001.api.local.constants import (
    LOCAL_TEMPLATE_ROOT,
    MAX_FILE_SIZE,
    MAX_FILE_SIZE_MB,
    TEMP_DIR,
    UPLOAD_CHUNK_SIZE,
)
from pain001.api.local.enums import LocalTemplateType
from pain001.api.local.responses import MESSAGE_CODES, error_response


def resolve_template_path(template_type: LocalTemplateType) -> Path:
    """Return the absolute path of the Jinja2 XML template.

    Raises:
        HTTPException 404: Template file not present in container image.
    """
    path = LOCAL_TEMPLATE_ROOT / "xml" / f"{template_type.value}.xml"
    if not path.exists():
        code = MESSAGE_CODES["error"]["payment"]["TEMPLATE_NOT_FOUND"]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code, errors=[{
                "field": "template",
                "code": code,
                "message": f"File not found: {path.name}",
            }]),
        )
    return path


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
        code = MESSAGE_CODES["error"]["fields"]["FILE_TOO_LARGE"]
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
        code = MESSAGE_CODES["error"]["fields"]["INVALID_FILE_TYPE"]
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
    size_code = MESSAGE_CODES["error"]["fields"]["FILE_TOO_LARGE"]
    read_code = MESSAGE_CODES["error"]["fields"]["FILE_READ_ERROR"]

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
    TEMP_DIR.mkdir(exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, mode="wb", dir=str(TEMP_DIR)
    )
    tmp.write(contents)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)