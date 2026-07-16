# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""HTTP contract tests for the local API (HN) — do not depend on the
real fixtures (PII) in tests/fixtures/real/, must always run.

The exception is `test_generate_json_valid_returns_xml`: it exercises
`/local/hn/generate` end to end and therefore does need the real Jinja2
template (`pain001/templates/local/bancatlan/.../xml/*.xml`), which — just
like the PII fixtures — lives outside the public repo (see
pain001/templates/local/bancatlan/docs/DEVELOPMENT.md, section "Files that
live only in this private repo") and is skipped if not present in the
environment where pytest runs.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from pain001.api.app_local import app
from pain001.api.local.constants import LOCAL_TEMPLATE_ROOT
from pain001.api.local.models import PaymentRow
from pain001.api.local.responses import MESSAGE_CODES

from .conftest import read_csv_rows, require_fixture

client = TestClient(app)

# snake_case (CSV column) -> camelCase (JSON API field), derived straight
# from PaymentRow's field aliases, used to build a camelCase payload from
# the same CSV fixture rows the snake_case golden test reads.
_SNAKE_TO_CAMEL_FIELD_MAP = {
    field_name: field_info.alias or field_name
    for field_name, field_info in PaymentRow.model_fields.items()
}


def _to_camel_case_rows(rows: list[dict]) -> list[dict]:
    return [
        {_SNAKE_TO_CAMEL_FIELD_MAP.get(key, key): value for key, value in row.items()}
        for row in rows
    ]


def test_health_returns_200() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == MESSAGE_CODES["success"]["payment"]["HEALTH_OK"]


def test_list_templates_returns_the_four_known_templates() -> None:
    response = client.get("/api/v1/local/hn/templates")

    assert response.status_code == 200
    body = response.json()
    templates = body["data"]

    assert len(templates) == 4
    assert {t["template"] for t in templates} == {
        "ach",
        "between_accounts",
        "odp",
        "mixed",
    }
    for entry in templates:
        assert "xmlPresent" in entry
        assert isinstance(entry["xmlPresent"], bool)


def test_generate_json_valid_returns_xml() -> None:
    xml_path = LOCAL_TEMPLATE_ROOT / "xml" / "transferencia_ach_Lempiras.xml"
    csv_path = LOCAL_TEMPLATE_ROOT / "csv" / "transferencia_ach_Lempiras.csv"
    require_fixture(xml_path, csv_path)

    payload = {"template": "ach", "data": read_csv_rows(csv_path)}

    response = client.post("/api/v1/local/hn/generate", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Document" in response.text


def test_generate_json_camel_case_body_returns_xml() -> None:
    """The public JSON contract uses camelCase; `PaymentRow` (see
    `pain001/api/local/models.py`) validates each row by its camelCase alias
    and `model_dump(by_alias=False)` hands it to `load_payment_data` in
    pain001's internal snake_case field names. Uses the same CSV fixture as
    `test_generate_json_valid_returns_xml`, translated to camelCase, so a
    green run here proves the camelCase contract works end to end."""
    xml_path = LOCAL_TEMPLATE_ROOT / "xml" / "transferencia_ach_Lempiras.xml"
    csv_path = LOCAL_TEMPLATE_ROOT / "csv" / "transferencia_ach_Lempiras.csv"
    require_fixture(xml_path, csv_path)

    payload = {"template": "ach", "data": _to_camel_case_rows(read_csv_rows(csv_path))}

    response = client.post("/api/v1/local/hn/generate", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Document" in response.text


def test_generate_json_empty_data_returns_422_envelope() -> None:
    response = client.post(
        "/api/v1/local/hn/generate",
        json={"template": "ach", "data": []},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == MESSAGE_CODES["error"]["fields"]["VALIDATION_FAILED"]
    fields_with_errors = {detail["field"] for detail in body["errors"]["details"]}
    assert "data" in fields_with_errors


def test_generate_json_unknown_field_returns_422_envelope() -> None:
    response = client.post(
        "/api/v1/local/hn/generate",
        json={
            "template": "ach",
            "data": [{"id": "1"}],
            "unexpected_field": "should not be allowed",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == MESSAGE_CODES["error"]["fields"]["VALIDATION_FAILED"]
    details = body["errors"]["details"]
    assert any(
        detail["field"] == "unexpected_field"
        and detail["code"] == MESSAGE_CODES["error"]["fields"]["UNKNOWN_FIELD"]
        for detail in details
    )


def test_unknown_route_returns_404_envelope() -> None:
    response = client.get("/api/v1/local/hn/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == MESSAGE_CODES["error"]["generic"]["NOT_FOUND"]


def test_wrong_method_returns_405_envelope() -> None:
    response = client.delete("/api/v1/local/hn/generate")

    assert response.status_code == 405
    body = response.json()
    assert body["code"] == MESSAGE_CODES["error"]["generic"]["METHOD_NOT_ALLOWED"]
