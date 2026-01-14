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

"""Custom exception hierarchy for Pain001.

This module provides granular exception types to enable precise error handling
in banking integrations. Instead of catching generic ValueError or TypeError,
consuming applications can distinguish between data validation errors,
configuration errors, and XML generation failures.

Example:
    >>> try:
    ...     process_files(...)
    ... except PaymentValidationError as e:
    ...     # Handle invalid IBAN/BIC - notify user
    ...     log.error(f"Payment data invalid: {e}")
    ... except XMLGenerationError as e:
    ...     # Handle XML generation failure - check templates
    ...     log.error(f"XML generation failed: {e}")
    ... except ConfigurationError as e:
    ...     # Handle config issues - check setup
    ...     log.error(f"Configuration error: {e}")
"""


class Pain001Error(Exception):
    """Base exception for all Pain001 errors.

    All custom exceptions in this library inherit from this base class,
    allowing consumers to catch any Pain001-specific error with a single
    except clause if needed.

    Example:
        >>> try:
        ...     process_files(...)
        ... except Pain001Error:
        ...     # Catch any Pain001-specific error
        ...     log.error("Pain001 operation failed")
    """


class PaymentValidationError(Pain001Error):
    """Raised when payment data validation fails.

    This exception indicates issues with input data such as:
    - Invalid IBAN format
    - Invalid BIC/SWIFT code
    - Invalid amount (negative, too large, wrong format)
    - Missing required fields (debtor name, creditor account, etc.)
    - Invalid date formats

    Example:
        >>> try:
        ...     validate_payment_data(data)
        ... except PaymentValidationError as e:
        ...     # User-facing error - show validation message
        ...     return {"error": str(e), "field": e.field}
    """

    def __init__(self, message: str, field: str = None):
        """Initialize validation error with optional field name.

        Args:
            message: Human-readable error message.
            field: Optional field name that caused the validation error.
        """
        super().__init__(message)
        self.field = field


class XMLGenerationError(Pain001Error):
    """Raised when XML generation or validation fails.

    This exception indicates issues with:
    - Jinja2 template rendering failures
    - XSD schema validation errors
    - XML namespace issues
    - Missing or corrupted template files
    - Invalid XML structure

    Example:
        >>> try:
        ...     generate_xml(data, template, schema)
        ... except XMLGenerationError as e:
        ...     # System error - check templates and schemas
        ...     log.error(f"XML generation failed: {e}")
        ...     alert_ops_team()
    """


class ConfigurationError(Pain001Error):
    """Raised when configuration or setup is invalid.

    This exception indicates issues with:
    - Missing or invalid setup.cfg
    - Invalid CLI arguments
    - Missing required environment variables
    - Invalid file paths
    - Unsupported ISO 20022 version

    Example:
        >>> try:
        ...     load_config("pain.001.001.99")
        ... except ConfigurationError as e:
        ...     # Config error - show usage help
        ...     print(f"Configuration error: {e}")
        ...     print_usage_help()
    """


class DataSourceError(Pain001Error):
    """Raised when data source access fails.

    This exception indicates issues with:
    - File not found (CSV, SQLite)
    - Database connection errors
    - Corrupted data files
    - Unsupported file formats
    - Empty data sources

    Example:
        >>> try:
        ...     load_payment_data("payments.csv")
        ... except DataSourceError as e:
        ...     # Data access error - check file exists
        ...     log.error(f"Cannot access data source: {e}")
    """


class SchemaValidationError(Pain001Error):
    """Raised when XSD schema validation fails.

    This exception indicates issues with:
    - Generated XML does not conform to ISO 20022 schema
    - Missing required XML elements
    - Invalid XML element values
    - Namespace mismatches

    Example:
        >>> try:
        ...     validate_xml_against_schema(xml, xsd)
        ... except SchemaValidationError as e:
        ...     # Schema validation error - check data mapping
        ...     log.error(f"XML schema validation failed: {e}")
        ...     log.debug(f"Validation errors: {e.errors}")
    """

    def __init__(self, message: str, errors: list = None):
        """Initialize schema validation error with optional error list.

        Args:
            message: Human-readable error message.
            errors: Optional list of detailed validation errors.
        """
        super().__init__(message)
        self.errors = errors or []
