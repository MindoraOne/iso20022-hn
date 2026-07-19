# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""
Endpoints (prefix defined once in API_PREFIX, see pain001/api/local/constants.py):
  GET  {API_PREFIX}/health                   — health check
  GET  {API_PREFIX}/local/hn/templates       — list available templates
  POST {API_PREFIX}/local/hn/generate        — JSON body (template + data) → XML
  POST {API_PREFIX}/local/hn/generate/csv    — upload CSV + template → XML
  POST {API_PREFIX}/local/hn/preview/csv     — JSON body (template + data) → CSV (sibling of /generate, for traceability)

Traceability: every request carries a `request_id` (incoming `X-Request-Id`
header, or a generated `uuid4` if none is provided) returned in the header of
EVERY response — success and error — and included in EVERY log line (see
`pain001/api/local/request_context.py`). No error, anticipated or not,
should escape without going through the standard envelope (`error_response`).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from pain001 import __version__
from pain001.api.local.constants import (
    API_PREFIX,
    LOCAL_TEMPLATE_ROOT,
    MESSAGE_TYPE,
    XSD_PATH,
)
from pain001.api.local.enums import LOCAL_TEMPLATE_FILENAMES, LocalTemplateType
from pain001.api.local.limiter import limiter
from pain001.api.local.models import GenerateJsonRequest
from pain001.api.local.request_context import (
    REQUEST_ID_HEADER,
    RequestIdLogFilter,
    reset_request_id,
    set_request_id,
)
from pain001.api.local.responses import (
    CLIENT_MESSAGES,
    error_response,
    message_code,
    success_response,
)
from pain001.api.local.settings import settings
from pain001.api.local.validators import (
    assert_consistent_debtor,
    assert_valid_row_types,
    check_content_length,
    resolve_template_path,
    rows_to_csv_text,
    save_to_temp,
    uses_mixed_template,
    validate_upload,
)
from pain001.data.loader import load_payment_data
from pain001.exceptions import DataSourceError, PaymentValidationError
from pain001.xml.generate_xml import generate_xml_string

# `force=True`: guarantees that the format with `request_id` is applied even if
# the root logger already has handlers configured by the runner (e.g. pytest).
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [request_id=%(request_id)s] %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

# The filter is added to the root HANDLER (not to this module's logger): the
# format above requires `%(request_id)s` on ANY record that passes through
# that handler, including those from third-party libraries (httpx, uvicorn,
# etc.) that propagate to the root — if we only filtered our own logger, those
# foreign records would blow up the Formatter with a KeyError at log time.
for _root_handler in logging.getLogger().handlers:
    _root_handler.addFilter(RequestIdLogFilter())

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
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _internal_error_response() -> JSONResponse:
    """Standard envelope for an unanticipated error (500), without leaking internal detail.

    Shared by the request_id middleware (which catches any uncontrolled
    exception BEFORE it escapes our own middleware stack) and by
    `unhandled_exception_handler` (safety net for anything happening outside
    that middleware, e.g. in `CORSMiddleware`).
    """
    code = message_code("error", "generic", "INTERNAL_ERROR")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response(code))


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Correlates each request with a `request_id` end to end.

    Takes `X-Request-Id` from the caller if provided, or generates a
    `uuid4`. Stores it in `request.state.request_id` and in the
    `ContextVar` from `request_context` (so `RequestIdLogFilter` injects it
    into every log line of this process). Added AFTER `CORSMiddleware` so
    that, in the middleware stack, it stays closer to the router.

    Starlette routes any handler registered for the base `Exception` class
    (see `unhandled_exception_handler`) through `ServerErrorMiddleware`,
    which is the OUTERMOST middleware — outside this one. If we let an
    uncontrolled exception simply escape `call_next`, that outer handler
    would respond without the `X-Request-Id` header (this middleware's
    context is already lost) and without being able to log with the
    correct request_id. That's why any unanticipated `Exception` is caught
    right here, logged with the current request_id, and the enveloped 500
    response is built — guaranteeing the header on EVERY response, success
    and error.
    """
    incoming_id = request.headers.get(REQUEST_ID_HEADER)
    request_id = incoming_id if incoming_id else str(uuid4())
    request.state.request_id = request_id
    token = set_request_id(request_id)
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error")
            response = _internal_error_response()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        reset_request_id(token)


# Exception handlers

# Our own codes per HTTP status for errors that Starlette/FastAPI raise
# outside our endpoints (nonexistent route, unsupported method).
_STATUS_CODE_MAP: dict[int, str] = {
    status.HTTP_404_NOT_FOUND: message_code("error", "generic", "NOT_FOUND"),
    status.HTTP_405_METHOD_NOT_ALLOWED: message_code("error", "generic", "METHOD_NOT_ALLOWED"),
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Wrap any HTTPException in the standard error envelope.

    Registered on Starlette's BASE class (not just FastAPI's): the 404/405
    errors built by Starlette's router are instances of that base class,
    and without this registration they would escape the envelope,
    responding in FastAPI's raw `{"detail": ...}` format.
    """
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)

    code = _STATUS_CODE_MAP.get(exc.status_code, message_code("error", "generic", "INTERNAL_ERROR"))
    logger.warning("HTTPException without its own envelope (status=%s): %s", exc.status_code, detail)
    return JSONResponse(status_code=exc.status_code, content=error_response(code))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        err_type = err.get("type", "")

        if err_type == "missing":
            code = message_code("error", "fields", "MISSING_FIELD")
        elif err_type == "extra_forbidden":
            code = message_code("error", "fields", "UNKNOWN_FIELD")
        else:
            code = message_code("error", "fields", "INVALID_FIELD")

        errors.append({"field": field, "code": code, "message": CLIENT_MESSAGES[code]})

    top_code = message_code("error", "fields", "VALIDATION_FAILED")
    logger.warning("RequestValidationError: %s", exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(top_code, errors=errors),
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return rate limit errors in the standard error envelope."""
    code = message_code("error", "generic", "RATE_LIMIT_EXCEEDED")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response(code),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Additional safety net for unanticipated errors.

    Starlette invokes this handler via `ServerErrorMiddleware` (the
    outermost in the stack), outside `request_id_middleware` — that's why,
    in the normal path, `request_id_middleware` already catches the
    exception before it gets here (see its docstring). This handler only
    acts if something blows up outside that middleware (e.g. in
    `CORSMiddleware`); it must never leak the stack/internal detail to the
    client.
    """
    logger.exception("Unhandled error (outside request_id_middleware)")
    return _internal_error_response()


# Routes

router = APIRouter(prefix=API_PREFIX)


@router.get("/health", tags=["Health"], summary="Health check")
@limiter.limit(settings.rate_limit_health)
async def health(request: Request) -> dict[str, Any]:
    code = message_code("success", "payment", "HEALTH_OK")
    return success_response(code, data={"version": __version__})


@router.get(
    "/local/hn/templates",
    tags=["Templates"],
    summary="List available local templates",
)
@limiter.limit(settings.rate_limit_templates)
async def list_templates(request: Request) -> dict[str, Any]:
    templates = []
    for t in LocalTemplateType:
        xml_path = LOCAL_TEMPLATE_ROOT / "xml" / f"{LOCAL_TEMPLATE_FILENAMES[t]}.xml"
        templates.append({
            "key": t.name,
            "template": t.value,
            "xmlPresent": xml_path.exists(),
        })
    code = message_code("success", "payment", "TEMPLATES_LISTED")
    return success_response(code, data=templates)


@router.post(
    "/local/hn/generate",
    tags=["Generation"],
    summary="Generate ISO 20022 XML from a JSON payload",
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
@limiter.limit(settings.rate_limit_generate)
async def generate_xml_json(
    request: Request,
    body: GenerateJsonRequest,
) -> Response:
    """Generate pain.001.001.05 XML from a JSON body (service-to-service).

    `body.data` rows carry camelCase keys (the public JSON contract),
    declared as `PaymentRow` (see `pain001/api/local/models.py`); each row
    is dumped to pain001's internal snake_case keys via
    `model_dump(by_alias=False)` before being handed to `load_payment_data`
    in memory — same field-level validation rules as the CSV path, no temp
    file involved.

    Returns application/xml on success.
    Returns the standard JSON error envelope on failure.
    """
    check_content_length(request)
    logger.info("Generate (JSON) — template=%s rows=%d", body.template.name, len(body.data))

    normalized_data = [row.model_dump(by_alias=False, exclude_none=True) for row in body.data]

    try:
        data = load_payment_data(normalized_data)
    except (ValueError, PaymentValidationError, DataSourceError) as exc:
        code = message_code("error", "payment", "CSV_INVALID")
        logger.warning("generate (json) rejected (%s): %s", code, exc)
        # The caller is the internal backend (trusted) — we return the real
        # reason from load_payment_data/validate_csv_data (row/field/rule that
        # failed) instead of the generic CLIENT_MESSAGES text.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code, errors=[{
                "field": "data",
                "code": code,
                "message": str(exc) or CLIENT_MESSAGES[code],
            }]),
        ) from exc

    # `nbOfTxs` (GrpHdr and PmtInf) is COMPUTED by this service, not trusted
    # from the caller: it is always overwritten with the real row count, so a
    # mismatched input value (e.g. "1" with 3 rows) can never desync the
    # header from the actual number of <CdtTrfTxInf> blocks in the XML.
    if data:
        data[0]["nb_of_txs"] = str(len(data))

    assert_valid_row_types(data)
    assert_consistent_debtor(data)

    template = LocalTemplateType.mixed if uses_mixed_template(body.template, data) else body.template
    xml_template_path = resolve_template_path(template)

    try:
        xml_content = generate_xml_string(
            data=data,
            payment_initiation_message_type=MESSAGE_TYPE,
            xml_template_path=str(xml_template_path),
            xsd_schema_path=str(XSD_PATH),
        )
    except RuntimeError as exc:
        code = message_code("error", "payment", "XSD_INVALID")
        logger.warning("generate (json) rejected (%s): %s", code, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code, errors=[{
                "field": "",
                "code": code,
                "message": CLIENT_MESSAGES[code],
            }]),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during generation")
        code = message_code("error", "payment", "GENERATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code),
        ) from exc

    logger.info("Generated (JSON) — template=%s (resolved=%s)", body.template.name, template.name)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{LOCAL_TEMPLATE_FILENAMES[template]}.xml"'
        },
    )


@router.post(
    "/local/hn/preview/csv",
    tags=["Generation"],
    summary="Preview the internal CSV equivalent of a JSON payload",
    response_class=Response,
    responses={
        200: {"content": {"text/csv": {}}, "description": "CSV equivalent of the JSON payload"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_generate)
async def preview_csv_json(
    request: Request,
    body: GenerateJsonRequest,
) -> Response:
    """Sibling of `/local/hn/generate`: same JSON body, but returns the
    internal CSV representation instead of the generated XML — useful for
    traceability/debug (see exactly what CSV pain001's engine would consume
    for a given JSON request).

    Does not touch XML generation nor `load_payment_data`'s field
    validation: it is a pure JSON -> CSV format translation, reusing the
    same row normalization (`model_dump(by_alias=False)`) and `nb_of_txs`
    computation as `generate_xml_json`, so the CSV emitted here is exactly
    what that endpoint would internally build before handing it to the
    XML template — round-trippable through `/local/hn/generate/csv`.

    Returns text/csv on success.
    Returns the standard JSON error envelope on failure (body validation).
    """
    logger.info("Preview CSV — template=%s rows=%d", body.template.name, len(body.data))

    normalized_data = [row.model_dump(by_alias=False, exclude_none=False) for row in body.data]

    # Same rationale as generate_xml_json: nb_of_txs always reflects the
    # real row count, so the CSV preview matches what generation would use.
    if normalized_data:
        normalized_data[0]["nb_of_txs"] = str(len(normalized_data))

    csv_content = rows_to_csv_text(normalized_data)

    logger.info("Preview CSV generated — template=%s rows=%d", body.template.name, len(normalized_data))
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{LOCAL_TEMPLATE_FILENAMES[body.template]}_preview.csv"'
        },
    )


@router.post(
    "/local/hn/generate/csv",
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
@limiter.limit(settings.rate_limit_generate)
async def generate_xml_csv(
    request: Request,
    template: Annotated[
        LocalTemplateType,
        Form(description="Template key: ach, between_accounts, odp, mixed"),
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

    # Reject unknown form fields
    ALLOWED_FIELDS = {"template", "csv_file"}
    form_data = await request.form()
    extra_fields = set(form_data.keys()) - ALLOWED_FIELDS
    if extra_fields:
        code = message_code("error", "fields", "UNKNOWN_FIELD")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(code, errors=[{
                "field": field,
                "code": code,
                "message": CLIENT_MESSAGES[code],
            } for field in sorted(extra_fields)]),
        )

    logger.info("Generate — template=%s file=%s", template.name, csv_file.filename)

    tmp_csv_path: Path | None = None
    try:
        contents = validate_upload(csv_file)
        tmp_csv_path = save_to_temp(contents)

        # PaymentValidationError is pain001's own exception — must be caught
        # explicitly as it does not inherit from ValueError
        try:
            data = load_payment_data(str(tmp_csv_path))
        except (ValueError, FileNotFoundError, PaymentValidationError) as exc:
            code = message_code("error", "payment", "CSV_INVALID")
            logger.warning("generate (csv) rejected (%s): %s", code, exc)
            # The caller is the internal backend (trusted) — we return the
            # real reason from load_payment_data (row/field/rule that failed)
            # instead of the generic CLIENT_MESSAGES text.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code, errors=[{
                    "field": "csv_file",
                    "code": code,
                    "message": str(exc) or CLIENT_MESSAGES[code],
                }]),
            ) from exc

        # `nbOfTxs` (GrpHdr and PmtInf) is COMPUTED by this service, not
        # trusted from the caller: see the JSON endpoint above for the
        # rationale (mismatched CSV `nb_of_txs` column is ignored).
        if data:
            data[0]["nb_of_txs"] = str(len(data))

        assert_valid_row_types(data)
        assert_consistent_debtor(data)

        resolved_template = LocalTemplateType.mixed if uses_mixed_template(template, data) else template
        xml_template_path = resolve_template_path(resolved_template)

        try:
            xml_content = generate_xml_string(
                data=data,
                payment_initiation_message_type=MESSAGE_TYPE,
                xml_template_path=str(xml_template_path),
                xsd_schema_path=str(XSD_PATH),
            )
        except RuntimeError as exc:
            code = message_code("error", "payment", "XSD_INVALID")
            logger.warning("generate (csv) rejected (%s): %s", code, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code, errors=[{
                    "field": "",
                    "code": code,
                    "message": CLIENT_MESSAGES[code],
                }]),
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error during generation")
            code = message_code("error", "payment", "GENERATION_FAILED")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(code),
            ) from exc

        logger.info("Generated — template=%s (resolved=%s)", template.name, resolved_template.name)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="{LOCAL_TEMPLATE_FILENAMES[resolved_template]}.xml"'
            },
        )

    finally:
        if tmp_csv_path and tmp_csv_path.exists():
            tmp_csv_path.unlink(missing_ok=True)


app.include_router(router)
