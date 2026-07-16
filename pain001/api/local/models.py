# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

"""Pydantic models for the local (HN) API — JSON generation contract.

This contract is specific to Banco Atlántida Honduras: it only declares the
fields the 4 HN templates (`pain001/templates/local/bancatlan/...`) actually
read. The OSS `pain001` schema exposes a much larger ISO 20022 field set
(control sums, payment method/service level, agent BICs, full postal
addresses, etc.) — those are NOT requested here because the HN templates
never reference them (they're either constant in the template or simply
absent from it).

The public JSON contract (request/response bodies) uses camelCase, per the
`api-standards` skill. Internally, `pain001`'s data pipeline
(`load_payment_data`, `validate_csv_data_detailed`, the CSV column headers,
the Jinja2 templates) still uses snake_case — including several fields that
embed an all-caps acronym (`debtor_account_IBAN`, `debtor_clearing_member_id`,
...), so a generic camelCase-to-snake_case regex would lowercase those
acronyms and stop matching the exact name `pain001` expects. `PaymentRow`
avoids that by declaring one snake_case field per camelCase key of the row
contract, each with an explicit `Field(alias=...)`.

Field-level business validation (which fields are actually required per
template, formats, cross-field rules) is NOT duplicated here — it stays in
`pain001.csv.validate_csv_data`, the single source of truth shared with the
CSV upload path. That's why every field is optional: `PaymentRow` only
performs the JSON casing translation, not the business validation.

`extra="allow"` (see `model_config` below) means old/removed field names
sent by a caller still pass through unchanged instead of raising — they're
just ignored by the HN templates, same as any other unrecognized key.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from pain001.api.local.enums import LocalTemplateType


class PaymentRow(BaseModel):
    """One payment data row, accepted in camelCase and read internally in snake_case.

    `model_config.populate_by_name=True` also accepts the row already in
    snake_case (e.g. rows read straight from a CSV fixture in tests), so the
    same model works for both casings without extra code.

    `extra="allow"`: any key not declared above (a future field, or a typo)
    passes through unchanged under its original key — same behavior the
    former `normalize_row_keys` had for keys missing from its lookup table.
    Its resolution (kept as-is or rejected) is left to `pain001`'s own
    downstream validation, not to this model.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = Field(default=None, alias="id")
    date: str | None = Field(default=None, alias="date")
    initiator_name: str | None = Field(default=None, alias="initiatorName")
    initiator_org_id: str | None = Field(default=None, alias="initiatorOrgId")
    initiator_contact_name: str | None = Field(default=None, alias="initiatorContactName")
    payment_information_id: str | None = Field(default=None, alias="paymentInformationId")
    requested_execution_date: str | None = Field(default=None, alias="requestedExecutionDate")
    debtor_name: str | None = Field(default=None, alias="debtorName")
    debtor_street_name: str | None = Field(default=None, alias="debtorStreetName")
    debtor_account_IBAN: str | None = Field(default=None, alias="debtorAccountIBAN")
    debtor_clearing_member_id: str | None = Field(default=None, alias="debtorClearingMemberId")
    payment_instruction_id: str | None = Field(default=None, alias="paymentInstructionId")
    payment_end_to_end_id: str | None = Field(default=None, alias="paymentEndToEndId")
    payment_amount: str | None = Field(default=None, alias="paymentAmount")
    payment_currency: str | None = Field(default=None, alias="paymentCurrency")
    creditor_name: str | None = Field(default=None, alias="creditorName")
    creditor_street_name: str | None = Field(default=None, alias="creditorStreetName")
    creditor_town_name: str | None = Field(default=None, alias="creditorTownName")
    creditor_country: str | None = Field(default=None, alias="creditorCountry")
    creditor_account_IBAN: str | None = Field(default=None, alias="creditorAccountIBAN")
    creditor_account_type: str | None = Field(default=None, alias="creditorAccountType")
    creditor_clearing_member_id: str | None = Field(default=None, alias="creditorClearingMemberId")
    creditor_private_id: str | None = Field(default=None, alias="creditorPrivateId")
    creditor_private_id_scheme: str | None = Field(default=None, alias="creditorPrivateIdScheme")
    creditor_mobile_number: str | None = Field(default=None, alias="creditorMobileNumber")
    creditor_email_address: str | None = Field(default=None, alias="creditorEmailAddress")
    category_purpose_code: str | None = Field(default=None, alias="categoryPurposeCode")
    reference_number: str | None = Field(default=None, alias="referenceNumber")
    remittance_information: str | None = Field(default=None, alias="remittanceInformation")

    # Row-level transaction-type marker (ach/between_accounts/odp) and its
    # local instrument, single-word/no-acronym fields — same in camelCase
    # and snake_case, listed too so the model is a complete, self-documenting
    # map of the row contract.
    type: str | None = Field(default=None, alias="type")
    local_instrument: str | None = Field(default=None, alias="localInstrument")


class GenerateJsonRequest(BaseModel):
    """Request body for JSON-based ISO 20022 XML generation.

    `data` rows are declared as `PaymentRow` (camelCase in, snake_case out
    via `model_dump(by_alias=False)`) and passed to
    `pain001.data.loader.load_payment_data`, which performs the actual
    field-level validation (same rules as the CSV path).

    Each row MAY carry an optional `type` key (ach / between_accounts / odp)
    to mark its transaction kind. If `template=mixed`, or any row carries a
    `type`, the request is routed to the mixed template regardless of the
    `template` value — see `_select_template_path` in `app_local.py` and
    `assert_valid_row_types` in `validators.py` for the enforcement.
    """

    model_config = ConfigDict(extra="forbid")

    template: LocalTemplateType = Field(
        ..., description="Template key: ach, between_accounts, odp, mixed"
    )
    data: list[PaymentRow] = Field(
        ...,
        min_length=1,
        description=(
            "Non-empty list of payment data rows. Each row may include an "
            "optional 'type' (ach/between_accounts/odp) for mixed requests."
        ),
    )
