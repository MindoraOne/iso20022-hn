# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Fixtures and helpers shared by the golden-file test suite for the local API (HN).

The reference XML/CSV files contain real PII and live outside version
control (see docs/pruebas-con-datos-reales.md, at the repo root). This
suite looks for them in REAL_FIXTURES_DIR (env var, default
"tests/fixtures/real/") and does a `pytest.skip` when they are missing, so
CI never fails because of their absence.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import pytest
from lxml import etree

from pain001.api.local.constants import XSD_PATH
from pain001.data.loader import load_payment_data
from pain001.xml.generate_xml import generate_xml_string

REAL_FIXTURES_DIR = Path(os.environ.get("REAL_FIXTURES_DIR", "tests/fixtures/real"))
EXPECTED_DIR = REAL_FIXTURES_DIR / "expected"
INPUT_DIR = REAL_FIXTURES_DIR / "input"

TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "pain001"
    / "templates"
    / "local"
    / "bancatlan"
    / "pain.001.001.05"
    / "xml"
)

PAIN001_05_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.05"
NS = {"p": PAIN001_05_NAMESPACE}

# Nodes excluded from the structural comparison: volatile due to generation
# (MsgId/CreDtTm). AddtlRmtInf is no longer ignored: the three occurrences
# per transaction now all render `tx.reference_number`, matching the real
# bank XML exactly.
DEFAULT_IGNORE_PATHS = ("GrpHdr/MsgId", "GrpHdr/CreDtTm")


def require_fixture(*paths: Path) -> None:
    """Skip the test if any of the real fixtures does not exist locally."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        pytest.skip(
            "real fixtures not available: see docs/pruebas-con-datos-reales.md "
            f"(missing: {', '.join(str(p) for p in missing)})"
        )


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    """Read a fixtures CSV as a list of dicts (same shape expected by GenerateJsonRequest.data)."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def generate_from_template(template_filename: str, csv_path: Path) -> str:
    """Generate the pain.001.001.05 XML for a fixtures CSV using a given template.

    `template_filename` is the actual filename without extension (see
    LOCAL_TEMPLATE_FILENAMES in pain001/api/local/enums.py), not the enum's
    public key.
    """
    data = load_payment_data(str(csv_path))
    template_path = TEMPLATE_ROOT / f"{template_filename}.xml"
    return generate_xml_string(
        data=data,
        payment_initiation_message_type="pain.001.001.05",
        xml_template_path=str(template_path),
        xsd_schema_path=str(XSD_PATH),
    )


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _path_is_ignored(path_parts: list[str], ignore_paths: tuple[str, ...]) -> bool:
    joined = "/".join(path_parts)
    return any(joined == ignore or joined.endswith("/" + ignore) for ignore in ignore_paths)


def _compare_elements(
    generated: etree._Element,
    expected: etree._Element,
    path_parts: list[str],
    ignore_paths: tuple[str, ...],
    errors: list[str],
) -> None:
    gen_tag = _strip_ns(generated.tag)
    exp_tag = _strip_ns(expected.tag)
    current_path = path_parts + [exp_tag]

    if _path_is_ignored(current_path, ignore_paths):
        return

    location = "/".join(current_path)

    if gen_tag != exp_tag:
        errors.append(f"different tag at {location}: generated={gen_tag!r} expected={exp_tag!r}")
        return

    gen_text = (generated.text or "").strip()
    exp_text = (expected.text or "").strip()
    if gen_text != exp_text:
        errors.append(f"different text at {location}: generated={gen_text!r} expected={exp_text!r}")

    gen_attrib = dict(generated.attrib)
    exp_attrib = dict(expected.attrib)
    if gen_attrib != exp_attrib:
        errors.append(f"different attributes at {location}: generated={gen_attrib} expected={exp_attrib}")

    gen_children = list(generated)
    exp_children = list(expected)
    if len(gen_children) != len(exp_children):
        errors.append(
            f"different child count at {location}: "
            f"generated={len(gen_children)} expected={len(exp_children)}"
        )
        return

    for gen_child, exp_child in zip(gen_children, exp_children):
        _compare_elements(gen_child, exp_child, current_path, ignore_paths, errors)


def assert_xml_equivalent(
    generated_xml: str,
    expected_xml: str,
    ignore_paths: tuple[str, ...] = DEFAULT_IGNORE_PATHS,
) -> None:
    """Compare two XML documents ignoring volatile nodes (MsgId, CreDtTm by default).

    Reusable by any golden-file test: parses both with lxml and recursively
    compares tag, text, and attributes of each node (order matters, as in
    the real XML), accumulating all differences before failing.
    """
    gen_root = etree.fromstring(generated_xml.encode("utf-8"))
    exp_root = etree.fromstring(expected_xml.encode("utf-8"))

    errors: list[str] = []
    _compare_elements(gen_root, exp_root, [], ignore_paths, errors)

    assert not errors, "Differences found between the generated and expected XML:\n" + "\n".join(errors)
