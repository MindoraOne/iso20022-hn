# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Golden-file tests: generated XML vs. real reference XML (see
docs/pruebas-con-datos-reales.md for how to obtain the fixtures).

Base cases (ach, between_accounts, odp): full structural comparison,
except for volatile nodes (MsgId/CreDtTm) and the free-form remittance
text (AddtlRmtInf, which carries a placeholder in the sample CSVs). They
use the real sample CSVs, so they must match the bank's XML exactly.

`varias_transferencias`: has no real input CSV (the input was derived
from the reference XML), so it is a STRUCTURAL test — it validates that
the 3 transactions are generated with their beneficiaries/amounts, not a
byte-by-byte comparison.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from pain001.api.app_local import app
from pain001.api.local.enums import LocalTemplateType

from .conftest import (
    EXPECTED_DIR,
    INPUT_DIR,
    NS,
    assert_xml_equivalent,
    generate_from_template,
    read_csv_rows,
    require_fixture,
)

BASE_CASES = [
    pytest.param(LocalTemplateType.ach, "transferencia_ach_Lempiras", id="ach"),
    pytest.param(
        LocalTemplateType.between_accounts,
        "transferencia_entre_cuentas_Lempiras",
        id="between_accounts",
    ),
    pytest.param(LocalTemplateType.odp, "transferencia_ordenes_de_pago_Lempiras", id="odp"),
]


@pytest.mark.parametrize("template, filename", BASE_CASES)
def test_base_case_matches_golden_xml(template: LocalTemplateType, filename: str) -> None:
    csv_path = INPUT_DIR / f"{filename}.csv"
    xml_path = EXPECTED_DIR / f"{filename}.xml"
    require_fixture(csv_path, xml_path)

    generated = generate_from_template(filename, csv_path)
    expected = xml_path.read_text(encoding="utf-8")

    assert_xml_equivalent(generated, expected)


@pytest.mark.parametrize(
    "template, filename",
    [BASE_CASES[0], BASE_CASES[1]],
)
def test_base_case_matches_golden_xml_via_json_endpoint(
    template: LocalTemplateType, filename: str
) -> None:
    """Same base case, but going through TestClient against /local/hn/generate (JSON)."""
    csv_path = INPUT_DIR / f"{filename}.csv"
    xml_path = EXPECTED_DIR / f"{filename}.xml"
    require_fixture(csv_path, xml_path)

    rows = read_csv_rows(csv_path)
    client = TestClient(app)
    response = client.post(
        "/api/v1/local/hn/generate",
        json={"template": template.value, "data": rows},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    expected = xml_path.read_text(encoding="utf-8")
    assert_xml_equivalent(response.text, expected)


def test_varias_transferencias_mixta_matches_golden_xml_exactly() -> None:
    """Mixed case (ach/odp/between_accounts in the same request): FULL
    STRUCTURAL comparison against the real reference XML (varias_transferencias.xml),
    using the mixed template (transferencia_mixta_Lempiras) and an input with a
    per-row `type` derived from the real XML (tx1=ach, tx2=odp, tx3=between_accounts).
    """
    csv_path = INPUT_DIR / "varias_transferencias_mixta.csv"
    xml_path = EXPECTED_DIR / "varias_transferencias.xml"
    require_fixture(csv_path, xml_path)

    generated = generate_from_template("transferencia_mixta_Lempiras", csv_path)
    expected = xml_path.read_text(encoding="utf-8")

    assert_xml_equivalent(generated, expected)


def test_varias_transferencias_mixta_via_json_endpoint() -> None:
    """Same mixed case, but going through TestClient against /local/hn/generate (JSON)
    with an explicit template=mixed."""
    csv_path = INPUT_DIR / "varias_transferencias_mixta.csv"
    xml_path = EXPECTED_DIR / "varias_transferencias.xml"
    require_fixture(csv_path, xml_path)

    rows = read_csv_rows(csv_path)
    client = TestClient(app)
    response = client.post(
        "/api/v1/local/hn/generate",
        json={"template": LocalTemplateType.mixed.value, "data": rows},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    expected = xml_path.read_text(encoding="utf-8")
    assert_xml_equivalent(response.text, expected)


def test_generate_json_ignores_incorrect_nb_of_txs_and_computes_real_count() -> None:
    """`nbOfTxs` is COMPUTED by the service (see app_local.generate_xml_json),
    not trusted from the caller: a request that lies about it (here "1" for
    3 rows) must still produce `NbOfTxs=3` in both GrpHdr and PmtInf — the
    real row count — instead of echoing the wrong input value.
    """
    csv_path = INPUT_DIR / "varias_transferencias_mixta.csv"
    xml_path = EXPECTED_DIR / "varias_transferencias.xml"
    require_fixture(csv_path, xml_path)

    rows = read_csv_rows(csv_path)
    rows[0]["nb_of_txs"] = "1"
    client = TestClient(app)
    response = client.post(
        "/api/v1/local/hn/generate",
        json={"template": LocalTemplateType.mixed.value, "data": rows},
    )

    assert response.status_code == 200
    root = etree.fromstring(response.text.encode("utf-8"))
    nb_of_txs_nodes = root.findall(".//p:NbOfTxs", NS)

    assert len(nb_of_txs_nodes) == 2
    assert [node.text for node in nb_of_txs_nodes] == ["3", "3"]


def test_varias_transferencias_genera_tres_transacciones() -> None:
    csv_path = INPUT_DIR / "varias_transferencias.csv"
    xml_path = EXPECTED_DIR / "varias_transferencias.xml"
    require_fixture(csv_path, xml_path)

    generated = generate_from_template("transferencia_ach_Lempiras", csv_path)
    gen_root = etree.fromstring(generated.encode("utf-8"))
    exp_root = etree.fromstring(xml_path.read_text(encoding="utf-8").encode("utf-8"))

    gen_tx = gen_root.findall(".//p:CdtTrfTxInf", NS)
    exp_tx = exp_root.findall(".//p:CdtTrfTxInf", NS)

    assert len(gen_tx) == 3
    assert len(exp_tx) == 3

    def _beneficiaries_and_amounts(nodes: list[etree._Element]) -> list[tuple[str | None, str | None]]:
        return [
            (
                node.findtext("p:Cdtr/p:Nm", namespaces=NS),
                node.findtext("p:Amt/p:InstdAmt", namespaces=NS),
            )
            for node in nodes
        ]

    assert _beneficiaries_and_amounts(gen_tx) == _beneficiaries_and_amounts(exp_tx)
