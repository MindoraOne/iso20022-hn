# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

from enum import Enum


class LocalTemplateType(str, Enum):
    """Available local payment transaction templates.

    The values are the PUBLIC contract of the API (ach, between_accounts, odp)
    and do NOT need to match the real file name on disk — that mapping lives
    in `LOCAL_TEMPLATE_FILENAMES` (see validators.resolve_template_path).

    To add a new template:
      1. Add a new member here with a clean public value.
      2. Add its real filename (without .xml extension) to LOCAL_TEMPLATE_FILENAMES.
      3. Place the corresponding .xml file in LOCAL_TEMPLATE_ROOT/xml/.
    """

    ach              = "ach"
    between_accounts = "between_accounts"
    odp              = "odp"
    mixed            = "mixed"


# Internal mapping enum-value -> real file name (without extension) in
# LOCAL_TEMPLATE_ROOT/xml/. Keeps the API contract clean even though
# the files on disk have Spanish names with the "_Lempiras" suffix.
LOCAL_TEMPLATE_FILENAMES: dict[LocalTemplateType, str] = {
    LocalTemplateType.ach: "transferencia_ach_Lempiras",
    LocalTemplateType.between_accounts: "transferencia_entre_cuentas_Lempiras",
    LocalTemplateType.odp: "transferencia_ordenes_de_pago_Lempiras",
    LocalTemplateType.mixed: "transferencia_mixta_Lempiras",
}

# `type` values allowed per row when a request uses (or is routed to) the
# mixed template — one CdtTrfTxInf can be ach/between_accounts/odp, but
# never "mixed" itself (that value only identifies the container template).
ROW_TYPE_VALUES: frozenset[str] = frozenset(
    {
        LocalTemplateType.ach.value,
        LocalTemplateType.between_accounts.value,
        LocalTemplateType.odp.value,
    }
)
