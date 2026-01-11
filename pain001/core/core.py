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

import json
import logging
import os
import sys
import time
from typing import Any, Union

from pain001.constants.constants import valid_xml_types
from pain001.context.context import Context
from pain001.data.loader import load_payment_data
from pain001.xml.generate_xml import generate_xml
from pain001.xml.register_namespaces import register_namespaces

# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def process_files(
    xml_message_type: str,
    xml_template_file_path: str,
    xsd_schema_file_path: str,
    data_file_path: Union[str, list[dict[str, Any]], dict[str, Any]],
) -> None:
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

    # Initialize context and timing
    context_logger = Context.get_instance().get_logger()
    start_time = time.time()

    # Log structured event
    logger.info(
        json.dumps(
            {
                "event": "process_files_start",
                "message_type": xml_message_type,
                "timestamp": start_time,
            }
        )
    )

    try:
        # Loop through the payment initiation message types and check if the XML
        # message type is supported.
        if xml_message_type not in valid_xml_types:
            error_message = (
                f"Error: Invalid XML message type: '{xml_message_type}'."
            )
            context_logger.error(error_message)
            logger.error(
                json.dumps(
                    {
                        "event": "invalid_message_type",
                        "message_type": xml_message_type,
                        "error": error_message,
                    }
                )
            )
            raise ValueError(error_message)

        # Check if the XML template file exists
        if not os.path.exists(xml_template_file_path):
            error_message = f"Error: XML template '{xml_template_file_path}' does not exist."
            context_logger.error(error_message)
            logger.error(
                json.dumps(
                    {
                        "event": "template_not_found",
                        "template_path": xml_template_file_path,
                    }
                )
            )
            raise FileNotFoundError(error_message)

        # Check if the XSD schema file exists
        if not os.path.exists(xsd_schema_file_path):
            error_message = f"Error: XSD schema file '{xsd_schema_file_path}' does not exist."
            context_logger.error(error_message)
            logger.error(
                json.dumps(
                    {
                        "event": "schema_not_found",
                        "schema_path": xsd_schema_file_path,
                    }
                )
            )
            raise FileNotFoundError(error_message)

        # Load and validate data from various sources
        logger.info(
            json.dumps(
                {
                    "event": "loading_payment_data",
                    "data_source": (
                        data_file_path
                        if isinstance(data_file_path, str)
                        else "python_object"
                    ),
                }
            )
        )

        try:
            data = load_payment_data(data_file_path)
            logger.info(
                json.dumps(
                    {
                        "event": "data_loaded",
                        "record_count": len(data),
                        "duration_ms": int((time.time() - start_time) * 1000),
                    }
                )
            )
        except (FileNotFoundError, ValueError) as e:
            logger.error(
                json.dumps(
                    {
                        "event": "data_load_error",
                        "error": str(e),
                        "duration_ms": int((time.time() - start_time) * 1000),
                    }
                )
            )
            raise

        # Register the namespace prefixes and URIs
        logger.info(
            json.dumps(
                {
                    "event": "registering_namespaces",
                    "message_type": xml_message_type,
                }
            )
        )
        register_namespaces(xml_message_type)

        # Generate XML
        gen_start = time.time()
        logger.info(
            json.dumps(
                {
                    "event": "generating_xml",
                    "message_type": xml_message_type,
                    "record_count": len(data),
                }
            )
        )

        generate_xml(
            data,
            xml_message_type,
            xml_template_file_path,
            xsd_schema_file_path,
        )

        gen_duration = int((time.time() - gen_start) * 1000)

        # Confirm success
        if os.path.exists(xml_template_file_path):
            total_duration = int((time.time() - start_time) * 1000)
            context_logger.info(
                f"Successfully generated XML file '{xml_template_file_path}'"
            )
            logger.info(
                json.dumps(
                    {
                        "event": "xml_generated_success",
                        "file_path": xml_template_file_path,
                        "message_type": xml_message_type,
                        "record_count": len(data),
                        "generation_ms": gen_duration,
                        "total_duration_ms": total_duration,
                    }
                )
            )
        else:
            error_msg = (
                f"Failed to generate XML file at '{xml_template_file_path}'"
            )
            context_logger.error(error_msg)
            logger.error(
                json.dumps(
                    {
                        "event": "xml_generation_failed",
                        "file_path": xml_template_file_path,
                    }
                )
            )

    except Exception as e:
        total_duration = int((time.time() - start_time) * 1000)
        logger.error(
            json.dumps(
                {
                    "event": "process_files_error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": total_duration,
                }
            ),
            exc_info=True,
        )
        raise


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
