#!/usr/bin/env python3
"""轻量检查 changed files 的文档注释、类型抑制和危险异常模式。"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path


SUPPRESSION_PATTERNS = (
    "type: ignore",
    "noqa",
    "nolint",
    "NOLINT",
    "@ts-ignore",
    "shellcheck disable",
)


def changed_files() -> list[Path]:
    """返回当前工作区内发生变化且存在的文件。"""
    names: set[str] = set()
    for args in (["git", "diff", "--name-only"], ["git", "diff", "--cached", "--name-only"]):
        try:
            out = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
        except Exception:
            continue
        names.update(line.strip() for line in out.splitlines() if line.strip())
    return [Path(name) for name in sorted(names) if Path(name).exists()]


def check_python(path: Path, failures: list[str], warnings: list[str]) -> None:
    """检查 Python public 接口 docstring 与异常模式。"""
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception as exc:
        failures.append(f"{path}: 无法解析 Python 文件: {exc}")
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            is_public = not name.startswith("_")
            if is_public and ast.get_docstring(node) is None:
                warnings.append(f"{path}:{node.lineno}: public {type(node).__name__} `{name}` 缺少 docstring")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public:
                if node.returns is None:
                    warnings.append(f"{path}:{node.lineno}: public function `{name}` 缺少返回类型")
                for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                    if arg.arg in {"self", "cls"}:
                        continue
                    if arg.annotation is None:
                        warnings.append(f"{path}:{node.lineno}: public function `{name}` 参数 `{arg.arg}` 缺少类型")
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                failures.append(f"{path}:{node.lineno}: 裸 except")
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                warnings.append(f"{path}:{node.lineno}: except Exception 需要确认是否记录/转换/重新抛出")

    for lineno, line in enumerate(text.splitlines(), start=1):
        if "type: ignore" in line and not re.search(r"type:\s*ignore(?:\[[^\]]+\])?\s*#\s*\S+", line):
            warnings.append(f"{path}:{lineno}: type ignore 缺少解释")


def check_text_patterns(path: Path, warnings: list[str]) -> None:
    """检查通用抑制指令是否缺少解释。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in SUPPRESSION_PATTERNS:
            if pattern in line and "reason" not in line.lower() and "原因" not in line:
                warnings.append(f"{path}:{lineno}: `{pattern}` 可能缺少解释")


def main() -> int:
    """执行轻量 changed-file 质量检查。"""
    failures: list[str] = []
    warnings: list[str] = []

    for path in changed_files():
        if path.suffix == ".py":
            check_python(path, failures, warnings)
        check_text_patterns(path, warnings)

    for item in warnings:
        print(f"WARNING: {item}", file=sys.stderr)
    for item in failures:
        print(f"ERROR: {item}", file=sys.stderr)

    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
