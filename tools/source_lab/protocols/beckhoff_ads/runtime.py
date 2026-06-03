"""Beckhoff ADS source_lab 工具层运行时。

本模块只为 source_lab 提供 `backend_kind=in_process` 的开发/测试用 ADS
simulator 内存态，不进入 `src/whale/shared/source` 或 `src/whale/ingest`
生产路径，也不应被表述为真实 Beckhoff ADS 协议服务端证据。
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic

from tools.source_lab.model import SimulatedPoint, SimulatedSource

_ADS_DATA_TYPE_SIZES: dict[str, int] = {
    "BOOL": 1,
    "INT": 2,
    "DINT": 4,
    "REAL": 4,
    "LREAL": 8,
}


class AdsRuntimeError(RuntimeError):
    """ADS tool runtime 的公共错误基类。"""


class AdsValidationError(AdsRuntimeError):
    """ADS 点位/端点配置不合法。"""


class AdsRuntimeUnavailableError(AdsRuntimeError):
    """ADS simulator 尚未启动或已清理。"""


@dataclass(frozen=True, slots=True)
class AdsPointDescriptor:
    """单个 ADS 点位的寻址与类型描述。"""

    point_key: str
    symbol_name: str
    index_group: int
    index_offset: int
    data_size: int
    ads_data_type: str


@dataclass(slots=True)
class AdsPointState:
    """单个 ADS 点位的当前值。"""

    descriptor: AdsPointDescriptor
    value: str | int | float | bool | None


@dataclass(slots=True)
class AdsServerState:
    """一个 ADS simulator 实例的运行态快照。"""

    source_name: str
    host: str
    router_port: int
    ams_net_id: str
    ads_server_port: int
    started_at_s: float
    point_states_by_key: dict[str, AdsPointState]
    point_keys_by_symbol: dict[str, str]
    point_keys_by_index: dict[tuple[int, int], str]


def _runtime_key(
    *,
    host: str,
    router_port: int,
    ams_net_id: str,
    ads_server_port: int,
) -> tuple[str, int, str, int]:
    return (host, router_port, ams_net_id, ads_server_port)


def _coerce_value(value: str | int | float | bool | None, ads_data_type: str) -> str | int | float | bool | None:
    """按 ADS 数据类型把值规范到稳定 Python 标量。"""

    normalized = ads_data_type.upper()
    if value is None:
        return None
    if normalized == "BOOL":
        return bool(value)
    if normalized in {"INT", "DINT"}:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    if normalized in {"REAL", "LREAL"}:
        return float(value)
    if normalized == "STRING":
        return str(value)
    raise AdsValidationError(f"unsupported ADS data type: {ads_data_type}")


def _validate_descriptor(point: SimulatedPoint) -> AdsPointDescriptor:
    """从统一点位模型恢复 ADS 寻址。"""

    params = point.protocol_params
    symbol_name = str(params.get("symbol_name", "")).strip()
    if not symbol_name:
        raise AdsValidationError(f"{point.key}: missing symbol_name")

    try:
        index_group = int(params["index_group"])
        index_offset = int(params["index_offset"])
        data_size = int(params["data_size"])
    except KeyError as exc:
        raise AdsValidationError(f"{point.key}: missing ADS address param {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise AdsValidationError(f"{point.key}: invalid ADS numeric param: {exc}") from exc

    if index_group < 0:
        raise AdsValidationError(f"{point.key}: invalid index_group={index_group}")
    if index_offset < 0:
        raise AdsValidationError(f"{point.key}: invalid index_offset={index_offset}")
    if data_size <= 0:
        raise AdsValidationError(f"{point.key}: invalid data_size={data_size}")

    ads_data_type = str(params.get("ads_data_type", "")).upper()
    if not ads_data_type:
        raise AdsValidationError(f"{point.key}: missing ads_data_type")

    if ads_data_type in _ADS_DATA_TYPE_SIZES:
        expected_size = _ADS_DATA_TYPE_SIZES[ads_data_type]
        if data_size != expected_size:
            raise AdsValidationError(
                f"{point.key}: invalid data_size={data_size} for ads_data_type={ads_data_type}, "
                f"expected={expected_size}"
            )
    elif ads_data_type == "STRING":
        if data_size < 2:
            raise AdsValidationError(f"{point.key}: STRING data_size must be >= 2, got {data_size}")
    else:
        raise AdsValidationError(f"{point.key}: unsupported ads_data_type={ads_data_type}")

    return AdsPointDescriptor(
        point_key=point.key,
        symbol_name=symbol_name,
        index_group=index_group,
        index_offset=index_offset,
        data_size=data_size,
        ads_data_type=ads_data_type,
    )


class AdsSimulatorRegistry:
    """source_lab ADS simulator 的进程内注册表。

    它只模拟 tool runtime 的寻址、读写和 readback 语义，不生成真实 ADS
    报文，也不替代 Round 22 需要补齐的 Beckhoff virtual server/client 证据。
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._servers: dict[tuple[str, int, str, int], AdsServerState] = {}

    def register(self, source: SimulatedSource) -> AdsServerState:
        """注册一个已启动的 ADS simulator 实例。"""

        host = source.connection.host
        router_port = int(source.connection.port or 0)
        ams_net_id = str(source.connection.params.get("ams_net_id", "")).strip()
        ads_server_port = int(source.connection.params.get("ads_server_port", 0))

        if not host:
            raise AdsValidationError("ADS source host is empty")
        if router_port <= 0:
            raise AdsValidationError(f"invalid ADS router port: {router_port}")
        if not ams_net_id:
            raise AdsValidationError("missing ADS ams_net_id")
        if ads_server_port <= 0:
            raise AdsValidationError(f"invalid ADS server port: {ads_server_port}")

        point_states_by_key: dict[str, AdsPointState] = {}
        point_keys_by_symbol: dict[str, str] = {}
        point_keys_by_index: dict[tuple[int, int], str] = {}

        for point in source.points:
            descriptor = _validate_descriptor(point)
            symbol_key = descriptor.symbol_name
            index_key = (descriptor.index_group, descriptor.index_offset)
            if symbol_key in point_keys_by_symbol:
                raise AdsValidationError(f"duplicate ADS symbol_name: {symbol_key}")
            if index_key in point_keys_by_index:
                raise AdsValidationError(
                    "duplicate ADS index address: "
                    f"index_group={descriptor.index_group}, index_offset={descriptor.index_offset}"
                )
            point_state = AdsPointState(
                descriptor=descriptor,
                value=_coerce_value(point.initial_value, descriptor.ads_data_type),
            )
            point_states_by_key[point.key] = point_state
            point_keys_by_symbol[symbol_key] = point.key
            point_keys_by_index[index_key] = point.key

        server = AdsServerState(
            source_name=source.connection.name,
            host=host,
            router_port=router_port,
            ams_net_id=ams_net_id,
            ads_server_port=ads_server_port,
            started_at_s=monotonic(),
            point_states_by_key=point_states_by_key,
            point_keys_by_symbol=point_keys_by_symbol,
            point_keys_by_index=point_keys_by_index,
        )
        with self._lock:
            self._servers[_runtime_key(
                host=host,
                router_port=router_port,
                ams_net_id=ams_net_id,
                ads_server_port=ads_server_port,
            )] = server
        return server

    def unregister(self, source: SimulatedSource) -> None:
        """注销一个 ADS simulator。"""

        with self._lock:
            self._servers.pop(
                _runtime_key(
                    host=source.connection.host,
                    router_port=int(source.connection.port or 0),
                    ams_net_id=str(source.connection.params.get("ams_net_id", "")),
                    ads_server_port=int(source.connection.params.get("ads_server_port", 0)),
                ),
                None,
            )

    def get(self, source: SimulatedSource) -> AdsServerState:
        """按运行时 source 取 ADS server。"""

        key = _runtime_key(
            host=source.connection.host,
            router_port=int(source.connection.port or 0),
            ams_net_id=str(source.connection.params.get("ams_net_id", "")),
            ads_server_port=int(source.connection.params.get("ads_server_port", 0)),
        )
        with self._lock:
            server = self._servers.get(key)
        if server is None:
            raise AdsRuntimeUnavailableError(
                "ADS simulator runtime not started: "
                f"host={key[0]}, router_port={key[1]}, ams_net_id={key[2]}, ads_server_port={key[3]}"
            )
        return server

    def read(
        self,
        source: SimulatedSource,
        point_keys: list[str] | None = None,
    ) -> dict[str, str | int | float | bool | None]:
        """从 ADS simulator 中读取当前点值。"""

        server = self.get(source)
        selected_keys = point_keys or list(server.point_states_by_key.keys())
        values: dict[str, str | int | float | bool | None] = {}
        for key in selected_keys:
            state = server.point_states_by_key.get(key)
            if state is None:
                continue
            values[key] = state.value
        return values

    def write(
        self,
        source: SimulatedSource,
        values: dict[str, str | int | float | bool | None],
    ) -> tuple[dict[str, str | int | float | bool | None], list[str]]:
        """写入 ADS simulator 并返回 readback 结果。"""

        server = self.get(source)
        readback: dict[str, str | int | float | bool | None] = {}
        errors: list[str] = []
        for key, value in values.items():
            state = server.point_states_by_key.get(key)
            if state is None:
                errors.append(f"point not found: {key}")
                continue
            try:
                coerced = _coerce_value(value, state.descriptor.ads_data_type)
            except (TypeError, ValueError, AdsValidationError) as exc:
                errors.append(f"{key}: {exc}")
                continue
            state.value = coerced
            readback[key] = coerced
        return readback, errors

    def update_values(
        self,
        source: SimulatedSource,
        values: dict[str, str | int | float | bool | None],
    ) -> list[str]:
        """直接覆盖 simulator 内存值。"""

        _, errors = self.write(source, values)
        return errors


ADS_SIMULATOR_REGISTRY = AdsSimulatorRegistry()


__all__ = [
    "ADS_SIMULATOR_REGISTRY",
    "AdsPointDescriptor",
    "AdsRuntimeError",
    "AdsRuntimeUnavailableError",
    "AdsServerState",
    "AdsValidationError",
]
