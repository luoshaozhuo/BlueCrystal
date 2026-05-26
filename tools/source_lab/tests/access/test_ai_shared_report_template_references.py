"""报告模板路径治理门禁测试。

验证：
1. ai_shared/reports/_template.md 不存在
2. ai_shared/templates/default_report_template.md 存在
3. 运行配置/skill/rule 中不再引用 reports/_template.md
4. 规则文件包含 "prompt 已明确反馈格式时优先使用 prompt 格式" 的语义
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]


def test_old_template_deleted() -> None:
    """旧报告模板必须删除。"""
    old = _REPO_ROOT / "ai_shared" / "reports" / "_template.md"
    assert not old.exists(), f"old template still exists: {old}"


def test_new_template_exists() -> None:
    """新报告模板必须存在。"""
    new = _REPO_ROOT / "ai_shared" / "templates" / "default_report_template.md"
    assert new.exists(), f"new template not found: {new}"


def test_no_residual_template_references_in_rules() -> None:
    """rules/ 中不得引用旧模板路径。"""
    rules_dir = _REPO_ROOT / "ai_shared" / "rules"
    for f in sorted(rules_dir.rglob("*")):
        if not f.is_file() or f.suffix not in (".md", ".py", ".txt", ".json", ".yaml", ".yml"):
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "reports/_template.md" in content or "_template.md" in content:
            pytest.fail(f"rule file {f.relative_to(_REPO_ROOT)} still references _template.md")


def test_no_residual_template_references_in_claude_agents() -> None:
    """CLAUDE.md / AGENTS.md / .claude/ / .agents/ 中不得引用旧模板路径。"""
    candidates = [
        _REPO_ROOT / "CLAUDE.md",
        _REPO_ROOT / "AGENTS.md",
    ]
    claude_dir = _REPO_ROOT / ".claude"
    agents_dir = _REPO_ROOT / ".agents"
    if claude_dir.exists():
        candidates.extend(claude_dir.rglob("*"))
    if agents_dir.exists():
        candidates.extend(agents_dir.rglob("*"))
    for f in candidates:
        if not f.is_file():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "reports/_template.md" in content or "_template.md" in content:
            pytest.fail(
                f"{f.relative_to(_REPO_ROOT)} still references _template.md"
            )


def test_reporting_rule_has_prompt_format_priority() -> None:
    """reporting.md 必须包含 prompt 格式优先于默认模板的规则。"""
    reporting = _REPO_ROOT / "ai_shared" / "rules" / "reporting.md"
    assert reporting.exists(), "reporting.md not found"
    content = reporting.read_text(encoding="utf-8")
    assert (
        "prompt 没有明确指定输出格式" in content or "prompt 已明确要求输出格式" in content or "prompt 未明确" in content
    ), "reporting.md must contain rule about prompt format priority over default template"
