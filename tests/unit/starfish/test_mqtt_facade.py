"""Starfish MqttDriverAdapter 测试。

验证 MqttDriverAdapter 的轻量级 MQTT-like 端点：
1. start/stop 真实 TCP server 进程。
2. health TCP connect 探测。
3. load_points + read initial_values。
4. update_values 后 read 反映新值 + subscribe 收到通知。
5. capabilities 返回 plan 中的能力声明。
6. subscribe 返回 SubscriptionQueue 并可轮询变更。
7. write/report 语义（NOT_IMPLEMENTED）。
8. TCP 线上协议 (read/read_all/publish JSON 行协议)。
9. 空 initial_values / 无 subscribers 边界。

测试阶段：开发期验证 (P1) + 模块集成期验证 (P3)。
使用的替身：MQTT 轻量级 TCP server（localhost 动态端口，JSON 行协议）。
外部依赖：无（纯 Python 标准库）。
不能证明：完整 MQTT v3.1.1 协议握手、QoS 1/2、遗嘱消息、
  生产级 broker 并发性能、TLS 加密、keep-alive。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import json
import queue
import socket

import pytest

from starfish.container import (
    create_ads_driver_adapter,
    create_default_backend_factory,
    create_default_driver_factory,
    create_goose_driver_adapter,
    create_http_rest_driver_adapter,
    create_iec101_driver_adapter,
    create_iec104_driver_adapter,
    create_iec61850_mms_driver_adapter,
    create_iec61850_report_driver_adapter,
    create_modbus_rtu_driver_adapter,
    create_modbus_tcp_driver_adapter,
    create_mqtt_driver_adapter,
    create_opcua_driver_adapter,
    create_server_simulator_driver_adapter,
    create_sv_driver_adapter,
)

from starfish.domain.server_config import (
    StarfishServerConfig,
    StarfishEndpointConfig,
    StarfishPointConfig,
    UnsupportedOperation,
)
from starfish.adapters.drivers.protocol.mqtt.mqtt_driver_adapter import MqttDriverAdapter, SubscriptionQueue


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_mqtt_plan(
    scenario_id: str = "mqtt_facade_test",
    initial_values: dict | None = None,
) -> StarfishServerConfig:
    """构造 MQTT 测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。
        initial_values: 初始值 dict。

    Returns:
        测试用 StarfishServerConfig。
    """
    if initial_values is None:
        initial_values = {"sensor_temp": 25.5, "sensor_humidity": 60.0, "sensor_pressure": 101.3}

    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_mqtt_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol="MQTT",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="sensor_temp",
                point_name="Temperature Sensor",
                node_key="/sensors/temperature",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="sensor_humidity",
                point_name="Humidity Sensor",
                node_key="/sensors/humidity",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="sensor_pressure",
                point_name="Pressure Sensor",
                node_key="/sensors/pressure",
                value_type="Float",
                access_mode="RO",
            ),
        ],
        capabilities=["READ", "SUBSCRIBE"],
        initial_values=initial_values,
    )


# ── SubscriptionQueue 单元测试 ──────────────────────────────────────────────────


class TestSubscriptionQueue:
    """SubscriptionQueue 独立单元测试。"""

    def test_get_nowait_empty(self) -> None:
        """空队列 get_nowait 应返回 None。"""
        q = SubscriptionQueue()
        assert q.get_nowait() is None

    def test_get_nowait_after_put(self) -> None:
        """_put 后 get_nowait 应返回对应值。"""
        q = SubscriptionQueue()
        q._put("sensor_1", 42.0)
        result = q.get_nowait()
        assert result == ("sensor_1", 42.0)
        assert q.get_nowait() is None

    def test_get_with_timeout_empty(self) -> None:
        """空队列 get(timeout) 应抛出 queue.Empty。"""
        q = SubscriptionQueue()
        with pytest.raises(queue.Empty):
            q.get(timeout=0.1)

    def test_get_with_timeout_after_put(self) -> None:
        """有数据时 get(timeout) 应立即返回。"""
        q = SubscriptionQueue()
        q._put("sensor_1", 99.9)
        result = q.get(timeout=1.0)
        assert result == ("sensor_1", 99.9)

    def test_multiple_puts(self) -> None:
        """多次 _put 应维持 FIFO 顺序。"""
        q = SubscriptionQueue()
        q._put("a", 1)
        q._put("b", 2)
        q._put("c", 3)
        assert q.get_nowait() == ("a", 1)
        assert q.get_nowait() == ("b", 2)
        assert q.get_nowait() == ("c", 3)
        assert q.get_nowait() is None


# ── MqttDriverAdapter 生命周期测试 ─────────────────────────────────────────────────────


class TestMqttDriverAdapterLifecycle:
    """MqttDriverAdapter start/stop 生命周期测试。"""

    def test_initial_state(self) -> None:
        """新建 facade 应为 stopped 状态。"""
        facade = create_mqtt_driver_adapter()
        h = facade.health()
        assert h["status"] == "stopped"
        assert h["running"] is False
        assert h["mode"] == "mqtt-lightweight"
        assert h["protocol"] == "MQTT"

    def test_start_and_stop(self) -> None:
        """start 后 server 应可连接，stop 后应断开。"""
        plan = _make_mqtt_plan("start_stop")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        h = facade.health()
        assert h["status"] == "started"
        assert h["running"] is True
        assert h["port"] > 0
        assert h["protocol"] == "MQTT"
        assert h["mode"] == "mqtt-lightweight"

        facade.stop()
        h2 = facade.health()
        assert h2["status"] == "stopped"
        assert h2["running"] is False

    def test_start_idempotent(self) -> None:
        """重复 start() 应为幂等。"""
        plan = _make_mqtt_plan("idempotent_start")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)

        facade.start()
        facade.start()  # 第二次应无操作
        assert facade.health()["running"] is True

        facade.stop()

    def test_stop_idempotent(self) -> None:
        """重复 stop() 应为幂等。"""
        plan = _make_mqtt_plan("idempotent_stop")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)

        facade.start()
        facade.stop()
        facade.stop()  # 第二次应无操作
        assert facade.health()["running"] is False

    def test_port_auto_allocation(self) -> None:
        """端口 0 时 OS 应自动分配端口。"""
        plan = _make_mqtt_plan("auto_port")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        actual_port = facade.health()["port"]
        assert actual_port > 0
        assert actual_port != 0

        facade.stop()


# ── MqttDriverAdapter 数据操作测试 ─────────────────────────────────────────────────────


class TestMqttDriverAdapterDataOperations:
    """MqttDriverAdapter 数据读写 + subscribe 测试。"""

    def test_load_points_populates_values(self) -> None:
        """load_points 应从 plan.initial_values 填充内存。"""
        plan = _make_mqtt_plan("load")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        values = facade.read()
        assert values["sensor_temp"] == 25.5
        assert values["sensor_humidity"] == 60.0
        assert values["sensor_pressure"] == 101.3

    def test_read_specific_points(self) -> None:
        """指定 point_ids 时应只返回对应值。"""
        plan = _make_mqtt_plan("specific")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        values = facade.read(["sensor_temp"])
        assert values == {"sensor_temp": 25.5}

    def test_read_nonexistent_point(self) -> None:
        """不存在 point_id 应返回 None。"""
        plan = _make_mqtt_plan("nonexist")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        values = facade.read(["nonexistent"])
        assert values == {"nonexistent": None}

    def test_read_all_after_load(self) -> None:
        """read() 无参数时应返回全部点位。"""
        plan = _make_mqtt_plan(
            "read_all",
            initial_values={"a": 1, "b": 2, "c": 3},
        )
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        values = facade.read()
        assert len(values) == 3
        assert values["a"] == 1
        assert values["b"] == 2
        assert values["c"] == 3

    def test_update_values(self) -> None:
        """update_values 应更新内存值。"""
        plan = _make_mqtt_plan("update")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        facade.update_values({"sensor_temp": 99.9, "new_point": 0})
        values = facade.read()
        assert values["sensor_temp"] == 99.9
        assert values["sensor_humidity"] == 60.0  # 未更新
        assert values["new_point"] == 0

    def test_update_values_empty(self) -> None:
        """空 dict 更新应无影响。"""
        plan = _make_mqtt_plan("empty_update")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        original = facade.read()
        facade.update_values({})
        assert facade.read() == original

    def test_capabilities_returns_plan_capabilities(self) -> None:
        """capabilities 应返回 plan 中的声明。"""
        plan = _make_mqtt_plan("caps")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        assert facade.capabilities() == ["READ", "SUBSCRIBE"]

    def test_capabilities_empty_without_load(self) -> None:
        """未 load_points 时 capabilities 应返回空列表。"""
        facade = create_mqtt_driver_adapter()
        assert facade.capabilities() == []

    def test_empty_initial_values(self) -> None:
        """空 initial_values 时 read() 应返回空 dict。"""
        plan = _make_mqtt_plan("empty_iv", initial_values={})
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)
        assert facade.read() == {}

    def test_health_without_load(self) -> None:
        """未 load_points 时 health 仍可调用。"""
        facade = create_mqtt_driver_adapter()
        h = facade.health()
        assert h["plan_loaded"] is False
        assert h["point_count"] == 0
        assert h["subscription_count"] == 0


# ── MqttDriverAdapter subscribe 测试 ───────────────────────────────────────────────────


class TestMqttDriverAdapterSubscribe:
    """MqttDriverAdapter subscribe 轮询队列测试。"""

    def test_subscribe_returns_queue(self) -> None:
        """subscribe 应返回 SubscriptionQueue 实例。"""
        plan = _make_mqtt_plan("sub_queue")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        sub_q = facade.subscribe(["sensor_temp"])
        assert isinstance(sub_q, SubscriptionQueue)
        assert sub_q.get_nowait() is None

    def test_subscribe_receives_update(self) -> None:
        """update_values 更新订阅点位后，队列应收到通知。"""
        plan = _make_mqtt_plan("sub_update")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        sub_q = facade.subscribe(["sensor_temp"])
        facade.update_values({"sensor_temp": 42.0})

        result = sub_q.get(timeout=0.5)
        assert result == ("sensor_temp", 42.0)
        assert sub_q.get_nowait() is None

    def test_subscribe_multiple_points(self) -> None:
        """订阅多个点位时，任一更新应收到通知。"""
        plan = _make_mqtt_plan("sub_multi")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        sub_q = facade.subscribe(["sensor_temp", "sensor_humidity"])

        # 更新 sensor_humidity
        facade.update_values({"sensor_humidity": 88.8})
        result = sub_q.get(timeout=0.5)
        assert result == ("sensor_humidity", 88.8)
        assert sub_q.get_nowait() is None

    def test_subscribe_unrelated_point_not_notified(self) -> None:
        """更新未订阅的点位时不应收到通知。"""
        plan = _make_mqtt_plan("sub_unrelated")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        sub_q = facade.subscribe(["sensor_temp"])
        # 更新未订阅的 sensor_pressure
        facade.update_values({"sensor_pressure": 999.0})

        assert sub_q.get_nowait() is None

    def test_multiple_subscribers_same_point(self) -> None:
        """同一 point_id 的多个订阅者应同时收到通知。"""
        plan = _make_mqtt_plan("sub_multi_sub")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        q1 = facade.subscribe(["sensor_temp"])
        q2 = facade.subscribe(["sensor_temp"])

        facade.update_values({"sensor_temp": 77.7})

        assert q1.get(timeout=0.5) == ("sensor_temp", 77.7)
        assert q2.get(timeout=0.5) == ("sensor_temp", 77.7)

    def test_subscribe_load_points_clears_old(self) -> None:
        """重新 load_points 后旧订阅队列不再有效。"""
        plan = _make_mqtt_plan("sub_reload")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        q1 = facade.subscribe(["sensor_temp"])
        # 重新加载相同 plan
        facade.load_points(plan)

        facade.update_values({"sensor_temp": 123.0})
        # 重新加载后旧订阅队列应已清空，q1 不应收到通知
        assert q1.get_nowait() is None

    def test_subscribe_from_tcp_publish(self) -> None:
        """TCP publish 应触发 subscribe 通知。"""
        plan = _make_mqtt_plan(
            "sub_tcp_pub",
            initial_values={"a": 1, "b": 2},
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)

        sub_q = facade.subscribe(["a"])
        facade.start()

        port = facade.health()["port"]
        try:
            # 通过 TCP 发送 publish
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            msg = json.dumps({"action": "publish", "point_id": "a", "value": 500})
            sock.sendall((msg + "\n").encode("utf-8"))

            # 读取响应
            resp = sock.recv(1024)
            sock.close()

            resp_obj = json.loads(resp.decode("utf-8").strip())
            assert resp_obj.get("published") is True
            assert resp_obj.get("point_id") == "a"

            # 验证 subscribe 队列收到通知
            result = sub_q.get(timeout=0.5)
            assert result == ("a", 500)
        finally:
            facade.stop()


# ── MqttDriverAdapter NOT_IMPLEMENTED 测试 ──────────────────────────────────────────────


class TestMqttDriverAdapterNotImplemented:
    """MqttDriverAdapter NOT_IMPLEMENTED 语义测试。"""

    def test_write_raises_unsupported(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        plan = _make_mqtt_plan("notimpl_write")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("sensor_temp", 100)

    def test_report_raises_unsupported(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        plan = _make_mqtt_plan("notimpl_report")
        facade = create_mqtt_driver_adapter()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()


# ── MqttDriverAdapter TCP 线上协议测试 ─────────────────────────────────────────────────


class TestMqttDriverAdapterTcpProtocol:
    """MqttDriverAdapter TCP JSON 行协议测试。"""

    def _send_and_recv(self, sock: socket.socket, msg: dict) -> dict:
        """发送 JSON 消息并接收响应。

        Args:
            sock: 已连接的 socket。
            msg: 要发送的消息 dict。

        Returns:
            解析后的响应 dict。
        """
        payload = json.dumps(msg).encode("utf-8") + b"\n"
        sock.sendall(payload)
        resp = sock.recv(4096)
        line = resp.split(b"\n")[0]
        return json.loads(line.decode("utf-8"))

    def test_read_specific_points(self) -> None:
        """TCP read action 应返回指定点位值。"""
        plan = _make_mqtt_plan(
            "tcp_read",
            initial_values={"x": 10, "y": 20},
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            resp = self._send_and_recv(
                sock, {"action": "read", "point_ids": ["x"]},
            )
            assert resp["values"]["x"] == 10
            sock.close()
        finally:
            facade.stop()

    def test_read_all(self) -> None:
        """TCP read_all action 应返回全部点位值。"""
        plan = _make_mqtt_plan(
            "tcp_read_all",
            initial_values={"p1": "hello", "p2": 42},
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            resp = self._send_and_recv(sock, {"action": "read_all"})
            assert "values" in resp
            assert resp["values"]["p1"] == "hello"
            assert resp["values"]["p2"] == 42
            sock.close()
        finally:
            facade.stop()

    def test_publish_updates_value(self) -> None:
        """TCP publish action 应更新点位值。"""
        plan = _make_mqtt_plan(
            "tcp_publish",
            initial_values={"count": 0},
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            # publish
            resp = self._send_and_recv(
                sock, {"action": "publish", "point_id": "count", "value": 99},
            )
            assert resp.get("published") is True

            # read 验证
            resp2 = self._send_and_recv(
                sock, {"action": "read", "point_ids": ["count"]},
            )
            assert resp2["values"]["count"] == 99
            sock.close()
        finally:
            facade.stop()

    def test_unsupported_action(self) -> None:
        """不支持的 action 应返回 error。"""
        plan = _make_mqtt_plan("tcp_bad_action")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            resp = self._send_and_recv(sock, {"action": "subscribe"})
            assert "error" in resp
            assert "unsupported action" in resp["error"]
            sock.close()
        finally:
            facade.stop()

    def test_invalid_json(self) -> None:
        """无效 JSON 应返回 error。"""
        plan = _make_mqtt_plan("tcp_bad_json")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            sock.sendall(b"not json\n")
            resp = sock.recv(4096)
            line = resp.split(b"\n")[0]
            resp_obj = json.loads(line.decode("utf-8"))
            assert "error" in resp_obj
            sock.close()
        finally:
            facade.stop()

    def test_missing_point_id_in_read(self) -> None:
        """read action 无 point_ids 时仍应正常返回（当作空 list）。"""
        plan = _make_mqtt_plan("tcp_read_no_ids")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            resp = self._send_and_recv(sock, {"action": "read"})
            assert "values" in resp
            assert resp["values"] == {}
            sock.close()
        finally:
            facade.stop()

    def test_multiple_clients(self) -> None:
        """多个客户端应能同时连接。"""
        plan = _make_mqtt_plan("tcp_multi_client")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        socks = []
        try:
            for _ in range(3):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.connect(("127.0.0.1", port))
                socks.append(sock)

            # 每个客户端执行一次 read_all
            for sock in socks:
                resp = self._send_and_recv(sock, {"action": "read_all"})
                assert "values" in resp
        finally:
            for sock in socks:
                try:
                    sock.close()
                except OSError:
                    pass
            facade.stop()


# ── MqttDriverAdapter 完整 smoke 流程测试 ───────────────────────────────────────────────


class TestMqttDriverAdapterSmokeFlow:
    """MqttDriverAdapter 完整 smoke 流程测试。"""

    def test_full_smoke_flow(self) -> None:
        """MqttDriverAdapter 完整 start/read/subscribe/stop 流程。"""
        plan = _make_mqtt_plan("smoke_flow")
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)

        # load_points
        assert facade.health()["plan_loaded"] is True

        # subscribe before start
        sub_q = facade.subscribe(["sensor_temp"])
        assert isinstance(sub_q, SubscriptionQueue)

        # start
        facade.start()
        assert facade.health()["running"] is True
        assert facade.health()["port"] > 0

        # read
        values = facade.read()
        assert values["sensor_temp"] == 25.5

        # capabilities
        assert "READ" in facade.capabilities()

        # update_values triggers subscribe
        facade.update_values({"sensor_temp": 99.9})
        result = sub_q.get(timeout=0.5)
        assert result == ("sensor_temp", 99.9)

        # read reflects update
        assert facade.read(["sensor_temp"]) == {"sensor_temp": 99.9}

        # NOT_IMPLEMENTED: write
        with pytest.raises(UnsupportedOperation):
            facade.write("sensor_temp", 999)

        # NOT_IMPLEMENTED: report
        with pytest.raises(UnsupportedOperation):
            facade.report()

        # stop
        facade.stop()
        assert facade.health()["running"] is False
