#!/usr/bin/env python3
"""
tok-meter — Sums input/output tokens from a Claude Code JSONL transcript
and appends a summary line to sessions/token-usage.jsonl.

Usage: tok-meter.py <path-to-transcript.jsonl>

Never fails the session: any error is ignored and the script exits with
exit 0, since it is invoked by a Stop/SessionEnd hook.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO / "sessions" / "token-usage.jsonl"


def sum_tokens(transcript_path: Path) -> dict:
    input_tokens = 0
    output_tokens = 0
    last_timestamp = None

    with transcript_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            usage = entry.get("message", {}).get("usage") or entry.get("usage")
            if usage:
                input_tokens += usage.get("input_tokens", 0) or 0
                output_tokens += usage.get("output_tokens", 0) or 0

            timestamp = entry.get("timestamp")
            if timestamp:
                last_timestamp = timestamp

    return {
        "session_id": transcript_path.stem,
        "timestamp": last_timestamp,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def main() -> int:
    if len(sys.argv) < 2:
        return 0

    transcript_path = Path(sys.argv[1])
    if not transcript_path.is_file():
        return 0

    try:
        summary = sum_tokens(transcript_path)
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(summary) + "\n")
    except Exception as exc:  # must never break the session
        print(f"tok-meter: non-fatal error ({exc})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
