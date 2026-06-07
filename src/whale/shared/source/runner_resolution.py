"""Shared native runner path resolution for production source clients.

生产路径与 starfish native bin dev/test 目录必须明确分离：

- 生产优先级：显式单 runner 环境变量 -> 共享 runner 目录环境变量 -> PATH / 安装路径。
- dev/test fallback：仅当 ``WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1`` 时允许。
- 本模块不 import starfish Python 包，只在文件系统层给出可选 fallback 路径。
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_PRODUCTION_RUNNER_DIR_ENV: Final[str] = "WHALE_SHARED_SOURCE_RUNNER_DIR"
_ALLOW_DEV_FALLBACK_ENV: Final[str] = "WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK"


@dataclass(frozen=True, slots=True)
class ResolvedRunnerPath:
    """Resolved native runner path with provenance metadata."""

    executable_name: str
    path: Path
    source: str
    evidence_level: str
    used_dev_fallback: bool


def _suffix() -> str:
    return ".exe" if os.name == "nt" else ""


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_install_candidate(executable_name: str) -> Path:
    return Path("/opt/whale/shared-source/bin") / executable_name


def _iter_install_candidates(executable_name: str) -> tuple[Path, ...]:
    return (
        Path("/opt/whale/shared-source/bin") / executable_name,
        Path("/usr/local/lib/whale/shared-source") / executable_name,
        Path("/usr/local/bin") / executable_name,
        Path("/usr/bin") / executable_name,
    )


def _dev_fallback_candidate(executable_name: str) -> Path:
    """Return the dev/test fallback path under src/starfish/native/bin/.

    This is only used when WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1.
    It replaces the old tools/source_lab/native/build/ path (deleted in Round 11).
    """
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "src" / "starfish" / "native" / "bin" / executable_name


def is_source_lab_dev_runner_path(path: Path) -> bool:
    """Return whether the path points to the starfish native bin tree.

    The function name is retained for backward compatibility with existing
    backends (lib60870, lib61850, libmodbus, open62541) that import it by name.
    Internally it now checks the ``src/starfish/native/bin`` subtree.
    """

    normalized_parts = tuple(part.lower() for part in path.parts)
    target = ("src", "starfish", "native", "bin")
    for index in range(len(normalized_parts) - len(target) + 1):
        if normalized_parts[index:index + len(target)] == target:
            return True
    return False


def resolve_native_runner_path(
    *,
    executable_stem: str,
    specific_env_var: str,
) -> ResolvedRunnerPath:
    """Resolve one shared_source native runner executable path.

    Args:
        executable_stem: Executable file stem without platform suffix.
        specific_env_var: Per-runner override env var.
    """

    executable_name = f"{executable_stem}{_suffix()}"

    specific_env = os.environ.get(specific_env_var)
    if specific_env:
        return ResolvedRunnerPath(
            executable_name=executable_name,
            path=Path(specific_env).expanduser().resolve(),
            source=f"env:{specific_env_var}",
            evidence_level="production_candidate",
            used_dev_fallback=False,
        )

    shared_dir = os.environ.get(_PRODUCTION_RUNNER_DIR_ENV)
    if shared_dir:
        return ResolvedRunnerPath(
            executable_name=executable_name,
            path=Path(shared_dir).expanduser().resolve() / executable_name,
            source=f"env:{_PRODUCTION_RUNNER_DIR_ENV}",
            evidence_level="production_candidate",
            used_dev_fallback=False,
        )

    path_lookup = shutil.which(executable_name)
    if path_lookup:
        return ResolvedRunnerPath(
            executable_name=executable_name,
            path=Path(path_lookup).expanduser().resolve(),
            source="PATH",
            evidence_level="production_candidate",
            used_dev_fallback=False,
        )

    for candidate in _iter_install_candidates(executable_name):
        if candidate.exists():
            return ResolvedRunnerPath(
                executable_name=executable_name,
                path=candidate.resolve(),
                source="install_path",
                evidence_level="production_candidate",
                used_dev_fallback=False,
            )

    if _is_truthy(os.environ.get(_ALLOW_DEV_FALLBACK_ENV)):
        return ResolvedRunnerPath(
            executable_name=executable_name,
            path=_dev_fallback_candidate(executable_name),
            source=f"env:{_ALLOW_DEV_FALLBACK_ENV}",
            evidence_level="dev_test_fallback",
            used_dev_fallback=True,
        )

    return ResolvedRunnerPath(
        executable_name=executable_name,
        path=_default_install_candidate(executable_name),
        source="default_install_path",
        evidence_level="production_candidate",
        used_dev_fallback=False,
    )


def build_runner_unavailable_message(
    *,
    runner_label: str,
    specific_env_var: str,
    resolution: ResolvedRunnerPath,
) -> str:
    """Build a clear unavailable message with production/dev boundary hints."""

    details = [
        f"{runner_label} executable does not exist: {resolution.path}.",
    ]
    if resolution.used_dev_fallback:
        details.append(
            "Current path is the explicit dev/test fallback from the starfish native bin "
            "directory; it does not count as a production runner artifact."
        )
        details.append(
            f"For production, set `{specific_env_var}` or `{_PRODUCTION_RUNNER_DIR_ENV}`, "
            "or install the runner into PATH."
        )
        details.append(
            f"For local dev/test only, compile `{resolution.executable_name}` in the "
            "starfish native bin directory."
        )
        return " ".join(details)

    details.append(
        f"Configure `{specific_env_var}` or `{_PRODUCTION_RUNNER_DIR_ENV}`, "
        f"or install `{resolution.executable_name}` into PATH or a production runner directory."
    )
    details.append(
        f"The starfish native bin directory is dev/test only; enable `{_ALLOW_DEV_FALLBACK_ENV}=1` "
        "only for local verification."
    )
    return " ".join(details)
