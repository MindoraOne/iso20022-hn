# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from enum import Enum


class LocalTemplateType(str, Enum):
    """Available local payment transaction templates.

    To add a new template:
      1. Add a new member here — the value must match the filename (without .xml extension) in LOCAL_TEMPLATE_ROOT/xml/.
      2. Place the corresponding .xml file in LOCAL_TEMPLATE_ROOT/xml/.
      3. Place the example .csv file in LOCAL_TEMPLATE_ROOT/csv/.
    """

    ach              = "transfer_ach"
    between_accounts = "transfer_between_accounts"
    odp              = "transfer_odp"