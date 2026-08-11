"""真实 Whale views 到 IEC104/ADS server 与真实 client 的协议闭环。

测试只读当前 comm/src views，分别启动 c104 与 AMS/TCP server，再使用真实 c104
client 和 pyads client 校验 view 描述的 endpoint、地址及数据类型。缺少数据库 URL
或 native client 依赖时属于外部环境 NOT_RUN，不能算作协议通过。
"""

from __future__ import annotations

from contextlib import ExitStack
import os
import threading
import time
from typing import Protocol

import pytest

from starfish.adapters.db_views import ConnectionDbViewLoader, DbViewLoadError
from starfish.adapters.db_views.ads import AdsDbViewLoadError, AdsDbViewLoader
from starfish.adapters.db_views.iec104 import (
    Iec104DbViewLoadError,
    Iec104DbViewLoader,
)
from starfish.adapters.protocols.ads import AdsServer
from starfish.adapters.protocols.iec104 import Iec104Server

pytestmark = [pytest.mark.integration, pytest.mark.external, pytest.mark.starfish]


class _AdsCleanupClient(Protocol):
    """声明真实 pyads client 在测试清理阶段使用的最小接口。"""

    def del_device_notification(
        self,
        notification_handle: int,
        user_handle: int,
    ) -> None:
        """删除一个 ADS notification 注册。"""

    def close(self) -> None:
        """关闭 ADS client 与其传输会话。"""


def _db_url() -> str:
    """取得外部 PostgreSQL URL，缺失时明确归为环境未提供。"""
    value = os.environ.get("WHALE_DB_URL", "").strip()
    if not value:
        pytest.skip("需要 WHALE_DB_URL 读取当前 Whale views")
    return value


def _delete_ads_notifications(
    plc: _AdsCleanupClient,
    handles: list[tuple[int, int]],
) -> None:
    """尝试删除所有存活 notification，并在全部尝试后传播首个异常。"""
    first_error: Exception | None = None
    for handle in tuple(handles):
        try:
            plc.del_device_notification(*handle)
            handles.remove(handle)
        except Exception as exc:  # noqa: BLE001 - 测试清理必须继续释放其余句柄。
            if first_error is None:
                first_error = exc
    if first_error is not None:
        raise first_error


def _wait_for_ads_session_cleanup(server: AdsServer) -> None:
    """在 server 停止前确认 client close 已释放 session 与 notification。"""
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        detail = server.status().detail
        if detail["notification_count"] == 0 and detail["client_count"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"ADS session 未在 client close 后清理: {server.status().detail}"
    )


@pytest.mark.parametrize(
    ("loader_type", "error_type"),
    [
        (ConnectionDbViewLoader, DbViewLoadError),
        (Iec104DbViewLoader, Iec104DbViewLoadError),
        (AdsDbViewLoader, AdsDbViewLoadError),
    ],
)
def test_current_views_support_all_partial_missing_and_empty_ids(
    loader_type: type[ConnectionDbViewLoader]
    | type[Iec104DbViewLoader]
    | type[AdsDbViewLoader],
    error_type: type[DbViewLoadError],
) -> None:
    """真实只读 view 验证 loader 的四种 connection_ids 查询语义。"""
    loader = loader_type(_db_url())
    all_rows = loader.load()
    assert not all_rows.empty
    available_ids = sorted(all_rows["connection_id"].astype(int).unique().tolist())

    selected = loader.load([available_ids[0]])
    assert selected["connection_id"].astype(int).unique().tolist() == [available_ids[0]]
    with pytest.raises(error_type, match="未找到.*connection_id"):
        loader.load([available_ids[0], 2_147_483_647])
    with pytest.raises(error_type, match="connection_ids 不能为空"):
        loader.load([])


def test_current_iec104_view_starts_server_for_real_c104_client() -> None:
    """从当前 IEC104 Source view 启动受控站并由真实 client 总召读取。"""
    c104 = pytest.importorskip("c104", reason="需要 c104==2.2.1 native client")
    server = Iec104Server(Iec104DbViewLoader(_db_url()).load([1]))
    definition = server.definition
    point_definition = definition.point_items[0]
    common_address = int(point_definition.metadata["common_address"])
    client = c104.Client(tick_rate_ms=50, command_timeout_ms=3000)
    connection = client.add_connection(
        ip="127.0.0.1",
        port=definition.bind_port,
        init=c104.Init.ALL,
    )
    assert connection is not None
    station = connection.add_station(common_address=common_address)
    assert station is not None
    point = station.add_point(
        io_address=int(point_definition.io_address),
        type=getattr(c104.Type, point_definition.type_id),
    )
    assert point is not None
    server.start()
    try:
        client.start()
        open_deadline = time.monotonic() + 3
        while time.monotonic() < open_deadline and not client.has_open_connections:
            time.sleep(0.02)
        assert client.has_open_connections
        expected = 2.5
        server.update_point(
            point_definition.point_item_id,
            expected,
            transmit_spontaneous=False,
        )
        assert connection.interrogation(
            common_address=common_address,
            wait_for_response=True,
        )
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if float(point.value) == pytest.approx(expected):
                break
            time.sleep(0.02)
        assert float(point.value) == pytest.approx(expected)
    finally:
        client.stop()
        server.stop()


def test_current_ads_view_starts_server_for_real_pyads_client() -> None:
    """真实 pyads 验证同步读、CYCLIC/ON_CHANGE 订阅、取消与清理。"""
    pyads = pytest.importorskip("pyads", reason="需要 pyads/AdsLib 真实 ADS client")
    server = AdsServer(AdsDbViewLoader(_db_url()).load([3]))
    definition = server.definition
    active_notifications: list[tuple[int, int]] = []
    with ExitStack() as cleanup:
        cleanup.callback(server.stop)
        server.start()
        cleanup.callback(_wait_for_ads_session_cleanup, server)
        plc = pyads.Connection(
            definition.connection_params["ams_net_id"],
            definition.connection_params["ams_port"],
            definition.bind_host,
        )
        cleanup.callback(plc.close)
        cleanup.callback(_delete_ads_notifications, plc, active_notifications)
        plc.open()
        assert plc.read_state() == (5, 0)
        assert plc.read_by_name(
            "MAIN.ActivePower", pyads.PLCTYPE_LREAL
        ) == pytest.approx(0.0)
        server.update_point("MAIN.ActivePower", 2.75)
        assert plc.read_by_name(
            "MAIN.ActivePower", pyads.PLCTYPE_LREAL
        ) == pytest.approx(2.75)
        assert plc.read_by_name("MAIN.Running", pyads.PLCTYPE_BOOL) is False

        cyclic_values: list[float] = []
        cyclic_event = threading.Event()

        def on_cyclic(notification: object, _data: object) -> None:
            """解析 AdsLib 交付的真实 LREAL notification。"""
            _handle, _timestamp, value = plc.parse_notification(
                notification, pyads.PLCTYPE_LREAL
            )
            cyclic_values.append(float(value))
            cyclic_event.set()

        cyclic_attr = pyads.NotificationAttrib(
            8,
            trans_mode=pyads.ADSTRANS_SERVERCYCLE,
            max_delay=0.1,
            cycle_time=0.05,
        )
        cyclic_handle = plc.add_device_notification(
            "MAIN.ActivePower", cyclic_attr, on_cyclic
        )
        assert cyclic_handle is not None
        active_notifications.append(cyclic_handle)
        assert cyclic_event.wait(2)
        cyclic_event.clear()
        server.update_point("MAIN.ActivePower", 3.25)
        assert cyclic_event.wait(2)
        assert cyclic_values[-1] == pytest.approx(3.25)
        plc.del_device_notification(*cyclic_handle)
        active_notifications.remove(cyclic_handle)
        count_after_delete = len(cyclic_values)
        time.sleep(0.2)
        assert len(cyclic_values) == count_after_delete

        change_values: list[bool] = []
        change_event = threading.Event()

        def on_change(notification: object, _data: object) -> None:
            """解析 AdsLib 交付的真实 BOOL notification。"""
            _handle, _timestamp, value = plc.parse_notification(
                notification, pyads.PLCTYPE_BOOL
            )
            change_values.append(bool(value))
            change_event.set()

        change_attr = pyads.NotificationAttrib(
            1,
            trans_mode=pyads.ADSTRANS_SERVERONCHA,
            max_delay=0.1,
            cycle_time=0.01,
        )
        change_handle = plc.add_device_notification(
            "MAIN.Running", change_attr, on_change
        )
        assert change_handle is not None
        active_notifications.append(change_handle)
        # ON_CHANGE 注册后允许初始样本；清空后只验证显式更新产生的新样本。
        time.sleep(0.05)
        change_values.clear()
        change_event.clear()
        server.update_point("MAIN.Running", True)
        assert change_event.wait(2)
        assert change_values[-1] is True
        plc.del_device_notification(*change_handle)
        active_notifications.remove(change_handle)
    assert server.status().detail["notification_count"] == 0
    assert server.status().detail["client_count"] == 0
