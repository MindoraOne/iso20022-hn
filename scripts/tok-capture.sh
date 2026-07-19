#!/usr/bin/env bash
# tok-capture — Launcher for the token capture hook.
#
# Invoked by Claude Code on the Stop/SessionEnd event. The event payload
# arrives via STDIN as JSON and includes "transcript_path". This script extracts
# that path and runs the tok-meter.py meter on it.
#
# Wired from .claude/settings.json. Must never fail the session: it always
# ends with exit 0, even if the meter fails.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="python3"

PAYLOAD="$(cat)"

TRANSCRIPT="$("$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('transcript_path',''))" <<<"$PAYLOAD" 2>/dev/null)"

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  echo "tok-capture: transcript_path ausente o inexistente, nada que medir." >&2
  exit 0
fi

"$PYTHON" "$REPO_DIR/scripts/tok-meter.py" "$TRANSCRIPT" >&2 || true
exit 0
