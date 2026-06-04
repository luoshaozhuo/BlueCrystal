"""TDengine waveform 真实写入/读回集成测试。

验证 TdengineStandardizedWaveformSink 在真实 TDengine 环境下的
write_waveform()、write()、readback() 和 health() 行为。

被验证对象：
- whale.storage.waveform: TdengineStandardizedWaveformSink, StandardizedWaveformValue

测试阶段：准生产依赖验证期 (integration，需真实 TDengine)。
环境依赖：TDengine taosAdapter (localhost:6041 或 WHALE_TDENGINE_DSN)。
不能证明：TDengine 不可达环境下的降级行为（由开发期验证覆盖）。
NOT_RUN 条件：MISSING_ENVIRONMENT — TDengine taosAdapter 不可达。
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone

import pytest

from whale.storage.waveform import (
    StandardizedWaveformValue,
    TdengineStandardizedWaveformSink,
)


# ---- 环境探测 ----

def _tcp_reachable(host: str, port: int, timeout: float = 3.0) -> bool:
    """探测指定 host:port 的 TCP 连通性。"""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except OSError:
        return False


def _resolve_tdengine_host_port() -> tuple[str, int]:
    """从环境变量或默认值解析 TDengine host:port。"""
    dsn = os.getenv("WHALE_TDENGINE_DSN") or os.getenv("TAOS_DSN") or "localhost:6041"
    cleaned = dsn
    for prefix in ("taosws://", "http://", "https://"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    parts = cleaned.rsplit(":", 1)
    host = parts[0].strip()
    try:
        port = int(parts[1].strip()) if len(parts) == 2 else 6041
    except ValueError:
        port = 6041
    return host, port


def _rest_api_alive(host: str, port: int, rest_path: str = "/rest/sql", timeout: float = 5.0) -> bool:
    """探测 TDengine REST API 是否可用。

    通过 HTTP POST 发送 SELECT 1 到 REST API 端点。
    如果主路径失败，尝试备选路径 /rest/sqlt。

    Args:
        host: TDengine taosAdapter 主机。
        port: REST API 端口。
        rest_path: 主 REST API 路径。
        timeout: HTTP 请求超时（秒）。

    Returns:
        True 表示 REST API 可用且 SELECT 1 返回成功。
    """
    paths_to_check = [rest_path]
    if rest_path != "/rest/sqlt":
        paths_to_check.append("/rest/sqlt")
    if rest_path != "/rest/sql":
        paths_to_check.append("/rest/sql")

    for path in paths_to_check:
        try:
            url = f"http://{host}:{port}{path}"
            sql = "SELECT 1"
            req = urllib.request.Request(
                url,
                data=sql.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                method="POST",
            )
            auth_bytes = base64.b64encode(b"root:taosdata")
            req.add_header("Authorization", f"Basic {auth_bytes.decode('ascii')}")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                if result.get("code", -1) == 0:
                    return True
        except Exception:
            continue
    return False


TD_HOST, TD_PORT = _resolve_tdengine_host_port()
TDENGINE_TCP_REACHABLE = _tcp_reachable(TD_HOST, TD_PORT)
REST_PATH = os.getenv("WHALE_TDENGINE_REST_PATH", "/rest/sql")
TDENGINE_REST_API_ALIVE = TDENGINE_TCP_REACHABLE and _rest_api_alive(
    TD_HOST, TD_PORT, REST_PATH
)

# 生成 skip reason，区分 TCP 不可达和 REST API 不可达
if not TDENGINE_TCP_REACHABLE:
    _NOT_RUN_REASON = (
        "NOT_RUN: MISSING_ENVIRONMENT: TDengine taosAdapter TCP 不可达 "
        f"({TD_HOST}:{TD_PORT})"
    )
else:
    _NOT_RUN_REASON = (
        f"NOT_RUN: MISSING_ENVIRONMENT: TDengine taosAdapter REST API 不可达 "
        f"({TD_HOST}:{TD_PORT}{REST_PATH})"
    )


# ---- 测试 ----

@pytest.mark.l5
@pytest.mark.skipif(not TDENGINE_REST_API_ALIVE, reason=_NOT_RUN_REASON)
class TestTdengineWaveformWriteReadback:
    """TDengine waveform 真实写入和读回集成测试。

    验证 TdengineStandardizedWaveformSink 在真实 TDengine 环境下的
    写入、查询和健康检查能力。
    """

    @pytest.mark.asyncio
    async def test_write_waveform_and_readback(self) -> None:
        """真实写入标准化波形数据并通过 readback 验证。

        通过条件：
        1. write_waveform() 返回 True。
        2. readback() 返回写入的记录，包含 event_id、channel_key、value 等字段。
        3. health() 返回 True。
        """
        db_name = f"whale_wf_test_{int(datetime.now(tz=timezone.utc).timestamp())}"
        event_id = f"wf-int-{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineStandardizedWaveformSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        # 写入一条波形
        ok = await sink.write_waveform(
            event_id=event_id,
            source_id="src-waveform-test",
            channel_key="voltage_phase_a",
            timestamps=[
                "2025-06-01T00:00:00Z",
                "2025-06-01T00:00:00.001Z",
                "2025-06-01T00:00:00.002Z",
            ],
            values=[220.5, 221.0, 220.8],
            sample_rate_hz=1000.0,
            unit="V",
            metadata={"location": "bus_1", "phase": "A"},
        )
        assert ok is True, f"waveform write 失败: event_id={event_id}"

        # 读回验证
        rows = await sink.readback(event_id=event_id, limit=10)
        assert len(rows) >= 1, f"readback 返回空，期望至少 1 条: event_id={event_id}"

        first_row = rows[0]
        assert first_row.get("event_id") == event_id, (
            f"event_id 不匹配: {first_row.get('event_id')} vs {event_id}"
        )
        assert first_row.get("source_id") == "src-waveform-test"
        assert first_row.get("channel_key") == "voltage_phase_a"
        assert first_row.get("sample_rate_hz") == 1000.0

        # 验证所有采样点
        assert len(rows) == 3, f"期望 3 条采样记录，实际 {len(rows)}"
        for i, row in enumerate(rows):
            assert row.get("sample_index") == i

        # health check
        healthy = await sink.health()
        assert healthy is True, "TDengine waveform health 应为 True"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_write_batch_with_standardized_waveform_value(self) -> None:
        """使用 StandardizedWaveformValue 批量写入并通过 readback 验证。

        通过条件：
        1. write() 接收 StandardizedWaveformValue 列表，返回 True。
        2. readback() 返回正确数量和顺序的记录。
        """
        db_name = f"whale_wf_batch_{int(datetime.now(tz=timezone.utc).timestamp())}"
        event_id = f"wf-batch-{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineStandardizedWaveformSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        samples = [
            StandardizedWaveformValue(
                timestamp="2025-06-01T00:00:00.000Z",
                value=10.5,
                sample_index=0,
                quality_code="0",
            ),
            StandardizedWaveformValue(
                timestamp="2025-06-01T00:00:00.010Z",
                value=11.2,
                sample_index=1,
                quality_code="0",
            ),
            StandardizedWaveformValue(
                timestamp="2025-06-01T00:00:00.020Z",
                value=10.9,
                sample_index=2,
                quality_code="1",
            ),
        ]

        ok = await sink.write(
            event_id=event_id,
            source_id="src-batch-test",
            channel_key="current_phase_a",
            samples=samples,
            sample_rate_hz=100.0,
            metadata={"simulation": "test"},
        )
        assert ok is True, f"batch write 失败: event_id={event_id}"

        rows = await sink.readback(event_id=event_id, limit=100)
        assert len(rows) == 3, f"期望 3 条记录，实际 {len(rows)}"

        # 验证 quality_code 差异正确存储
        qc_values = [row.get("quality_code") for row in rows]
        assert "1" in qc_values, "quality_code=1 的记录缺失"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_readback_nonexistent_event(self) -> None:
        """验证查询不存在的事件返回空列表。

        通过条件：readback() 返回空列表，不抛异常。
        """
        db_name = f"whale_wf_empty_{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineStandardizedWaveformSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        rows = await sink.readback(event_id="nonexistent-event-id", limit=10)
        assert rows == [], f"不存在的事件应返回空列表，实际 {len(rows)} 条"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """验证 health() 方法在真实 TDengine 环境下返回 True。

        通过条件：health() 返回 True。
        """
        sink = TdengineStandardizedWaveformSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database="whale_wf_health_test",
        )
        healthy = await sink.health()
        assert healthy is True, "TDengine waveform health 应为 True"
