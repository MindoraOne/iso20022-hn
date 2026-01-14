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

"""Universal data loader supporting multiple input sources."""

from typing import Any, Union

from pain001.csv.load_csv_data import load_csv_data
from pain001.csv.validate_csv_data import validate_csv_data
from pain001.db.load_db_data import load_db_data
from pain001.db.validate_db_data import validate_db_data
from pain001.exceptions import DataSourceError, PaymentValidationError


def load_payment_data(
    data_source: Union[str, list[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Universal data loader supporting multiple input sources.

    This function provides a unified interface for loading payment data from
    various sources while maintaining backward compatibility with existing
    file-based workflows.

    Args:
        data_source: The payment data source. Supports:
            - str: File path to CSV (.csv) or SQLite (.db) file
            - list: List of dictionaries with payment data
            - dict: Single payment transaction as dictionary

    Returns:
        List[Dict[str, Any]]: List of payment data dictionaries

    Raises:
        ValueError: If data source type is unsupported or data is invalid
        FileNotFoundError: If file path doesn't exist

    Examples:
        # Existing file-based usage (backward compatible)
        >>> data = load_payment_data('payments.csv')
        >>> data = load_payment_data('payments.db')

        # New direct Python data usage
        >>> data = load_payment_data([
        ...     {'id': 'MSG001', 'amount': '1000.00', ...},
        ...     {'id': 'MSG002', 'amount': '500.00', ...}
        ... ])

        # Single transaction
        >>> data = load_payment_data({
        ...     'id': 'MSG001', 'amount': '1000.00', ...
        ... })
    """
    # TODO: add streaming/chunked loaders for large CSV/DB sources to reduce memory usage.
    # Handle file path (existing behavior - backward compatible)
    if isinstance(data_source, str):
        return _load_from_file(data_source)

    # Handle Python dict/list (new feature)
    elif isinstance(data_source, list):
        return _load_from_list(data_source)

    elif isinstance(data_source, dict):
        return _load_from_dict(data_source)

    else:
        raise DataSourceError(
            f"Unsupported data source type: {type(data_source).__name__}. "
            f"Expected str (file path), list, or dict."
        )


def _load_from_file(file_path: str) -> list[dict[str, Any]]:
    """
    Load data from file (CSV or SQLite).

    This preserves the existing behavior for backward compatibility.
    """
    if file_path.endswith(".csv"):
        data = load_csv_data(file_path)
        if not validate_csv_data(data):
            raise PaymentValidationError(
                f"CSV data validation failed for {file_path}"
            )
        return data

    elif file_path.endswith(".db"):
        data = load_db_data(file_path, table_name="pain001")
        if not validate_db_data(data):
            raise PaymentValidationError(
                f"Database data validation failed for {file_path}"
            )
        return data

    else:
        raise DataSourceError(
            f"Unsupported file type: {file_path}. Expected .csv or .db file."
        )


def _load_from_list(data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Load data from Python list of dictionaries.

    New feature for direct Python data input.
    """
    if not data_list:
        raise DataSourceError("Empty data list provided.")

    if not all(isinstance(item, dict) for item in data_list):
        raise PaymentValidationError(
            "All items in data list must be dictionaries. "
            f"Found: {[type(item).__name__ for item in data_list if not isinstance(item, dict)]}"
        )

    # Mandatory validation for data integrity
    if not validate_csv_data(data_list):
        raise PaymentValidationError("Data list validation failed")
    return data_list


def _load_from_dict(data_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Load data from a single Python dictionary.

    New feature for single transaction input.
    """
    if not data_dict:
        raise DataSourceError("Empty data dictionary provided.")

    # Wrap single dict in list and validate
    data_list = [data_dict]
    if not validate_csv_data(data_list):
        raise PaymentValidationError("Data dictionary validation failed")
    return data_list
