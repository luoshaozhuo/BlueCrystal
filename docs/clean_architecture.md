# Clean Architecture Blueprint & Codex Constraint Specification

版本：4.0  
适用语言：Python 3.10+  
目标：易读、稳定、可约束 Coding Agent、适用于一般中大型 Python 工程。

---

# 0. 总则

本规范定义 Python 工程的 Clean Architecture 目录结构、依赖方向、命名规则和 Coding Agent 执行约束。

本规范的核心目标：

1. 固定目录结构，避免随意新增 `services/`、`helpers/`、`managers/`、`common/` 等含混目录；
2. 固定依赖方向，避免 Domain / Application 直接依赖数据库、ORM、SDK、driver、framework；
3. 固定文件落位规则，避免同类职责在不同模块中反复漂移；
4. 固定外部能力接入方式，统一通过 `application/ports/` 抽象；
5. 固定装配位置，统一通过 `container.py` 完成 wiring；
6. 支持 Codex / Coding Agent 按机械规则修改项目，而不是自由发挥。

---

# 1. 约束等级

本文使用以下约束词：

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

系统依赖方向必须向内：

```text
Interface Adapters / Presentation
        ↓
API / Facade
        ↓
Application
        ↓
Domain
```

Infrastructure 是最外层的具体技术实现。  
Application 只能通过 `application/ports/` 访问外部能力。  
Domain 和 Application 禁止直接依赖 Infrastructure。

允许关系：

```text
adapters         → api / application
api              → application
application      → domain
infrastructure   → application.ports / domain
container.py     → all layers
```

禁止关系：

```text
domain           → application / api / adapters / infrastructure
application      → api / adapters / infrastructure
api              → infrastructure concrete implementation
infrastructure   → adapters
```

`container.py` 是唯一允许同时 import Application、Adapters、Infrastructure 的集中装配点。

---

# 3. 架构 Profile

每个模块必须在 `README.md` 或 `architecture.md` 中声明一个 Profile。  
未声明 Profile 时，默认采用 `application_profile`。

## 3.1 library_profile

适用于纯算法库、纯模型库、纯领域规则库。

允许目录：

```text
src/<package_name>/
├── README.md
├── __init__.py
└── domain/
```

可选目录：

```text
tests/
```

禁止：

```text
api/
application/
adapters/
infrastructure/
container.py
```

除非该库开始接入外部系统或提供运行入口。

---

## 3.2 application_profile

适用于一般业务模块、平台服务、领域服务、CLI 工具、数据处理模块。

必须目录：

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

---

## 3.3 runtime_engine_profile

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

---

## 3.4 strict_driver_di_profile

适用于多协议、多 driver、native、SDK、外部 simulator、OS 进程、C/C++ 后端等强外部依赖模块。

在 `application_profile` 或 `runtime_engine_profile` 基础上，必须启用：

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
5. UseCase 禁止依赖 `adapters/drivers/backend_ports.py`。

---

# 4. 标准目录白名单

## 4.1 包根目录白名单

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
```

如确需新增包根一级目录，必须先修改 `architecture.md` 的白名单，并说明原因。

---

## 4.2 domain 白名单

```text
domain/
├── __init__.py
├── exceptions.py
├── entities/
├── value_objects/
├── services/
└── protocols/
```

说明：

1. `domain/entities/`：有业务身份和生命周期的实体；
2. `domain/value_objects/`：不可变值对象；
3. `domain/services/`：无状态纯规则、纯算法、纯编解码；
4. `domain/protocols/`：可选，纯协议模型、帧结构、编码规则，不含网络 I/O。

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

---

## 4.3 application 白名单

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
```

这些职责必须归入：

```text
application/use_cases/
application/ports/
application/runtime/
```

---

## 4.4 application/use_cases 白名单

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

---

## 4.5 application/ports 白名单

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

---

## 4.6 application/runtime 白名单

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
6. runtime 可以维护进程内状态，但业务规则不得堆入 RuntimeContext；
7. 状态变化应交给 `state.py`、`graph.py`、`event_bus.py` 等专门组件。

---

## 4.7 api 白名单

```text
api/
├── __init__.py
└── <package>_facade.py
```

规则：

1. API / Facade 是公共稳定入口；
2. CLI、Web、测试脚本、外部 SDK 消费者应调用 API / Facade；
3. API / Facade 不暴露 RuntimeContext；
4. API / Facade 不暴露 infrastructure exception；
5. API / Facade 不要求调用者理解内部 UseCase 拆分；
6. 包根 `__init__.py` 只导出稳定 Facade，不导出内部 UseCase、RuntimeContext、Port 实现。

---

## 4.8 adapters 白名单

```text
adapters/
├── __init__.py
├── controllers/
├── presenters/
├── serializers/
├── gateways/
└── drivers/
```

职责：

| 目录 | 职责 |
|---|---|
| `controllers/` | CLI / Web / RPC / Message controller，负责输入解析 |
| `presenters/` | 输出格式化 |
| `serializers/` | JSON / YAML / CSV / JSONL / 外部格式转换 |
| `gateways/` | Application Port 的适配外壳 |
| `drivers/` | DriverPort adapter，做转换、委托和 backend protocol 适配 |

规则：

1. Controller 应调用 API / Facade；
2. Presenter 不得包含业务规则；
3. Serializer 不得访问数据库、driver、runtime；
4. Gateway 可以实现 Application Port；
5. Adapter 不得把外部技术模型泄漏到 Application；
6. Strict Driver DI 下，`adapters/drivers/` 禁止直接 import infrastructure。

---

## 4.9 infrastructure 白名单

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

说明：

| 目录 | 职责 |
|---|---|
| `repositories/` | 数据库、缓存、对象存储实现 |
| `file_loaders/` | 文件系统配置读取 |
| `drivers/` | socket、SDK、native、process、protocol backend |
| `native/` | C/C++/Rust、FFI、二进制、子进程底座 |
| `messaging/` | MQ、Kafka、事件流客户端 |
| `data_sources/` | 外部数据源、replay、采样、文件流 |
| `schedulers/` | 真实调度器、sleep、timer、event loop、thread |
| `telemetry/` | 日志、指标、trace、诊断后端 |
| `web/` | FastAPI、Flask、ASGI 等框架底座 |

规则：

1. Infrastructure 承载所有具体技术实现；
2. Infrastructure 可以 import 第三方库、ORM、SDK、driver、native binding；
3. Infrastructure 可以实现 Application Port；
4. Infrastructure 禁止被 Domain / Application 直接 import；
5. Infrastructure 必须收敛底层异常；
6. Infrastructure 不得把底层模型直接泄漏到 Application。

---

# 5. 文件落位决策表

Coding Agent 新增文件前，必须先查此表。

| 目标职责 | 固定位置 |
|---|---|
| 领域实体 | `domain/entities/` |
| 值对象 | `domain/value_objects/` |
| 纯业务规则 | `domain/services/` |
| 纯算法 | `domain/services/` |
| 纯协议帧 / 编码模型 | `domain/protocols/` |
| 原子用例 | `application/use_cases/atomic/` |
| 组合用例 / workflow | `application/use_cases/workflows/` |
| UseCase 输入输出 DTO | `application/use_cases/dtos.py` 或 `application/use_cases/dtos/` |
| 外部能力抽象 | `application/ports/<capability>_port.py` |
| 运行态上下文 | `application/runtime/context.py` |
| 运行态状态机 | `application/runtime/state.py` |
| 执行图 / 拓扑图 | `application/runtime/graph.py` |
| 进程内事件总线 | `application/runtime/event_bus.py` |
| 运行态快照 / 诊断视图 | `application/runtime/snapshot.py` |
| CLI 参数解析 | `adapters/controllers/` |
| Web / RPC 输入转换 | `adapters/controllers/` |
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
| 公共入口 | `api/` |

如果表中没有对应项，禁止直接新增目录。  
必须先更新本文档的目录白名单和落位表。

---

# 6. 命名规则

## 6.1 目录命名

固定使用：

```text
api
domain
application
use_cases
ports
runtime
adapters
controllers
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
| `engine` at package root | `application/runtime/engine.py` |
| `scheduler` at package root | `infrastructure/schedulers` 或 `application/runtime/scheduler_state.py` |
| `client` at package root | `infrastructure/<capability>/` 或 `adapters/gateways/` |

---

## 6.2 文件命名

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
```

---

# 7. 分层职责

## 7.1 Domain

Domain 负责最核心、最稳定、与外部技术无关的模型和规则。

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

Domain 可以表达抽象时间：

```python
tick(now)
deadline
timestamp
duration
```

Domain 禁止直接 sleep、等待事件或创建 event loop。

---

## 7.2 Application

Application 负责用例执行、流程编排、端口调用和运行态管理。

允许：

```text
use case
workflow
DTO
port
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
Web request object
```

Application 只能通过 `application/ports/` 访问外部能力。

---

## 7.3 API / Facade

API / Facade 负责提供稳定公共入口。

规则：

1. 外部消费者调用 API / Facade；
2. API / Facade 可以调用 UseCase 或通过 `container.py` 获取运行入口；
3. API / Facade 禁止暴露 RuntimeContext；
4. API / Facade 禁止暴露底层异常；
5. API / Facade 返回稳定 DTO、value object、dict view 或 response model；
6. API / Facade 不包含具体 wiring 细节。

---

## 7.4 Adapters

Adapters 负责内外数据转换。

允许：

```text
CLI controller
Web controller
RPC handler
message consumer
presenter
serializer
gateway
driver adapter
```

禁止：

```text
业务规则
领域状态转移
直接堆运行态状态
把 ORM / SDK / driver model 泄漏到 Application
```

---

## 7.5 Infrastructure

Infrastructure 负责所有具体技术实现。

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

规则：

1. Infrastructure 可以实现 Application Port；
2. Infrastructure 可以依赖第三方库；
3. Infrastructure 禁止被 Domain / Application import；
4. Infrastructure 必须捕获底层异常并转换；
5. 高频边界必须优先 batch / buffer / stream。

---

# 8. Import 边界矩阵

| From \ To | domain | application | api | adapters | infrastructure |
|---|---:|---:|---:|---:|---:|
| domain | ✅ | ❌ | ❌ | ❌ | ❌ |
| application | ✅ | ✅ | ❌ | ❌ | ❌ |
| api | ✅ | ✅ | ✅ | ❌ | ❌ |
| adapters | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| infrastructure | ✅ | ✅ ports only | ❌ | ❌ | ✅ |
| container.py | ✅ | ✅ | ✅ | ✅ | ✅ |

说明：

1. `infrastructure → application` 只允许依赖 `application/ports/` 和稳定 DTO；
2. `adapters → infrastructure` 默认允许 gateway 委托场景使用；
3. 启用 `strict_driver_di_profile` 后，`adapters/drivers/ → infrastructure` 禁止；
4. `container.py` 可以 import 所有层，但只能负责装配，禁止承载业务规则。

---

# 9. Codex 执行规则

Coding Agent 修改项目时，必须遵守以下流程。

## 9.1 新增能力流程

新增能力必须按顺序执行：

```text
1. 判断能力类型
2. 查询文件落位决策表
3. 若涉及外部能力，先定义 application/ports/
4. 再实现 adapters 或 infrastructure
5. 在 container.py 组装
6. 通过 api/facade 暴露
7. 更新 README.md 或 architecture.md 的目录树
8. 运行边界检查
```

禁止：

```text
先创建 helpers/utils/common 放临时代码
在 use case 中直接创建 DB / driver / SDK
在 application 下新建 services/managers/orchestration
在包根新建 clients/repositories/drivers
绕过 api/facade 让 CLI 直接调用深层 use case
```

---

## 9.2 修改目录结构流程

如需移动或新增目录，必须：

```text
1. 先确认当前模块 Profile
2. 检查目标目录是否在白名单中
3. 若不在白名单，先修改本规范或模块 architecture.md
4. 迁移 import
5. 更新 __init__.py 导出
6. 更新 README.md 目录树
7. 运行边界检查
```

禁止 Codex 为了解决一个局部问题随意创建新一级目录。

---

## 9.3 外部能力接入流程

外部能力包括：

```text
database
file system
network
message queue
SDK
driver
native binding
subprocess
scheduler
clock
telemetry
external API
```

接入流程：

```text
1. 在 application/ports/ 定义 port
2. 在 infrastructure/ 或 adapters/ 实现 port
3. 在 container.py 注入 use case 或 runtime
4. UseCase 只依赖 port
5. Runtime 只依赖 port 或已装配组件
```

禁止：

```python
# 禁止
from package.infrastructure.repositories.xxx import XxxRepository

class SomeUseCase:
    ...
```

推荐：

```python
# 推荐
from package.application.ports.xxx_repository_port import XxxRepositoryPort

class SomeUseCase:
    def __init__(self, repository: XxxRepositoryPort) -> None:
        self._repository = repository
```

---

# 10. 边界检查

项目必须提供静态边界检查。

最低要求：

```bash
rg "from <package>.infrastructure|import <package>.infrastructure" src/<package>/domain src/<package>/application
rg "from <package>.adapters|import <package>.adapters" src/<package>/domain src/<package>/application src/<package>/infrastructure
rg "from <package>.api|import <package>.api" src/<package>/domain src/<package>/application src/<package>/infrastructure
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
8. 包根无未登记一级目录
9. public API 和 ports 有完整类型注解
10. hot path port 使用 batch / buffer / stream 接口
```

边界检查失败时，必须修复架构边界，禁止修改检查规则来绕过失败。

---

# 11. 标准工程树

## 11.1 application_profile 标准树

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py
├── container.py
│
├── api/
│   ├── __init__.py
│   └── <package>_facade.py
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
│   │   └── <capability>_port.py
│   └── runtime/
│       ├── __init__.py
│       ├── context.py
│       ├── state.py
│       ├── graph.py
│       ├── event_bus.py
│       └── snapshot.py
│
├── adapters/
│   ├── __init__.py
│   ├── controllers/
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

---

## 11.2 runtime_engine_profile 标准树

```text
src/<package_name>/
├── README.md
├── __init__.py
├── __main__.py
├── container.py
│
├── api/
│   ├── __init__.py
│   └── <package>_facade.py
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
│   │   └── telemetry_port.py
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
│   ├── controllers/
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

---

## 11.3 strict_driver_di_profile 增强树

```text
src/<package_name>/
├── adapters/
│   └── drivers/
│       ├── __init__.py
│       ├── backend_ports.py
│       ├── factory/
│       │   ├── __init__.py
│       │   └── driver_adapter_factory.py
│       └── <driver_adapter>.py
│
└── infrastructure/
    └── drivers/
        ├── __init__.py
        ├── backend_factory.py
        └── <driver_backend>.py
```

规则：

```text
UseCase → application/ports/<driver>_port.py
Gateway / DriverAdapter → adapters/drivers/backend_ports.py
BackendFactory → infrastructure/drivers/backend_factory.py
ConcreteBackend → infrastructure/drivers/<driver_backend>.py
Wiring → container.py
```

---

# 12. 例外机制

允许例外，但必须显式登记。

例外必须写入 `architecture.md`：

```text
## Architecture Exceptions

| 日期 | 例外项 | 原因 | 影响范围 | 负责人 | 回收条件 |
|---|---|---|---|---|---|
| YYYY-MM-DD | xxx | xxx | xxx | xxx | xxx |
```

禁止无记录例外。

以下情况不能作为例外理由：

```text
Codex 自动生成
临时方便
测试能过
文件太少
以后再整理
不知道放哪里
```

如果不知道放哪里，必须先查文件落位决策表。

---

# 13. 最小 Codex Prompt 约束模板

给 Coding Agent 下发任务时，应附带以下约束：

```text
请严格遵守项目 clean_architecture.md。

要求：
1. 不得新增未登记一级目录。
2. application 下只能使用 use_cases、ports、runtime。
3. 新增外部能力必须先定义 application/ports。
4. UseCase 禁止 import infrastructure、adapters、framework、ORM、SDK、driver。
5. 具体技术实现必须放入 infrastructure。
6. 输入输出转换放入 adapters。
7. 依赖装配只允许放在 container.py。
8. 不得创建 services、helpers、managers、common、utils、orchestration 等含混目录。
9. 修改目录后必须更新 README.md 或 architecture.md 的目录树。
10. 完成后执行 import 边界检查。
```

---

# 14. 最终判定规则

当目录设计有争议时，按以下优先级判定：

```text
1. 依赖方向是否正确
2. 是否在 Profile 白名单内
3. 是否符合文件落位决策表
4. 是否避免含混命名
5. 是否通过 import 边界检查
6. 是否对外保持 API / Facade 稳定
7. 是否减少未来目录漂移
```

如果一个设计会导致 Codex 后续频繁新增同义目录、重复目录或绕过端口，则该设计不合格。

本规范的最终目标不是追求目录数量最少，而是追求：

```text
职责稳定
命名稳定
依赖稳定
入口稳定
装配稳定
Codex 修改稳定
```