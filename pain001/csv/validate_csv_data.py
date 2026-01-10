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

# Validate the CSV data before processing it. The CSV data must contain
# the following columns:
#
# - id (int) - unique identifier
# - date (str) - date of the payment
# - nb_of_txs (int) - number of transactions
# - initiator_name (str) - name of the initiator
# - payment_information_id (str) - payment information identifier
# - payment_method (str) - payment method
# - batch_booking (bool) - batch booking
# - ctrl_sum (int) - control sum
# - service_level_code (str) - service level code
# - requested_execution_date (str) - requested execution date
# - debtor_name (str) - debtor name
# - debtor_account_IBAN (str) - debtor account IBAN
# - debtor_agent_BIC (str) - debtor agent BIC
# - forwarding_agent_BIC (str) - forwarding agent BIC
# - charge_bearer (str) - charge bearer
# - payment_id (str) - payment identifier
# - payment_amount (str) - payment amount
# - currency (str) - currency
# - creditor_agent_BIC (str) - creditor agent BIC
# - creditor_name (str) - creditor name
# - creditor_account_IBAN (str) - creditor account IBAN
# - remittance_information (str) - remittance information


import datetime
from typing import Any


def validate_csv_data(data: list[dict[str, Any]]) -> bool:
    """Validate the CSV data before processing it.

    Args:
        data (list): A list of dictionaries containing the CSV data.

    Returns:
        bool: True if the data is valid, False otherwise.
    """
    required_columns = {
        "id": int,
        "date": datetime.datetime,
        "nb_of_txs": int,
        "ctrl_sum": float,
        "initiator_name": str,
        "payment_information_id": str,
        "payment_method": str,
        "batch_booking": bool,
        "service_level_code": str,
        "requested_execution_date": datetime.datetime,
        "debtor_name": str,
        "debtor_account_IBAN": str,
        "debtor_agent_BIC": str,
        "forwarding_agent_BIC": str,
        "charge_bearer": str,
        "payment_id": str,
        "payment_amount": float,
        "currency": str,
        "creditor_agent_BIC": str,
        "creditor_name": str,
        "creditor_account_IBAN": str,
        "remittance_information": str,
    }

    if not data:
        print("Error: The CSV data is empty.")
        return False

    is_valid = True
    errors = []  # Batch error messages for better performance

    for _row_idx, row in enumerate(data):
        missing_columns = []
        invalid_columns = []

        for column, data_type in required_columns.items():
            raw_value = row.get(column)

            # Single strip operation, cached result
            if raw_value is None:
                missing_columns.append(column)
                is_valid = False
                continue

            value = raw_value.strip()

            if not value:
                missing_columns.append(column)
                is_valid = False
                continue

            # Optimized type validation
            try:
                if data_type is int:
                    int(value)
                elif data_type is float:
                    float(value)
                elif data_type is bool:
                    if value.lower() not in ("true", "false"):
                        raise ValueError
                elif data_type is datetime.datetime:
                    # Handle the "Z" suffix for UTC
                    if value.endswith("Z"):
                        value = value[:-1] + "+00:00"
                    try:
                        datetime.datetime.fromisoformat(value)
                    except ValueError:
                        datetime.datetime.strptime(value, "%Y-%m-%d")
                # str type always passes if not empty
            except ValueError:
                invalid_columns.append(column)
                is_valid = False

        # Batch error messages per row
        if missing_columns:
            errors.append(
                f"Error: Missing value(s) for column(s) {missing_columns} in row: {row}"
            )
        if invalid_columns:
            expected_types = [
                required_columns[col].__name__ for col in invalid_columns
            ]
            errors.append(
                f"Error: Invalid data type for column(s) "
                f"{invalid_columns}, expected {expected_types} in row: {row}"
            )

    # Single print operation for all errors
    if errors:
        print("\n".join(errors))

    return is_valid
