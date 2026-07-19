# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""El pais del beneficiario sale del dato, no de una constante.

Antes los templates HN tenian `<Ctry>HN</Ctry>` quemado dentro de `Cdtr/PstlAdr`
e ignoraban el campo `creditor_country` que la API si aceptaba: un beneficiario
no hondureno producia un archivo que mentia. Ahora el nodo se llena con el dato,
con fallback a `HN` cuando no viene (el caso historico y el de la banca local).

El `Ctry` de `DbtrAgt`/`CdtrAgt` es el pais del BANCO y sigue fijo en `HN` a
proposito: no debe seguir al beneficiario.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from pain001.api.app_local import app

from .conftest import INPUT_DIR, NS, read_csv_rows, require_fixture

CSV_NAME = "transferencia_ach_Lempiras.csv"


def _generate(rows: list[dict[str, str]]) -> etree._Element:
    client = TestClient(app)
    response = client.post("/api/v1/local/hn/generate", json={"template": "ach", "data": rows})
    assert response.status_code == 200, response.text
    return etree.fromstring(response.text.encode("utf-8"))


def _creditor_countries(root: etree._Element) -> list[str | None]:
    return [node.text for node in root.findall(".//p:CdtTrfTxInf/p:Cdtr/p:PstlAdr/p:Ctry", NS)]


def _agent_countries(root: etree._Element) -> list[str | None]:
    return [node.text for node in root.findall(".//p:FinInstnId/p:PstlAdr/p:Ctry", NS)]


@pytest.fixture
def base_row() -> dict[str, str]:
    csv_path = INPUT_DIR / CSV_NAME
    require_fixture(csv_path)
    return dict(read_csv_rows(csv_path)[0])


def test_creditor_country_se_toma_del_dato(base_row: dict[str, str]) -> None:
    """Un beneficiario no hondureno debe salir con su propio pais."""
    base_row["creditor_country"] = "US"

    root = _generate([base_row])

    assert _creditor_countries(root) == ["US"]


def test_creditor_country_no_arrastra_el_pais_del_banco(base_row: dict[str, str]) -> None:
    """El `Ctry` de los agentes (DbtrAgt/CdtrAgt) es del banco: sigue en HN."""
    base_row["creditor_country"] = "US"

    root = _generate([base_row])

    assert set(_agent_countries(root)) == {"HN"}


def test_creditor_country_ausente_cae_a_HN(base_row: dict[str, str]) -> None:
    """Sin el campo, el XML sigue siendo valido y mantiene el HN historico.

    Cubre la regresion: sin fallback el template renderiza `<Ctry/>` vacio y el
    XSD rechaza el archivo (pattern `[A-Z]{2}`), devolviendo 400.
    """
    base_row.pop("creditor_country", None)

    root = _generate([base_row])

    assert _creditor_countries(root) == ["HN"]
