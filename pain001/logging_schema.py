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

"""Standardized logging schema for Pain001.

This module provides a centralized logging structure for consistent,
machine-parsable log output across CLI and library components.
All log entries are JSON-formatted for easy integration with log
aggregation systems (Elasticsearch, Splunk, CloudWatch, etc.).

IMPORTANT: PII Protection
-------------------------
This module implements automatic PII redaction for sensitive fields.
Any field containing IBAN, BIC, or personal names is automatically
masked before logging to ensure GDPR/PCI-DSS compliance.

Request Tracing
---------------
Every operation is assigned a unique request_id (UUID) to enable
end-to-end request tracking across distributed systems and microservices.
This is essential for API Layer (#149) observability.

Log Severity Mapping (ISO 20022 Context)
-----------------------------------------
- DEBUG: XSD traversal, template loading, variable substitution
- INFO: Process start/success, validation success, file generation
- WARNING: Schema deprecation, character truncation, missing optional fields
- ERROR: XSD validation failure, checksum failure, bank profile violations
- CRITICAL: Missing dependencies, memory overflow, configuration corruption

Event Naming Convention:
    - Use snake_case for event names
    - Format: <component>_<action>_<state>
    - Examples: "process_start", "validation_success", "xml_generated"

Field Naming Convention:
    - Use snake_case for field names
    - Be consistent with terminology across all events
    - Include units where applicable (e.g., "duration_ms", "size_bytes")
    - All logs are flat JSON objects for easy indexing
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Optional

# Context variable for request tracing across async operations
_request_id_context: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)


# Execution Status Constants
class ExecutionStatus:  # pylint: disable=too-few-public-methods
    """High-level execution status for summary reports."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    ABORTED = "ABORTED"


# Standard Event Names
class Events:  # pylint: disable=too-few-public-methods
    """Standardized event names for structured logging."""

    # Process lifecycle events
    PROCESS_START = "process_start"
    PROCESS_SUCCESS = "process_success"
    PROCESS_ERROR = "process_error"
    EXECUTION_SUMMARY = "execution_summary"  # Final summary report

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

    # Core fields (always present)
    EVENT = "event"
    TIMESTAMP = "timestamp"
    LEVEL = "level"
    REQUEST_ID = "request_id"  # UUID for request tracing
    LOGGER_NAME = "logger"

    # Component identification
    COMPONENT = "component"
    MODULE = "module"
    FUNCTION = "function"
    VERSION = "version"  # Pain001 library version

    # Message type and version
    MESSAGE_TYPE = "message_type"
    ISO_VERSION = "iso_version"
    DRY_RUN = "dry_run"  # Boolean flag
    BANK_PROFILE = "bank_profile"  # e.g., hsbc_uk, jpm_cbpr_plus

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

    # Error information (flat structure)
    ERROR_TYPE = "error_type"
    ERROR_MESSAGE = "error_message"
    ERROR_FIELD = "error_field"  # Which field failed validation
    ERROR_INVALID_VALUE = (
        "error_invalid_value"  # The invalid value (masked if PII)
    )
    ERROR_REASON = (
        "error_reason"  # Detailed reason (e.g., "Invalid checksum (ISO 7064)")
    )

    # Validation details
    VALIDATION_TYPE = "validation_type"  # schema, data, business_rules
    END_TO_END_ID = "end_to_end_id"  # Transaction reference for tracing


def generate_request_id() -> str:
    """Generate a unique request ID for request tracing.

    Returns:
        A short UUID-based request ID (format: req-<8-char-hex>).

    Example:
        >>> generate_request_id()
        'req-88f24b21'
    """
    return f"req-{uuid.uuid4().hex[:8]}"


def get_request_id() -> str:
    """Get or create request ID for current context.

    Returns:
        The request ID for the current execution context.
    """
    request_id = _request_id_context.get()
    if request_id is None:
        request_id = generate_request_id()
        _request_id_context.set(request_id)
    return request_id


def set_request_id(request_id: str) -> None:
    """Set request ID for current context (useful for API handlers).

    Args:
        request_id: The request ID to set.
    """
    _request_id_context.set(request_id)


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


def _redact_pii_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Redact PII from dictionary fields recursively.

    This function implements GDPR/PCI-DSS compliant logging by automatically
    masking sensitive fields before they reach log aggregation systems.

    Redacted fields:
    - *iban* (any key containing 'iban'): Shows first 4 + last 4 chars
    - *bic* (any key containing 'bic'): Shows first 4 + last 2 chars
    - *name* (any key containing 'name'): Replaced with [REDACTED]
    - *account* (any key containing 'account'): Shows first 4 + last 4 chars

    Args:
        data: Dictionary that may contain PII fields.

    Returns:
        New dictionary with PII fields redacted.

    Example:
        >>> _redact_pii_from_dict({"debtor_iban": "GB29NWBK60161331926819"})
        {'debtor_iban': 'GB29****6819'}
    """
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Recursively handle nested dicts
        if isinstance(value, dict):
            redacted[key] = _redact_pii_from_dict(value)
        # Handle lists of dicts
        elif isinstance(value, list):
            redacted[key] = [
                _redact_pii_from_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        # Redact IBAN fields
        elif "iban" in key_lower and isinstance(value, str):
            redacted[key] = mask_sensitive_data(value, visible_chars=4)
        # Redact BIC fields
        elif "bic" in key_lower and isinstance(value, str):
            redacted[key] = (
                f"{value[:4]}**{value[-2:]}" if len(value) > 6 else "****"
            )
        # Redact name fields
        elif "name" in key_lower and isinstance(value, str):
            redacted[key] = "[REDACTED]"
        # Redact account number fields
        elif "account" in key_lower and isinstance(value, str):
            redacted[key] = mask_sensitive_data(value, visible_chars=4)
        else:
            redacted[key] = value

    return redacted


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """Log a structured event with standardized format and PII redaction.

    This function automatically:
    1. Adds request_id for distributed tracing
    2. Adds ISO 8601 timestamp
    3. Redacts PII before logging (GDPR/PCI-DSS compliance)
    4. Outputs flat JSON for easy indexing

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
        # Output: {"timestamp": "2026-01-14T21:59:55Z", "level": "INFO",
        #          "request_id": "req-88f24b21", "event": "process_start", ...}
    """
    from pain001 import __version__  # pylint: disable=import-outside-toplevel

    # Build flat JSON structure
    log_data = {
        Fields.TIMESTAMP: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        Fields.LEVEL: logging.getLevelName(level),
        Fields.LOGGER_NAME: logger.name,
        Fields.REQUEST_ID: get_request_id(),
        Fields.EVENT: event,
        Fields.VERSION: __version__,
        **fields,
    }

    # Redact PII before logging
    redacted_data = _redact_pii_from_dict(log_data)

    logger.log(level, json.dumps(redacted_data))


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


class ExecutionSummaryTracker:  # pylint: disable=too-many-instance-attributes
    """Track execution metrics for final summary report.

    This class provides automatic log event counting and execution
    metrics tracking for generating comprehensive summary reports.
    Use as a context manager for automatic start/end tracking.

    Example:
        >>> with ExecutionSummaryTracker(logger) as tracker:
        ...     # Your execution logic here
        ...     tracker.increment_processed_records(1250)
        ...     tracker.set_validation_result("schema_validation", "PASSED")
        # Summary report automatically logged on exit

        >>> # Or use manually:
        >>> tracker = ExecutionSummaryTracker(logger, dry_run=True)
        >>> tracker.start()
        >>> # ... execution logic ...
        >>> tracker.log_summary()
    """

    def __init__(
        self,
        logger: logging.Logger,
        dry_run: bool = False,
        message_type: Optional[str] = None,
    ):
        """Initialize execution summary tracker.

        Args:
            logger: Logger instance to use for summary report.
            dry_run: Whether this is a dry-run execution.
            message_type: ISO 20022 message type (if applicable).
        """
        self.logger = logger
        self.dry_run = dry_run
        self.message_type = message_type

        # Execution metrics
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.start_time_iso: Optional[str] = None
        self.end_time_iso: Optional[str] = None

        # Event counts
        self.counts = {
            "debug": 0,
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0,
        }

        # Processing metrics
        self.total_records_processed = 0
        self.validation_metrics: dict[str, str] = {}
        self.output_file: Optional[str] = None
        self.log_file: Optional[str] = None

        # Status tracking
        self.has_errors = False
        self.has_warnings = False
        self.aborted = False

    def start(self) -> None:
        """Mark execution start time."""
        self.start_time = time.time()
        self.start_time_iso = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )

    def increment_event_count(self, level: str) -> None:
        """Increment count for a specific log level.

        Args:
            level: Log level name (debug, info, warning, error, critical).
        """
        level_lower = level.lower()
        if level_lower in self.counts:
            self.counts[level_lower] += 1

        if level_lower in ("error", "critical"):
            self.has_errors = True
        elif level_lower == "warning":
            self.has_warnings = True

    def increment_processed_records(self, count: int = 1) -> None:
        """Increment total records processed count.

        Args:
            count: Number of records to add (default: 1).
        """
        self.total_records_processed += count

    def set_validation_result(self, validation_type: str, result: str) -> None:
        """Set validation result for a specific validation type.

        Args:
            validation_type: Type of validation (e.g., "schema_validation").
            result: Result status (e.g., "PASSED", "FAILED").
        """
        self.validation_metrics[validation_type] = result

    def set_output_file(self, file_path: Optional[str]) -> None:
        """Set output file path.

        Args:
            file_path: Path to generated output file (None for dry-run).
        """
        self.output_file = file_path

    def set_log_file(self, file_path: str) -> None:
        """Set log file path.

        Args:
            file_path: Path to log file.
        """
        self.log_file = file_path

    def abort(self) -> None:
        """Mark execution as aborted."""
        self.aborted = True

    def _get_status(self) -> str:
        """Determine execution status based on tracked metrics.

        Returns:
            Status string from ExecutionStatus constants.
        """
        if self.aborted:
            return ExecutionStatus.ABORTED
        if self.has_errors:
            return ExecutionStatus.FAILED
        if self.has_warnings:
            return ExecutionStatus.COMPLETED_WITH_WARNINGS
        return ExecutionStatus.SUCCESS

    def log_summary(self) -> None:
        """Log execution summary report."""
        self.end_time = time.time()
        self.end_time_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        duration_ms = 0
        if self.start_time is not None:
            duration_ms = int((self.end_time - self.start_time) * 1000)

        summary_data = {
            "status": self._get_status(),
            "execution_mode": "dry_run" if self.dry_run else "production",
            "total_records_processed": self.total_records_processed,
            "counts": self.counts,
            "performance": {
                "start_time": self.start_time_iso,
                "end_time": self.end_time_iso,
                "total_duration_ms": duration_ms,
            },
        }

        # Add validation metrics if any were tracked
        if self.validation_metrics:
            summary_data["validation_metrics"] = self.validation_metrics  # type: ignore[assignment]

        # Add artifacts info
        output_file_value = "None"
        if self.output_file:
            output_file_value = self.output_file
        elif self.dry_run:
            output_file_value = "None (Dry Run)"

        summary_data["artifacts"] = {  # type: ignore[assignment]
            "output_file": output_file_value,
            "log_file": self.log_file if self.log_file else "None",
        }

        # Add message type if provided
        if self.message_type:
            summary_data["message_type"] = self.message_type

        log_event(
            self.logger,
            logging.INFO,
            Events.EXECUTION_SUMMARY,
            message="Execution Summary Report",
            summary=summary_data,
        )

    def __enter__(self) -> "ExecutionSummaryTracker":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - log summary automatically."""
        if exc_type is not None:
            # Exception occurred - mark as error and aborted
            self.increment_event_count("error")
            self.abort()

        self.log_summary()
