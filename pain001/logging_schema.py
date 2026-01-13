# Copyright (C) 2023-2026 Sebastien Rousseau.
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
# See the License for the specific language governing permissions and
# limitations under the License.

"""Structured logging schema for Pain001.

This module defines standardized event names, field names, and logging
helpers to ensure consistent structured logging across CLI and library.

Event Naming Convention:
    - Use snake_case for event names
    - Format: <component>_<action>_<state>
    - Examples: "process_start", "validation_success", "xml_generated"

Field Naming Convention:
    - Use snake_case for field names
    - Be consistent with terminology across all events
    - Include units where applicable (e.g., "duration_ms", "size_bytes")
"""

import json
import logging
import time
from typing import Any, Optional


# Standard Event Names
class Events:  # pylint: disable=too-few-public-methods
    """Standardized event names for structured logging."""

    # Process lifecycle events
    PROCESS_START = "process_start"
    PROCESS_SUCCESS = "process_success"
    PROCESS_ERROR = "process_error"

    # CLI events
    CLI_ARGS_PARSED = "cli_args_parsed"
    CLI_DRY_RUN = "cli_dry_run"

    # Validation events
    VALIDATION_START = "validation_start"
    VALIDATION_SUCCESS = "validation_success"
    VALIDATION_ERROR = "validation_error"

    # Data loading events
    DATA_LOAD_START = "data_load_start"
    DATA_LOAD_SUCCESS = "data_load_success"
    DATA_LOAD_ERROR = "data_load_error"

    # XML generation events
    XML_GENERATE_START = "xml_generate_start"
    XML_GENERATE_SUCCESS = "xml_generate_success"
    XML_GENERATE_ERROR = "xml_generate_error"

    # XSD validation events
    XSD_VALIDATION_START = "xsd_validation_start"
    XSD_VALIDATION_SUCCESS = "xsd_validation_success"
    XSD_VALIDATION_ERROR = "xsd_validation_error"

    # Namespace registration events
    NAMESPACE_REGISTER = "namespace_register"


# Standard Field Names
class Fields:  # pylint: disable=too-few-public-methods
    """Standardized field names for structured logging."""

    # Core fields
    EVENT = "event"
    TIMESTAMP = "timestamp"
    LEVEL = "level"

    # Component identification
    COMPONENT = "component"
    MODULE = "module"
    FUNCTION = "function"

    # Message type and version
    MESSAGE_TYPE = "message_type"
    ISO_VERSION = "iso_version"

    # File paths (never log sensitive data)
    TEMPLATE_PATH = "template_path"
    SCHEMA_PATH = "schema_path"
    DATA_SOURCE_TYPE = "data_source_type"  # csv, sqlite, list, dict

    # Record counts and statistics
    RECORD_COUNT = "record_count"
    TRANSACTION_COUNT = "transaction_count"

    # Performance metrics
    DURATION_MS = "duration_ms"
    SIZE_BYTES = "size_bytes"

    # Error information
    ERROR_TYPE = "error_type"
    ERROR_MESSAGE = "error_message"
    ERROR_DETAILS = "error_details"

    # Validation details
    VALIDATION_TYPE = "validation_type"  # schema, data, business_rules


def mask_sensitive_data(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging.

    Args:
        value: The sensitive value to mask.
        visible_chars: Number of characters to show at start and end.

    Returns:
        Masked string showing only first and last visible_chars.

    Examples:
        >>> mask_sensitive_data("GB29NWBK60161331926819", 4)
        'GB29****6819'
        >>> mask_sensitive_data("Short", 4)
        '****'
    """
    if len(value) <= visible_chars * 2:
        return "****"
    masked_length = len(value) - (visible_chars * 2)
    return (
        f"{value[:visible_chars]}{'*' * masked_length}{value[-visible_chars:]}"
    )


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """Log a structured event with standardized format.

    Args:
        logger: The logger instance to use.
        level: Logging level (logging.INFO, logging.ERROR, etc.).
        event: Event name from Events class.
        **fields: Additional fields to include in the log entry.

    Example:
        >>> log_event(
        ...     logger,
        ...     logging.INFO,
        ...     Events.PROCESS_START,
        ...     message_type="pain.001.001.03",
        ...     record_count=10
        ... )
    """
    log_data = {
        Fields.EVENT: event,
        Fields.TIMESTAMP: time.time(),
        **fields,
    }
    logger.log(level, json.dumps(log_data))


def log_process_start(
    logger: logging.Logger,
    message_type: str,
    data_source_type: str,
    **extra_fields: Any,
) -> float:
    """Log process start event and return start timestamp.

    Args:
        logger: The logger instance to use.
        message_type: ISO 20022 message type.
        data_source_type: Type of data source (csv, sqlite, list, dict).
        **extra_fields: Additional fields to include.

    Returns:
        Start timestamp for duration calculation.
    """
    start_time = time.time()
    log_event(
        logger,
        logging.INFO,
        Events.PROCESS_START,
        message_type=message_type,
        data_source_type=data_source_type,
        **extra_fields,
    )
    return start_time


def log_process_success(
    logger: logging.Logger,
    start_time: float,
    message_type: str,
    record_count: int,
    **extra_fields: Any,
) -> None:
    """Log process success event with duration.

    Args:
        logger: The logger instance to use.
        start_time: Start timestamp from log_process_start().
        message_type: ISO 20022 message type.
        record_count: Number of records processed.
        **extra_fields: Additional fields to include.
    """
    duration_ms = int((time.time() - start_time) * 1000)
    log_event(
        logger,
        logging.INFO,
        Events.PROCESS_SUCCESS,
        message_type=message_type,
        record_count=record_count,
        duration_ms=duration_ms,
        **extra_fields,
    )


def log_process_error(
    logger: logging.Logger,
    error: Exception,
    message_type: Optional[str] = None,
    **extra_fields: Any,
) -> None:
    """Log process error event.

    Args:
        logger: The logger instance to use.
        error: The exception that occurred.
        message_type: ISO 20022 message type (if known).
        **extra_fields: Additional fields to include.
    """
    log_event(
        logger,
        logging.ERROR,
        Events.PROCESS_ERROR,
        error_type=type(error).__name__,
        error_message=str(error),
        message_type=message_type,
        **extra_fields,
    )


def log_validation_event(
    logger: logging.Logger,
    validation_type: str,
    success: bool,
    error: Optional[Exception] = None,
    **extra_fields: Any,
) -> None:
    """Log validation event (success or error).

    Args:
        logger: The logger instance to use.
        validation_type: Type of validation (schema, data, business_rules).
        success: Whether validation succeeded.
        error: Exception if validation failed (None if success).
        **extra_fields: Additional fields to include.
    """
    if success:
        log_event(
            logger,
            logging.INFO,
            Events.VALIDATION_SUCCESS,
            validation_type=validation_type,
            **extra_fields,
        )
    else:
        log_event(
            logger,
            logging.ERROR,
            Events.VALIDATION_ERROR,
            validation_type=validation_type,
            error_type=type(error).__name__ if error else "Unknown",
            error_message=str(error) if error else "Validation failed",
            **extra_fields,
        )


def log_data_load_event(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    logger: logging.Logger,
    data_source_type: str,
    success: bool,
    record_count: Optional[int] = None,
    error: Optional[Exception] = None,
    duration_ms: Optional[int] = None,
) -> None:
    """Log data loading event.

    Args:
        logger: The logger instance to use.
        data_source_type: Type of data source (csv, sqlite, list, dict).
        success: Whether data loading succeeded.
        record_count: Number of records loaded (if success).
        error: Exception if loading failed (None if success).
        duration_ms: Loading duration in milliseconds.
    """
    if success:
        log_event(
            logger,
            logging.INFO,
            Events.DATA_LOAD_SUCCESS,
            data_source_type=data_source_type,
            record_count=record_count,
            duration_ms=duration_ms,
        )
    else:
        log_event(
            logger,
            logging.ERROR,
            Events.DATA_LOAD_ERROR,
            data_source_type=data_source_type,
            error_type=type(error).__name__ if error else "Unknown",
            error_message=str(error) if error else "Data load failed",
        )


def log_xml_generation_event(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    logger: logging.Logger,
    message_type: str,
    success: bool,
    record_count: Optional[int] = None,
    error: Optional[Exception] = None,
    duration_ms: Optional[int] = None,
) -> None:
    """Log XML generation event.

    Args:
        logger: The logger instance to use.
        message_type: ISO 20022 message type.
        success: Whether XML generation succeeded.
        record_count: Number of records in generated XML.
        error: Exception if generation failed (None if success).
        duration_ms: Generation duration in milliseconds.
    """
    if success:
        log_event(
            logger,
            logging.INFO,
            Events.XML_GENERATE_SUCCESS,
            message_type=message_type,
            record_count=record_count,
            duration_ms=duration_ms,
        )
    else:
        log_event(
            logger,
            logging.ERROR,
            Events.XML_GENERATE_ERROR,
            message_type=message_type,
            error_type=type(error).__name__ if error else "Unknown",
            error_message=str(error) if error else "XML generation failed",
        )
