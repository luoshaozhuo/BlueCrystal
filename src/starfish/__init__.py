"""starfish — 多协议 server simulator 工具层。

starfish 是 Whale 平台的协议 server 模拟运行时，负责根据 Seahorse 导出的
starfish_server_plan.json 契约文件启动多协议模拟服务端，供平台调试、联调和
数字孪生前置验证使用。

架构分层：
- models: Starfish 侧最小数据模型，镜像 Seahorse JSON 契约。
- loader: ServerPlan JSON 加载器，读入并校验契约文件。
- facade: 协议 server 模拟门面（in-memory stub / simulator）。
- registry: 运行时注册表，根据协议名创建对应 facade。
- protocols: 协议编解码器骨架（ASDU/COT/IOA/CA 等协议级编解码）。
- tools: 轻量诊断工具（probe / profile / capacity）。

架构隔离（硬边界）：
- starfish 不得 import seahorse。
- starfish 不得 import whale.ingest。
- starfish 不得 import whale.shared.source。
- starfish 与 Seahorse 的交互仅通过读入纯 JSON 文件完成。
- starfish 不进入 Whale 生产采集链路，所有数据标识 synthetic=True。

当前能力声明（Round 14 更新）：
- SF-FR-001: JSON 契约加载与校验（loader）。
- SF-FR-002: in-memory/local stub simulator facade（ServerSimulatorFacade, fallback）。
- SF-FR-003: HTTP REST 真实 server（ThreadingHTTPServer, GET /points）。
- SF-FR-004: Modbus TCP 真实 server（socket, FC03/FC06）。
- SF-FR-005: MQTT 轻量级端点（TCP JSON 行协议, subscribe 轮询队列）。
- SF-FR-006: OPC UA 门面（open62541 C runner 子进程，real/unavailable 模式）。
- SF-FR-007: IEC104 门面（iec104_simulator_server C runner 子进程，real/unavailable 模式）。
- SF-FR-008: IEC61850 MMS 门面（iec61850_simulator_server C runner 子进程，real/unavailable 模式）。
- SF-FR-009: IEC61850 Report 门面（iec61850_simulator_server + iec61850_report_runner C runner 子进程，real/report-lightweight 模式；ReportQueue 事件队列）。
- SF-FR-010: CLI load-server-plan 子命令。
- SF-FR-011: CLI smoke-server-plan 子命令。
- SF-FR-012: CLI probe-server-plan 子命令。
- SF-FR-013: CLI profile-server-plan 子命令。
- SF-FR-014: CLI capacity-server-plan 子命令。
- SF-FR-015: MODBUS_RTU rtu-lightweight FC01-FC06/FC15/FC16 + 四数据区模型（Round 14）。
- SF-FR-016: IEC101 编解码器骨架（TypeId/COT/ASDUHeader/IOA/CA，codec-skeleton 模式，Round 14）。
- SF-FR-020: IEC101 server simulator facade（codec-skeleton stub，ASDU/COT/IOA/CA 编解码就绪）。
- SF-FR-021: MODBUS_RTU server simulator facade（rtu-lightweight/codebase-pending，FC01-FC06/FC15/FC16）。
- SF-FR-022: Beckhoff ADS server simulator facade（codebase-pending stub，.NET/TwinCAT runtime 未就绪）。
- SF-FR-023: GOOSE server simulator facade（environment-pending stub，L2 veth 网络未就绪）。
- SF-FR-024: SV server simulator facade（environment-pending stub，L2 veth + PTP 时间同步未就绪）。
- actual runtime availability: HTTP_REST 和 MODBUS_TCP 为 real mode，
  MQTT 为 mqtt-lightweight mode，
  OPC_UA / IEC104 / IEC61850_MMS 为 real mode（native binary 可用时）或 unavailable mode（binary 缺失时），
  IEC61850_REPORT 为 real mode（native binary 可用时）或 report-lightweight mode（binary 缺失时），
  MODBUS_RTU 为 rtu-lightweight mode（PTY 可用时）或 codebase-pending mode（PTY 不可用时），
  IEC101 为 codec-skeleton mode（编解码器骨架就绪），
  BECKHOFF_ADS 为 codebase-pending mode（实现未就绪），
  GOOSE / SV 为 environment-pending mode（运行环境未就绪）。
- NOT_IMPLEMENTED: write/subscribe/report（OpcUaFacade、Iec104Facade、Iec61850MmsFacade）；
  write/report（MqttFacade）；subscribe/report（HTTP_REST、Modbus TCP）；
  read/write/subscribe（Iec61850ReportFacade，report 已实现）；
  write/subscribe/report（Iec101Facade、AdsFacade）；
  subscribe/report（ModbusRtuFacade）；
  write/subscribe/report（GooseFacade、SvFacade）。
- codebase-pending: Beckhoff ADS 真实 server 启动。
- codec-skeleton: IEC101 编解码器骨架就绪（不等同完整 server）。
- environment-pending: GOOSE / SV 二层协议（需 L2 veth 环境和 raw socket / CAP_NET_RAW）。
- 新增：protocols 编解码器子包（IEC101 ASDU/COT/IOA/CA 编解码）。

安全边界：
- 不连接生产数据库。
- 不调用 whale.ingest / whale.message_pipeline / whale.speed_layer / whale.storage。
- 不 import seahorse Python 模块。
- 所有数据标注 synthetic，不得写成真实现场验证。
"""

from __future__ import annotations
