# iso20022-hn — Copyright (c) 2026 MindoraOne. All rights reserved.
# This file is original work, not derived from pain001 (Sebastien Rousseau).

from pathlib import Path

from pain001.api.local.settings import settings
from pain001.api.models import MessageType

# Unique API prefix — changing it here is enough to version all routes
API_PREFIX = "/api/v1"

# Root directory of the local Jinja2 XML templates inside the container.
# The active bank (subfolder under templates/local/) is configurable via
# Settings.local_template_bank — default "bancatlan" (only source available today).
LOCAL_TEMPLATE_ROOT = (
    Path(__file__).parent.parent.parent
    / "templates"
    / "local"
    / settings.local_template_bank
    / "pain.001.001.05"
)

# XSD schema reused from the standard pain001 templates
XSD_PATH = (
    Path(__file__).parent.parent.parent
    / "templates"
    / "pain.001.001.05"
    / "pain.001.001.05.xsd"
)

# Temp directory for CSV uploads. Configurable via Settings.temp_dir (env
# TEMP_DIR): default "<cwd>/tmp" outside Docker; in the container it is set to
# /app/tmp via env (see .env.example / docs-intern/configuracion.md). Must stay
# INSIDE the process cwd — pain001.data.loader anchors path validation
# to os.getcwd() (see Settings._default_temp_dir in settings.py).
TEMP_DIR = Path(settings.temp_dir)

# ISO 20022 message type handled by this extension — single source of truth in
# pain001.api.models.MessageType (avoids duplicating the string literal)
MESSAGE_TYPE = MessageType.PAIN_001_05.value

# Maximum allowed CSV upload size (comes from Settings)
MAX_FILE_SIZE = settings.max_body_size
MAX_FILE_SIZE_MB = MAX_FILE_SIZE // (1024 * 1024)

# Chunk size for streaming upload reads
UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB
