#!/usr/bin/env python3
"""阻断明显危险的 shell 命令。"""

from __future__ import annotations

import json
import re
import sys


def extract_command(payload: str) -> str:
    """从 hook payload 中尽量提取 shell 命令。"""
    try:
        data = json.loads(payload or "{}")
    except json.JSONDecodeError:
        return payload
    tool_input = data.get("tool_input") or data.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return payload


def main() -> int:
    """检查危险命令。"""
    command = extract_command(sys.stdin.read())
    patterns = [
        r"\brm\s+-rf\b",
        r"\bgit\s+reset\s+--hard\b",
        r"\bgit\s+clean\b",
        r"\bgit\s+push\b",
        r"\bsudo\b",
        r"\bchmod\s+-R\s+777\b",
        r"\bcat\s+\.env",
    ]
    for pattern in patterns:
        if re.search(pattern, command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"危险命令被阻断: {pattern}",
                }
            }, ensure_ascii=False))
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
