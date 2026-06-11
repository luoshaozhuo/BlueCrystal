#!/usr/bin/env python3
"""阻断默认不允许的 Git/GitHub 写操作。"""

from __future__ import annotations

import json
import re
import sys


READ_ONLY_GIT_PATTERNS = (
    r"^\s*git\s+status(?:\s|$)",
    r"^\s*git\s+diff(?:\s|$)",
    r"^\s*git\s+log(?:\s|$)",
    r"^\s*git\s+show(?:\s|$)",
    r"^\s*git\s+rev-parse(?:\s|$)",
)

DENIED_GIT_PATTERNS = (
    r"^\s*git\s+commit(?:\s|$)",
    r"^\s*git\s+push(?:\s|$)",
    r"^\s*git\s+reset(?:\s|$)",
    r"^\s*git\s+clean(?:\s|$)",
    r"^\s*git\s+checkout\s+--(?:\s|$)",
    r"^\s*git\s+restore(?:\s|$)",
    r"^\s*git\s+switch(?:\s|$)",
    r"^\s*git\s+merge(?:\s|$)",
    r"^\s*git\s+rebase(?:\s|$)",
    r"^\s*git\s+cherry-pick(?:\s|$)",
    r"^\s*git\s+tag(?:\s|$)",
    r"^\s*git\s+stash\s+(?:pop|drop|clear)(?:\s|$)",
    r"^\s*git\s+remote\s+set-url(?:\s|$)",
)

DENIED_GH_PATTERNS = (
    r"^\s*gh\s+pr\s+(?:merge|close|edit|review)(?:\s|$)",
    r"^\s*gh\s+repo\s+(?:rename|edit|delete|archive)(?:\s|$)",
    r"^\s*gh\s+release\s+(?:create|delete|edit)(?:\s|$)",
)


def extract_command(payload: str) -> str:
    """从 hook payload 中提取 shell 命令文本。"""
    try:
        data = json.loads(payload or "{}")
    except json.JSONDecodeError:
        return payload
    tool_input = data.get("tool_input") or data.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        if isinstance(command, list):
            return " ".join(str(part) for part in command)
        return str(command)
    return payload


def deny(message: str) -> int:
    """输出统一 deny payload。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }, ensure_ascii=False))
    return 2


def is_read_only_git(command: str) -> bool:
    """判断命令是否属于只读 Git 检查。"""
    return any(re.search(pattern, command, flags=re.IGNORECASE) for pattern in READ_ONLY_GIT_PATTERNS)


def main() -> int:
    """阻断默认不允许的 Git/GitHub 写操作。"""
    command = extract_command(sys.stdin.read()).strip()
    if not command:
        return 0

    if is_read_only_git(command):
        return 0

    for pattern in DENIED_GIT_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return deny(f"默认禁止自动执行 Git 写操作: {command}")

    for pattern in DENIED_GH_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return deny(f"默认禁止自动执行 GitHub 写操作: {command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
