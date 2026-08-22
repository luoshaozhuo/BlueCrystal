"""从 YAML 加载并严格校验可观测性配置。"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import ObservabilityConfig


class ObservabilityConfigError(ValueError):
    """表示 YAML、环境变量或强类型配置校验失败。"""


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def load_observability_config(path: str | Path) -> ObservabilityConfig:
    """加载 ``observability`` YAML 根节点并构造强类型配置。

    Args:
        path: YAML 文件路径。

    Returns:
        完成环境变量替换和严格校验的配置对象。

    Raises:
        ObservabilityConfigError: 文件内容、根节点或配置字段不合法。
    """
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ObservabilityConfigError(f"cannot load config {config_path}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"observability"}:
        raise ObservabilityConfigError(
            "config root must contain only the 'observability' mapping"
        )
    section = raw["observability"]
    if not isinstance(section, dict):
        raise ObservabilityConfigError("observability must be a mapping")
    try:
        expanded = _expand_environment(section, path="observability")
        return ObservabilityConfig.model_validate(expanded)
    except (ObservabilityConfigError, ValidationError) as exc:
        raise ObservabilityConfigError(f"invalid observability config: {exc}") from exc


def _expand_environment(value: Any, *, path: str) -> Any:
    """递归替换字符串中的 ``${NAME}`` 或 ``${NAME:-default}``。"""
    if isinstance(value, dict):
        return {
            key: _expand_environment(item, path=f"{path}.{key}")
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _expand_environment(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        """解析单个环境变量表达式并提供精确配置路径错误。"""
        name, default = match.groups()
        resolved = os.getenv(name, default)
        if resolved is None:
            raise ObservabilityConfigError(
                f"{path}: environment variable {name!r} is not set"
            )
        return resolved

    return _ENV_PATTERN.sub(replace, value)
