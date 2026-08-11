"""ADS pandas 配置到 AMS/TCP runtime 的 worker 边界。

单 connection DataFrame 在此转换为 backend 必需的原生 definition；socket、线程、
session、notification handle 与可变点值仍完全由原生 backend 结构管理。
"""

from __future__ import annotations

from typing import Protocol, cast

import pandas as pd

from starfish.adapters.protocols.ads.backend import AdsTcpBackend
from starfish.core.definitions import (
    PointItemDefinition,
    ServerDefinition,
    ServerStatus,
)


class AdsBackendPort(Protocol):
    """ADS worker 依赖的最小 backend port。"""

    def load_points(self, definition: ServerDefinition) -> None:
        """校验并保存 view 映射完成的 ADS Source definition。

        Args:
            definition: 不含数据库对象的 core server definition。

        Raises:
            AdsOperationError: definition 角色、地址或数据类型不受支持。
        """

    def connect(self) -> None:
        """绑定 definition endpoint，但不启动 accept loop。

        Raises:
            AdsOperationError: endpoint 绑定失败或 definition 尚未加载。
        """

    def start(self) -> None:
        """启动 socket 与 notification workers；重复调用安全。

        Raises:
            AdsOperationError: socket 资源无法创建。
        """

    def stop(self) -> None:
        """停止 workers 并释放 client、symbol 与 notification handles。

        Raises:
            AdsOperationError: 线程未能在停止期限内退出。
        """

    def update_point(self, point: int | str, value: object) -> dict[str, object]:
        """更新 Source 点并触发符合 view 语义的 ON_CHANGE 通知。

        Args:
            point: point item ID 或 ADS symbol。
            value: 与 ADS 数据类型兼容的新值。

        Returns:
            更新后的稳定点状态。

        Raises:
            AdsOperationError: 点不存在或值不能按 ADS 类型编码。
        """

    def point_state(self, point: int | str) -> dict[str, object]:
        """读取 Source 点状态。

        Args:
            point: point item ID 或 ADS symbol。

        Returns:
            不暴露 socket/native handle 的状态字典。

        Raises:
            AdsOperationError: 点不存在。
        """

    def health(self) -> dict[str, object]:
        """返回 socket、client 与 notification 生命周期摘要。

        Returns:
            manager 可消费的健康状态字典。
        """


class AdsServer:
    """一个 ADS SERVER connection 对应的 Starfish worker。"""

    def __init__(
        self,
        definition: ServerDefinition | pd.DataFrame,
        *,
        backend: AdsBackendPort | None = None,
    ) -> None:
        """保存 definition 并延迟创建 socket 资源。

        Args:
            definition: 单 connection 公共配置帧，或协议级调用直接提供的 definition。
            backend: 可选 backend port；生产默认使用 AMS/TCP backend。

        Raises:
            ValueError: definition 不是 ADS 协议。
        """
        runtime_definition = (
            _definition_from_configuration(definition)
            if isinstance(definition, pd.DataFrame)
            else definition
        )
        if runtime_definition.protocol != "ADS":
            raise ValueError(
                f"AdsServer 只能接收 ADS definition: {runtime_definition.protocol}"
            )
        self._definition = runtime_definition
        self._backend = backend or AdsTcpBackend()
        self._initialized = False

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 的 core definition。

        Returns:
            loader 映射完成的不可变 definition。
        """
        return self._definition

    def init(self) -> None:
        """加载点位并绑定 endpoint；重复调用安全。

        Raises:
            AdsOperationError: definition 或 endpoint 不满足运行契约。
        """
        if self._initialized:
            return
        self._backend.load_points(self._definition)
        self._backend.connect()
        self._initialized = True

    def start(self) -> None:
        """启动 ADS server；未初始化时自动初始化。

        Raises:
            AdsOperationError: socket 或 worker 启动失败。
        """
        self.init()
        self._backend.start()

    def stop(self) -> None:
        """停止 ADS server 并释放 socket、client threads 与 handles。

        Raises:
            AdsOperationError: worker 未能在停止期限内退出。
        """
        self._backend.stop()

    def update_point(self, point: int | str, value: object) -> dict[str, object]:
        """更新 simulator Source 值。

        Args:
            point: point item ID 或 ADS symbol。
            value: 与 view ``ads_data_type`` 兼容的新值。

        Returns:
            更新后的稳定点状态。

        Raises:
            AdsOperationError: 点不存在或值类型不兼容。
        """
        self.init()
        return self._backend.update_point(point, value)

    def point_state(self, point: int | str) -> dict[str, object]:
        """读取进程内 Source 点值快照。

        Args:
            point: point item ID 或 ADS symbol。

        Returns:
            不包含 socket/native handle 的点状态。

        Raises:
            AdsOperationError: 点不存在。
        """
        self.init()
        return self._backend.point_state(point)

    def status(self) -> ServerStatus:
        """返回 manager 使用的 ADS 生命周期状态。

        Returns:
            core ``ServerStatus`` 快照。
        """
        health = self._backend.health()
        raw_point_count = health.get("point_count")
        point_count = (
            raw_point_count
            if isinstance(raw_point_count, int)
            else len(self._definition.point_items)
        )
        return ServerStatus(
            connection_id=self._definition.connection_id,
            protocol="ADS",
            status=str(health.get("status") or "unknown"),
            mode=str(health.get("mode") or "unknown"),
            running=bool(health.get("running")),
            point_count=point_count,
            detail={
                key: value
                for key, value in health.items()
                if key not in {"status", "mode", "running", "point_count", "reason"}
            },
        )


def _definition_from_configuration(configuration: pd.DataFrame) -> ServerDefinition:
    """在 AMS/TCP 创建边界把单 connection 配置组转为 runtime definition。

    Args:
        configuration: ADS loader 产生的一行一个 point DataFrame。

    Returns:
        不含 pandas 对象、可由 backend 持有的原生 definition。

    Raises:
        ValueError: 配置为空或混入多个 connection。
    """
    if configuration.empty:
        raise ValueError("ADS worker 配置不能为空")
    connection_ids = configuration["connection_id"].drop_duplicates()
    if len(connection_ids) != 1:
        raise ValueError(
            f"ADS worker 配置必须只有一个 connection: {connection_ids.tolist()}"
        )
    first = configuration.iloc[0]
    connection_id = int(first["connection_id"])
    host = str(first["bind_host"])
    port = int(first["bind_port"])
    return ServerDefinition(
        connection_id=connection_id,
        name=str(first["name"]),
        protocol="ADS",
        bind_host=host,
        bind_port=port,
        connection_params={
            "host": host,
            "port": port,
            "ams_net_id": str(first["ams_net_id"]),
            "ams_port": _integer(first, "ams_port"),
            "reconnect_enabled": bool(_optional(first, "reconnect_enabled")),
            "reconnect_interval_ms": _integer(
                first, "reconnect_interval_ms", default=0
            ),
        },
        point_items=tuple(
            _point_from_configuration(row) for _index, row in configuration.iterrows()
        ),
        capabilities=("ADS_SOURCE_SIMULATOR", "ADS_SYMBOL_READ"),
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
    """把一个 ADS point 配置行转换为 backend 点定义。"""
    return PointItemDefinition(
        point_item_id=int(row["point_item_id"]),
        point_identifier=str(row["point_identifier"]),
        semantic_name=str(row["semantic_name"]),
        data_type=str(row["data_type"]),
        type_id=str(row["type_id"]),
        io_address=str(row["io_address"]),
        initial_value=_optional(row, "initial_value"),
        metadata={
            key: _optional(row, key)
            for key in (
                "point_table_id",
                "sort_order",
                "business_semantic_identifier",
                "business_semantic_name_zh",
                "physical_quantity_category",
                "unit",
                "scale_factor",
                "offset_value",
                "value_min",
                "value_max",
                "allowed_values",
                "value_update_mode",
                "value_update_interval_ms",
                "addressing_mode",
                "symbol_name",
                "index_group",
                "index_offset",
                "notification_mode",
                "cycle_time_ms",
                "max_delay_ms",
            )
        },
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
            raise ValueError(f"ADS 配置缺少 {key}")
        return default
    return int(float(str(value)))


__all__ = ["AdsServer"]
