# Copyright (C) 2023 Sebastien Rousseau.
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
#
# See the License for the specific language governing permissions and
# limitations under the License.

import configparser
import logging
import os
import sys
from typing import Optional

import click
from rich import box

# pylint: disable=duplicate-code
from rich.console import Console
from rich.table import Table

from pain001.constants.constants import valid_xml_types
from pain001.context.context import Context
from pain001.core.core import process_files
from pain001.data.loader import load_payment_data
from pain001.logging_schema import (
    Events,
    Fields,
    log_event,
    log_validation_event,
)
from pain001.xml.validate_via_xsd import validate_via_xsd

console = Console()

description = """
A powerful Python library that enables you to create
ISO 20022-compliant payment files directly from CSV or SQLite Data files.\n
https://pain001.com
"""
title = "Pain001"

table = Table(box=box.ROUNDED, safe_box=True, show_header=False, title=title)

table.add_column(justify="center", no_wrap=False, vertical="middle")
table.add_row(description)
table.width = 80
console.print(table)


@click.command(
    help=("To use Pain001, you must specify the following options:\n\n"),
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "-t",
    "--xml_message_type",
    default=None,
    help="Type of XML message (required)",
)
@click.option(
    "-m",
    "--xml_template_file_path",
    default=None,
    type=click.Path(),
    help="Path to XML template file (required)",
)
@click.option(
    "-s",
    "--xsd_schema_file_path",
    default=None,
    type=click.Path(),
    help="Path to XSD template file (required)",
)
@click.option(
    "-d",
    "--data_file_path",
    default=None,
    type=click.Path(),
    help="Path to data file (CSV or SQLite) (required)",
)
@click.option(
    "-c",
    "--config_file",
    default=None,
    type=click.Path(),
    help="Path to configuration file (optional)",
)
@click.option(
    "--dry-run",
    "--validate-only",
    "dry_run",
    is_flag=True,
    default=False,
    help=(
        "Validate templates, schema, and data without generating XML output. "
        "Returns exit code 0 on success."
    ),
)
def main(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    xml_message_type: Optional[str],
    xml_template_file_path: Optional[str],
    xsd_schema_file_path: Optional[str],
    data_file_path: Optional[str],
    config_file: Optional[str],
    dry_run: bool = False,
) -> None:
    """CLI entry point for Pain001 ISO 20022 payment file generation.

    Args:
        xml_message_type: ISO 20022 message type (e.g., 'pain.001.001.03').
        xml_template_file_path: Path to Jinja2 XML template file.
        xsd_schema_file_path: Path to XSD schema for validation.
        data_file_path: Path to CSV or SQLite data file.
        config_file: Optional configuration file path.
        dry_run: If True, validate inputs without generating XML.

    Exits:
        0 on success, 1 on validation or processing error.
    """
    # Check that the required arguments are provided first
    if not xml_message_type:
        print("The XML message type is required.")
        sys.exit(1)
    if not xml_template_file_path:
        print("The XML template file path is required.")
        sys.exit(1)
    if not xsd_schema_file_path:
        print("The XSD schema file path is required.")
        sys.exit(1)
    if not data_file_path:
        print("The data file path is required.")
        sys.exit(1)

    # Expand user-friendly paths (now guaranteed to be non-None)
    xml_template_file_path = os.path.expanduser(xml_template_file_path)
    xsd_schema_file_path = os.path.expanduser(xsd_schema_file_path)
    data_file_path = os.path.expanduser(data_file_path)

    # Load configuration file if provided
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)
        if "Paths" in config:
            xml_template_file_path = config["Paths"].get(
                "xml_template_file_path", xml_template_file_path
            )
            xsd_schema_file_path = config["Paths"].get(
                "xsd_schema_file_path", xsd_schema_file_path
            )
            data_file_path = config["Paths"].get(
                "data_file_path", data_file_path
            )

    # Check file existence
    for file_path in [
        xml_template_file_path,
        xsd_schema_file_path,
        data_file_path,
    ]:
        if not os.path.isfile(file_path):
            print(f"The file '{file_path}' does not exist.")
            sys.exit(1)

    logger = Context.get_instance().get_logger()

    log_event(
        logger,
        logging.INFO,
        Events.CLI_ARGS_PARSED,
        **{
            Fields.MESSAGE_TYPE: xml_message_type,
            "dry_run": dry_run,
        },
    )

    # Check that the XML message type is valid
    if xml_message_type not in valid_xml_types:
        log_validation_event(
            logger,
            "message_type",
            False,
            ValueError(f"Invalid XML message type: {xml_message_type}"),
            message_type=xml_message_type,
        )
        print(
            f"""
                Invalid XML message type: {xml_message_type}.
                Valid types are: {", ".join(valid_xml_types)}.
            """
        )
        sys.exit(1)

    # Validate XML and XSD schemas
    try:
        validate_via_xsd(xml_template_file_path, xsd_schema_file_path)
        log_validation_event(
            logger,
            "xsd_schema",
            True,
            message_type=xml_message_type,
        )
    except Exception as e:
        log_validation_event(
            logger,
            "xsd_schema",
            False,
            e,
            message_type=xml_message_type,
        )
        print(f"Schema validation failed: {e}")
        sys.exit(1)

    if dry_run:
        # Validate payment data (same path as generation) but skip XML output
        try:
            load_payment_data(data_file_path)
            log_validation_event(
                logger,
                "payment_data",
                True,
                message_type=xml_message_type,
            )
        except (FileNotFoundError, ValueError) as e:
            log_validation_event(
                logger,
                "payment_data",
                False,
                e,
                message_type=xml_message_type,
            )
            print(f"Data validation failed: {e}")
            sys.exit(1)

        log_event(
            logger,
            logging.INFO,
            Events.CLI_DRY_RUN,
            **{
                Fields.MESSAGE_TYPE: xml_message_type,
                "validation_passed": True,
            },
        )
        print("Validation succeeded. No XML generated (--dry-run).")
        return

    process_files(
        xml_message_type,
        xml_template_file_path,
        xsd_schema_file_path,
        data_file_path,
    )


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
