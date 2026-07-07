#!/usr/bin/env python3
"""
guard-precheck — PreToolUse hook that protects the iso20022-hn repo.

This repo is a Python library/service (local FastAPI) that generates pain.001
(ISO 20022) payment initiation messages for Honduran banks from CSV/JSON/DB
input. It intercepts every call to Bash/Read/Write/Edit/NotebookEdit BEFORE it
runs and blocks it if it violates the local security policy.
Returns a 'deny' decision with a clear reason.

Claude MUST NOT delete files, run dangerous system commands, operate outside
the repo, or read/write secrets (.env*) or the restricted/ folder.

Receives the event via STDIN (JSON) and responds via STDOUT (JSON). Wired up
from .claude/settings.json as a PreToolUse hook with matcher
"Bash|Read|Write|Edit|NotebookEdit". See this repo's docs/.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def deny(reason: str) -> None:
    """Blocks the tool with a reason and exits."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"blocked by guard policy: {reason}",
        }
    }))
    sys.exit(0)


def allow_passthrough() -> None:
    """Does not interfere: lets the normal permission rules apply."""
    sys.exit(0)


# Dangerous Bash command patterns. Each tuple: (regex, reason).
DANGEROUS_BASH = [
    # Destructive deletions
    (r"\brm\s+(-[a-zA-Z]*\s+)*", "file deletion (rm)"),
    (r"\brmdir\b", "directory deletion (rmdir)"),
    (r"\bunlink\b", "file deletion (unlink)"),
    (r"\bfind\b.*-delete\b", "bulk deletion (find -delete)"),
    (r"\bshred\b", "destructive secure deletion (shred)"),
    (r">\s*/dev/sd", "direct write to disk"),
    (r"\bdd\b\s+if=", "low-level copy (dd)"),
    (r"\bmkfs\b", "filesystem formatting (mkfs)"),
    (r":\(\)\s*\{.*\};", "fork bomb"),
    # System / privileges
    (r"\bsudo\b", "privilege escalation (sudo)"),
    (r"\bsu\b\s", "user switch (su)"),
    (r"\bchmod\s+(-[a-zA-Z]*\s+)*[0-7]*777\b", "dangerous permissions (chmod 777)"),
    (r"\bchown\b", "ownership change (chown)"),
    (r"\bkill(all)?\b", "process termination (kill)"),
    (r"\breboot\b|\bshutdown\b|\bhalt\b|\bpoweroff\b", "system shutdown/reboot"),
    (r"\bmount\b|\bumount\b", "filesystem mounting"),
    (r"\bcurl\b.*\|\s*(ba)?sh\b", "remote script execution (curl | sh)"),
    (r"\bwget\b.*\|\s*(ba)?sh\b", "remote script execution (wget | sh)"),
]

# References to .env files in Bash commands. Only .env.example is a public
# template without secrets (allowed); everything else is always blocked.
ENV_TOKEN_RE = re.compile(r"\.env(?:\.[A-Za-z0-9_]+)*(?![A-Za-z0-9_])")
ENV_ALWAYS_OK = {".env.example"}

# Allowed absolute paths (the repo and Claude's own temp files).
ALLOWED_ABS_PREFIXES = [
    str(REPO),
    "/tmp",  # noqa: S108
]

# Read/write ALWAYS allowed: the only public template without secrets.
ALWAYS_OK_PATTERNS = [
    r"(^|/)\.env\.example$",
]
# Read/write ALWAYS forbidden: .env with real values and protected paths.
FORBIDDEN_PATTERNS = [
    (r"(^|/)\.env$", "reading/writing the real .env (secrets)"),
    (r"(^|/)\.env\.[A-Za-z0-9_]+$", "reading/writing a .env variant (secrets)"),
    (r"(^|/)restricted(/|$)", "access to the restricted folder (restricted/)"),
    (r"(^|/)\.ssh(/|$)", "reading SSH keys"),
]


def check_env_refs_bash(cmd: str) -> None:
    """Blocks terminal references to any .env with secrets."""
    for tok in ENV_TOKEN_RE.findall(cmd):
        if tok in ENV_ALWAYS_OK:
            continue
        deny(f"access to an environment/secrets file via terminal ({tok})")


def check_bash(command: str) -> None:
    cmd = command.strip()
    for pattern, reason in DANGEROUS_BASH:
        if re.search(pattern, cmd):
            deny(reason)
    check_env_refs_bash(cmd)
    for token in re.findall(r"(?<!\w)(/[^\s'\";|&]+)", cmd):
        if any(token == p or token.startswith(p + "/") for p in ALLOWED_ABS_PREFIXES):
            continue
        if token.startswith("/dev/null") or token in ("/dev/stdin", "/dev/stdout", "/dev/stderr"):
            continue
        deny(f"operation outside the repo on absolute path: {token}")
    allow_passthrough()


def check_file_access(file_path: str, action: str) -> None:
    """Applies the same secrets/restricted policy to reads and writes."""
    fp = file_path or ""
    for pattern in ALWAYS_OK_PATTERNS:
        if re.search(pattern, fp):
            allow_passthrough()
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, fp):
            deny(f"{action} on {reason}: {fp}")
    allow_passthrough()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow_passthrough()
        return 0

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool == "Bash":
        check_bash(tool_input.get("command", ""))
    elif tool == "Read":
        check_file_access(tool_input.get("file_path", ""), "read")
    elif tool in ("Write", "Edit", "NotebookEdit"):
        check_file_access(tool_input.get("file_path", ""), "write")

    allow_passthrough()
    return 0


if __name__ == "__main__":
    main()
