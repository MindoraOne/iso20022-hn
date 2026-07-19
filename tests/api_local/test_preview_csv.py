# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Tests for `/local/hn/preview/csv`, the sibling of `/local/hn/generate` that
returns the internal CSV representation of a JSON payload instead of XML.

Uses a real input CSV under `tests/fixtures/input/` (PII, copied from the
private repo iso20022-local-templates), skipped if absent — same pattern as
`test_generate_json_valid_returns_xml` in `test_endpoints.py`.
"""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from pain001.api.app_local import app
from pain001.api.local.models import PaymentRow

from .conftest import (
    INPUT_DIR,
    assert_xml_equivalent,
    read_csv_rows,
    require_fixture,
)

client = TestClient(app)

# snake_case (CSV column) -> camelCase (JSON API field), same mapping used by
# test_endpoints.py's _to_camel_case_rows, built straight from PaymentRow's aliases.
_SNAKE_TO_CAMEL_FIELD_MAP = {
    field_name: field_info.alias or field_name
    for field_name, field_info in PaymentRow.model_fields.items()
}


def _to_camel_case_rows(rows: list[dict]) -> list[dict]:
    return [
        {_SNAKE_TO_CAMEL_FIELD_MAP.get(key, key): value for key, value in row.items()}
        for row in rows
    ]


def test_preview_csv_valid_json_returns_csv_with_one_row_per_transaction() -> None:
    csv_path = INPUT_DIR / "transferencia_ach_Lempiras.csv"
    require_fixture(csv_path)

    payload = {"template": "ach", "data": _to_camel_case_rows(read_csv_rows(csv_path))}

    response = client.post("/api/v1/local/hn/preview/csv", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == len(payload["data"])
    # nb_of_txs is computed by the service, same as /generate — only data[0] carries it.
    assert rows[0]["nb_of_txs"] == str(len(payload["data"]))


def test_preview_csv_empty_data_returns_422_envelope() -> None:
    response = client.post(
        "/api/v1/local/hn/preview/csv",
        json={"template": "ach", "data": []},
    )

    assert response.status_code == 422


def test_preview_csv_round_trips_to_the_same_xml_as_generate() -> None:
    """Proves the two endpoints are siblings: JSON -> XML (via /generate)
    must equal JSON -> CSV (via /preview/csv) -> XML (via /generate/csv)."""
    csv_path = INPUT_DIR / "transferencia_ach_Lempiras.csv"
    require_fixture(csv_path)

    payload = {"template": "ach", "data": _to_camel_case_rows(read_csv_rows(csv_path))}

    direct_response = client.post("/api/v1/local/hn/generate", json=payload)
    assert direct_response.status_code == 200
    expected_xml = direct_response.text

    preview_response = client.post("/api/v1/local/hn/preview/csv", json=payload)
    assert preview_response.status_code == 200
    preview_csv_text = preview_response.text

    round_trip_response = client.post(
        "/api/v1/local/hn/generate/csv",
        data={"template": "ach"},
        files={"csv_file": ("preview.csv", preview_csv_text, "text/csv")},
    )
    assert round_trip_response.status_code == 200
    round_trip_xml = round_trip_response.text

    assert_xml_equivalent(round_trip_xml, expected_xml)
