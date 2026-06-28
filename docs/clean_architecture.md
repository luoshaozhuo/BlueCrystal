# Clean Architecture Blueprint & Standard Specification
# 版本：3.3（面向 Python 中大型可演进系统） | 适用语言：Python 3.10+

本规范定义一种面向 Python 中大型工程的 Clean Architecture 工程结构，适用于需要长期演进、边界清晰、外部依赖可替换、运行状态可管理的系统。

适用场景包括但不限于：

- 业务应用、平台服务、领域服务；
- 长生命周期 runtime / daemon 服务；
- 任务调度、执行引擎、仿真运行时；
- 数据采集、设备接入、协议网关、边缘服务；
- 多后端驱动、多外部系统集成、多技术栈适配工程；
- 需要隔离 domain、application、adapter、infrastructure 的复杂 Python 系统。

本规范不绑定任何具体业务领域。文中涉及协议、驱动、C/C++ Native、设备、仿真等表述，均作为高外部依赖、高运行态复杂度场景的示例，不构成本规范的适用前提。

本规范使用以下约束级别：

- **MUST / 必须**：强制规则，违反即视为架构错误。
- **MUST NOT / 禁止**：强制禁令，违反即视为架构错误。
- **SHOULD / 应当**：默认规则。只有存在明确工程理由、且不破坏依赖方向时，才允许偏离。
- **MAY / 可以**：允许选项。使用时仍必须满足本规范的依赖边界和目录边界。
- **示例**：仅用于解释规则，不得反向推导为强制业务前提。

核心目标：

1. 保持 Domain 与 Application 的稳定性；
2. 隔离外部技术栈、物理驱动、框架、数据库、网络 I/O、Native 模块与第三方 SDK；
3. 通过 API / Facade 提供稳定公共入口；
4. 通过 Ports 实现依赖倒置；
5. 支持 Coding Agent 基于明确目录、依赖规则、类型规则和边界断言进行可验证改造。

---

## 一、 架构分层设计与边界约束

### 0. 依赖方向总则

系统依赖方向必须向内：

```text
Presentation / Interface Adapters
        ↓
API / Facade
        ↓
Application
        ↓
Domain
```

Infrastructure 是最外层的具体技术实现。Application 只能通过 `application/ports/` 中定义的抽象契约访问外部能力。Infrastructure 可以实现这些 Ports，但 Application 和 Domain 禁止直接依赖 Infrastructure。

```text
                  ┌──────────────────────────────────────────────┐
                  │  Infrastructure                              │
                  │  DB / FS / Network / Native / SDK / Drivers   │
                  └──────────────────────────────────────────────┘
                                    ▲
                                    │ implements
                                    │
Presentation / Interface Adapters ──┼──▶ API / Facade ──▶ Application ──▶ Domain
                                    │
                                    │ via application/ports only
                                    ▼
                              External Capabilities
```

`API / Facade` 是公共稳定入口。它不是 Domain 内层，也不是具体 UI / Web / CLI 框架层。Controller、CLI、Web Handler、测试脚本和外部 SDK 消费者应当依赖 API / Facade，而不是绕过它直接依赖 Application 内部用例。

---

### 1. Domain 层（核心模型 / 规则层）

#### 1.1 职责

Domain 层必须承载系统最核心、最稳定、与外部技术无关的业务模型、业务规则、纯算法、纯状态转移逻辑与纯协议/格式计算逻辑。

在不同系统中，Domain 可包含：

- 业务实体与聚合；
- 值对象；
- 领域服务；
- 纯算法；
- 纯规则校验；
- 纯状态机；
- 纯编解码逻辑；
- 不依赖外部 I/O 的策略计算。

在协议仿真、网关、设备接入等系统中，协议帧结构、寄存器编码、ASDU、Frame、Quality、点位值规范等纯模型与纯编解码逻辑属于 Domain。该类内容只是示例，不限定本规范只用于协议系统。

#### 1.2 包含元素

##### Entities（实体）

实体必须具有业务身份标识。实体生命周期内可以发生状态变化，但状态变化必须体现领域规则。

实体内部方法只能处理该实体自身的状态流转、约束校验与领域不变量维护。

##### Value Objects（值对象）

值对象必须通过值相等表达业务等价性。值对象应当不可变。

值对象可以包含局部计算逻辑。值对象不得持有数据库连接、Socket、文件句柄、线程、进程、driver、repository、session 等外部资源。

高频数据或协议载荷场景中，值对象可以使用 `bytes`、只读 `memoryview` 等表达零拷贝或低拷贝数据视图。可变 `bytearray` 只能用于明确标注的内部缓冲对象，不得伪装成不可变值对象。

##### Domain Services（领域服务）

领域服务必须是无状态的纯规则或纯算法服务。

当某项核心规则涉及多个实体或值对象，且不适合放入单一实体或值对象时，必须放入 Domain Service。

#### 1.3 禁止规则

Domain 层禁止：

1. import Web 框架、CLI 框架、ORM、数据库客户端、消息队列客户端、网络库、物理驱动库、C FFI 库、第三方 SDK；
2. 读取文件、写文件、访问数据库、打开 Socket、启动进程、创建线程；
3. 初始化 event loop、创建 asyncio task、调用 `asyncio.sleep()`、`asyncio.Event`、`asyncio.Queue` 等运行时调度原语；
4. 持有或传递 infrastructure 对象；
5. 引入任何由外部技术栈决定的数据模型作为领域模型父类。

#### 1.4 异步与时间建模规则

Domain 可以使用 `async def` 表达纯异步接口，但该函数不得依赖 asyncio 运行时原语，不得触发 I/O，不得创建 event loop，不得调度 task。

Domain 中的时间驱动逻辑必须通过抽象时间表达，例如：

- `tick(now)`；
- `deadline`；
- `timestamp`；
- `duration`；
- domain event；
- caller-provided clock value。

协议超时、重传、过期、定时状态迁移等逻辑应当建模为纯状态转移，不得在 Domain 中直接 sleep 或等待事件。

---

### 2. Application 层（应用执行层）

#### 2.1 职责

Application 层是系统用例执行与运行时编排层。它必须负责编排 Domain 模型与外部能力抽象，以完成一个具体的用户意图或系统意图。

Application 层只关心：

- 做什么；
- 按什么流程做；
- 依赖哪些抽象能力；
- 如何维护本进程内执行状态；
- 如何将失败收敛成应用层异常。

Application 层禁止关心外部能力如何实现。数据库、文件系统、网络服务、Native C/C++ 模块、第三方 API、协议 driver 等具体实现必须通过 Ports 间接访问。

#### 2.2 Application 层唯一合法一级子目录

Application 层下只能使用以下三个一级子目录承载核心代码：

```text
application/
├── use_cases/
├── ports/
└── runtime/
```

允许存在 `application/__init__.py`、`application/exceptions.py` 等少量跨切面根模块。禁止新增 `services/`、`orchestration/`、`managers/`、`helpers/`、`misc/` 等语义含混的一级目录。

---

#### 2.3 use_cases

##### 2.3.1 职责

`use_cases/` 必须承载系统所有应用行为入口。

这里的 Use Case 是广义概念，表示 Application 层对外表达的一个执行意图。它包含：

- 原子 UseCase；
- Workflow / Composite UseCase；
- UseCase 输入输出 DTO；
- UseCase 内部组合规则。

##### 2.3.2 原子 UseCase

原子 UseCase 是最小执行单元。

原子 UseCase 必须满足：

1. 必须以明确的类、函数或可调用对象表达；
2. 类形式的 UseCase 必须提供 `execute()` 方法；
3. 必须只表达单一执行意图；
4. 禁止直接 import infrastructure；
5. 禁止直接创建 driver、repository、socket、process、native handle；
6. 必须通过 `application/ports/` 访问外部能力；
7. 输入输出必须使用明确类型，禁止无约束 `dict` 横向传播。

##### 2.3.3 Workflow / Composite UseCase

Workflow 是 UseCase 的组合执行模式，不是独立架构层。

Workflow 必须满足：

1. 必须放在 `application/use_cases/` 内部；
2. 可以放在 `application/use_cases/workflows/`；
3. 必须通过调用原子 UseCase 或其他明确的应用行为完成组合；
4. 禁止绕过 UseCase 直接调用 infrastructure；
5. 禁止成为与 `use_cases/`、`ports/`、`runtime/` 平级的新目录；
6. 禁止被命名为独立 layer。

因此，`use_cases/` 不是“只允许原子用例”的目录，而是 Application 行为表达目录。原子 UseCase 与 Workflow 都属于 Use Case 范畴：前者是最小执行单元，后者是组合执行单元。这不违反 Clean Architecture。

##### 2.3.4 DTO

DTO 是跨边界或跨 UseCase 传递数据的结构，不是 runtime state，不是 domain entity。

Application DTO 必须满足：

1. SHOULD 使用 `dataclasses.dataclass(frozen=True)` 定义；
2. API / Adapter 边界 DTO MAY 使用 Pydantic frozen model；
3. MUST 不包含业务逻辑方法；
4. MUST 不持有 driver、repository、session、socket、process handle、native pointer；
5. MUST 不继承 ORM 模型、Web request model、driver model 或第三方 SDK model；
6. MUST 具有完整类型注解；
7. MUST 不使用动态属性挂载；
8. MUST 不作为 runtime context 使用。

---

#### 2.4 ports

##### 2.4.1 职责

`ports/` 必须定义 Application 访问外部能力所依赖的抽象契约。

Application ports 是 UseCase 层面向外部能力的 outport 抽象。Application 只依赖 application ports，Infrastructure 或 Interface Adapter 负责实现这些 ports。

application ports 只表达业务执行所需的外部能力，例如配置加载、driver 装配、repository、事件发布、外部系统调用等。它们不是 adapter 内部 backend 协议，也不描述 socket、subprocess、native runner、SDK client 等物理实现细节。

##### 2.4.2 强制规则

Ports 必须满足：

1. MUST 使用 `abc.ABC`、`typing.Protocol` 或等价抽象形式；
2. MUST 只包含接口契约，不得包含具体实现；
3. MUST 具备完整类型提示与返回值注解；
4. MUST 不 import infrastructure；
5. MUST 不 import adapters；
6. MUST 不 import Web / CLI / ORM / driver / native / SDK；
7. MUST 只被 `application/use_cases/`、`application/runtime/` 或 application 内部装配对象依赖，不得被当作具体实现容器；
8. MUST 不引用 adapter-local backend protocol，例如 `adapters/drivers/backend_ports.py`；
9. MUST 不使用 `Any`，除非该值被明确建模为不透明载荷；
10. 使用不透明值时，MUST 定义类型别名并说明语义，例如 `PointValue = Any`、`OpaquePayload = bytes | memoryview`。

##### 2.4.3 性能与批量边界

当系统存在高频 I/O、批量数据处理、Native FFI、协议帧编解码、点位批量读写、消息批处理或流式数据通道时，Ports 必须优先提供批量或缓冲区级别接口。

禁止在 hot path 中设计以下接口模式：

```text
for item in items:
    port.write_one(item)
```

应当设计为：

```text
port.write_batch(items)
port.write_frame(frame)
port.write_buffer(buffer)
port.read_batch(query)
```

跨进程、跨网络、跨 FFI、跨数据库、跨 SDK 的边界调用必须尽量减少调用次数，避免单字节、单寄存器、单点位、单事件频繁跨层调用。

---

#### 2.5 runtime

##### 2.5.1 职责

`runtime/` 是 Application 层内部的进程内执行内核状态系统。

runtime 只用于管理当前进程中的执行状态、运行图、事件流、状态机、快照、上下文等对象。它不是 DTO，不是 Domain，不是 API contract，不是 Infrastructure。

##### 2.5.2 必须包含的核心概念

runtime 可以包含以下模块：

```text
application/runtime/
├── context.py
├── state.py
├── graph.py
├── event_bus.py
└── snapshot.py
```

其中：

- `context.py`：Runtime Kernel Root Object，运行态唯一入口；
- `state.py`：运行状态机；
- `graph.py`：执行拓扑、依赖图、运行图；
- `event_bus.py`：进程内事件分发；
- `snapshot.py`：运行态快照、诊断视图或恢复视图。

##### 2.5.3 RuntimeContext 强约束

RuntimeContext 必须满足：

1. MUST 是显式强类型 root object；
2. MUST 显式声明其包含的子上下文或运行组件类型；
3. MUST NOT 使用 `kwargs`、`setattr`、动态属性挂载运行期对象；
4. MUST NOT 作为 DTO 传出 API / Facade；
5. MUST NOT 被 adapters 当作 response schema；
6. MUST NOT 包含业务规则；
7. MAY 持有可变 runtime component，但状态变更必须委托给 `state`、`graph`、`event_bus` 等专门组件；
8. MUST 不 import infrastructure。

示例：

```python
class RuntimeContext:
    state: RuntimeStateMachine
    graph: ExecutionGraph
    event_bus: InProcessEventBus
```

##### 2.5.4 runtime 边界

runtime 只能被 Application 内部和 API / Facade 的运行入口持有或间接使用。Controller、Presenter、Web Handler、CLI Controller 禁止直接依赖 runtime 结构。

---

### 3. API / Facade 层（公共应用入口层）

#### 3.1 职责

API / Facade 是系统的稳定公共入口。它负责向外部程序、CLI、Web Controller、测试框架、自动化脚本或 SDK 消费者暴露简洁、稳定、面向用例的接口。

API / Facade 必须隐藏 Application 内部的 UseCase 拆分、RuntimeContext 结构、Ports 结构、Infrastructure 装配细节。

#### 3.2 规则

API / Facade 必须满足：

1. MUST 暴露稳定公共方法；
2. MUST 调用 Application use cases 或通过 composition root 获取 Application runtime；
3. MUST 不暴露 RuntimeContext 作为公共契约；
4. MUST 不把 infrastructure exception 原样抛给调用方；
5. SHOULD 只返回稳定 DTO、dict view、value object 或明确 response model；
6. MUST 不要求外部消费者理解内部 UseCase 目录结构；
7. MUST 不直接调用具体 C library、driver、database、network client。

#### 3.3 Composition Root

`container.py` 或等价 composition root 可以位于包根目录。Composition Root 是唯一允许同时 import Application、Infrastructure、Adapters 的组装点。

API / Facade 可以通过 Composition Root 构建运行态对象，但 API / Facade 自身不得散落具体依赖组装逻辑。

Composition Root 负责 wiring，而不是业务规则。典型职责包括：

1. 创建 config loader；
2. 创建 infrastructure backend factory；
3. 创建 driver adapter factory；
4. 将 backend 注入 adapter；
5. 调用 Application workflow 构建 runtime context。

Composition Root 可以 import adapters 与 infrastructure；除 Composition Root 和明确的 infrastructure factory 外，业务路径不得把具体 backend 创建逻辑散落到 API、UseCase、runtime 或 adapter wrapper 中。

---

### 4. Interface Adapters 层（接口适配器层）

#### 4.1 职责

Interface Adapters 层是内外层之间的数据转译层。

它负责将外部输入转换为 API / Facade 或 Application 可理解的数据结构，并将内部输出转换为外部展示、传输或响应格式。

#### 4.2 包含元素

Interface Adapters 可包含：

- CLI Controller；
- Web Controller；
- RPC Handler；
- Message Consumer；
- Presenter；
- Serializer / Deserializer；
- Gateway / Repository Adapter；
- Port implementation wrapper。

#### 4.3 规则

Interface Adapters 必须满足：

1. Controller 必须调用 API / Facade，禁止直接跨过 API / Facade 调用深层 use case，除非该工程明确不提供 API / Facade；
2. Presenter 只负责格式转换，不得执行业务规则；
3. Adapter 可实现 Application Port，但不得把具体技术模型泄漏到 Application；
4. Adapter 可以调用 Infrastructure，但必须把 Infrastructure 返回值转换为 Application 所需模型；
5. Adapter 必须捕获外部输入格式错误，并转换为稳定的应用层错误；
6. Adapter 禁止持有 Domain 不允许出现的物理资源作为领域对象成员。

#### 4.4 Strict Driver DI 变体

当系统采用驱动后端注入模式时，Driver Adapter 必须满足更严格边界：

1. Adapter 禁止直接 import Infrastructure；
2. Adapter 只依赖本层本地 Protocol 或 Application Port；
3. 具体 backend 必须由 `container.py`、Infrastructure backend factory 或等价 composition root 创建；
4. Adapter 必须通过构造函数接收 backend，不得自行创建 socket、process、native runner 或具体 SDK 对象；
5. 测试必须能注入 fake backend 或替换 composition root。

`adapters/drivers/backend_ports.py` 属于 adapter-local backend protocol，只用于隔离 adapter wrapper 与 infrastructure backend。它不属于 application port，不得被 UseCase 当作业务 outport 使用，也不得进入 `application/ports/`。

adapter-local backend protocol 可以描述 adapter 委托所需的 backend 操作，例如 `start()`、`stop()`、`read()`、`write()`、`health()`、`capabilities()`、环境探测或 backend 创建接口。该 protocol 的语义是“adapter 到 backend 的局部委托契约”，不是“Application 到外部能力的业务契约”。

---

### 5. Infrastructure 层（基础设施层）

#### 5.1 职责

Infrastructure 层承载所有具体技术实现和物理外部依赖。

包括但不限于：

- 数据库；
- 文件系统；
- 网络 I/O；
- Web 框架底座；
- CLI 框架底座；
- 消息队列；
- 第三方 SDK；
- Native C/C++/Rust 模块；
- OS 进程、线程、信号；
- 硬件设备；
- 协议 driver；
- 缓存、对象存储、搜索引擎；
- 运行时监控和底层日志接入。

#### 5.2 规则

Infrastructure 必须满足：

1. MAY import Application Ports 并实现它们；
2. MAY import 第三方库、driver、native binding、framework；
3. MUST NOT 被 Domain 直接依赖；
4. MUST NOT 被 Application 直接依赖，除 Composition Root 外；
5. MUST 捕获 native/network/OS/framework exception，并转换为 application-level 或 domain-level exception；
6. MUST 不把底层异常穿透到 API / Facade；
7. SHOULD 把高频跨边界操作设计为 batch / buffer / stream；
8. SHOULD 隔离 ctypes / cffi / subprocess / socket / database session 等资源生命周期。

#### 5.3 Infrastructure backend factory

`infrastructure/drivers/backend_factory.py` 或等价 infrastructure backend factory 负责创建真实 backend，并集中处理 socket、PTY、native runner、subprocess、环境变量、二进制探测、第三方 SDK client 等物理实现细节。

Infrastructure backend factory 必须满足：

1. MAY import 具体 infrastructure backend、第三方库、native/process/socket 支撑模块；
2. MUST NOT 被 Domain 或 Application import；
3. MUST 不把 socket、process handle、native pointer、SDK client 等物理细节泄漏给 adapters 的 public API；
4. SHOULD 返回符合 adapter-local backend protocol 的对象；
5. SHOULD 把环境探测结果收敛为稳定 mode、reason 或结构化结果，供 adapter factory 使用；
6. MUST 不承载业务规则。

---

## 二、 工程树结构

以下工程树是通用模板。`<package_name>` 应替换为实际项目包名。示例中的协议、驱动、native、device、runtime 等命名用于说明高外部依赖系统如何落位；普通业务系统可以替换为 database、payment、notification、workflow、reporting、search 等业务命名，但不得改变分层边界和依赖方向。

```text
src/<package_name>/
├── README.md                        — 包级架构、运行方式、公共入口说明
├── __init__.py                      — 对外只导出稳定 API / Facade，不导出内部 use case
├── __main__.py                      — 可选：CLI 启动入口，只调用 adapters 或 api/facade
├── container.py                     — Composition Root；唯一允许集中组装 Application 与 Infrastructure 的位置
│
├── api/                             # ===== API / FACADE 层：公共稳定入口 =====
│   ├── __init__.py                  — 导出公共 Facade
│   └── runtime_facade.py            — 示例：class XxxRuntime / XxxManager / XxxClientFacade
│
├── domain/                          # ===== DOMAIN 层：纯核心模型、规则、算法 =====
│   ├── __init__.py
│   ├── exceptions.py                — 领域规则异常；不得承载底层 I/O 异常
│   ├── entities/                    — 具有业务身份和生命周期的实体
│   │   └── <entity>.py
│   ├── value_objects/               — 不可变值对象
│   │   └── <value_object>.py
│   ├── services/                    — 无状态领域服务；纯业务/纯算法/纯编解码
│   │   └── <domain_service>.py
│   └── protocols/                   — 可选：纯协议/格式/帧/编码模型；无网络 I/O
│       └── <protocol_name>/
│           ├── frame.py
│           ├── codec.py
│           └── types.py
│
├── application/                     # ===== APPLICATION 层：用例执行、端口、运行态 =====
│   ├── __init__.py
│   ├── exceptions.py                — 应用执行异常；对 infrastructure 异常进行收敛后的稳定异常
│   │
│   ├── use_cases/                   # ===== 行为入口：原子 UseCase + Workflow + DTO =====
│   │   ├── __init__.py
│   │   ├── dtos.py                  — UseCase 输入/输出 DTO；优先 frozen dataclass
│   │   ├── atomic/                  — 原子用例；每个用例表达单一执行意图
│   │   │   ├── __init__.py
│   │   │   ├── start.py             — 示例：启动类动作
│   │   │   ├── stop.py              — 示例：停止类动作
│   │   │   ├── status.py            — 示例：状态查询类动作
│   │   │   └── describe.py          — 示例：结构描述类动作
│   │   └── workflows/               — Composite UseCase；组合原子 UseCase，不是独立层
│   │       ├── __init__.py
│   │       └── <workflow>.py
│   │
│   ├── ports/                       # ===== 输出端口：Application 依赖外部能力的抽象契约 =====
│   │   ├── __init__.py
│   │   ├── config_loader_port.py    — 示例：配置/计划加载抽象
│   │   ├── driver_port.py           — 示例：外部执行驱动抽象
│   │   ├── repository_port.py       — 示例：持久化抽象
│   │   └── event_publisher_port.py  — 示例：事件发布抽象
│   │
│   └── runtime/                     # ===== Execution Kernel：进程内运行态模型 =====
│       ├── __init__.py
│       ├── context.py               — RuntimeContext；runtime root object
│       ├── state.py                 — 状态机 / 生命周期状态
│       ├── graph.py                 — 执行图 / 拓扑图 / 依赖图
│       ├── event_bus.py             — 进程内事件分发
│       └── snapshot.py              — 快照 / 诊断视图 / 恢复视图
│
├── adapters/                        # ===== INTERFACE ADAPTERS 层：输入输出转译 =====
│   ├── __init__.py
│   ├── controllers/                 — CLI / Web / RPC / Message controllers
│   │   ├── __init__.py
│   │   └── cli_controller.py
│   ├── presenters/                  — 输出格式化
│   │   ├── __init__.py
│   │   └── status_presenter.py
│   ├── serializers/                 — 外部格式与 DTO 转换
│   │   ├── __init__.py
│   │   └── json_serializer.py
│   ├── gateways/                    — Port 实现外壳；可委托 infrastructure
│   │   ├── __init__.py
│   │   └── <gateway_adapter>.py
│   └── drivers/                     — DriverPort adapter；只做转换、委托和端口适配
│       ├── __init__.py
│       ├── backend_ports.py         — adapter-local backend protocol；不是 application port
│       ├── factory/
│       │   ├── __init__.py          — driver adapter factory；接收 backend factory 注入
│       └── <driver_adapter>.py
│
└── infrastructure/                  # ===== INFRASTRUCTURE 层：具体技术实现 =====
    ├── __init__.py
    ├── file_loaders/                — 文件系统配置/计划加载实现
    │   ├── __init__.py
    │   └── json_config_loader.py
    ├── repositories/                — 数据库 / 缓存 / 对象存储实现
    │   ├── __init__.py
    │   └── <repository_impl>.py
    ├── drivers/                     — socket / PTY / subprocess / SDK / native backend 实现
    │   ├── __init__.py
    │   ├── backend_factory.py       — 创建真实 backend；集中物理探测与 backend wiring
    │   └── <driver_backend>.py
    ├── native/                      — 可选：C/C++/Rust/二进制/子进程/FFI 底座
    │   ├── __init__.py
    │   ├── process_handle.py
    │   ├── bindings.py
    │   └── bin/
    ├── messaging/                   — 可选：MQ / Event streaming 具体实现
    │   ├── __init__.py
    │   └── <message_client>.py
    └── web/                         — 可选：FastAPI / Flask / ASGI 等框架底座
        ├── __init__.py
        └── app.py
```

工程树约束：

1. `application/` 下核心子目录必须稳定为 `use_cases/`、`ports/`、`runtime/`。
2. Workflow 必须归入 `application/use_cases/workflows/`，禁止作为 application 一级目录。
3. DTO 必须归入 `application/use_cases/dtos.py` 或 `application/use_cases/dtos/`，禁止作为 application 一级目录。
4. Ports 必须归入 `application/ports/`，禁止放入 infrastructure。
5. runtime 必须归入 `application/runtime/`，禁止归入 DTO、Domain 或 Infrastructure。
6. Composition Root 必须集中在 `container.py` 或等价位置，禁止散落在 manager、controller、use case 中。
7. 具体技术实现必须归入 `infrastructure/`，外部输入输出转换必须归入 `adapters/`。
8. 包根 `__init__.py` 只能导出公共 API / Facade，不得导出 Application 内部对象。

---

## 三、 研发守则

### 1. 依赖方向守则

1. Domain 禁止依赖 Application、API、Adapters、Infrastructure。
2. Application 禁止依赖 API、Adapters、Infrastructure。
3. Application 只能通过 Ports 表达外部能力需求。
4. API / Facade 可以依赖 Application，但禁止依赖具体 Infrastructure 实现。
5. Adapters 可以依赖 API / Facade、Application DTO、Application Ports。
6. Infrastructure 可以依赖 Application Ports 并实现它们。
7. Composition Root 可以 import 所有层，但只能负责装配，不得承载业务逻辑。
8. Strict Driver DI 模式下，Adapters 禁止直接 import Infrastructure，必须通过 adapter-local backend protocol 与构造注入委托 backend。
9. adapter-local backend protocol 不等于 Application outport；UseCase 不得依赖 `adapters/drivers/backend_ports.py`。
10. backend 创建只能发生在 `container.py`、`infrastructure/drivers/backend_factory.py` 或等价 composition root / infrastructure factory。

---

### 2. 自动化边界校验守则

项目必须支持架构边界的静态校验。

建议使用：

- import-linter；
- deptry；
- ruff；
- mypy / pyright；
- pytest import boundary tests。

CI 中应当至少校验：

1. Domain 不 import 外层；
2. Application 不 import Infrastructure；
3. Application 不 import Adapters；
4. Ports 不 import Infrastructure；
5. Ports 不 import Adapters；
6. Strict Driver DI 模式下，Adapters 不 import Infrastructure；
7. Infrastructure 不 import Adapters；
8. API 不暴露 RuntimeContext；
9. infrastructure exception 不穿透 API；
10. public API 和 ports 无未解释的 `Any`。

可使用 grep、import-linter 或等价工具固化以下检查：

```text
rg "from <package>.infrastructure|import <package>.infrastructure" src/<package>/adapters
rg "from <package>.adapters|import <package>.adapters|from <package>.infrastructure|import <package>.infrastructure" src/<package>/application src/<package>/domain
rg "from <package>.adapters|import <package>.adapters" src/<package>/infrastructure
```

Coding Agent 生成或移动文件后，必须执行边界检查；边界检查失败时，必须优先修复架构边界，而不是修改测试规避失败。

---

### 3. API / Facade 守则

1. 外部消费者必须通过包根或 `api/` 暴露的 Facade 使用系统。
2. CLI、Web、测试脚本不得直接调用 `application/use_cases/atomic/` 内部文件。
3. API / Facade 不得暴露 RuntimeContext。
4. API / Facade 不得暴露 infrastructure 原生异常。
5. API / Facade 的 public method 必须有完整类型提示和返回值注解。
6. API / Facade 返回值必须稳定，禁止返回内部可变状态对象。

---

### 4. UseCase 守则

1. 原子 UseCase 必须表达单一执行意图。
2. Workflow 是 Composite UseCase，必须放在 `use_cases/workflows/`。
3. Workflow 不得成为独立架构层。
4. UseCase 不得直接创建或调用具体 driver、DB、socket、C library、SDK。
5. UseCase 必须通过 Ports 使用外部能力。
6. UseCase 中不得出现框架绑定代码，例如 Typer、FastAPI、Click、SQLAlchemy session、ctypes binding。
7. UseCase 的输入输出必须具有明确类型。
8. UseCase 异常必须收敛为 application-level exception。

---

### 5. DTO 守则

1. Application DTO SHOULD 使用 `dataclass(frozen=True)`。
2. API / Adapter 边界 DTO MAY 使用 Pydantic frozen model。
3. DTO 禁止包含业务逻辑。
4. DTO 禁止持有依赖注入对象。
5. DTO 禁止继承 ORM、Web Request、Driver Model、SDK Model。
6. DTO 禁止作为 runtime state 使用。
7. DTO 必须具备完整类型注解。
8. DTO 禁止通过 `dict[str, Any]` 长距离传递，除非该结构被显式定义为稳定 schema。

---

### 6. Ports 守则

1. Ports 必须是 ABC、Protocol 或等价抽象契约。
2. Ports 必须包含完整类型提示和返回值注解。
3. Ports 禁止包含具体实现。
4. Ports 禁止 import infrastructure。
5. Ports 禁止 import adapters。
6. Ports 禁止 import framework。
7. Ports 是 Application outport，只能表达 UseCase 所需外部能力，不得表达 adapter-local backend 委托细节。
8. Ports 禁止使用未解释的 `Any`。
9. 高频路径 Ports 必须优先设计 batch / buffer / frame-level 接口。
10. 新增业务外部能力时，必须先定义 application port，再实现 Infrastructure 或 Adapter。

---

### 7. Runtime 守则

1. runtime 是 Application 内部执行内核状态系统。
2. RuntimeContext 是 runtime root object。
3. RuntimeContext 必须显式声明所有子组件类型。
4. RuntimeContext 禁止使用 kwargs / setattr 动态挂载。
5. RuntimeContext 禁止作为 DTO、API response、adapter schema。
6. runtime 禁止 import infrastructure。
7. runtime 可维护状态，但业务规则不得堆入 RuntimeContext。
8. runtime 状态变化必须由 state、graph、event_bus 等专门组件承担。

---

### 8. Domain 纯洁度守则

1. Domain 禁止 import 外部技术栈。
2. Domain 禁止执行 I/O。
3. Domain 禁止创建线程、进程、Socket、event loop。
4. Domain 禁止 import asyncio 运行时原语。
5. Domain 可以建模抽象时间、deadline、tick、duration。
6. Domain 可以使用纯 Python 内存结构表达高性能数据视图。
7. Domain 中的协议、格式、算法、状态机必须可脱离外部环境单元测试。
8. Domain exception 只能表示领域规则或协议规则违反。

---

### 9. Infrastructure 守则

1. Infrastructure 承载所有具体技术实现。
2. Infrastructure 可以 import 第三方库、driver、native binding、framework。
3. Infrastructure 必须实现 Application Ports 或被 Adapter 委托调用。
4. Infrastructure 必须管理底层资源生命周期。
5. Infrastructure 必须捕获底层异常并转换为 application/domain exception。
6. Infrastructure 禁止把底层模型直接泄漏到 Application。
7. Infrastructure 高频操作必须优先使用 batch / buffer / stream。
8. Native / FFI 调用必须避免单元素频繁跨边界调用。
9. Infrastructure backend factory 负责创建真实 backend 和执行物理探测。
10. Infrastructure backend factory 禁止被 Application / Domain import。
11. Infrastructure backend factory 不得把物理资源对象泄漏到 Adapter public API。

---

### 10. Interface Adapter 守则

1. Controller 负责外部输入解析，不负责业务逻辑。
2. Presenter 负责输出格式化，不负责业务逻辑。
3. Serializer 负责格式转换，不负责业务逻辑。
4. Adapter 可以实现 Port，但不得让具体技术模型越过 Port 边界。
5. Adapter 必须调用 API / Facade 或稳定 Application contract。
6. Adapter 不得绕过 API / Facade 直接操作 runtime。
7. Adapter 捕获外部输入错误后，必须转换为稳定错误模型。
8. Strict Driver DI 模式下，Adapter 禁止直接 import Infrastructure。
9. Adapter-local backend protocol 只隔离 Adapter 与 backend，不得作为 UseCase outport。
10. Driver Adapter 必须通过构造函数接收 backend，不得自行创建真实 backend。

### 10.1 Composition Root 守则

1. `container.py` 是默认 composition root。
2. Composition Root 可以同时 import Application、Adapters 与 Infrastructure。
3. Composition Root 负责 wiring config loader、backend factory、driver adapter factory 与 runtime context。
4. Composition Root 不得包含业务规则、协议规则或领域状态转移逻辑。
5. Composition Root 不得替代 Application UseCase；它只负责组装并调用 UseCase / workflow。

---

### 11. 异常收敛守则

1. Domain exception 表示领域规则、协议规则、核心不变量违反。
2. Application exception 表示用例执行失败、外部能力不可用、runtime 装配失败。
3. Infrastructure 原生异常必须被捕获。
4. Native crash、socket error、database error、SDK error、filesystem error 不得穿透到 API / Facade。
5. API / Facade 只能暴露稳定异常、错误码或错误响应模型。
6. 不得在上层代码中依赖底层第三方异常类型。

---

### 12. Agent 自动化与类型提示守则

1. Coding Agent 新增能力时，必须先定位目标层，再创建文件。
2. Coding Agent 禁止创建 `services/`、`helpers/`、`misc/`、`common/` 等含混目录来逃避分层。
3. Coding Agent 新增外部能力时，必须先定义 `application/ports/` 契约，再实现 `infrastructure/`。
4. Coding Agent 新增 UseCase 时，必须同步补充 DTO、测试和异常路径。
5. `api/` 和 `ports/` 层 public method 必须 100% 具备类型提示和返回值注解。
6. 禁止在 public API 和 ports 中生成未解释的 `Any`。
7. 若必须使用不透明值，必须定义类型别名并写明语义。
8. Coding Agent 修改目录结构后，必须更新工程树文档和边界校验。
9. Coding Agent 不得因测试失败而放宽架构边界。
10. Coding Agent 不得将 framework、driver、native、ORM 模型直接塞入 DTO 或 Domain。
