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

import os

# Import the standard libraries
import sys
from typing import Any, Dict, List, Union

# Import the pain001 library functions
from pain001.constants.constants import valid_xml_types
from pain001.context.context import Context
from pain001.data.loader import load_payment_data
from pain001.xml.generate_xml import generate_xml
from pain001.xml.register_namespaces import register_namespaces


def process_files(
    xml_message_type: str,
    xml_template_file_path: str,
    xsd_schema_file_path: str,
    data_file_path: Union[str, List[Dict[str, Any]], Dict[str, Any]],
):
    """
    This function generates an ISO 20022 payment message from various data sources.

    Args:
        xml_message_type (str): The type of XML message to generate. Valid
        options are 'pain.001.001.03', 'pain.001.001.04', 'pain.001.001.05',
        'pain.001.001.06', 'pain.001.001.07', 'pain.001.001.08', and
        'pain.001.001.09'.
        xml_template_file_path (str): The path of the XML template file.
        xsd_schema_file_path (str): The path of the XSD schema file.
        data_file_path (Union[str, List[Dict], Dict]): The payment data source.
            Supports:
            - str: Path to CSV (.csv) or SQLite (.db) file (backward compatible)
            - list: List of payment data dictionaries (new feature)
            - dict: Single payment transaction dictionary (new feature)

    Returns:
        None

    Raises:
        ValueError: If the XML message type is not supported or data is invalid.
        FileNotFoundError: If the XML template file or data file does not exist.

    Examples:
        # Existing file-based usage (backward compatible)
        >>> process_files('pain.001.001.03', 'template.xml', 'schema.xsd', 'data.csv')

        # New direct Python data usage
        >>> data = [{'id': 'MSG001', 'date': '2026-01-09', ...}]
        >>> process_files('pain.001.001.03', 'template.xml', 'schema.xsd', data)
    """

    # Initialize the context and log a message.
    logger = Context.get_instance().get_logger()

    # Loop through the payment initiation message types and check if the XML
    # message type is supported.
    if xml_message_type not in valid_xml_types:
        error_message = (
            f"Error: Invalid XML message type: '{xml_message_type}'."
        )
        logger.error(error_message)
        raise ValueError(error_message)

    # Check if the XML template file exists
    if not os.path.exists(xml_template_file_path):
        error_message = (
            f"Error: XML template '{xml_template_file_path}' "
            f"does not exist."
        )
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Check if the XSD schema file exists
    if not os.path.exists(xsd_schema_file_path):
        error_message = (
            f"Error: XSD schema file '{xsd_schema_file_path}' "
            f"does not exist."
        )
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Load and validate data from various sources using unified loader
    # This supports: file paths (str), Python lists, and Python dicts
    try:
        data = load_payment_data(data_file_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error loading payment data: {e}")
        raise

    # Register the namespace prefixes and URIs for the XML message type
    register_namespaces(xml_message_type)

    # Generate the updated XML file path
    generate_xml(
        data,
        xml_message_type,
        xml_template_file_path,
        xsd_schema_file_path,
    )

    # Confirm the XML file has been created
    if os.path.exists(xml_template_file_path):
        logger.info(
            f"Successfully generated XML file '{xml_template_file_path}'"
        )
    else:
        logger.error(
            f"Failed to generate XML file at '{xml_template_file_path}'"
        )


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(
            "Usage: python3 -m pain001 "
            + " ".join(
                [
                    "<xml_message_type>",
                    "<xml_template_file_path>",
                    "<xsd_schema_file_path>",
                    "<data_file_path>",
                ]
            )
        )

        sys.exit(1)
    process_files(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
