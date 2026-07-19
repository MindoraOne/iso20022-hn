# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Regla del banco: "si no hay dato, que no vaya el nodo".

Los nodos que ISO marca opcionales (`minOccurs=0`) y que la guia del banco no
exige se emiten SOLO si hay valor: en los templates locales van envueltos en un
`{%- if valor %}`. Asi, el backend simplemente no manda el campo y el nodo
desaparece — no hace falta ninguna bandera.

Historia: antes existian los marcadores `DELETE`/`EMPTY` (invencion nuestra, no
del banco) para forzar esto a mano. Se eliminaron el 2026-07-15 porque preguntar
"hay dato?" hace lo mismo sin obligar al caller a mandar una palabra magica, y
sin el riesgo de que la palabra viajara literal al banco si se usaba en un campo
que no la implementaba (bug real que ocurrio en `entre_cuentas` y `odp`).

Antes de esto, omitir cualquiera de estos 17 campos devolvia 400 `xsd_invalid`:
el template emitia el nodo vacio y el XSD lo rechazaba (`minLength=1`, o el
patron de `MobNb`). Un beneficiario sin telefono no podia pagarse.
"""

from __future__ import annotations

import csv

import pytest
from lxml import etree

from pain001.api.local.constants import XSD_PATH
from pain001.data.loader import load_payment_data
from pain001.xml.generate_xml import generate_xml_string

from .conftest import INPUT_DIR, NS, TEMPLATE_ROOT, require_fixture

TEMPLATE_CASES = [
    pytest.param("transferencia_ach_Lempiras", "transferencia_ach_Lempiras.csv", id="ach"),
    pytest.param(
        "transferencia_entre_cuentas_Lempiras",
        "transferencia_entre_cuentas_Lempiras.csv",
        id="between_accounts",
    ),
    pytest.param(
        "transferencia_ordenes_de_pago_Lempiras",
        "transferencia_ordenes_de_pago_Lempiras.csv",
        id="odp",
    ),
    pytest.param("transferencia_mixta_Lempiras", "varias_transferencias_mixta.csv", id="mixed"),
]

# Campos opcionales (ISO minOccurs=0 + la guia del banco no los exige).
# `creditor_account_IBAN` no aplica a odp (ese template no lleva CdtrAcct).
OPTIONAL_FIELDS = [
    "initiator_org_id",
    "initiator_contact_name",
    "category_purpose_code",
    "debtor_street_name",
    "debtor_clearing_member_id",
    "payment_instruction_id",
    "creditor_clearing_member_id",
    "creditor_street_name",
    "creditor_town_name",
    "creditor_private_id",
    "creditor_private_id_scheme",
    "creditor_mobile_number",
    "creditor_email_address",
    "creditor_account_IBAN",
    "creditor_account_type",
    "reference_number",
]


def _rows(csv_name: str, **overrides: str) -> list[dict[str, str]]:
    csv_path = INPUT_DIR / csv_name
    require_fixture(csv_path)
    with csv_path.open(encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    for row in rows:
        row.update(overrides)
    return rows


def _generate(template_filename: str, rows: list[dict[str, str]]) -> etree._Element:
    xml = generate_xml_string(
        data=load_payment_data(rows),
        payment_initiation_message_type="pain.001.001.05",
        xml_template_path=str(TEMPLATE_ROOT / f"{template_filename}.xml"),
        xsd_schema_path=str(XSD_PATH),
    )
    return etree.fromstring(xml.encode("utf-8"))


@pytest.mark.parametrize("template_filename, csv_name", TEMPLATE_CASES)
@pytest.mark.parametrize("field", OPTIONAL_FIELDS)
def test_campo_opcional_ausente_genera_xml_valido(
    template_filename: str, csv_name: str, field: str
) -> None:
    """Sin el dato, el XML sigue siendo valido contra el XSD.

    `generate_xml_string` valida contra el XSD internamente: si el template
    emitiera el nodo vacio, esto lanzaria y el test falla.
    """
    _generate(template_filename, _rows(csv_name, **{field: ""}))


@pytest.mark.parametrize("template_filename, csv_name", TEMPLATE_CASES)
def test_sin_telefono_ni_correo_se_omite_el_bloque_padre(
    template_filename: str, csv_name: str
) -> None:
    """El caso que motivo todo: un beneficiario sin datos de contacto.

    Omitir los dos hijos debe llevarse el `<CtctDtls>`: dejarlo vacio tambien
    romperia el XSD.
    """
    root = _generate(
        template_filename,
        _rows(csv_name, creditor_mobile_number="", creditor_email_address=""),
    )

    assert root.findall(".//p:CdtTrfTxInf/p:Cdtr/p:CtctDtls", NS) == []


@pytest.mark.parametrize("template_filename, csv_name", TEMPLATE_CASES)
def test_con_un_solo_dato_de_contacto_el_bloque_sobrevive(
    template_filename: str, csv_name: str
) -> None:
    """Con telefono pero sin correo, el bloque queda solo con el telefono."""
    root = _generate(
        template_filename,
        _rows(csv_name, creditor_email_address=""),
    )
    blocks = root.findall(".//p:CdtTrfTxInf/p:Cdtr/p:CtctDtls", NS)

    assert blocks
    for block in blocks:
        assert block.find("p:MobNb", NS) is not None
        assert block.find("p:EmailAdr", NS) is None


@pytest.mark.parametrize("template_filename, csv_name", TEMPLATE_CASES)
def test_sin_identidad_se_omite_el_bloque_id(template_filename: str, csv_name: str) -> None:
    root = _generate(
        template_filename,
        _rows(csv_name, creditor_private_id="", creditor_private_id_scheme=""),
    )

    assert root.findall(".//p:CdtTrfTxInf/p:Cdtr/p:Id", NS) == []


@pytest.mark.parametrize("template_filename, csv_name", TEMPLATE_CASES)
def test_ya_no_hay_banderas_el_valor_viaja_tal_cual(
    template_filename: str, csv_name: str
) -> None:
    """`DELETE` dejo de ser bandera: hoy es un texto como cualquier otro.

    Se documenta el cambio de contrato — quien quiera omitir el nodo debe dejar
    el campo vacio, no mandar la palabra.
    """
    root = _generate(template_filename, _rows(csv_name, initiator_contact_name="DELETE"))
    contacto = root.find(".//p:GrpHdr/p:InitgPty/p:CtctDtls/p:Nm", NS)

    assert contacto is not None
    assert contacto.text == "DELETE"
