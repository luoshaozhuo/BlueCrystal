"""TDengine simulation_result 真实写入/读回集成测试。

验证 TdengineSimulationResultTimeSeriesSink 在真实 TDengine 环境下的
write_result_series()、read_result_series() 和 health() 行为。

被验证对象：
- whale.storage.simulation_result: TdengineSimulationResultTimeSeriesSink

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

from whale.storage.simulation_result import TdengineSimulationResultTimeSeriesSink


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
class TestTdengineSimulationResultWriteReadback:
    """TDengine simulation_result 真实写入和读回集成测试。

    验证 TdengineSimulationResultTimeSeriesSink 在真实 TDengine 环境下的
    写入、查询和健康检查能力。
    """

    @pytest.mark.asyncio
    async def test_write_and_read_result_series(self) -> None:
        """真实写入仿真结果时序数据并通过 read_result_series 验证。

        通过条件：
        1. write_result_series() 返回 True。
        2. read_result_series() 返回写入的记录。
        3. 记录包含 result_code、metric_key、value 等字段。
        4. health() 返回 True。
        """
        db_name = f"whale_sr_test_{int(datetime.now(tz=timezone.utc).timestamp())}"
        result_code = f"sr-int-{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineSimulationResultTimeSeriesSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        # 写入仿真结果时序
        ok = await sink.write_result_series(
            result_code=result_code,
            channel_name="gen_speed_rpm",
            timestamps=[
                "2025-06-01T00:00:00Z",
                "2025-06-01T00:00:01Z",
                "2025-06-01T00:00:02Z",
            ],
            values=[1200.0, 1215.0, 1208.0],
            unit="rpm",
            value_type="FLOAT64",
            metadata={"simulator": "OpenFAST", "version": "3.5"},
        )
        assert ok is True, f"write_result_series 失败: result_code={result_code}"

        # 读回验证
        rows = await sink.read_result_series(
            result_code=result_code,
            channel_name="gen_speed_rpm",
        )
        assert len(rows) == 3, f"期望 3 条记录，实际 {len(rows)}"

        for row in rows:
            assert row.get("result_code") == result_code
            assert row.get("metric_key") == "gen_speed_rpm"

        # 验证值
        values_read = [float(str(row.get("value", 0))) for row in rows]
        assert 1200.0 in values_read
        assert 1215.0 in values_read
        assert 1208.0 in values_read

        # health check
        healthy = await sink.health()
        assert healthy is True, "TDengine simulation_result health 应为 True"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_write_multiple_channels(self) -> None:
        """验证多通道数据的独立写入和查询。

        通过条件：
        1. 不同 channel_name 的数据可独立写入。
        2. 按 channel_name 查询返回正确数量和内容。
        """
        db_name = f"whale_sr_multi_{int(datetime.now(tz=timezone.utc).timestamp())}"
        result_code = f"sr-multi-{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineSimulationResultTimeSeriesSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        # 写入两个通道
        await sink.write_result_series(
            result_code=result_code,
            channel_name="wind_speed_mps",
            timestamps=["2025-06-01T00:00:00Z", "2025-06-01T00:00:01Z"],
            values=[8.0, 8.5],
            unit="m/s",
        )
        await sink.write_result_series(
            result_code=result_code,
            channel_name="pitch_angle_deg",
            timestamps=["2025-06-01T00:00:00Z", "2025-06-01T00:00:01Z"],
            values=[0.0, 2.5],
            unit="deg",
        )

        # 分别验证两个通道
        wind_rows = await sink.read_result_series(
            result_code=result_code,
            channel_name="wind_speed_mps",
        )
        assert len(wind_rows) == 2
        assert all(r.get("metric_key") == "wind_speed_mps" for r in wind_rows)

        pitch_rows = await sink.read_result_series(
            result_code=result_code,
            channel_name="pitch_angle_deg",
        )
        assert len(pitch_rows) == 2
        assert all(r.get("metric_key") == "pitch_angle_deg" for r in pitch_rows)

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_time_range_query(self) -> None:
        """验证时间范围过滤查询。

        通过条件：
        1. start_time 过滤正确。
        2. end_time 过滤正确。
        3. 同时指定 start_time 和 end_time 过滤正确。
        """
        db_name = f"whale_sr_time_{int(datetime.now(tz=timezone.utc).timestamp())}"
        result_code = f"sr-time-{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineSimulationResultTimeSeriesSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        timestamps = [
            "2025-06-01T00:00:00Z",
            "2025-06-01T00:00:05Z",
            "2025-06-01T00:00:10Z",
        ]
        values = [1.0, 2.0, 3.0]

        await sink.write_result_series(
            result_code=result_code,
            channel_name="power_kw",
            timestamps=timestamps,
            values=values,
        )

        # 查询中间段
        subset = await sink.read_result_series(
            result_code=result_code,
            channel_name="power_kw",
            start_time="2025-06-01T00:00:02Z",
            end_time="2025-06-01T00:00:08Z",
        )
        assert len(subset) == 1, f"期望 1 条中间段记录，实际 {len(subset)}"
        assert float(str(subset[0].get("value", 0))) == 2.0

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_read_nonexistent_result(self) -> None:
        """验证查询不存在的结果返回空列表。

        通过条件：read_result_series() 返回空列表，不抛异常。
        """
        db_name = f"whale_sr_nonexist_{int(datetime.now(tz=timezone.utc).timestamp())}"

        sink = TdengineSimulationResultTimeSeriesSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database=db_name,
        )

        rows = await sink.read_result_series(
            result_code="nonexistent-code",
            channel_name="nonexistent_channel",
        )
        assert rows == [], f"不存在的结果应返回空列表，实际 {len(rows)} 条"

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
        sink = TdengineSimulationResultTimeSeriesSink(
            dsn=f"{TD_HOST}:{TD_PORT}",
            database="whale_sr_health_test",
        )
        healthy = await sink.health()
        assert healthy is True, "TDengine simulation_result health 应为 True"
