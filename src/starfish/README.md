# Starfish

Starfish 是协议数据源 simulator 的运行时管理模块。当前实现采用 Hexagonal
Architecture，并在 core 内使用 Supervisor/Worker 模式管理多个 connection。
依赖装配集中在 `starfish.composition`，不再保留单独的 API facade 层。

## CLI

数据库连接由 `WHALE_DB_URL` 提供：

```bash
python -m starfish run -id 1001
python -m starfish run -a
```

Starfish IEC104 的受支持运行环境为 CPython 3.13，并需显式安装可选依赖：

```bash
pip install -e ".[dev,iec104]"
```

当前固定 `c104==2.2.1`，PyPI 提供 CPython 3.13 wheel。`c104` 和其
lib60870-C 依赖采用 GPLv3；它不是 BlueCrystal 核心依赖，分发包含该 extra 的
环境或镜像前必须完成 GPLv3 合规审查。

`-id` 按 `connection_id` 启动一个 simulator，`-a` 选择 DB view 中全部
connection，两者必须且只能选择一个。Starfish 会先读取每个 connection 的
protocol，再调用对应协议 loader；当前只注册 IEC104，其他协议会明确报错。

## 数据来源

Starfish 从以下 Whale 执行视图构建 IEC104 受控站或控制站：

- `vw_connection_object_full`
- `vw_task_full`
- `vw_task_point_item`
- connection 中登记的协议 point item view

IEC104 adapter 延迟加载项目采用的 `c104` Python 扩展。受控站通过
`Iec104Server.update_point()` 更新模拟数据源；View task 声明 connection
能力，Point 参数控制周期、自发等发送条件；控制站通过
`Iec104Server.execute_task()` 发起召唤、读、时钟同步及控制命令。Starfish
不写 Whale 基础表，运行装配只依赖上述 view。

## IEC104 功能

| 角色 | 当前支持的 View operation |
|---|---|
| `CONTROLLED_STATION` | 响应站总召、一般累计量召唤和单点读；周期、自发、背景上送；接收单点、双点、设点命令和时钟同步 |
| `CONTROLLING_STATION` | 接收监视数据；发送站总召、一般累计量召唤、单点读、时钟同步、单点命令、双点命令和设点命令 |

受控站的站总召、一般累计量召唤和单点读响应由 `iec104-python` 内置
handler 完成；周期传输使用 Point 的 `report_ms`，自发传输由
`update_point()` 按死区和最小间隔触发，背景传输由 adapter 调度。
`point_state()` 返回当前值、质量、协议时标以及 `updated_at`、
`changed_at`、`last_sent_at` 等进程内状态。

当前 `c104` 没有逐 Point 的“参与站总召/组召”注册开关。View task 成员用于
能力声明和主动任务范围；受控站内建站总召会处理已注册的相应监视方向 Point，
不能把 task 成员误解为内建总召 handler 的逐点过滤条件。

当前边界：

- 不支持组召、组累计量召唤以及累计量冻结/复位。
- 不注册当前 `iec104-python` 不支持的 CP24Time2a Point。
- `c104` 是 IEC104 runtime 的延迟依赖；没有可导入且二进制兼容的扩展时，
  IEC104 connection 在装配阶段明确失败，但不阻断 Starfish 其他模块导入。
- `execute_task()` 使用 task deadline 和有限重试，但同步 `c104` 调用进入后
  adapter 无法精确取消，只能在调用返回后判定是否已经超时。
- 背景发送线程若未在停止期限内结束，`stop()` 报错，health 保持
  `shutdown_incomplete`，直到该线程真实退出。

BlueCrystal 验证环境使用 CPython 3.13.14 和 `c104==2.2.1` 的 CPython
3.13 native wheel。真实网络 integration test 使用纯 Starfish View-shaped
definitions，在未设置 `WHALE_DB_URL` 时通过，不依赖 PostgreSQL 样例数据，
覆盖 TCP/STARTDT、站总召、一般累计量召唤、单点读、周期/自发/背景上送、
时钟同步及三类控制命令。View loader 由独立内存契约测试覆盖，AST 门禁确认
Starfish 生产代码和专属测试对其他业务 Python 包的 import 为零；该结论不
外推到真实数据库部署状态或组召等未实现功能。

详细边界见 [ARCHITECTURE.md](ARCHITECTURE.md)。
