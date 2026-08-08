"""基于 iec104-python 的 Starfish IEC104 双角色 backend。

第三方扩展通过延迟 import 加载，避免在不支持当前 Python 版本的平台上阻断
Starfish 其他模块导入。受控站使用包内建总召、单点读和一般累计量召唤处理器；
控制站通过稳定的 ``execute_task`` 接口发起读取、召唤、控制和时钟同步。

背景传输由本 adapter 的可停止线程调度；周期传输交给 ``report_ms``；自发传输
由 ``update_point`` 的变化检测触发。运行状态保存在 adapter 中，不向 pybind11
的 ``c104.Point`` 动态添加属性。
"""

from __future__ import annotations

import importlib
import math
import re
import threading
import time
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

from starfish.core.definitions import (
    PointItemDefinition,
    ServerDefinition,
    TaskDefinition,
)

_SERVER_ROLE = "CONTROLLED_STATION"
_CLIENT_ROLE = "CONTROLLING_STATION"
_BACKGROUND_STOP_TIMEOUT_S = 2.0
_RETRY_BACKOFF_BASE_S = 0.1
_RATE_EXPRESSION_RE = re.compile(r"^rate\(\s*(\d+)\s*(ms|s|m|h)\s*\)$", re.IGNORECASE)
_SUPPORTED_TASKS_BY_ROLE = {
    _SERVER_ROLE: {
        "IEC104_RESPOND_GENERAL_INTERROGATION",
        "IEC104_RESPOND_COUNTER_INTERROGATION",
        "IEC104_RESPOND_READ_COMMAND",
        "IEC104_SEND_CYCLIC_DATA",
        "IEC104_SEND_SPONTANEOUS_DATA",
        "IEC104_SEND_BACKGROUND_DATA",
        "IEC104_ACCEPT_SINGLE_COMMAND",
        "IEC104_ACCEPT_DOUBLE_COMMAND",
        "IEC104_ACCEPT_SETPOINT_COMMAND",
        "IEC104_ACCEPT_CLOCK_SYNCHRONIZATION",
    },
    _CLIENT_ROLE: {
        "IEC104_RECEIVE_MONITOR_DATA",
        "IEC104_SEND_GENERAL_INTERROGATION",
        "IEC104_SEND_COUNTER_INTERROGATION",
        "IEC104_SEND_READ_COMMAND",
        "IEC104_SEND_SINGLE_COMMAND",
        "IEC104_SEND_DOUBLE_COMMAND",
        "IEC104_SEND_SETPOINT_COMMAND",
        "IEC104_SEND_CLOCK_SYNCHRONIZATION",
    },
}


class Iec104DependencyError(RuntimeError):
    """当前环境无法加载 iec104-python 扩展。"""


class Iec104OperationError(RuntimeError):
    """IEC104 task 执行失败、超时或返回否定结果。"""


class _RetryableTransmissionError(Iec104OperationError):
    """安全主动请求返回 False，可在 deadline 内有限重试。"""


@dataclass
class _PointState:
    """adapter 自己维护的 Point 时序状态。"""

    value: Any
    updated_at: datetime
    changed_at: datetime
    last_sent_at: datetime | None = None
    last_sent_value: Any = None
    quality: Any = None
    recorded_at: datetime | None = None


def load_c104_module() -> ModuleType:
    """延迟加载 c104，并转换为稳定依赖错误。"""
    try:
        return importlib.import_module("c104")
    except (ImportError, OSError) as exc:
        raise Iec104DependencyError(
            "IEC104 runtime 需要可导入的 iec104-python(c104) 扩展；"
            "当前环境未安装或二进制与 Python 不兼容"
        ) from exc


class Iec104Backend:
    """一个 Whale IEC104 connection 对应的真实 c104 runtime。

    ``connect`` 只创建 c104 对象和注册 Point；``start`` 才启动 socket/连接和
    后台调度。``stop`` 设置停止事件、等待线程退出并停止 c104，重复调用安全。
    """

    def __init__(
        self,
        *,
        c104_module: ModuleType | Any | None = None,
    ) -> None:
        """创建尚未装配的 backend。

        Args:
            c104_module: 测试可注入的 c104 API 替身；生产环境保持为空以延迟导入。
        """
        self._c104: Any = c104_module
        self._definition: ServerDefinition | None = None
        self._runtime: Any = None
        self._connection: Any = None
        self._points: dict[int, Any] = {}
        self._point_defs: dict[int, PointItemDefinition] = {}
        self._point_states: dict[int, _PointState] = {}
        self._callbacks: list[Any] = []
        self._started = False
        self._started_at: datetime | None = None
        self._stop_event = threading.Event()
        self._background_threads: list[threading.Thread] = []
        self._lock = threading.RLock()

    @property
    def protocol(self) -> str:
        """返回协议 registry key。"""
        return "IEC104"

    @property
    def mode(self) -> str:
        """返回 c104 真实 runtime 模式。"""
        return "c104"

    def load_points(self, definition: ServerDefinition) -> None:
        """保存完整 definition；必须在 connect/start 前调用。"""
        if self._runtime is not None:
            raise Iec104OperationError("IEC104 runtime 已装配，不能重新加载 definition")
        _validate_definition(definition)
        self._definition = definition
        self._point_defs = {point.point_item_id: point for point in definition.point_items}
        now = datetime.now(timezone.utc)
        self._point_states = {
            point.point_item_id: _PointState(
                value=point.initial_value,
                updated_at=now,
                changed_at=now,
            )
            for point in definition.point_items
        }

    def connect(self) -> None:
        """根据 station_role 创建 Server 或 Client 并注册全部 view Point。"""
        if self._runtime is not None:
            return
        definition = self._require_definition()
        c104 = self._c104 or load_c104_module()
        self._c104 = c104
        if definition.station_role == _SERVER_ROLE:
            self._build_server(c104, definition)
        elif definition.station_role == _CLIENT_ROLE:
            self._build_client(c104, definition)
        else:
            raise Iec104OperationError(f"不支持的 IEC104 station_role: {definition.station_role}")

    def start(self) -> None:
        """启动 c104 socket/连接和配置为 SCHEDULED 的背景任务。"""
        if self._started:
            return
        self.connect()
        definition = self._require_definition()
        if definition.station_role == _SERVER_ROLE:
            for task in definition.tasks:
                if task.task_type == "IEC104_SEND_BACKGROUND_DATA":
                    _background_period_ms(task)
        try:
            self._runtime.start()
        except Exception as exc:
            raise Iec104OperationError(f"启动 IEC104 {self._role_label()} 失败: {exc}") from exc
        self._stop_event.clear()
        self._started = True
        self._started_at = datetime.now(timezone.utc)
        if definition.station_role == _CLIENT_ROLE:
            try:
                self._wait_connection_open(
                    int(
                        definition.connection_params.get("t0_ms")
                        or definition.connection_params.get("timeout_ms")
                        or 10000
                    )
                )
            except Iec104OperationError:
                self.stop()
                raise
        else:
            self._start_background_tasks()

    def stop(self) -> None:
        """停止调度和 c104 runtime；未回收线程会保留并明确报告。"""
        self._stop_event.set()
        runtime_error: Exception | None = None
        try:
            if self._runtime is not None:
                self._runtime.stop()
        except Exception as exc:
            runtime_error = exc
        finally:
            self._started = False
        for thread in self._background_threads:
            thread.join(timeout=_BACKGROUND_STOP_TIMEOUT_S)
        self._prune_background_threads()
        if runtime_error is not None:
            raise Iec104OperationError(
                f"停止 IEC104 runtime 失败: {runtime_error}"
            ) from runtime_error
        if self._background_threads:
            raise Iec104OperationError(
                "IEC104 background shutdown incomplete: "
                f"{len(self._background_threads)} 个线程仍在结束当前发送"
            )

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        """更新受控站数据源 Point，并按死区/最小间隔决定是否自发上送。

        Args:
            point: point_item_id 或 point_identifier。
            value: 符合 Type ID 信息值结构的 Python 值。
            transmit_spontaneous: 是否允许本次更新触发 SPONTANEOUS。
            quality: 可选 c104 quality 枚举或枚举成员名。
            recorded_at: 可选协议时标；仅带 CP56Time2a 的 Type ID 可使用。

        Returns:
            更新后的公开状态快照。

        Raises:
            Iec104OperationError: Point 不存在、当前不是受控站或 c104 拒绝赋值。
        """
        definition = self._require_definition()
        if definition.station_role != _SERVER_ROLE:
            raise Iec104OperationError("只有 CONTROLLED_STATION 可作为数据源更新 Point")
        point_id = self._resolve_point_id(point)
        point_def = self._point_defs[point_id]
        runtime_point = self._points.get(point_id)
        if runtime_point is None:
            raise Iec104OperationError(f"Point 尚未注册: {point}")
        now = datetime.now(timezone.utc)
        with self._lock:
            state = self._point_states[point_id]
            value_changed = _value_changed(state.value, value, 0)
            spontaneous_reference = (
                state.last_sent_value if state.last_sent_at is not None else point_def.initial_value
            )
            spontaneous_changed = _value_changed(
                spontaneous_reference,
                value,
                float(point_def.metadata.get("spontaneous_deadband") or 0),
            )
            try:
                _assign_point_information(
                    self._c104,
                    runtime_point,
                    point_def,
                    value,
                    quality=quality,
                    recorded_at=recorded_at,
                )
            except Exception as exc:
                raise Iec104OperationError(
                    f"IEC104 Point 赋值失败 point={point_def.point_identifier}: {exc}"
                ) from exc
            state.value = value
            state.quality = getattr(runtime_point, "quality", quality)
            state.recorded_at = getattr(runtime_point, "recorded_at", recorded_at)
            state.updated_at = now
            if value_changed:
                state.changed_at = now
            if (
                self._started
                and transmit_spontaneous
                and spontaneous_changed
                and self._spontaneous_due(point_id, now)
            ):
                self._transmit_points((point_id,), self._c104.Cot.SPONTANEOUS)
        return self.point_state(point_id)

    def point_state(self, point: int | str) -> dict[str, Any]:
        """返回 adapter 保存的当前值和更新时间，不暴露第三方 Point。"""
        point_id = self._resolve_point_id(point)
        with self._lock:
            state = self._point_states[point_id]
            return {
                "point_item_id": point_id,
                "point_identifier": self._point_defs[point_id].point_identifier,
                "value": state.value,
                "updated_at": state.updated_at,
                "changed_at": state.changed_at,
                "last_sent_at": state.last_sent_at,
                "last_sent_value": state.last_sent_value,
                "quality": state.quality,
                "recorded_at": state.recorded_at,
            }

    def execute_task(
        self,
        task: int | str,
        *,
        values: Mapping[int | str, Any] | None = None,
    ) -> dict[str, Any]:
        """同步执行可主动调用的 IEC104 task。

        c104 的命令等待使用 Client 构造时的 ``command_timeout_ms``；本方法在
        返回 ``success=False`` 时抛出稳定异常，不把否定确认伪装成成功。仅站
        总召、一般累计量召唤和读命令的 False 结果可有限退避重试；第三方异常
        默认不可安全分类，因此不重试。控制与时钟命令始终不自动重试。
        """
        task_def = self._resolve_task(task)
        operation = task_def.task_type
        if self._require_definition().station_role == _SERVER_ROLE:
            send_causes = {
                "IEC104_SEND_BACKGROUND_DATA": self._c104.Cot.BACKGROUND_SCAN,
                "IEC104_SEND_CYCLIC_DATA": self._c104.Cot.PERIODIC,
                "IEC104_SEND_SPONTANEOUS_DATA": self._c104.Cot.SPONTANEOUS,
            }
            if operation in send_causes:
                sent = self._transmit_points(
                    task_def.point_item_ids,
                    send_causes[operation],
                    max_objects=int(task_def.params.get("max_objects_per_asdu", 40)),
                )
                return _task_result(task_def, sent)
            if operation in {
                "IEC104_RESPOND_GENERAL_INTERROGATION",
                "IEC104_RESPOND_COUNTER_INTERROGATION",
                "IEC104_RESPOND_READ_COMMAND",
                "IEC104_ACCEPT_SINGLE_COMMAND",
                "IEC104_ACCEPT_DOUBLE_COMMAND",
                "IEC104_ACCEPT_SETPOINT_COMMAND",
                "IEC104_ACCEPT_CLOCK_SYNCHRONIZATION",
            }:
                return _task_result(task_def, True, automatic=True)
            raise Iec104OperationError(f"受控站 task 不可主动执行: {operation}")

        return self._execute_client_task(task_def, values or {})

    def health(self) -> dict[str, Any]:
        """返回生命周期、角色、连接和 Point 状态摘要。"""
        self._prune_background_threads()
        definition = self._definition
        runtime_running = bool(
            self._runtime is not None and getattr(self._runtime, "is_running", self._started)
        )
        if definition and definition.station_role == _CLIENT_ROLE and self._runtime is not None:
            running = bool(getattr(self._runtime, "has_open_connections", runtime_running))
        else:
            running = runtime_running
        shutdown_incomplete = bool(self._background_threads and not self._started)
        return {
            "status": (
                "shutdown_incomplete"
                if shutdown_incomplete
                else ("started" if self._started else "stopped")
            ),
            "mode": self.mode,
            "running": running,
            "definition_loaded": definition is not None,
            "station_role": definition.station_role if definition else None,
            "point_count": len(self._point_defs),
            "task_count": len(definition.tasks) if definition else 0,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "background_thread_count": len(self._background_threads),
            "shutdown_incomplete": shutdown_incomplete,
            "synthetic": False,
            "protocol": self.protocol,
        }

    def _build_server(self, c104: Any, definition: ServerDefinition) -> None:
        params = definition.connection_params
        self._runtime = c104.Server(
            ip=definition.bind_host,
            port=definition.bind_port,
            tick_rate_ms=int(params.get("tick_rate_ms", 100)),
            select_timeout_ms=_select_timeout_ms(definition),
            max_connections=int(params.get("max_client_count", 0)),
        )
        _apply_protocol_parameters(self._runtime.protocol_parameters, params)
        self._register_points(c104, self._runtime, server_side=True)

        def on_clock_sync(server: Any, ip: str, date_time: datetime) -> Any:
            accepted = self._has_enabled_task("IEC104_ACCEPT_CLOCK_SYNCHRONIZATION")
            return c104.ResponseState.SUCCESS if accepted else c104.ResponseState.FAILURE

        on_clock_sync.__annotations__ = {
            "server": getattr(c104, "Server", Any),
            "ip": str,
            "date_time": datetime,
            "return": c104.ResponseState,
        }
        self._callbacks.append(on_clock_sync)
        self._runtime.on_clock_sync(callable=on_clock_sync)

    def _build_client(self, c104: Any, definition: ServerDefinition) -> None:
        params = definition.connection_params
        self._runtime = c104.Client(
            tick_rate_ms=int(params.get("tick_rate_ms", 100)),
            command_timeout_ms=_client_command_timeout_ms(definition),
        )
        self._connection = self._runtime.add_connection(
            ip=definition.bind_host,
            port=definition.bind_port,
            init=c104.Init.NONE,
        )
        if self._connection is None:
            raise Iec104OperationError("c104.Client.add_connection 返回空")
        _apply_protocol_parameters(self._connection.protocol_parameters, params)
        self._register_points(c104, self._connection, server_side=False)

    def _register_points(self, c104: Any, parent: Any, *, server_side: bool) -> None:
        stations: dict[int, Any] = {}
        for point_def in self._point_defs.values():
            if not bool(point_def.metadata.get("point_registration_supported", True)):
                raise Iec104OperationError(f"view 声明 Point 不可注册: {point_def.type_id}")
            common_address = int(point_def.metadata.get("common_address") or 0)
            station = stations.get(common_address)
            if station is None:
                station = parent.add_station(common_address=common_address)
                if station is None:
                    raise Iec104OperationError(f"无法创建 IEC104 Station CA={common_address}")
                stations[common_address] = station
            command_mode_name = str(point_def.metadata.get("command_mode") or "DIRECT")
            kwargs = {
                "io_address": int(point_def.io_address),
                "type": _enum_member(c104.Type, point_def.type_id),
                "report_ms": self._effective_report_ms(point_def) if server_side else 0,
                "related_io_address": (
                    int(point_def.metadata["related_io_address"])
                    if server_side and point_def.metadata.get("related_io_address") is not None
                    else None
                ),
                "related_io_autoreturn": bool(
                    server_side and point_def.metadata.get("related_io_autoreturn")
                ),
                "command_mode": _enum_member(c104.CommandMode, command_mode_name),
            }
            try:
                runtime_point = station.add_point(**kwargs)
            except Exception as exc:
                raise Iec104OperationError(
                    f"注册 IEC104 Point 失败 CA={common_address} "
                    f"IOA={point_def.io_address} Type={point_def.type_id}: {exc}"
                ) from exc
            if runtime_point is None:
                raise Iec104OperationError(
                    f"注册 IEC104 Point 返回空: {point_def.point_identifier}"
                )
            self._points[point_def.point_item_id] = runtime_point
            runtime_point.value = _c104_value(
                c104,
                point_def.type_id,
                point_def.initial_value,
            )
            self._register_point_callbacks(c104, point_def, runtime_point, server_side)

    def _register_point_callbacks(
        self,
        c104: Any,
        point_def: PointItemDefinition,
        runtime_point: Any,
        server_side: bool,
    ) -> None:
        if _is_command_type(point_def.type_id) or not server_side:

            def on_receive(point: Any, previous_info: Any, message: Any) -> Any:
                try:
                    with self._lock:
                        if server_side and not self._command_is_enabled(
                            point_def.point_item_id,
                            point_def.type_id,
                        ):
                            return c104.ResponseState.FAILURE
                        self._capture_received_point(point_def.point_item_id, point)
                        if server_side:
                            self._update_related_monitor_point(point_def, point.value)
                except Exception:
                    return c104.ResponseState.FAILURE
                return c104.ResponseState.SUCCESS

            on_receive.__annotations__ = {
                "point": getattr(c104, "Point", Any),
                "previous_info": getattr(c104, "Information", Any),
                "message": getattr(c104, "IncomingMessage", Any),
                "return": c104.ResponseState,
            }
            self._callbacks.append(on_receive)
            runtime_point.on_receive(callable=on_receive)
        if server_side and not _is_command_type(point_def.type_id):

            def on_before_read(point: Any) -> None:
                self._mark_sent(point_def.point_item_id)

            on_before_read.__annotations__ = {
                "point": getattr(c104, "Point", Any),
                "return": None,
            }
            self._callbacks.append(on_before_read)
            runtime_point.on_before_read(callable=on_before_read)
        if server_side and self._effective_report_ms(point_def) > 0:

            def on_before_auto_transmit(point: Any) -> None:
                self._mark_sent(point_def.point_item_id)

            on_before_auto_transmit.__annotations__ = {
                "point": getattr(c104, "Point", Any),
                "return": None,
            }
            self._callbacks.append(on_before_auto_transmit)
            runtime_point.on_before_auto_transmit(callable=on_before_auto_transmit)

    def _capture_received_point(self, point_id: int, runtime_point: Any) -> None:
        """保存收到的值、质量和协议时标。"""
        with self._lock:
            now = datetime.now(timezone.utc)
            state = self._point_states[point_id]
            changed = _value_changed(state.value, runtime_point.value, 0)
            state.value = runtime_point.value
            state.updated_at = now
            if changed:
                state.changed_at = now
            state.quality = getattr(runtime_point, "quality", None)
            state.recorded_at = getattr(runtime_point, "recorded_at", None)

    def _update_related_monitor_point(
        self,
        command_def: PointItemDefinition,
        command_value: Any,
    ) -> None:
        """命令成功时先更新关联监视点，供 c104 autoreturn 发送新值。"""
        with self._lock:
            related_io = command_def.metadata.get("related_io_address")
            if related_io is None:
                return
            common_address = int(command_def.metadata.get("common_address") or 0)
            matches = [
                point
                for point in self._point_defs.values()
                if int(point.metadata.get("common_address") or 0) == common_address
                and int(point.io_address) == int(related_io)
            ]
            if len(matches) != 1:
                raise Iec104OperationError(
                    f"命令关联监视点无法唯一定位 CA={common_address} IOA={related_io}"
                )
            related_def = matches[0]
            runtime_point = self._points[related_def.point_item_id]
            source_value = _related_monitor_value(
                command_def.type_id,
                related_def.type_id,
                command_value,
            )
            runtime_point.value = _c104_value(
                self._c104,
                related_def.type_id,
                source_value,
            )
            now = datetime.now(timezone.utc)
            state = self._point_states[related_def.point_item_id]
            state.value = runtime_point.value
            state.updated_at = now
            state.changed_at = now
            state.quality = getattr(runtime_point, "quality", None)
            state.recorded_at = getattr(runtime_point, "recorded_at", None)

    def _execute_client_task(
        self,
        task: TaskDefinition,
        values: Mapping[int | str, Any],
    ) -> dict[str, Any]:
        if self._connection is None:
            raise Iec104OperationError("IEC104 client connection 尚未装配")
        timeout_ms = max(int(task.params.get("timeout_ms", 10000)), 1)
        operation = task.task_type
        safe_retry_operations = {
            "IEC104_SEND_GENERAL_INTERROGATION",
            "IEC104_SEND_COUNTER_INTERROGATION",
            "IEC104_SEND_READ_COMMAND",
        }
        configured_retries = max(int(task.params.get("retry_count", 0)), 0)
        retries = configured_retries if operation in safe_retry_operations else 0
        last_error: Iec104OperationError | None = None
        deadline = time.monotonic() + timeout_ms / 1000
        for attempt in range(1, retries + 2):
            if self._stop_event.is_set():
                raise Iec104OperationError(f"执行 {operation} 已被 stop 中断")
            try:
                remaining_ms = math.ceil((deadline - time.monotonic()) * 1000)
                if remaining_ms <= 0:
                    raise Iec104OperationError(
                        f"执行 {operation} 超过 task timeout_ms={timeout_ms}"
                    )
                self._wait_connection_open(remaining_ms)
                result = self._execute_client_task_once(task, values)
                if time.monotonic() > deadline:
                    raise Iec104OperationError(
                        f"执行 {operation} 超过 task timeout_ms={timeout_ms}；"
                        "c104 同步调用内部不可由 adapter 取消，仅能在返回后判定超时"
                    )
                result["attempts"] = attempt
                if configured_retries and not retries:
                    result["retry_suppressed"] = (
                        "控制/时钟命令不自动重试，避免不确定确认导致重复执行"
                    )
                return result
            except _RetryableTransmissionError as exc:
                last_error = exc
                if attempt > retries or time.monotonic() >= deadline:
                    break
                self._wait_retry_backoff(operation, attempt, deadline)
            except Iec104OperationError:
                # 配置、输入、Type/Key 等错误默认不可重试；第三方异常也不猜测。
                raise
        suffix = (
            "；控制/时钟命令不自动重试，避免不确定确认导致重复执行"
            if configured_retries and not retries
            else ""
        )
        raise Iec104OperationError(f"{last_error}{suffix}") from last_error

    def _wait_retry_backoff(
        self,
        operation: str,
        failed_attempt: int,
        deadline: float,
    ) -> None:
        """递增退避，等待可被 stop 中断且不能跨过 task deadline。"""
        backoff_s = _RETRY_BACKOFF_BASE_S * failed_attempt
        remaining_s = deadline - time.monotonic()
        if remaining_s <= backoff_s:
            raise Iec104OperationError(
                f"执行 {operation} 重试预算不足：剩余 deadline "
                f"{max(remaining_s, 0) * 1000:.0f}ms，小于 backoff "
                f"{backoff_s * 1000:.0f}ms"
            )
        if self._stop_event.wait(backoff_s):
            raise Iec104OperationError(f"执行 {operation} 的 retry backoff 被 stop 中断")

    def _execute_client_task_once(
        self,
        task: TaskDefinition,
        values: Mapping[int | str, Any],
    ) -> dict[str, Any]:
        """执行一次控制站 task；重试策略由外层统一约束。"""
        operation = task.task_type
        wait = bool(task.params.get("wait_activation_confirmation", True))
        common_addresses = _task_common_addresses(task, self._point_defs)
        results: list[bool] = []
        try:
            if operation == "IEC104_SEND_GENERAL_INTERROGATION":
                results = [
                    bool(
                        self._connection.interrogation(
                            common_address=ca,
                            cause=self._c104.Cot.ACTIVATION,
                            qualifier=self._c104.Qoi.STATION,
                            wait_for_response=wait,
                        )
                    )
                    for ca in common_addresses
                ]
            elif operation == "IEC104_SEND_COUNTER_INTERROGATION":
                results = [
                    bool(
                        self._connection.counter_interrogation(
                            common_address=ca,
                            cause=self._c104.Cot.ACTIVATION,
                            qualifier=self._c104.Rqt.GENERAL,
                            freeze=self._c104.Frz.READ,
                            wait_for_response=wait,
                        )
                    )
                    for ca in common_addresses
                ]
            elif operation == "IEC104_SEND_CLOCK_SYNCHRONIZATION":
                default_ca = int(self._require_definition().connection_params["common_address"])
                results = [
                    bool(
                        self._connection.clock_sync(
                            common_address=default_ca,
                            wait_for_response=True,
                        )
                    )
                ]
            elif operation == "IEC104_SEND_READ_COMMAND":
                results = [bool(self._points[point_id].read()) for point_id in task.point_item_ids]
            elif operation in {
                "IEC104_SEND_SINGLE_COMMAND",
                "IEC104_SEND_DOUBLE_COMMAND",
                "IEC104_SEND_SETPOINT_COMMAND",
            }:
                results = [
                    self._transmit_command(
                        point_id, _lookup_value(values, point_id, self._point_defs)
                    )
                    for point_id in task.point_item_ids
                ]
            elif operation == "IEC104_RECEIVE_MONITOR_DATA":
                return _task_result(task, True, automatic=True)
            else:
                raise Iec104OperationError(f"控制站不支持主动执行 task: {operation}")
        except Iec104OperationError:
            raise
        except Exception as exc:
            raise Iec104OperationError(f"执行 {operation} 失败: {exc}") from exc
        if not results or not all(results):
            raise _RetryableTransmissionError(f"执行 {operation} 收到失败或超时结果: {results}")
        return _task_result(task, True, operation_count=len(results))

    def _wait_connection_open(self, timeout_ms: int) -> None:
        """等待 c104 异步连接进入 OPEN，deadline 到期或 stop 时稳定失败。"""
        if self._connection is None:
            raise Iec104OperationError("IEC104 client connection 尚未装配")
        deadline = time.monotonic() + max(timeout_ms, 1) / 1000
        while not _connection_is_open(self._c104, self._connection):
            if self._stop_event.is_set():
                raise Iec104OperationError("等待 IEC104 connection OPEN 已被 stop 中断")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Iec104OperationError(
                    f"等待 IEC104 connection OPEN 超时 timeout_ms={timeout_ms}"
                )
            self._stop_event.wait(min(remaining, 0.01))

    def _transmit_command(self, point_id: int, value: Any) -> bool:
        point_def = self._point_defs[point_id]
        point = self._points[point_id]
        point.value = _c104_value(self._c104, point_def.type_id, value)
        return bool(point.transmit(cause=self._c104.Cot.ACTIVATION))

    def _transmit_points(
        self,
        point_ids: tuple[int, ...] | list[int],
        cause: Any,
        *,
        max_objects: int = 127,
    ) -> bool:
        groups: dict[tuple[int, str], list[int]] = defaultdict(list)
        for point_id in point_ids:
            point_def = self._point_defs[point_id]
            groups[
                (
                    int(point_def.metadata.get("common_address") or 0),
                    point_def.type_id,
                )
            ].append(point_id)
        success = True
        for ids in groups.values():
            for start in range(0, len(ids), max(1, max_objects)):
                chunk = ids[start : start + max(1, max_objects)]
                batch = self._c104.Batch(
                    cause=cause,
                    points=[self._points[point_id] for point_id in chunk],
                )
                batch_success = bool(self._runtime.transmit_batch(batch))
                success = batch_success and success
                if batch_success:
                    for point_id in chunk:
                        self._mark_sent(point_id)
        return success

    def _spontaneous_due(self, point_id: int, now: datetime) -> bool:
        task_ids = {
            point
            for task in self._require_definition().tasks
            if task.task_type == "IEC104_SEND_SPONTANEOUS_DATA" and _task_is_enabled(task)
            for point in task.point_item_ids
        }
        if point_id not in task_ids:
            return False
        if not bool(
            self._point_defs[point_id].metadata.get(
                "spontaneous_transmission_supported",
                True,
            )
        ):
            return False
        minimum_ms = int(
            self._point_defs[point_id].metadata.get("spontaneous_min_interval_ms") or 0
        )
        last = self._point_states[point_id].last_sent_at
        return last is None or minimum_ms <= 0 or (now - last).total_seconds() * 1000 >= minimum_ms

    def _mark_sent(self, point_id: int) -> None:
        with self._lock:
            state = self._point_states[point_id]
            state.last_sent_at = datetime.now(timezone.utc)
            state.last_sent_value = state.value

    def _start_background_tasks(self) -> None:
        for task in self._require_definition().tasks:
            if task.task_type != "IEC104_SEND_BACKGROUND_DATA" or not _task_is_enabled(task):
                continue
            period_ms = _background_period_ms(task)
            thread = threading.Thread(
                target=self._background_loop,
                args=(task, period_ms),
                name=f"starfish-iec104-background-{task.task_id}",
                daemon=True,
            )
            self._background_threads.append(thread)
            thread.start()

    def _background_loop(self, task: TaskDefinition, period_ms: int) -> None:
        while not self._stop_event.wait(max(period_ms, 1) / 1000):
            if self._stop_event.is_set():
                return
            try:
                self.execute_task(task.task_id)
            except Iec104OperationError:
                # health/status 保持 runtime 存活；下一周期仍可恢复发送。
                if self._stop_event.is_set():
                    return
                continue
            if self._stop_event.is_set():
                return

    def _prune_background_threads(self) -> None:
        """仅移除真实结束的背景线程，保留未完成 shutdown 的证据。"""
        with self._lock:
            self._background_threads = [
                thread for thread in self._background_threads if thread.is_alive()
            ]

    def _resolve_point_id(self, point: int | str) -> int:
        if isinstance(point, int):
            point_id = point
        else:
            matches = [
                item.point_item_id
                for item in self._point_defs.values()
                if item.point_identifier == point
            ]
            if len(matches) != 1:
                raise Iec104OperationError(f"无法唯一定位 IEC104 Point: {point}")
            point_id = matches[0]
        if point_id not in self._point_defs:
            raise Iec104OperationError(f"IEC104 Point 不存在: {point}")
        return point_id

    def _resolve_task(self, task: int | str) -> TaskDefinition:
        tasks = self._require_definition().tasks
        matches = [
            item
            for item in tasks
            if item.task_id == task or item.task_identifier == task or item.task_type == task
        ]
        if len(matches) != 1:
            raise Iec104OperationError(f"无法唯一定位 IEC104 task: {task}")
        task_def = matches[0]
        if not _task_is_enabled(task_def):
            raise Iec104OperationError(f"IEC104 task 未启用: {task_def.task_identifier}")
        return task_def

    def _effective_report_ms(self, point_def: PointItemDefinition) -> int:
        """返回同时被周期 task 和 Point 能力允许的 c104 report 周期。"""
        if not bool(point_def.metadata.get("periodic_transmission_supported", True)):
            return 0
        if not self._task_contains_point(
            "IEC104_SEND_CYCLIC_DATA",
            point_def.point_item_id,
        ):
            return 0
        return max(int(point_def.metadata.get("report_ms") or 0), 0)

    def _command_is_enabled(self, point_id: int, type_id: str) -> bool:
        """按命令 Type 与启用 task 成员关系判断受控站是否接受命令。"""
        operation = _command_accept_operation(type_id)
        return bool(operation and self._task_contains_point(operation, point_id))

    def _has_enabled_task(self, operation: str) -> bool:
        """返回 definition 是否声明了指定启用 operation。"""
        return any(
            task.task_type == operation and _task_is_enabled(task)
            for task in self._require_definition().tasks
        )

    def _task_contains_point(self, operation: str, point_id: int) -> bool:
        """返回指定 Point 是否属于启用 operation task。"""
        return any(
            task.task_type == operation
            and _task_is_enabled(task)
            and point_id in task.point_item_ids
            for task in self._require_definition().tasks
        )

    def _require_definition(self) -> ServerDefinition:
        if self._definition is None:
            raise Iec104OperationError("IEC104 definition 尚未加载")
        return self._definition

    def _role_label(self) -> str:
        definition = self._require_definition()
        return "server" if definition.station_role == _SERVER_ROLE else "client"


# 兼容既有 wiring 名称；实现已不再使用固定 C runner。
Iec104NativeBackend = Iec104Backend


def _enum_member(enum_type: Any, name: str) -> Any:
    try:
        return getattr(enum_type, name)
    except AttributeError as exc:
        raise Iec104OperationError(f"c104 enum 不包含 {name}") from exc


def _validate_definition(definition: ServerDefinition) -> None:
    """拒绝当前 c104 adapter 未声明支持的角色、task 和 CP24 Point。"""
    supported_tasks = _SUPPORTED_TASKS_BY_ROLE.get(definition.station_role)
    if supported_tasks is None:
        raise Iec104OperationError(f"不支持的 IEC104 station_role: {definition.station_role}")
    unsupported_tasks = sorted(
        {task.task_type for task in definition.tasks if task.task_type not in supported_tasks}
    )
    if unsupported_tasks:
        raise Iec104OperationError("当前 c104 adapter 不支持 IEC104 task: " f"{unsupported_tasks}")
    cp24_points = sorted(
        point.point_identifier
        for point in definition.point_items
        if str(point.metadata.get("time_tag_type") or "").strip().upper() == "CP24TIME2A"
    )
    if cp24_points:
        raise Iec104OperationError(f"c104 2.2.1 不支持注册 CP24Time2a Point: {cp24_points}")


def _c104_value(c104: Any, type_id: str, value: Any) -> Any:
    value = _plain_value(value)
    if type_id.startswith(("M_DP_", "C_DC_")):
        enum_name = getattr(value, "name", None)
        if isinstance(value, str):
            enum_name = value
        if enum_name in {"INDETERMINATE", "OFF", "ON", "INTERMEDIATE"}:
            return _enum_member(c104.Double, enum_name)
        mapping = {0: "INDETERMINATE", 1: "OFF", 2: "ON", 3: "INTERMEDIATE"}
        return _enum_member(c104.Double, mapping.get(int(value), "INDETERMINATE"))
    if type_id.startswith(("M_ST_", "C_RC_")):
        return c104.Int7(int(value))
    if type_id.startswith(("M_ME_NA_", "M_ME_TD_", "C_SE_NA_", "C_SE_TA_")):
        return c104.NormalizedFloat(float(value))
    if type_id.startswith(("M_ME_NB_", "M_ME_TE_", "C_SE_NB_", "C_SE_TB_")):
        return c104.Int16(int(value))
    if type_id.startswith(("M_ME_NC_", "M_ME_TF_", "C_SE_NC_", "C_SE_TC_")):
        return float(value)
    if type_id.startswith(("M_BO_", "C_BO_")):
        return c104.Byte32(value)
    if type_id.startswith(("M_SP_", "C_SC_")):
        return bool(value)
    if type_id.startswith(("M_IT_",)):
        return int(value)
    return float(value) if isinstance(value, Decimal) else value


def _plain_value(value: Any) -> Any:
    """从 c104 数值包装器提取可再次赋值的主值，枚举保留名称。"""
    if getattr(value, "name", None) is not None:
        return value
    return getattr(value, "value", value)


def _related_monitor_value(
    command_type_id: str,
    target_type_id: str,
    command_value: Any,
) -> Any:
    """按目标监视 Type 将控制意图转换为 simulator 数据源值。

    当前真实 View 把三类控制点都关联到 ``M_ME_TF_1``。模拟器约定单点
    OFF/ON 为 0.0/1.0；双点 OFF/ON 为 0.0/1.0，INTERMEDIATE 为 0.5，
    INDETERMINATE 保守回落为 0.0；设点直接转换为 float。
    """
    if not target_type_id.startswith("M_ME_"):
        return _plain_value(command_value)
    if command_type_id.startswith("C_SC_"):
        return 1.0 if bool(_plain_value(command_value)) else 0.0
    if command_type_id.startswith("C_DC_"):
        name = getattr(command_value, "name", None)
        if isinstance(command_value, str):
            name = command_value
        if name is not None:
            mapping = {
                "INDETERMINATE": 0.0,
                "OFF": 0.0,
                "ON": 1.0,
                "INTERMEDIATE": 0.5,
            }
            if name not in mapping:
                raise Iec104OperationError(f"无法转换双点命令值: {name}")
            return mapping[name]
        raw = int(_plain_value(command_value))
        numeric_mapping = {0: 0.0, 1: 0.0, 2: 1.0, 3: 0.5}
        if raw not in numeric_mapping:
            raise Iec104OperationError(f"无法转换双点命令值: {raw}")
        return numeric_mapping[raw]
    if command_type_id.startswith("C_SE_"):
        return float(_plain_value(command_value))
    raise Iec104OperationError(f"不支持 {command_type_id} 关联到模拟量 {target_type_id}")


def _assign_point_information(
    c104: Any,
    runtime_point: Any,
    point_def: PointItemDefinition,
    value: Any,
    *,
    quality: Any,
    recorded_at: datetime | None,
) -> None:
    """按 Point Type 写值，并在需要时构造带质量/CP56 时标的 Information。"""
    converted = _c104_value(c104, point_def.type_id, value)
    converted_quality = (
        _quality_value(c104, point_def.type_id, quality) if quality is not None else None
    )
    if recorded_at is not None:
        time_tag_type = str(point_def.metadata.get("time_tag_type") or "NONE")
        if time_tag_type != "CP56TIME2A":
            raise Iec104OperationError(f"{point_def.type_id} 不支持 recorded_at={time_tag_type}")
        runtime_point.info = _monitor_information(
            c104,
            point_def.type_id,
            converted,
            converted_quality,
            recorded_at,
        )
        return
    runtime_point.value = converted
    if converted_quality is not None:
        runtime_point.quality = converted_quality


def _quality_value(c104: Any, type_id: str, quality: Any) -> Any:
    """把 quality 成员名转换为对应 c104 质量枚举。"""
    if not isinstance(quality, str):
        return quality
    enum_type = c104.BinaryCounterQuality if type_id.startswith("M_IT_") else c104.Quality
    return _enum_member(enum_type, quality)


def _monitor_information(
    c104: Any,
    type_id: str,
    value: Any,
    quality: Any,
    recorded_at: datetime,
) -> Any:
    """为 c104 支持的监视方向 Type 创建带 CP56Time2a 的 Information。"""
    common = {"recorded_at": recorded_at}
    if quality is not None:
        common["quality"] = quality
    if type_id.startswith("M_SP_"):
        return c104.SingleInfo(on=bool(value), **common)
    if type_id.startswith("M_DP_"):
        return c104.DoubleInfo(state=value, **common)
    if type_id.startswith("M_ST_"):
        return c104.StepInfo(position=value, transient=False, **common)
    if type_id.startswith(("M_ME_NA_", "M_ME_TD_")):
        return c104.NormalizedInfo(actual=value, **common)
    if type_id.startswith(("M_ME_NB_", "M_ME_TE_")):
        return c104.ScaledInfo(actual=value, **common)
    if type_id.startswith(("M_ME_NC_", "M_ME_TF_")):
        return c104.ShortInfo(actual=float(value), **common)
    if type_id.startswith("M_BO_"):
        return c104.BinaryInfo(blob=value, **common)
    if type_id.startswith("M_IT_"):
        return c104.BinaryCounterInfo(
            counter=int(value),
            sequence=c104.UInt5(0),
            **common,
        )
    raise Iec104OperationError(f"{type_id} 不支持带协议时标的 Information 赋值")


def _is_command_type(type_id: str) -> bool:
    return type_id.startswith("C_") and type_id not in {
        "C_IC_NA_1",
        "C_CI_NA_1",
        "C_RD_NA_1",
        "C_CS_NA_1",
    }


def _command_accept_operation(type_id: str) -> str | None:
    """将 c104 支持的当前命令 Type 映射到 View 接收 operation。"""
    if type_id.startswith("C_SC_"):
        return "IEC104_ACCEPT_SINGLE_COMMAND"
    if type_id.startswith("C_DC_"):
        return "IEC104_ACCEPT_DOUBLE_COMMAND"
    if type_id.startswith("C_SE_"):
        return "IEC104_ACCEPT_SETPOINT_COMMAND"
    return None


def _task_is_enabled(task: TaskDefinition) -> bool:
    """按 View task_status 判断 task 是否参与运行装配。"""
    return task.task_status.strip().upper() not in {
        "DISABLED",
        "INACTIVE",
        "STOPPED",
        "DELETED",
    }


def _value_changed(previous: Any, current: Any, deadband: float) -> bool:
    if isinstance(previous, (int, float)) and isinstance(current, (int, float)):
        return abs(float(current) - float(previous)) > deadband
    return bool(previous != current)


def _select_timeout_ms(definition: ServerDefinition) -> int:
    """选择仅适用于 SELECT_AND_EXECUTE 控制任务的 server 超时。"""
    operations = {
        "IEC104_ACCEPT_SINGLE_COMMAND",
        "IEC104_ACCEPT_DOUBLE_COMMAND",
        "IEC104_ACCEPT_SETPOINT_COMMAND",
    }
    values = [
        int(task.params.get("timeout_ms", 10000))
        for task in definition.tasks
        if task.task_type in operations
    ]
    return max(values, default=int(definition.connection_params.get("timeout_ms", 10000)))


def _client_command_timeout_ms(definition: ServerDefinition) -> int:
    """选择最大主动 task timeout，避免 c104 全局值提前截断长任务。"""
    active = [
        int(task.params.get("timeout_ms", 10000))
        for task in definition.tasks
        if task.task_type.startswith("IEC104_SEND_")
    ]
    return max(max(active, default=10000), 1)


def _apply_protocol_parameters(protocol_parameters: Any, params: Mapping[str, Any]) -> None:
    """把 View 中毫秒制链路参数映射到 c104 秒制属性及 k/w 窗口。"""
    timeout_fields = {
        "t0_ms": "connection_timeout",
        "t1_ms": "message_timeout",
        "t2_ms": "confirm_interval",
        "t3_ms": "keep_alive_interval",
    }
    for source, target in timeout_fields.items():
        if params.get(source) is not None:
            setattr(
                protocol_parameters,
                target,
                max(math.ceil(int(params[source]) / 1000), 1),
            )
    if params.get("k_value") is not None:
        protocol_parameters.send_window_size = int(params["k_value"])
    if params.get("w_value") is not None:
        protocol_parameters.receive_window_size = int(params["w_value"])


def _connection_is_open(c104: Any, connection: Any) -> bool:
    """兼容真实 enum 与测试替身判断异步 connection OPEN。"""
    state = connection.state
    expected = c104.ConnectionState.OPEN
    return bool(state == expected or getattr(state, "name", None) == "OPEN")


def _background_period_ms(task: TaskDefinition) -> int:
    """将 view 的简单 ``rate(...)`` 调度表达式转换为可停止线程周期。"""
    if "period_ms" in task.params:
        return max(int(task.params["period_ms"]), 1)
    expression = str(task.params.get("schedule_expression") or "rate(60s)").strip()
    match = _RATE_EXPRESSION_RE.fullmatch(expression)
    if match is None:
        raise Iec104OperationError(f"IEC104 背景任务仅支持 rate(Nms|Ns|Nm|Nh): {expression}")
    amount = int(match.group(1))
    multiplier = {"ms": 1, "s": 1000, "m": 60000, "h": 3600000}[match.group(2).lower()]
    return max(amount * multiplier, 1)


def _task_common_addresses(
    task: TaskDefinition,
    point_defs: Mapping[int, PointItemDefinition],
) -> list[int]:
    addresses = sorted(
        {
            int(point_defs[point_id].metadata.get("common_address") or 0)
            for point_id in task.point_item_ids
        }
    )
    return addresses or [1]


def _lookup_value(
    values: Mapping[int | str, Any],
    point_id: int,
    point_defs: Mapping[int, PointItemDefinition],
) -> Any:
    point_def = point_defs[point_id]
    if point_id in values:
        return values[point_id]
    if point_def.point_identifier in values:
        return values[point_def.point_identifier]
    raise Iec104OperationError(f"命令 task 缺少 Point 值: {point_def.point_identifier}")


def _task_result(task: TaskDefinition, success: bool, **detail: Any) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "task_identifier": task.task_identifier,
        "operation_identifier": task.task_type,
        "success": success,
        **detail,
    }


__all__ = [
    "Iec104Backend",
    "Iec104DependencyError",
    "Iec104NativeBackend",
    "Iec104OperationError",
    "load_c104_module",
]
