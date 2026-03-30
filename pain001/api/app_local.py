# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Endpoints:
  GET  /api/v1/health                   — health check
  GET  /api/v1/local/hn/templates       — list available templates
  POST /api/v1/local/hn/generate        — upload CSV + template → XML
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded

from pain001 import __version__
from pain001.api.local.constants import LOCAL_TEMPLATE_ROOT, MESSAGE_TYPE, XSD_PATH
from pain001.api.local.enums import LocalTemplateType
from pain001.api.local.limiter import limiter
from pain001.api.local.responses import MESSAGE_CODES, error_response, success_response
from pain001.api.local.validators import resolve_template_path, save_to_temp, validate_upload, check_content_length
from pain001.data.loader import load_payment_data
from pain001.exceptions import PaymentValidationError
from pain001.xml.generate_xml import generate_xml_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App

app = FastAPI(
    title="Pain001 Local API",
    description="ISO 20022 pain.001.001.05 XML generation for local bank payment templates.",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Wrap plain HTTPException detail in the standard error envelope."""
    detail = exc.detail
    if not isinstance(detail, dict):
        code = MESSAGE_CODES["error"]["generic"]["INTERNAL_ERROR"]
        detail = error_response(code, errors=[{
            "field": "",
            "code": code,
            "message": str(detail),
        }])
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        err_type = err.get("type", "")
 
        if err_type == "missing":
            code = MESSAGE_CODES["error"]["fields"]["MISSING_FIELD"]
            message = "This field is required"
        else:
            code = MESSAGE_CODES["error"]["fields"]["INVALID_FIELD"]
            message = "Invalid value for this field"
 
        errors.append({"field": field, "code": code, "message": message})
 
    top_code = MESSAGE_CODES["error"]["fields"]["VALIDATION_FAILED"]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(top_code, errors=errors),
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return rate limit errors in the standard error envelope."""
    code = MESSAGE_CODES["error"]["generic"]["RATE_LIMIT_EXCEEDED"]
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response(code),
    )

# Routes

@app.get("/api/v1/health", tags=["Health"], summary="Health check")
@limiter.limit("60/minute")
async def health(request: Request) -> dict[str, Any]:
    code = MESSAGE_CODES["success"]["payment"]["HEALTH_OK"]
    return success_response(code, data={"version": __version__})


@app.get(
    "/api/v1/local/hn/templates",
    tags=["Templates"],
    summary="List available local templates",
)
@limiter.limit("30/minute")
async def list_templates(request: Request) -> dict[str, Any]:
    templates = []
    for t in LocalTemplateType:
        xml_path = LOCAL_TEMPLATE_ROOT / "xml" / f"{t.value}.xml"
        templates.append({
            "key": t.name,
            "template": t.value,
            "xml_present": xml_path.exists(),
        })
    code = MESSAGE_CODES["success"]["payment"]["TEMPLATES_LISTED"]
    return success_response(code, data=templates)


@app.post(
    "/api/v1/local/hn/generate",
    tags=["Generation"],
    summary="Generate ISO 20022 XML from CSV upload",
    response_class=Response,
    responses={
        200: {"content": {"application/xml": {}}, "description": "ISO 20022 XML"},
        400: {"description": "Invalid input"},
        404: {"description": "Template not found"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Generation failed"},
    },
)
@limiter.limit("10/minute")
async def generate_xml(
    request: Request,
    template: Annotated[
        LocalTemplateType,
        Form(description="Template key: ach, between_accounts, odp"),
    ],
    csv_file: Annotated[
        UploadFile,
        File(description="CSV file with payment data"),
    ],
) -> Response:
    """Generate pain.001.001.05 XML from a CSV upload.

    Returns application/xml on success.
    Returns the standard JSON error envelope on failure.
    """
    check_content_length(request)
    logger.info("Generate — template=%s file=%s", template.name, csv_file.filename)

    xml_template_path = resolve_template_path(template)
    tmp_csv_path: Path | None = None

    try:
        contents = validate_upload(csv_file)
        tmp_csv_path = save_to_temp(contents)

        # PaymentValidationError is pain001's own exception — must be caught
        # explicitly as it does not inherit from ValueError
        try:
            data = load_payment_data(str(tmp_csv_path))
        except (ValueError, FileNotFoundError, PaymentValidationError) as exc:
            code = MESSAGE_CODES["error"]["payment"]["CSV_INVALID"]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code, errors=[{
                    "field": "csv_file",
                    "code": code,
                    "message": "Invalid or missing required columns in the uploaded CSV."
                }]),
            ) from exc

        try:
            xml_content = generate_xml_string(
                data=data,
                payment_initiation_message_type=MESSAGE_TYPE,
                xml_template_path=str(xml_template_path),
                xsd_schema_path=str(XSD_PATH),
            )
        except RuntimeError as exc:
            code = MESSAGE_CODES["error"]["payment"]["XSD_INVALID"]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code, errors=[{
                    "field": "",
                    "code": code,
                    "message": "The generated XML does not comply with the ISO 20022 XSD schema.",
                }]),
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error during generation")
            code = MESSAGE_CODES["error"]["payment"]["GENERATION_FAILED"]
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(code),
            ) from exc

        logger.info("Generated — template=%s", template.name)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="{template.value}.xml"'
            },
        )

    finally:
        if tmp_csv_path and tmp_csv_path.exists():
            tmp_csv_path.unlink(missing_ok=True)