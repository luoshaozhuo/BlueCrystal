# Python 中文注释与 Google-style Docstring 规则

本规则补充 `coding.md`，不削弱其中任何要求。适用于 Python 生产代码、工具代码、测试代码、脚本代码和迁移脚本。

## 1. 总原则

1. Python 文件必须同时接受文件级、类级、函数级、测试证据级检查。
2. 新增或修改的业务注释、module docstring、class docstring、function docstring 正文默认使用中文。
3. 英文业务注释/docstring 属于违规；以下可保留英文：第三方 API 名称、协议字段名（如 `GOOSE`、`SV`、`MMS`、`IEC 61850`、`Modbus`、`OPC UA`、`MQTT`、`IEC 104`）、标准字段名、日志 key、异常类名、CLI 参数名、环境变量名、配置键、数据库字段名、错误码、命令名、库名。
4. 不为翻译而翻译标准名词；协议、库、命令、错误码应保持原文准确。
5. 文档注释解释职责、边界、假设、风险和语义，不重复代码表面行为。
6. 不允许把补注释当成行为修复；代码行为仍必须由测试验证。
7. 中文规则适用优先级：文件头 > 类/函数 docstring > 内联注释。任一层级使用英文业务说明即为违规。
8. Docstring 不能替代类型标注。mypy/pyright 能发现的问题必须通过准确类型或显式边界类型修复，不能只靠说明文字掩盖。

## 2. 文件头 / Module Docstring

每个 `.py` 文件必须有 module docstring。简单文件也至少要说明用途；复杂文件必须说明职责边界。

### 2.1 生产代码文件头至少说明

```text
1. 本文件在架构中的位置，例如 use case、adapter、repository、runtime、route、runner；
2. 主要职责；
3. 明确不负责什么；
4. 关键外部依赖或边界；
5. 关键 side effect；
6. 资源生命周期、事务、并发、超时、重试、回滚语义中涉及的关键项；
7. 安全、权限、审计、脱敏、证据等级中涉及的关键项。
```

不是每个文件都要包含全部条目，但涉及的关键语义必须写清楚。

### 2.2 测试文件头至少说明

```text
1. 被验证对象；
2. 证据等级：unit/mock、contract/stub、simulator、integration、e2e/field；
3. 使用的 fake/mock/stub/simulator 与真实依赖的差异；
4. 不能证明什么；
5. 关键环境依赖或跳过条件。
```

### 2.3 文件头禁止事项

1. 禁止只有 `Utilities`、`Tests for xxx`、`CRUD routes`、`Helpers` 这类空泛说明。
2. 禁止英文业务说明，除非文件本身是第三方协议/标准名词密集且中文会降低准确性；即便如此，职责和边界仍应中文说明。
3. 禁止文件头写“已完成真实验证”，但测试实际只是 mock/contract/simulator。
4. 禁止文件职责变化后不更新文件头。

## 3. 必须写 Docstring 的对象

### 3.1 生产代码必须写 docstring 的对象

```text
1. public class / Protocol / ABC / dataclass / enum / TypedDict / Pydantic model
2. public function / method
3. FastAPI route handler / CLI command / entrypoint / composition root
4. use case / service / repository / adapter / provider / gateway / runner / driver
5. runtime / scheduler / worker / daemon / job handler
6. 协议解析、序列化、反序列化、stdin/stdout 协议、socket/subprocess 边界
7. 权限、认证、审计、指标、脱敏、密钥、证书、TLS、安全策略
8. lease、fencing、事务、幂等、乐观并发、回滚、重试、超时、backpressure
9. ORM -> DTO、ORM -> API Response、DTO -> ORM、API payload -> domain object、dict -> model、model -> dict、protocol frame -> DTO 的转换函数
```

### 3.2 复杂 private helper 也必须写 docstring

以下 private helper 即使名称以 `_` 开头，也必须有 docstring 或关键注释：

```text
1. 返回多字段结构（dict/tuple/dataclass）且调用方需要理解字段语义的 helper；
2. 修改外部状态（module-level variable、class attribute、global config）的 helper；
3. 捕获通用异常后继续执行的函数，必须说明为什么继续安全；
4. 创建、释放或持有资源（文件、socket、subprocess、DB session、锁、lease）的函数；
5. 涉及调度、协议解析、安全边界、审计逻辑的 helper；
6. 实现超时、重试、回滚、fallback 逻辑的 helper；
7. API route 模块中参与权限、审计、session、事务、响应模型转换、分页、错误转换的 helper。
```

### 3.3 测试代码必须写 docstring 的对象

```text
1. 测试文件：module docstring 说明被验证对象、证据等级、fake/mock/stub 与真实依赖的差异、不能证明什么；
2. 复杂 fixture：说明装配了哪些替身、与真实依赖的差异、覆盖的场景范围；
3. fake 实现：说明行为边界——哪些行为被真实模拟、哪些行为是硬编码/简化；
4. mock 配置：如果 mock 行为影响业务语义（如 return_value 模拟异常路径），需要注释说明；
5. stub 实现：说明哪些接口被实现、哪些被跳过、与真实实现的语义差异；
6. 证据等级判定函数/装饰器：说明判定逻辑、门禁条件和误判风险；
7. 并发、故障注入、超时、权限、审计、回滚、lease/fencing、协议、native runner 相关的测试函数。
```

## 4. Function / Method Docstring 内容要求

复杂 public interface 的 docstring 至少覆盖相关项：职责边界；不负责什么；关键参数；返回值或输出语义；稳定异常、错误码或错误分类；side effect；资源生命周期；并发、幂等、事务、超时、取消、重试、回滚语义；安全、权限、审计、脱敏；测试替身与真实依赖差异。

### 4.1 Google-style 标题

允许保留以下英文标题：

```text
Args:
Returns:
Raises:
Yields:
Attributes:
Examples:
Notes:
```

标题下的正文默认中文。

### 4.2 Args / Returns / Raises 硬性要求

以下对象只要存在参数，就必须写 `Args`；只要返回值不是 `None`，就必须写 `Returns`；只要主动抛出稳定异常、转换异常、依赖外部系统异常，或调用方必须理解异常传播，就必须写 `Raises` 或在正文中说明异常传播策略：

```text
1. public function / method；
2. FastAPI route handler；
3. CLI command / entrypoint / composition root；
4. use case / service / repository / adapter / provider / gateway / runner / driver；
5. runtime / scheduler / worker / daemon / job handler；
6. ORM/API/DTO/schema/protocol 转换函数；
7. 涉及权限、审计、事务、lease、fencing、重试、超时、回滚、资源释放的 private helper；
8. 复杂 fixture / fake / mock / stub / evidence gate。
```

### 4.3 Side Effects / Notes 要求

以下函数必须在正文或 `Notes` 中说明 side effect：

```text
1. 修改数据库、缓存、队列、文件、子进程、网络连接、审计、指标、lease、lock 的函数；
2. 打开或关闭资源的函数；
3. 改变全局配置、环境变量、运行时状态、scheduler job、worker 状态的函数；
4. 触发外部系统调用或依赖外部系统状态的函数。
```

## 5. 类型标注与 Any 约束

1. public interface 必须有清晰类型、签名或 schema。
2. ORM 行、DTO、Pydantic schema、API response、repository 返回值、配置模型、消息模型和协议帧的转换函数不得使用无约束 `Any`。
3. 对于 ORM -> API Response、ORM -> DTO、DTO -> ORM、API payload -> domain object、dict -> model、model -> dict 的转换函数，参数和返回值必须使用真实类型、Protocol、TypedDict 或稳定 DTO。
4. `Any` 只能用于外部未知边界、第三方库、动态反序列化或测试替身；使用后应尽快收敛到内部稳定类型，并通过注释或 docstring 说明原因。
5. 类型检查、lint 或静态分析抑制指令必须写明原因和后续移除条件，例如 `type: ignore`、`# noqa`、`# pylint: disable`。
6. nullable / Optional 使用前必须判断或转换。
7. 如果 IDE/mypy/pyright 提示函数参数缺少类型标注，不能通过补 docstring 替代，必须补签名类型。

## 6. 不合格 Docstring 判定

以下 docstring 一律判为不合格：

```text
1. 只有一句“将 X 转换为 Y”“获取 X”“创建 X”“更新 X”“删除 X”“返回 X”；
2. 只有英文短句业务说明；
3. 有参数但缺少 Args，且函数属于 4.2 的范围；
4. 返回值不是 None 但缺少 Returns，且函数属于 4.2 的范围；
5. 涉及权限、审计、事务、ORM、数据库 session、外部依赖、资源释放、lease/fencing、子进程、socket，却没有说明 side effect、失败边界或资源边界；
6. 只描述“做了什么”，没有说明调用契约、输入输出语义、边界或风险；
7. 把 mock/contract/simulator 证据写成真实生产验证；
8. 保留 Any、type: ignore、# noqa 等但没有说明原因和退出条件。
```

## 7. 类与数据模型 Docstring

1. 类 docstring 必须说明职责，不只重复类名。
2. dataclass / Pydantic model / DTO / TypedDict 必须说明字段整体语义和生命周期。
3. Protocol / ABC 必须说明调用方契约、实现方责任、异常和 side effect。
4. adapter / repository / runner / client 必须说明外部系统边界和错误转换。
5. runtime / scheduler / worker 必须说明并发模型、生命周期和失败传播。

## 8. API Route / CLI / Entrypoint / Composition Root Docstring

1. API route handler 即使函数体简单，也必须说明权限、审计、dry_run、幂等、乐观并发、事务和返回语义中涉及的关键项。
2. API route 模块中的 `_authorize`、`_open_session`、`_emit_success`、`_response`、`_paginate`、`_ensure_*` 等 helper 只要参与权限、session、审计、事务、响应模型转换、分页或错误转换，也必须写完整 docstring。
3. CLI command / entrypoint 必须说明启动的运行时组件、配置来源（环境变量/配置文件/CLI 参数）、资源生命周期和失败退出语义。
4. composition root / bootstrap / wiring 函数必须说明默认注入的安全、审计、指标、租约、重试、缓存、外部依赖；不得把 no-op/allow-all 默认写入 docstring 时写成“生产安全完成”，必须如实说明当前为最小装配，注明风险。

## 9. 测试代码 Docstring

1. 测试文件必须在 module docstring 说明被验证对象、证据等级（L1-L5）、使用的 fake/mock/stub 与真实依赖的差异、不能证明什么、关键环境依赖或跳过条件。
2. 复杂 fixture、factory、fake、mock、stub 必须说明边界和不能证明的能力。
3. 测试 fake 必须注释行为边界——哪些行为被真实模拟、哪些是硬编码/简化；不得在 fake 实现中写“生产可用”。
4. 测试 mock 如果影响业务语义（如 return_value 模拟异常路径），需要注释说明。
5. 测试 stub 需要说明哪些接口被实现、哪些被跳过、与真实实现的语义差异。
6. 测试函数如果只验证简单纯函数，可依赖清晰名称；否则必须写 docstring。
7. 并发、故障注入、超时、权限、审计、回滚、lease/fencing、协议、native runner、subprocess、socket、数据库、Redis、Kafka、证据等级容易混淆的测试函数必须写 docstring。
8. skip/xfail 必须说明环境条件、跳过原因和退出条件；不得隐藏失败。

## 10. 普通注释

1. 注释解释为什么，而不是重复做了什么。
2. 适合写注释的内容包括：非显然业务规则、安全或审计要求、并发和时序约束、兼容性取舍、为什么不能简化、为什么使用 fallback、为什么某个异常允许继续、测试中 fake/mock 与真实依赖的差异。
3. 不适合写注释的内容包括：与代码明显重复的描述、过期 TODO、没有 owner/条件/退出标准的临时说明。
4. TODO 必须说明触发条件或后续处理方式，不能长期悬空。
5. 英文业务注释应改为中文；标准名、协议名、字段名、错误码和命令可保留英文。

## 11. 异常与清理说明

1. 裸 `except` 禁止。
2. 捕获通用 `Exception` 必须有明确处理意图，并且不得静默吞掉。
3. 捕获异常后如果继续执行，必须说明为什么继续是安全的。
4. 需要释放资源的函数，docstring 或注释必须说明释放路径，代码必须使用 finally、context manager 或等价机制。
5. 对 lease、lock、transaction、subprocess、socket、file handle、数据库 session、Redis/Kafka 连接等资源，必须说明异常路径是否释放。

## 12. 质量治理清单格式

执行注释治理任务时，必须先生成清单，再修复。清单至少包含：文件路径；文件类型；是否有 module docstring；文件头是否说明职责边界；英文业务 docstring/注释；缺失 docstring 的 public class/function/method；缺失 docstring 的复杂 private helper；缺失 Args / Returns / Raises 的对象；无约束 Any；无解释 type: ignore / noqa / pylint disable；裸 except / 静默吞异常；证据等级误写风险；优先级；修复状态。

## 13. 禁止事项

1. public interface 无类型、签名或契约说明。
2. 复杂 public interface 无文档注释。
3. 文件无 module docstring。
4. 文件头只有空泛描述。
5. 新增或修改业务注释使用英文。
6. 有参数的关键函数缺少 Args。
7. 返回值非 None 的关键函数缺少 Returns。
8. ORM/API/DTO/schema 转换函数使用无约束 Any。
9. 无解释的类型检查或 lint 抑制指令。
10. 裸 `except`。
11. 静默吞异常。
12. 大量无意义注释。
13. 把注释当作修复，代码行为没有对应改变。
14. 把测试替身注释成真实生产能力。
