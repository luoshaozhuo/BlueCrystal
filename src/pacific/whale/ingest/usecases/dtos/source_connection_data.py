"""采集连接 DTO。

这个对象只保存最基础的连接事实，不负责派生 protocol endpoint：

- application_protocol：应用层协议，如 `opcua`
- transport：传输层协议，如 `tcp`
- host / port：目标地址
- ied / ld / path_prefix：设备与逻辑设备上下文
- namespace_uri：命名空间信息，适用于 OPC UA 等协议
- 安全 / 认证信息：与 `scada_communication_endpoint` 对齐
- params：协议专属扩展字段

真正的 endpoint 组装职责应下沉到 adapter 或 shared 协议边界。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SourceConnectionData:
    """描述一个 source 的基础连接信息。"""

    host: str
    port: int
    ied_name: str
    ld_name: str
    namespace_uri: str
    security_policy: str | None = None
    security_mode: str | None = None
    auth_type: str | None = None
    credential_ref: str | None = None
    params: dict[str, str | int | float | bool] = field(default_factory=dict)
