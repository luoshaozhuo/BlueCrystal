"""IEC104 Starfish connection worker。

本 adapter 是 pandas 公共配置到 c104 原生 runtime 的转换边界。它把单 connection
DataFrame 转换为 backend 使用的 ``ServerDefinition``；backend、线程与点位索引
不依赖 pandas。直接传入 definition 的 API 仍用于协议级测试和主动 client 装配。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, cast

import pandas as pd

from starfish.adapters.protocols.iec104.backend import Iec104Backend
from starfish.core.definitions import (
    PointItemDefinition,
    ServerDefinition,
    ServerStatus,
)


class Iec104BackendPort(Protocol):
    """IEC104 worker 依赖的最小 backend 接口。"""

    def load_points(self, definition: ServerDefinition) -> None: ...

    def connect(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]: ...

    def point_state(self, point: int | str) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...


class Iec104Server:
    """一个 IEC104 connection 对应的 Starfish worker。"""

    def __init__(
        self,
        definition: ServerDefinition | pd.DataFrame,
        *,
        backend: Iec104BackendPort | None = None,
    ) -> None:
        """初始化 IEC104 server worker。

        Args:
            definition: 单 connection 公共配置帧，或协议级调用直接提供的 definition。
            backend: 测试可注入的 backend；未传入时创建 c104 backend。
        """
        runtime_definition = (
            _definition_from_configuration(definition)
            if isinstance(definition, pd.DataFrame)
            else definition
        )
        if runtime_definition.protocol != "IEC104":
            raise ValueError(
                "Iec104Server 只能接收 IEC104 definition: "
                f"{runtime_definition.protocol}"
            )
        self._definition = runtime_definition
        self._backend = backend or Iec104Backend()
        self._initialized = False
        self._started = False

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""
        return self._definition

    @property
    def backend(self) -> Iec104BackendPort:
        """返回注入的 backend，供测试验证 wiring。"""
        return self._backend

    def init(self) -> None:
        """加载点位并执行 backend 预连接；重复调用安全。"""
        if self._initialized:
            return
        self._backend.load_points(self._definition)
        self._backend.connect()
        self._initialized = True

    def start(self) -> None:
        """启动 IEC104 backend；未 init 时会先 init。"""
        if self._started:
            return
        self.init()
        self._backend.start()
        self._started = True

    def stop(self) -> None:
        """停止 IEC104 backend。"""
        try:
            self._backend.stop()
        finally:
            self._started = False

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        """更新受控站数据源值，并可按 view 配置触发自发上送。"""
        self.init()
        return self._backend.update_point(
            point,
            value,
            transmit_spontaneous=transmit_spontaneous,
            quality=quality,
            recorded_at=recorded_at,
        )

    def point_state(self, point: int | str) -> dict[str, Any]:
        """读取 adapter 保存的 Point 值与发送时间状态。"""
        self.init()
        return self._backend.point_state(point)

    def status(self) -> ServerStatus:
        """返回 IEC104 server 当前运行状态。"""
        health = self._backend.health()
        reason = health.get("reason")
        return ServerStatus(
            connection_id=self._definition.connection_id,
            protocol=self._definition.protocol,
            status=str(health.get("status") or "unknown"),
            mode=str(health.get("mode") or "unknown"),
            running=bool(health.get("running")),
            point_count=int(
                health.get("point_count") or len(self._definition.point_items)
            ),
            reason=str(reason) if reason else None,
            detail=_health_detail(health),
        )


def _health_detail(health: dict[str, Any]) -> dict[str, Any]:
    """过滤核心字段外的 backend health 细节。"""
    excluded = {"status", "mode", "running", "point_count", "reason"}
    return {key: value for key, value in health.items() if key not in excluded}


def _definition_from_configuration(configuration: pd.DataFrame) -> ServerDefinition:
    """在 c104 创建边界把单 connection 配置组转换为 runtime definition。

    Args:
        configuration: IEC104 loader 产生的一行一个 point DataFrame。

    Returns:
        不含 pandas 对象、可由 backend 持有的原生 definition。

    Raises:
        ValueError: 配置为空或混入多个 connection。
    """
    if configuration.empty:
        raise ValueError("IEC104 worker 配置不能为空")
    connection_ids = configuration["connection_id"].drop_duplicates()
    if len(connection_ids) != 1:
        raise ValueError(
            f"IEC104 worker 配置必须只有一个 connection: {connection_ids.tolist()}"
        )
    first = configuration.iloc[0]
    connection_id = int(first["connection_id"])
    points = tuple(
        _point_from_configuration(row) for _index, row in configuration.iterrows()
    )
    host = str(first["bind_host"])
    port = int(first["bind_port"])
    return ServerDefinition(
        connection_id=connection_id,
        name=str(first["name"]),
        protocol="IEC104",
        bind_host=host,
        bind_port=port,
        connection_params={
            "host": host,
            "port": port,
            "listen_host": host,
            "listen_port": port,
            "reconnect_enabled": bool(_optional(first, "reconnect_enabled")),
            "reconnect_interval_ms": _integer(
                first, "reconnect_interval_ms", default=0
            ),
            **{
                key: _integer(first, key)
                for key in ("t0_ms", "t1_ms", "t2_ms", "t3_ms", "k_value", "w_value")
            },
        },
        point_items=points,
        capabilities=_point_capabilities(points),
        metadata={
            "interface_id": _optional(first, "interface_id"),
            "interface_type": _optional(first, "interface_type"),
            "equipment_id": _optional(first, "equipment_id"),
            "source_point_table_ids": tuple(
                int(value)
                for value in configuration["point_table_id"]
                .dropna()
                .drop_duplicates()
                .tolist()
            ),
        },
        station_role=str(first["station_role"]),
    )


def _point_from_configuration(row: pd.Series) -> PointItemDefinition:
    """把一个 IEC104 point 配置行转换为 backend 点定义。"""
    interval = _integer(row, "periodic_interval_ms", default=0)
    return PointItemDefinition(
        point_item_id=int(row["point_item_id"]),
        point_identifier=str(row["point_identifier"]),
        semantic_name=str(row["semantic_name"]),
        data_type=str(row["data_type"]),
        type_id=str(row["type_id"]),
        io_address=int(row["io_address"]),
        initial_value=_optional(row, "initial_value"),
        metadata={
            "point_table_id": int(row["point_table_id"]),
            "sort_order": _integer(row, "sort_order", default=0),
            "common_address": _integer(row, "common_address"),
            "type_id_value": _integer(row, "iec104_type_id"),
            "business_semantic_identifier": _optional(
                row, "business_semantic_identifier"
            ),
            "business_semantic_name_zh": _optional(row, "business_semantic_name_zh"),
            "physical_quantity_category": _optional(row, "physical_quantity_category"),
            "unit": _optional(row, "unit"),
            "scale_factor": _optional(row, "scale_factor"),
            "offset_value": _optional(row, "offset_value"),
            "value_min": _optional(row, "value_min"),
            "value_max": _optional(row, "value_max"),
            "allowed_values": _optional(row, "allowed_values"),
            "value_update_mode": _optional(row, "value_update_mode"),
            "value_update_interval_ms": _optional(row, "value_update_interval_ms"),
            "point_registration_supported": True,
            "general_interrogation_supported": bool(
                _optional(row, "general_interrogation_enabled")
            ),
            "general_interrogation_group": _optional(
                row, "general_interrogation_group"
            ),
            "counter_interrogation_supported": bool(
                _optional(row, "counter_interrogation_enabled")
            ),
            "periodic_transmission_supported": bool(
                _optional(row, "periodic_transmission_enabled")
            ),
            "report_ms": interval,
            "spontaneous_transmission_supported": bool(
                _optional(row, "spontaneous_transmission_enabled")
            ),
            "spontaneous_deadband": float(str(_optional(row, "deadband") or 0)),
            "spontaneous_min_interval_ms": 0,
            "background_transmission_supported": bool(
                _optional(row, "background_transmission_enabled")
            ),
            "quality_descriptor_enabled": bool(_optional(row, "quality_enabled")),
            "time_tag_type": "NONE",
            "command_mode": "DIRECT",
        },
    )


def _point_capabilities(
    points: tuple[PointItemDefinition, ...],
) -> tuple[str, ...]:
    """直接从 point 元数据汇总 server 能力声明，不构造任务对象。"""
    specs = (
        ("IEC104_RESPOND_GENERAL_INTERROGATION", "general_interrogation_supported"),
        ("IEC104_RESPOND_COUNTER_INTERROGATION", "counter_interrogation_supported"),
        ("IEC104_SEND_CYCLIC_DATA", "periodic_transmission_supported"),
        ("IEC104_SEND_SPONTANEOUS_DATA", "spontaneous_transmission_supported"),
        ("IEC104_SEND_BACKGROUND_DATA", "background_transmission_supported"),
    )
    enabled = {
        operation
        for operation, flag in specs
        if any(bool(point.metadata.get(flag)) for point in points)
    }
    return (
        "IEC104_SOURCE_SIMULATOR",
        "IEC104_RESPOND_READ_COMMAND",
        *sorted(enabled),
    )


def _optional(row: pd.Series, key: str) -> object | None:
    """把协议边界单元格的 pandas 缺失值恢复为 ``None``。"""
    value = row.get(key)
    if value is None or value is pd.NA:
        return None
    missing = pd.isna(value)
    if not hasattr(missing, "__len__") and bool(missing):
        return None
    return cast(object, value)


def _integer(row: pd.Series, key: str, *, default: int | None = None) -> int:
    """在原生边界把已由 view 提供的数值单元格转换为整数。"""
    value = _optional(row, key)
    if value is None:
        if default is None:
            raise ValueError(f"IEC104 配置缺少 {key}")
        return default
    return int(float(str(value)))


__all__ = ["Iec104Server"]
