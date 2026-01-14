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

"""Tests for pain001.exceptions module."""

from pain001.exceptions import (
    ConfigurationError,
    DataSourceError,
    Pain001Error,
    PaymentValidationError,
    SchemaValidationError,
    XMLGenerationError,
)


def test_pain001_error_base():
    """Test that Pain001Error is the base exception."""
    error = Pain001Error("Base error")
    assert str(error) == "Base error"
    assert isinstance(error, Exception)


def test_payment_validation_error():
    """Test PaymentValidationError with field attribute."""
    error = PaymentValidationError("Invalid IBAN", field="iban")
    assert str(error) == "Invalid IBAN"
    assert error.field == "iban"
    assert isinstance(error, Pain001Error)


def test_payment_validation_error_without_field():
    """Test PaymentValidationError without field attribute."""
    error = PaymentValidationError("Invalid data")
    assert str(error) == "Invalid data"
    assert error.field is None


def test_xml_generation_error():
    """Test XMLGenerationError."""
    error = XMLGenerationError("Template rendering failed")
    assert str(error) == "Template rendering failed"
    assert isinstance(error, Pain001Error)


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Invalid log level")
    assert str(error) == "Invalid log level"
    assert isinstance(error, Pain001Error)


def test_data_source_error():
    """Test DataSourceError."""
    error = DataSourceError("File not found: data.csv")
    assert str(error) == "File not found: data.csv"
    assert isinstance(error, Pain001Error)


def test_schema_validation_error():
    """Test SchemaValidationError with errors list."""
    errors = [
        "Line 10: Invalid element 'Amt'",
        "Line 15: Missing required element 'Dbtr'",
    ]
    error = SchemaValidationError("XSD validation failed", errors=errors)
    assert str(error) == "XSD validation failed"
    assert error.errors == errors
    assert isinstance(error, Pain001Error)


def test_schema_validation_error_without_errors():
    """Test SchemaValidationError without errors list."""
    error = SchemaValidationError("XSD validation failed")
    assert str(error) == "XSD validation failed"
    assert error.errors == []


def test_exception_inheritance():
    """Test that all custom exceptions inherit from Pain001Error."""
    exceptions = [
        PaymentValidationError,
        XMLGenerationError,
        ConfigurationError,
        DataSourceError,
        SchemaValidationError,
    ]
    for exc_class in exceptions:
        assert issubclass(exc_class, Pain001Error)
        assert issubclass(exc_class, Exception)


def test_exception_messages_preserved():
    """Test that exception messages are preserved through inheritance."""
    message = "Test error message with details"
    for exc_class in [
        Pain001Error,
        PaymentValidationError,
        XMLGenerationError,
        ConfigurationError,
        DataSourceError,
        SchemaValidationError,
    ]:
        error = exc_class(message)
        assert str(error) == message


def test_payment_validation_error_repr():
    """Test PaymentValidationError string representation with field."""
    error = PaymentValidationError("Invalid BIC format", field="bic")
    repr_str = repr(error)
    assert "PaymentValidationError" in repr_str
    assert "Invalid BIC format" in repr_str


def test_schema_validation_error_repr():
    """Test SchemaValidationError string representation with errors."""
    errors = ["Error 1", "Error 2"]
    error = SchemaValidationError("Validation failed", errors=errors)
    repr_str = repr(error)
    assert "SchemaValidationError" in repr_str
    assert "Validation failed" in repr_str
