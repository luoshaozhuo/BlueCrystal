"""shared_source native runner path resolution boundary tests."""

from __future__ import annotations

from pathlib import Path

from whale.shared.source.runner_resolution import (
    build_runner_unavailable_message,
    resolve_native_runner_path,
)


def test_resolve_native_runner_uses_production_runner_dir(monkeypatch, tmp_path: Path) -> None:
    """默认应先走生产 runner 目录，而不是 source_lab build 目录。"""
    monkeypatch.delenv("WHALE_OPEN62541_CLIENT_RUNNER_PATH", raising=False)
    monkeypatch.setenv("WHALE_SHARED_SOURCE_RUNNER_DIR", str(tmp_path / "prod-runners"))
    monkeypatch.delenv("WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK", raising=False)

    resolution = resolve_native_runner_path(
        executable_stem="open62541_client_runner",
        specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH",
    )

    assert resolution.source == "env:WHALE_SHARED_SOURCE_RUNNER_DIR"
    assert resolution.used_dev_fallback is False
    assert resolution.evidence_level == "production_candidate"
    assert resolution.path == (tmp_path / "prod-runners" / "open62541_client_runner").resolve()


def test_resolve_native_runner_allows_explicit_dev_fallback(monkeypatch) -> None:
    """显式开启时才允许落回 source_lab native build。"""
    monkeypatch.delenv("WHALE_MODBUS_CLIENT_RUNNER_PATH", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_RUNNER_DIR", raising=False)
    monkeypatch.setenv("WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK", "1")

    resolution = resolve_native_runner_path(
        executable_stem="modbus_tcp_polling_runner",
        specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH",
    )

    assert resolution.used_dev_fallback is True
    assert resolution.evidence_level == "dev_test_fallback"
    assert "source_lab/native/build" in str(resolution.path)


def test_resolve_native_runner_without_dev_fallback_does_not_point_to_source_lab(monkeypatch) -> None:
    """未显式开启 fallback 时，默认路径不能再指向 source_lab build。"""
    monkeypatch.delenv("WHALE_IEC104_CLIENT_RUNNER_PATH", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_RUNNER_DIR", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK", raising=False)

    resolution = resolve_native_runner_path(
        executable_stem="iec104_client_runner",
        specific_env_var="WHALE_IEC104_CLIENT_RUNNER_PATH",
    )

    assert resolution.used_dev_fallback is False
    assert "tools/source_lab/native/build" not in str(resolution.path)
    assert str(resolution.path).endswith("/opt/whale/shared-source/bin/iec104_client_runner")


def test_runner_unavailable_message_marks_dev_fallback_as_non_production(monkeypatch) -> None:
    """dev fallback 缺失时错误提示必须强调其不是 production artifact。"""
    monkeypatch.delenv("WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_RUNNER_DIR", raising=False)
    monkeypatch.setenv("WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK", "true")
    resolution = resolve_native_runner_path(
        executable_stem="iec61850_mms_client_runner",
        specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
    )

    message = build_runner_unavailable_message(
        runner_label="IEC 61850 MMS client runner",
        specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
        resolution=resolution,
    )

    assert "dev/test fallback" in message
    assert "does not count as a production runner artifact" in message
    assert "source_lab native build" in message


def test_runner_unavailable_message_without_fallback_guides_to_production_install(monkeypatch) -> None:
    """缺少生产 runner 时应优先给出生产安装提示。"""
    monkeypatch.delenv("WHALE_IEC61850_REPORT_RUNNER_PATH", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_RUNNER_DIR", raising=False)
    monkeypatch.delenv("WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK", raising=False)
    resolution = resolve_native_runner_path(
        executable_stem="iec61850_report_runner",
        specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
    )

    message = build_runner_unavailable_message(
        runner_label="IEC 61850 report runner",
        specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
        resolution=resolution,
    )

    assert "WHALE_IEC61850_REPORT_RUNNER_PATH" in message
    assert "WHALE_SHARED_SOURCE_RUNNER_DIR" in message
    assert "dev/test only" in message
