# Other imports remain the same
import os
import sys
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from pain001.constants.constants import valid_xml_types
from pain001.context.context import Context
from pain001.core.core import process_files
from pain001.data.loader import load_payment_data
from pain001.xml.validate_via_xsd import validate_via_xsd

console = Console()

description = None
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
def cli(
    xml_message_type: Optional[str],
    xml_template_file_path: Optional[str],
    xsd_schema_file_path: Optional[str],
    data_file_path: Optional[str],
    dry_run: bool = False,
) -> None:
    """Click CLI wrapper for Pain001.

    Args:
        xml_message_type: ISO 20022 message type.
        xml_template_file_path: Path to XML template.
        xsd_schema_file_path: Path to XSD schema.
        data_file_path: Path to data file (CSV/SQLite).
        dry_run: Validate without generating XML.
    """
    main(
        xml_message_type,
        xml_template_file_path,
        xsd_schema_file_path,
        data_file_path,
        dry_run,
    )


def main(
    xml_message_type: Optional[str],
    xml_template_file_path: Optional[str],
    xsd_schema_file_path: Optional[str],
    data_file_path: Optional[str],
    dry_run: bool = False,
) -> None:
    """Main entry point for python -m pain001.

    Args:
        xml_message_type: ISO 20022 message type (e.g., 'pain.001.001.03').
        xml_template_file_path: Path to Jinja2 XML template file.
        xsd_schema_file_path: Path to XSD schema for validation.
        data_file_path: Path to CSV or SQLite data file.
        dry_run: If True, validate inputs without generating XML.

    Exits:
        0 on success, 1 on validation or processing error.
    """
    try:
        # Check that the required arguments are provided
        if not xml_message_type:
            console.print(
                "The XML message type is required. Use -h for help.\n"
            )
            sys.exit(1)

        if not xml_template_file_path:
            console.print("XXThe XML template file path is required.\nXX")
            sys.exit(1)

        if not xsd_schema_file_path:
            console.print("The XSD schema file path is required.\n")
            sys.exit(1)

        if not data_file_path:
            console.print("The data file path is required.\n")
            sys.exit(1)

        logger = Context.get_instance().get_logger()

        logger.info("Parsing command line arguments.\n")

        # Check that the XML message type is valid
        if xml_message_type not in valid_xml_types:
            logger.info(f"Invalid XML message type: {xml_message_type}.")
            console.print(f"Invalid XML message type: {xml_message_type}.")
            sys.exit(1)

        if not os.path.isfile(xml_template_file_path):
            logger.info(
                f"""
            The XML template file '{xml_template_file_path}' does not exist.
            """
            )
            console.print(
                f"""
            The XML template file '{xml_template_file_path}' does not exist.
            """
            )
            sys.exit(1)

        if not os.path.isfile(xsd_schema_file_path):
            logger.info(
                f"""
            The XSD template file '{xsd_schema_file_path}' does not exist.
            """
            )
            console.print(
                f"""
            The XSD template file '{xsd_schema_file_path}' does not exist.
            """
            )
            sys.exit(1)

        if not os.path.isfile(data_file_path):
            logger.info(f"The data file '{data_file_path}' does not exist.")
            console.print(f"The data file '{data_file_path}' does not exist.")
            sys.exit(1)

        try:
            validate_via_xsd(xml_template_file_path, xsd_schema_file_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error(f"Schema validation failed: {exc}")
            console.print(f"Schema validation failed: {exc}")
            sys.exit(1)

        if dry_run:
            try:
                load_payment_data(data_file_path)
            except (FileNotFoundError, ValueError) as exc:
                logger.error(f"Data validation failed: {exc}")
                console.print(f"Data validation failed: {exc}")
                sys.exit(1)

            console.print("Validation succeeded. No XML generated (--dry-run).")
            return

        process_files(
            xml_message_type,
            xml_template_file_path,
            xsd_schema_file_path,
            data_file_path,
        )
    except Exception as e:
        console.print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
