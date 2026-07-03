# Clean Architecture Blueprint & Codex Constraint Specification

版本：4.2  
适用语言：Python 3.10+  
CLI 规范：统一使用 Typer。  
目标：易读、稳定、可约束 Coding Agent、适用于一般中大型 Python 工程。  
核心取向：**输入侧由 `__main__.py` 承载 Typer 薄入口，输出侧通过 OutPort + Adapter 解耦外部系统。**

---

# 0. 总则

本规范定义 Python 工程的 Clean Architecture 目录结构、依赖方向、命名规则和 Coding Agent 执行约束。

核心目标：

1. 固定目录结构，避免随意新增 `services/`、`helpers/`、`managers/`、`common/` 等含混目录；
2. 固定依赖方向，避免 Domain / Application 直接依赖数据库、ORM、SDK、driver、framework；
3. 固定文件落位规则，避免同类职责在不同模块中漂移；
4. 固定外部能力接入方式，统一通过 `application/ports/` 抽象；
5. 固定装配位置，统一通过 `container.py` 完成 wiring；
6. 固定 CLI 输入侧入口：CLI 统一由 `__main__.py` 使用 Typer 实现，并调用 `api/` Facade；
7. 固定输出侧适配：`adapters/` 主要承载 OutPort 的适配实现或外部格式转换，不作为通用 Input Controller 目录；
8. 支持 Codex / Coding Agent 按机械规则修改项目，而不是自由发挥。

---

# 1. 约束等级

| 关键词 | 含义 |
|---|---|
| MUST / 必须 | 强制规则，违反即视为架构错误 |
| MUST NOT / 禁止 | 强制禁令，违反即视为架构错误 |
| SHOULD / 应当 | 默认规则，只有明确工程理由且不破坏依赖方向时才可偏离 |
| MAY / 可以 | 允许选项，但必须满足目录白名单和依赖规则 |
| PROFILE | 项目选择的架构形态，一旦选择即冻结对应目录结构 |

Coding Agent 必须优先满足 `MUST / MUST NOT`。  
测试失败时，禁止通过破坏架构边界来绕过失败。

---

# 2. 核心依赖方向

## 2.1 输入侧依赖方向

```text
External Actor
  ↓
__main__.py
(Typer CLI thin entry)
  ↓
API Facade / InPort
  ↓
Application UseCase / Runtime
  ↓
Domain
```

规则：

1. CLI 统一使用 Typer；
2. CLI 入口固定在 `__main__.py`；
3. `__main__.py` 可以定义 Typer app、命令、参数、帮助文本、退出码；
4. `__main__.py` 只能调用 `api/` Facade，不得直接访问 `domain/`、`application/`、`adapters/`、`infrastructure/`；
5. `__main__.py` 不应构造 Domain 模型。CLI 参数应以 primitives / Path / list / dict 等形式传给 Facade，由 Facade 负责转换为稳定 DTO 或 Domain model；
6. `api/` 下禁止放 `<package>_cli.py`、`cli.py`、`controllers.py` 等 CLI helper；
7. `adapters/` 下禁止放 CLI controller；
8. Web / RPC / Message Consumer 如果复杂，必须单独登记 Architecture Exception；但 CLI 不走该例外，CLI 一律在 `__main__.py`。

## 2.2 输出侧依赖方向

```text
Application UseCase / Runtime
  ↓
OutPort
(application/ports/<capability>_port.py)
  ↓
Output Adapter
(adapters/gateways | adapters/drivers | adapters/serializers | adapters/presenters)
  ↓
Infrastructure / External System
```

规则：

1. Application 定义 OutPort；
2. Application 依赖 OutPort 抽象；
3. Output Adapter 实现 OutPort 或完成输出格式适配；
4. Infrastructure 承载真实数据库、SDK、socket、file system、native、scheduler、driver backend；
5. Application / Domain 禁止直接依赖 Adapter / Infrastructure。

## 2.3 允许关系

```text
__main__.py        → api
api                → application
api                → domain                 # 仅 Facade 签名/转换所需；禁止把 domain 逻辑堆到 api
application        → domain
application        → application.ports
adapters           → application.ports / application DTO / domain
infrastructure     → application.ports / domain
container.py       → api / application / adapters / infrastructure / domain
```

## 2.4 禁止关系

```text
domain             → application / api / adapters / infrastructure
application        → api / adapters / infrastructure
api                → infrastructure concrete implementation
infrastructure     → adapters
adapters/drivers   → infrastructure       # strict_driver_di_profile 下禁止
__main__.py        → domain
__main__.py        → application
__main__.py        → adapters
__main__.py        → infrastructure
```

`container.py` 是唯一允许同时 import Application、Adapters、Infrastructure 的集中装配点。  
`container.py` 只能负责依赖组装，禁止承载业务规则。

---

# 3. InPort / OutPort 语义

## 3.1 InPort

InPort 是外部调用 Application 的输入边界。

Python 项目中允许三种实现方式：

| 方式 | 适用场景 | 推荐程度 |
|---|---|---|
| `api/<package>_facade.py` | 大多数模块的稳定入口 | 推荐 |
| `application/use_cases/*.py` 的 `execute()` | 内部调用、测试、简单模块 | 可用 |
| 显式 `application/ports/<xxx>_inport.py` | 大型系统、强接口约束 | 按需 |

本规范默认使用：

```text
External Actor → __main__.py Typer CLI → api Facade → Application UseCase
```

不新增 `InputAdapter`、`Controller` 或 `api/<package>_cli.py`。

## 3.2 OutPort

OutPort 是 Application 调用外部能力的输出边界。

固定位置：

```text
application/ports/<capability>_port.py
```

典型 OutPort：

```text
whale_metadata_port.py
starfish_writer_port.py
scheduler_port.py
clock_port.py
telemetry_port.py
repository_port.py
message_bus_port.py
file_store_port.py
```

规则：

1. UseCase / Runtime 只能依赖 OutPort；
2. OutPort 不能 import Adapter / Infrastructure / ORM / SDK / framework；
3. Output Adapter 或 Infrastructure 实现 OutPort；
4. 高频 I/O 必须使用 batch / buffer / stream 接口。

---

# 4. 架构 Profile

每个模块必须在 `README.md` 或 `architecture.md` 中声明一个 Profile。  
未声明 Profile 时，默认采用 `application_profile`。

## 4.1 library_profile

适用于纯算法库、纯模型库、纯领域规则库。

```text
src/<package_name>/
├── README.md
├── __init__.py
└── domain/
```

除非该库开始接入外部系统或提供运行入口，否则禁止：

```text
api/
application/
adapters/
infrastructure/
container.py
__main__.py
```

## 4.2 application_profile

适用于一般业务模块、平台服务、领域服务、CLI 工具、数据处理模块。

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py
├── container.py
├── api/
├── domain/
├── application/
├── adapters/
└── infrastructure/
```

其中 `application/` 必须固定为：

```text
application/
├── __init__.py
├── exceptions.py
├── use_cases/
├── ports/
└── runtime/
```

如果项目没有长生命周期运行态，`application/runtime/` 可以只保留空包和说明文件，但禁止改名为 `services/`、`orchestration/`、`manager/`。

## 4.3 runtime_engine_profile

适用于 daemon、调度器、执行引擎、仿真运行时、采集运行时、协议网关、设备接入模块。

在 `application_profile` 基础上，必须启用：

```text
application/runtime/
├── __init__.py
├── context.py
├── state.py
├── graph.py
├── event_bus.py
└── snapshot.py
```

可以按需增加：

```text
application/runtime/
├── engine.py
├── task_group.py
├── lifecycle.py
├── scheduler_state.py
└── diagnostics.py
```

但这些文件必须仍在 `application/runtime/` 下，禁止新建包根一级 `engine/`、`scheduler/`、`runtime_engine/`。

## 4.4 strict_driver_di_profile

适用于多协议、多 driver、native、SDK、外部 simulator、OS 进程、C/C++ 后端等强外部依赖模块。

必须启用：

```text
adapters/drivers/
├── __init__.py
├── backend_ports.py
├── factory/
└── <driver_adapter>.py

infrastructure/drivers/
├── __init__.py
├── backend_factory.py
└── <driver_backend>.py
```

规则：

1. `adapters/drivers/` 只做转换、委托和端口适配；
2. `adapters/drivers/` 禁止直接创建 socket、process、native handle、SDK client；
3. 真实 backend 只能由 `infrastructure/drivers/backend_factory.py` 或 `container.py` 创建；
4. `adapters/drivers/backend_ports.py` 是 adapter-local backend protocol，不是 application port；
5. UseCase 禁止依赖 `adapters/drivers/backend_ports.py`；
6. 如果某个文件是真实数据源、真实文件读取、真实 replay、真实 socket、真实 SDK 调用，应放入 `infrastructure/`，不得放入 `adapters/drivers/`。

---

# 5. 标准目录白名单

## 5.1 包根目录白名单

`application_profile`、`runtime_engine_profile`、`strict_driver_di_profile` 下，包根只允许：

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py
├── container.py
├── api/
├── domain/
├── application/
├── adapters/
└── infrastructure/
```

禁止在包根新增：

```text
core/
common/
utils/
helpers/
services/
service/
managers/
manager/
orchestration/
engine/
runtime/
scheduler/
clients/
repositories/
drivers/
controllers/
presentation/
cli/
```

## 5.2 `__main__.py` 定位

`__main__.py` 是输入侧 Typer CLI 薄入口。

允许：

```text
import typer
Typer app 定义
命令参数声明
参数基本合法性检查
调用 api Facade
打印输出
raise typer.Exit
```

禁止：

```text
argparse
业务规则
直接构造 domain model
直接访问 application/runtime 内部状态
直接访问 adapters
直接访问 infrastructure
直接创建 backend
直接访问 ORM/session
直接调用 driver/socket/SDK
直接操作 OutPort 实现
```

推荐调用链：

```text
__main__.py
  ↓
api/<package>_facade.py
  ↓
application/use_cases
```

## 5.3 api 白名单

```text
api/
├── __init__.py
└── <package>_facade.py
```

禁止：

```text
api/<package>_cli.py
api/cli.py
api/controllers.py
api/*_controller.py
```

规则：

1. API / Facade 是公共稳定入口；
2. CLI、Web、测试脚本、外部 SDK 消费者应调用 API / Facade；
3. API / Facade 可以调用 UseCase 或通过 `container.py` 获取运行入口；
4. API / Facade 可以接收 primitives / Path / dict / list 等 CLI 友好的参数，并在内部构造 DTO / Domain model；
5. API / Facade 禁止暴露 RuntimeContext；
6. API / Facade 禁止暴露 infrastructure exception；
7. API / Facade 不要求调用者理解内部 UseCase 拆分；
8. API / Facade 不包含具体 wiring 细节；
9. 包根 `__init__.py` 只导出稳定 Facade，不导出内部 UseCase、RuntimeContext、Port 实现。

## 5.4 domain 白名单

```text
domain/
├── __init__.py
├── exceptions.py
├── entities/
├── value_objects/
├── services/
└── protocols/
```

Domain 禁止：

```text
ORM
database session
socket
file I/O
thread
process
asyncio runtime primitive
framework
SDK client
driver object
infrastructure object
```

## 5.5 application 白名单

```text
application/
├── __init__.py
├── exceptions.py
├── use_cases/
├── ports/
└── runtime/
```

application 一级目录禁止新增：

```text
services/
service/
orchestration/
workflow/
workflows/
manager/
managers/
helper/
helpers/
common/
utils/
engine/
scheduler/
controllers/
cli/
```

## 5.6 application/use_cases 白名单

```text
application/use_cases/
├── __init__.py
├── dtos.py
├── atomic/
└── workflows/
```

允许扩展：

```text
application/use_cases/dtos/
application/use_cases/common/
```

规则：

1. 原子 UseCase 放入 `atomic/`；
2. 组合流程放入 `workflows/`；
3. DTO 放入 `dtos.py` 或 `dtos/`；
4. UseCase 类必须提供 `execute()` 方法；
5. UseCase 禁止直接 import infrastructure、adapters、framework、ORM、driver、SDK；
6. UseCase 必须通过 `application/ports/` 访问外部能力。

## 5.7 application/ports 白名单

```text
application/ports/
├── __init__.py
├── <capability>_port.py
└── types.py
```

规则：

1. Port 必须使用 `abc.ABC`、`typing.Protocol` 或等价抽象；
2. Port 只定义契约，不包含具体实现；
3. Port 必须有完整类型注解；
4. Port 禁止 import infrastructure；
5. Port 禁止 import adapters；
6. Port 禁止 import framework、ORM、driver、SDK、native binding；
7. 高频 I/O 必须优先设计 batch / buffer / stream 接口。

禁止 hot path 设计：

```python
for item in items:
    port.write_one(item)
```

推荐：

```python
port.write_batch(items)
port.write_frame(frame)
port.write_buffer(buffer)
port.read_batch(query)
```

## 5.8 application/runtime 白名单

```text
application/runtime/
├── __init__.py
├── context.py
├── state.py
├── graph.py
├── event_bus.py
└── snapshot.py
```

可选：

```text
engine.py
task_group.py
lifecycle.py
diagnostics.py
scheduler_state.py
```

规则：

1. RuntimeContext 是运行态 root object；
2. RuntimeContext 必须显式声明子组件类型；
3. 禁止使用 `kwargs`、`setattr` 动态挂载运行期对象；
4. RuntimeContext 禁止作为 API response、DTO、adapter schema；
5. runtime 禁止 import infrastructure；
6. runtime 禁止 import adapters；
7. runtime 可以维护进程内状态，但业务规则不得堆入 RuntimeContext。

## 5.9 adapters 白名单

`adapters/` 在本规范中主要表示 **Output Adapters**。

```text
adapters/
├── __init__.py
├── presenters/
├── serializers/
├── gateways/
└── drivers/
```

规则：

1. `adapters/` 不放 CLI / Web / RPC Controller；
2. `adapters/` 主要承载 OutPort 实现、输出格式适配和 driver adapter；
3. Presenter 不得包含业务规则；
4. Serializer 不得访问数据库、driver、runtime；
5. Gateway 可以实现 Application Port；
6. Adapter 不得把外部技术模型泄漏到 Application；
7. Strict Driver DI 下，`adapters/drivers/` 禁止直接 import infrastructure；
8. 真实 backend 不能放在 `adapters/`，必须放在 `infrastructure/`。

## 5.10 infrastructure 白名单

```text
infrastructure/
├── __init__.py
├── repositories/
├── file_loaders/
├── drivers/
├── native/
├── messaging/
├── data_sources/
├── schedulers/
├── telemetry/
└── web/
```

规则：

1. Infrastructure 承载所有具体技术实现；
2. Infrastructure 可以 import 第三方库、ORM、SDK、driver、native binding；
3. Infrastructure 可以实现 Application Port；
4. Infrastructure 禁止被 Domain / Application import；
5. Infrastructure 必须捕获底层异常并转换；
6. Infrastructure 不得把底层模型直接泄漏到 Application。

---

# 6. 文件落位决策表

| 目标职责 | 固定位置 |
|---|---|
| CLI / Typer 薄入口 | `__main__.py` |
| 公共稳定入口 / Facade | `api/<package>_facade.py` |
| 领域实体 | `domain/entities/` |
| 值对象 | `domain/value_objects/` |
| 纯业务规则 | `domain/services/` |
| 纯算法 | `domain/services/` |
| 纯协议帧 / 编码模型 | `domain/protocols/` |
| 原子用例 | `application/use_cases/atomic/` |
| 组合用例 / workflow | `application/use_cases/workflows/` |
| UseCase 输入输出 DTO | `application/use_cases/dtos.py` 或 `application/use_cases/dtos/` |
| 外部能力抽象 / OutPort | `application/ports/<capability>_port.py` |
| 运行态上下文 | `application/runtime/context.py` |
| 运行态状态机 | `application/runtime/state.py` |
| 执行图 / 拓扑图 | `application/runtime/graph.py` |
| 进程内事件总线 | `application/runtime/event_bus.py` |
| 运行态快照 / 诊断视图 | `application/runtime/snapshot.py` |
| 输出展示格式化 | `adapters/presenters/` |
| JSON / JSONL / YAML / CSV 转换 | `adapters/serializers/` |
| Application Port 实现外壳 | `adapters/gateways/` |
| driver adapter | `adapters/drivers/` |
| adapter-local backend protocol | `adapters/drivers/backend_ports.py` |
| 数据库实现 | `infrastructure/repositories/` |
| 文件读取实现 | `infrastructure/file_loaders/` |
| 真实 driver / SDK / socket / process backend | `infrastructure/drivers/` |
| native / FFI / binary 支撑 | `infrastructure/native/` |
| MQ / Kafka / Event Stream 客户端 | `infrastructure/messaging/` |
| 真实数据源实现 | `infrastructure/data_sources/` |
| 真实调度器实现 | `infrastructure/schedulers/` |
| 日志 / 指标 / trace 后端 | `infrastructure/telemetry/` |
| Web framework 底座 | `infrastructure/web/` |
| 依赖组装 | `container.py` |

如果表中没有对应项，禁止直接新增目录。  
必须先更新本文档的目录白名单和落位表。

---

# 7. 命名规则

固定目录名：

```text
api
domain
application
use_cases
ports
runtime
adapters
presenters
serializers
gateways
drivers
infrastructure
repositories
file_loaders
native
messaging
data_sources
schedulers
telemetry
```

禁止同义替换：

| 禁止 | 应改为 |
|---|---|
| `usecases` | `use_cases` |
| `service` / `services` under application | `use_cases` / `runtime` / `domain/services` |
| `manager` / `managers` | 按职责落入 `use_cases` 或 `runtime` |
| `helper` / `helpers` | 按职责落入明确目录 |
| `common` / `utils` | 按职责落入明确目录 |
| `orchestration` under application | `application/use_cases/workflows` |
| `controller` / `controllers` under adapters | 禁止；CLI 必须在 `__main__.py`，Web/RPC 需登记例外 |
| `cli` under api/application/adapters | 禁止；CLI 必须在 `__main__.py` |
| `engine` at package root | `application/runtime/engine.py` |
| `scheduler` at package root | `infrastructure/schedulers` 或 `application/runtime/scheduler_state.py` |
| `client` at package root | `infrastructure/<capability>/` 或 `adapters/gateways/` |

文件命名：

| 类型 | 命名格式 |
|---|---|
| Port | `<capability>_port.py` |
| UseCase | 动词短语，例如 `start_runtime.py`、`build_write_plan.py` |
| Workflow | 业务流程名，例如 `run_scenario.py` |
| DTO | `dtos.py` 或 `<name>_dto.py` |
| Gateway | `<capability>_gateway.py` |
| Serializer | `<format>_serializer.py` 或 `<object>_serializer.py` |
| Backend | `<capability>_backend.py` |
| Factory | `<capability>_factory.py` |
| Runtime state | `state.py` |
| Runtime context | `context.py` |
| CLI entry | `__main__.py` |

禁止：

```text
xxx_helper.py
xxx_utils.py
xxx_manager.py
xxx_service.py  # application 下禁止；domain/services 下允许
misc.py
common.py
temp.py
new.py
test2.py
*_cli.py        # api/application/adapters 下禁止
cli.py          # api/application/adapters 下禁止
```

---

# 8. 分层职责

## 8.1 Thin Entry Point

允许：

```text
Typer command declaration
Typer option / argument declaration
参数基本合法性检查
调用 API Facade
打印输出
raise typer.Exit
```

禁止：

```text
argparse
业务规则
直接构造 domain model
直接操作 UseCase 复杂编排
直接访问 Infrastructure
直接创建 backend
直接读取 ORM/session
直接操作 RuntimeContext 内部状态
```

## 8.2 API / Facade

允许：

```text
调用 UseCase
调用 container 获取已装配 runtime/usecase
聚合多个 UseCase
将 primitives / Path / dict / list 转为 DTO / Domain model
返回稳定 DTO / dict view / value object
```

禁止：

```text
直接 new infrastructure backend
暴露 RuntimeContext
暴露底层异常
执行业务规则
直接访问数据库/driver/socket
```

## 8.3 Domain

允许：

```text
entity
value object
domain service
pure algorithm
pure validation
pure state transition
pure codec / protocol format calculation
```

禁止：

```text
database
ORM
file I/O
network I/O
socket
thread
process
asyncio task
SDK client
driver
framework
infrastructure model
```

## 8.4 Application

允许：

```text
use case
workflow
DTO
OutPort
runtime context
runtime state
runtime graph
runtime event bus
application exception
```

禁止：

```text
ORM session
database client
socket
SDK client
driver object
native handle
framework binding
CLI parser
Typer object
Web request object
Adapter implementation
Infrastructure object
```

## 8.5 Adapters

允许：

```text
presenter
serializer
gateway
driver adapter
adapter-local backend protocol
```

禁止：

```text
CLI controller
Typer app
业务规则
领域状态转移
直接堆运行态状态
真实 socket / SDK / native backend
把 ORM / SDK / driver model 泄漏到 Application
```

## 8.6 Infrastructure

允许：

```text
database
ORM
file system
network
socket
SDK
driver
native binding
subprocess
thread
event loop
message queue
framework
monitoring backend
```

---

# 9. Import 边界矩阵

| From \ To | domain | application | api | adapters | infrastructure |
|---|---:|---:|---:|---:|---:|
| domain | ✅ | ❌ | ❌ | ❌ | ❌ |
| application | ✅ | ✅ | ❌ | ❌ | ❌ |
| api | ✅ | ✅ | ✅ | ❌ | ❌ |
| adapters | ✅ | ✅ ports only | ❌ | ✅ | ⚠️ |
| infrastructure | ✅ | ✅ ports only | ❌ | ❌ | ✅ |
| __main__.py | ❌ | ❌ | ✅ | ❌ | ❌ |
| container.py | ✅ | ✅ | ✅ | ✅ | ✅ |

说明：

1. `adapters → application` 只允许依赖 `application/ports/`、稳定 DTO 和必要 domain model；
2. `infrastructure → application` 只允许依赖 `application/ports/` 和稳定 DTO；
3. `adapters → infrastructure` 默认不推荐；启用 `strict_driver_di_profile` 后，`adapters/drivers/ → infrastructure` 禁止；
4. `__main__.py` 只能 import `api`、Typer 和标准库；
5. `container.py` 可以 import 所有层，但只能负责装配，禁止承载业务规则。

---

# 10. Codex 执行规则

新增能力流程：

```text
1. 判断能力类型
2. 查询文件落位决策表
3. 若涉及外部能力，先定义 application/ports/
4. 再实现 adapters 或 infrastructure
5. 在 container.py 组装
6. 通过 api/facade 暴露
7. 如涉及 CLI，在 __main__.py 用 Typer 暴露命令
8. 更新 README.md 或 architecture.md 的目录树
9. 运行边界检查
```

禁止：

```text
先创建 helpers/utils/common 放临时代码
在 use case 中直接创建 DB / driver / SDK
在 application 下新建 services/managers/orchestration
在包根新建 clients/repositories/drivers/controllers/cli
绕过 api/facade 让 CLI 直接调用深层 use case
创建 api/<package>_cli.py
创建 adapters/controllers
```

外部能力接入流程：

```text
1. 在 application/ports/ 定义 port
2. 在 adapters/ 或 infrastructure/ 实现 port
3. 在 container.py 注入 use case 或 runtime
4. UseCase 只依赖 port
5. Runtime 只依赖 port 或已装配组件
```

---

# 11. 边界检查

最低要求：

```bash
rg "from <package>.infrastructure|import <package>.infrastructure" src/<package>/domain src/<package>/application
rg "from <package>.adapters|import <package>.adapters" src/<package>/domain src/<package>/application src/<package>/infrastructure
rg "from <package>.api|import <package>.api" src/<package>/domain src/<package>/application src/<package>/infrastructure
rg "from <package>.domain|import <package>.domain" src/<package>/__main__.py
rg "from <package>.application|import <package>.application" src/<package>/__main__.py
rg "from <package>.adapters|import <package>.adapters" src/<package>/__main__.py
rg "from <package>.infrastructure|import <package>.infrastructure" src/<package>/__main__.py
find src/<package>/api -maxdepth 1 -type f \( -name "*_cli.py" -o -name "cli.py" \)
find src/<package>/adapters -maxdepth 1 -type d -name "controllers"
```

启用 `strict_driver_di_profile` 时，增加：

```bash
rg "from <package>.infrastructure|import <package>.infrastructure" src/<package>/adapters/drivers
```

CI 至少检查：

```text
1. Domain 不 import 外层
2. Application 不 import API / Adapters / Infrastructure
3. Ports 不 import Adapters / Infrastructure / Framework / SDK
4. Infrastructure 不 import Adapters
5. API 不暴露 RuntimeContext
6. UseCase 不直接创建 driver / repository / socket / SDK client
7. application 下无 services / helpers / managers / orchestration 一级目录
8. adapters 下无 controllers
9. api 下无 *_cli.py / cli.py
10. 包根无未登记一级目录
11. __main__.py 不直接 import domain / application / adapters / infrastructure
12. __main__.py 使用 Typer，不使用 argparse
13. public API 和 ports 有完整类型注解
14. hot path port 使用 batch / buffer / stream 接口
```

---

# 12. 标准工程树

## 12.1 application_profile 标准树

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py                         — Typer CLI 薄输入入口，只调用 api Facade
├── container.py                        — Composition Root，集中装配 use case、port 实现、runtime
│
├── api/
│   ├── __init__.py                     — 稳定 API 导出入口
│   └── <package>_facade.py             — Public API Facade / InPort 门面
│
├── domain/
│   ├── __init__.py                     — domain 导出入口
│   ├── exceptions.py                   — 领域异常
│   ├── entities/                       — 领域实体
│   ├── value_objects/                  — 值对象
│   └── services/                       — 纯规则、纯算法、纯校验
│
├── application/
│   ├── __init__.py                     — application 层入口
│   ├── exceptions.py                   — 应用层稳定异常
│   ├── use_cases/
│   │   ├── __init__.py                 — use case 导出入口
│   │   ├── dtos.py                     — UseCase DTO
│   │   ├── atomic/                     — 原子 UseCase
│   │   └── workflows/                  — 组合 workflow
│   ├── ports/
│   │   ├── __init__.py                 — OutPort 导出入口
│   │   └── <capability>_port.py        — 外部能力抽象
│   └── runtime/
│       ├── __init__.py                 — runtime 导出入口
│       ├── context.py                  — RuntimeContext
│       ├── state.py                    — 状态机
│       ├── graph.py                    — 执行图 / 拓扑
│       ├── event_bus.py                — 进程内事件总线
│       └── snapshot.py                 — 诊断快照
│
├── adapters/
│   ├── __init__.py                     — output adapter 层入口
│   ├── presenters/                     — 输出展示格式化
│   ├── serializers/                    — JSON / YAML / CSV / JSONL 转换
│   ├── gateways/                       — OutPort gateway / handoff gateway
│   └── drivers/                        — driver adapter，委托 backend protocol
│
└── infrastructure/
    ├── __init__.py                     — infrastructure 层入口
    ├── repositories/                   — 数据库、缓存、对象存储实现
    ├── file_loaders/                   — 文件读取实现
    ├── drivers/                        — 真实 SDK / socket / protocol backend
    ├── messaging/                      — MQ / Kafka / Event Stream 客户端
    ├── data_sources/                   — 真实数据源、replay、采样、文件流
    ├── schedulers/                     — 真实调度器、clock、timer、thread
    └── telemetry/                      — logger、metrics、trace
```

## 12.2 runtime_engine_profile 标准树

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py                         — Typer CLI 薄输入入口，只调用 api Facade
├── container.py                        — 运行时装配根
│
├── api/
│   ├── __init__.py
│   └── <package>_facade.py             — runtime API Facade
│
├── domain/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── entities/
│   ├── value_objects/
│   └── services/
│
├── application/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── dtos.py
│   │   ├── atomic/
│   │   └── workflows/
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── clock_port.py
│   │   ├── scheduler_port.py
│   │   ├── event_port.py
│   │   ├── telemetry_port.py
│   │   └── <capability>_port.py
│   └── runtime/
│       ├── __init__.py
│       ├── context.py
│       ├── state.py
│       ├── graph.py
│       ├── event_bus.py
│       ├── snapshot.py
│       ├── engine.py
│       ├── task_group.py
│       ├── lifecycle.py
│       └── diagnostics.py
│
├── adapters/
│   ├── __init__.py
│   ├── presenters/
│   ├── serializers/
│   ├── gateways/
│   └── drivers/
│
└── infrastructure/
    ├── __init__.py
    ├── repositories/
    ├── file_loaders/
    ├── drivers/
    ├── messaging/
    ├── data_sources/
    ├── schedulers/
    └── telemetry/
```

## 12.3 strict_driver_di_profile 增强树

```text
src/<package_name>/
├── adapters/
│   └── drivers/
│       ├── __init__.py
│       ├── backend_ports.py            — adapter-local backend protocol
│       ├── factory/
│       │   ├── __init__.py
│       │   └── driver_adapter_factory.py
│       └── <driver_adapter>.py         — adapter，只做转换和委托
│
└── infrastructure/
    └── drivers/
        ├── __init__.py
        ├── backend_factory.py          — 创建真实 backend
        └── <driver_backend>.py         — 真实 SDK / socket / native / protocol backend
```

---

# 13. 例外机制

允许例外，但必须显式登记。

例外必须写入 `architecture.md`：

```text
## Architecture Exceptions

| 日期 | 例外项 | 原因 | 影响范围 | 负责人 | 回收条件 |
|---|---|---|---|---|---|
| YYYY-MM-DD | xxx | xxx | xxx | xxx | xxx |
```

以下情况不能作为例外理由：

```text
Codex 自动生成
临时方便
测试能过
文件太少
以后再整理
不知道放哪里
```

---

# 14. 最小 Codex Prompt 约束模板

```text
请严格遵守项目 clean_architecture.md。

要求：
1. 不得新增未登记一级目录。
2. CLI 统一使用 Typer。
3. __main__.py 是唯一 CLI 入口，可定义 Typer app，但只能调用 api Facade。
4. __main__.py 禁止 import domain、application、adapters、infrastructure。
5. api 下只允许 facade，不得创建 *_cli.py / cli.py。
6. adapters 下不得新增 controllers。
7. application 下只能使用 use_cases、ports、runtime。
8. 新增外部能力必须先定义 application/ports。
9. UseCase 禁止 import infrastructure、adapters、framework、ORM、SDK、driver。
10. 具体技术实现必须放入 infrastructure。
11. OutPort 适配实现放入 adapters/gateways 或 adapters/drivers。
12. 依赖装配只允许放在 container.py。
13. 不得创建 services、helpers、managers、common、utils、orchestration 等含混目录。
14. 修改目录后必须更新 README.md 或 architecture.md 的目录树。
15. 完成后执行 import 边界检查。
```

---

# 15. 最终判定规则

当目录设计有争议时，按以下优先级判定：

```text
1. 依赖方向是否正确
2. 是否在 Profile 白名单内
3. 是否符合文件落位决策表
4. 是否避免含混命名
5. 是否通过 import 边界检查
6. CLI 是否统一使用 Typer
7. CLI 是否只在 __main__.py
8. __main__.py 是否只调用 API Facade
9. 是否让 adapters 主要承载 OutPort 适配实现
10. 是否对外保持 API / Facade 稳定
11. 是否减少未来目录漂移
```

本规范的最终目标不是追求目录数量最少，而是追求：

```text
职责稳定
命名稳定
依赖稳定
入口稳定
装配稳定
Codex 修改稳定
```
