# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from pathlib import Path

# Root directory of the local Jinja2 XML templates inside the container
LOCAL_TEMPLATE_ROOT = (
    Path(__file__).parent.parent.parent
    / "templates"
    / "local"
    / "pain.001.001.05"
)

# XSD schema reused from the standard pain001 templates
XSD_PATH = (
    Path(__file__).parent.parent.parent
    / "templates"
    / "pain.001.001.05"
    / "pain.001.001.05.xsd"
)

# Temp directory for CSV uploads — must be inside /app for path validator
TEMP_DIR = Path("/app/tmp")

# ISO 20022 message type handled by this extension
MESSAGE_TYPE = "pain.001.001.05"

# Maximum allowed CSV upload size
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_FILE_SIZE_MB = MAX_FILE_SIZE // (1024 * 1024)

# Chunk size for streaming upload reads
UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB