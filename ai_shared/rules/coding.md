# 通用编码、接口、类型与注释规则

## 0. 规则定位

本规则适用于生产代码、工具代码、测试代码、脚本、迁移脚本和运维脚本。语言专属文档注释细则见 `python-docstring-cn.md`。本规则不替代测试、质量门禁、报告和需求跟踪规则；发生冲突时，采用更严格者。

## 1. 基本原则

1. 优先清晰、直接、可读。
2. 保持当前模块、语言和框架的局部风格。
3. 控制函数、方法、过程、脚本和模块复杂度；一个单元同时承担校验、编排、外部调用、异常转换、审计、持久化或资源管理时，应拆分阶段。
4. 不过度抽象，不为单一调用点制造复杂层级。
5. 不隐藏关键业务逻辑；安全、审计、租约、权限、回滚、重试、幂等、事务边界必须显式可见。
6. 不静默吞异常；捕获异常后必须转换稳定错误、记录审计/指标/日志、保留原始异常链、执行必要清理后继续，或明确说明为什么允许忽略。
7. 外部边界差异应隔离在 adapter、provider、repository、gateway、client、runner、driver、connector 或同等边界层。
8. 不做无关格式化，不批量重排与本任务无关的代码。
9. 不引入未经确认的新依赖。
10. 不恢复废弃文件，不把实验、测试、诊断能力接入生产路径。
11. 不把 mock、fake、stub、health check、脚本存在、单文件 passed 伪装成真实闭环。
12. 修改代码必须同步考虑测试、类型、注释、配置、schema、文档和需求状态的影响。

## 2. 架构与边界

1. 生产路径、工具路径、测试路径必须边界清楚；工具/实验模块不得被生产路径直接依赖，除非已有明确 ADR 允许。
2. 业务用例、应用服务或 orchestrator 负责业务编排，不应包含协议细节、数据库细节、CLI 解析或测试专用分支。
3. adapter / runner / repository / provider / gateway / driver 负责外部系统差异，不应泄漏到领域层或核心业务层。
4. composition root / bootstrap / wiring 层负责依赖装配；安全、审计、指标、租约、熔断、重试等生产横切能力不得在生产默认装配中缺失。
5. CRUD/API/CLI 层不得绕过权限、审计、dry_run、幂等、乐观并发、事务和输入校验要求。
6. scheduler / worker / lease / fencing / retry / backpressure 等运行时能力必须明确失败语义和恢复语义。
7. 运行时能力声明必须区分 declared capability、actual runtime availability、validated evidence。
8. 文档、需求和报告不得把 declared capability 写成 actual runtime availability。

## 3. 接口、类型与契约

1. public interface 必须语义清楚，包括输入、输出、错误、side effect、幂等性、事务边界和资源生命周期。
2. 支持类型系统的语言中，public function / method / class / struct / interface / API handler 应有清晰类型、签名或 schema。
3. 弱类型或脚本语言必须通过 schema、参数校验、注释、测试或文档表达输入输出契约。
4. 稳定多字段数据不应长期使用松散 map/dict/object；优先使用 dataclass、struct、record、DTO、schema、TypedDict、Pydantic model、Protocol、interface 或领域模型。
5. 不使用无约束动态类型；确需使用时必须限制在外部边界、反序列化边界、第三方库边界或测试替身，并说明原因。
6. ORM 行、DTO、Pydantic schema、API response、repository 返回值、配置模型、消息模型和协议帧的转换函数不得使用无约束 `Any`。必须使用真实类型、Protocol、TypedDict 或稳定 DTO。
7. 只有下列边界可临时使用 `Any`：第三方库返回值、动态反序列化入口、测试替身、兼容历史接口。使用时必须在局部注释或 docstring 中说明原因、收敛方式和退出条件。
8. 不使用无解释的类型检查、lint 或静态分析抑制指令，例如 `type: ignore`、`# noqa`、`// @ts-ignore`、`nolint`、`NOLINT`、`shellcheck disable`。
9. nullable / optional / pointer / nil / null 使用前必须显式处理。
10. SQL schema、ORM 字段、配置项、环境变量、CLI 参数、消息格式、文件格式、API schema 都视为数据契约。
11. 修改 public interface 时，必须同步修改调用方、测试、文档和需求状态。
12. 并发、异步、线程、进程、子进程、socket、文件句柄、数据库 session、锁、lease 等资源必须有关闭、释放或取消路径。

## 4. 文件级说明

1. 生产代码、工具代码、测试代码和脚本文件都必须有文件头说明或模块文档注释。
2. 文件头不得只写一句空泛描述，例如 `Utilities`、`Tests for xxx`、`CRUD routes`、`Helpers`。
3. 文件头应按文件类型说明：架构位置、主要职责、不负责什么、关键外部依赖或边界、关键 side effect、资源生命周期、事务/并发/超时/重试/回滚语义、安全/权限/审计/脱敏要求、测试证据等级。
4. 简单 `__init__.py` 可使用简短文件头；如果导出 public interface，必须说明导出边界。
5. 批量治理任务中不得只补空泛文件头；必须补足真实职责和边界。

## 5. 函数、方法、类与 API 注释

1. public class / Protocol / dataclass / enum / function / method / API route / CLI command 必须有文档注释。
2. private 函数如果涉及调度、协议、权限、审计、lease、fencing、事务、重试、异常转换、资源释放、复杂 fixture，也必须有文档注释或关键注释。
3. API route 模块内的 private helper，只要参与权限、审计、session、事务、响应模型转换、分页、错误转换，也必须按 API 边界函数写完整 docstring。
4. ORM -> DTO、ORM -> API Response、DTO -> ORM、API payload -> domain object、dict -> model、model -> dict、protocol frame -> DTO 的转换函数必须写完整 docstring，且不得使用无约束 `Any`。
5. 文档注释必须说明语义，不只是重复函数名。
6. 对以下函数，若存在参数，必须写 `Args`；若返回值不是 `None`，必须写 `Returns`；若可能主动抛出稳定异常或依赖外部系统异常，必须写 `Raises` 或在正文中说明异常传播：
   - public function / method；
   - API route handler；
   - CLI command / entrypoint / composition root；
   - use case / service / repository / adapter / provider / gateway / runner / driver；
   - ORM/API/DTO/schema/protocol 转换函数；
   - 涉及权限、审计、事务、lease、fencing、重试、超时、回滚、资源释放的 private helper；
   - 复杂 fixture / fake / mock / stub / evidence gate。
7. API route handler 即使函数体简单，也必须说明权限、审计、dry_run、幂等、乐观并发、事务和返回语义中涉及的关键项。
8. adapter / runner / repository / gateway / client 方法必须说明外部系统失败如何转换、是否重试、是否释放资源。
9. 测试代码中的复杂 fixture、fake、mock、stub、环境门禁和证据等级判断必须说明边界，避免把测试替身误认为真实闭环。

## 6. 不合格 docstring 判定

以下 docstring 一律判为不合格，需要重写：

1. 只有一句“将 X 转换为 Y”“获取 X”“创建 X”“更新 X”“删除 X”“返回 X”。
2. 有参数但缺少 `Args`，且该函数属于本规则第 5.6 条范围。
3. 返回值不是 `None` 但缺少 `Returns`，且该函数属于本规则第 5.6 条范围。
4. 涉及权限、审计、事务、ORM、数据库 session、外部依赖、资源释放、lease/fencing、子进程、socket，却未说明 side effect、失败边界或资源边界。
5. 使用英文业务说明，且不属于协议名、标准名、第三方 API、日志 key、配置键、错误码、命令或库名。
6. 只描述“做了什么”，不说明调用契约、输入输出语义、边界或风险。
7. 把 mock/contract/simulator 证据写成真实生产验证。
8. 保留 `Any`、`type: ignore`、`# noqa` 等但没有说明原因和退出条件。

## 7. 多语言代码质量

1. 遵循仓库配置的 lint、format、type-check、test 工具。
2. 修改代码后，必须优先执行或说明未执行原因：语法/编译检查、lint/static analysis、type-check、affected tests。
3. 涉及全局质量治理时，应执行目录级检查，并对既有问题与本轮新增问题分开归类。
4. 禁止裸 catch / except / rescue。
5. 捕获通用异常或错误时，必须转换稳定错误、记录日志/审计/指标、执行清理后重新抛出，或说明继续执行为何安全。
6. 异步、并发和子进程代码必须注意取消、清理、超时和 backpressure。
7. 网络、文件、数据库、队列、子进程、外部系统调用必须有超时、deadline 或可取消机制；长期任务必须有可观测心跳或状态。
8. 重试必须有上限、退避策略和错误分类，不得无限重试。
9. 不在生产代码中保留未隔离的调试分支、临时开关和测试专用逻辑。
10. 日志不得泄漏密钥、凭证、token、个人信息或敏感配置。

## 8. SQL / ORM / 配置

1. 不凭记忆推断字段，必须读取当前 ORM、schema、migration 或配置定义。
2. 查询优先沿用仓库当前风格。
3. 事务边界必须清晰；跨 session / context / transaction 对象不得直接修改并假设自动持久化。
4. schema 变化必须说明兼容性、迁移策略和存量数据处理。
5. 新增 NOT NULL 字段必须处理已有数据。
6. 配置项变化必须检查默认值、示例、测试、部署文档和回滚影响。
7. 运行时配置变更必须考虑并发、幂等、版本冲突和审计记录。
8. 外部依赖配置不得默认开启危险能力；写入、控制、删除等高风险能力应默认关闭。

## 9. 注释与文档注释

1. 注释解释原因、边界、假设、风险、约束和非显然行为，不重复代码表面行为。
2. public interface、复杂调度、协议、性能指标、异常边界、权限、审计、租约、fencing、事务、回滚、重试、子进程协议应有必要注释或文档注释。
3. 新增或修改的业务注释默认使用项目主要语言（中文）；第三方 API、协议字段、标准字段、日志 key、异常类名、CLI 参数、环境变量可保留英文。
4. 不给简单代码堆无意义注释。
5. 修改旧代码时，不只修逻辑；如果相关接口缺少必要文档注释，应一并补齐。
6. 文件头、类、public 函数、API route、CLI command、复杂 private helper 五类对象必须分别判断；不能只补类注释后跳过函数注释。
7. 英文业务注释/docstring 明确属于违规，除非属于协议名、标准名、第三方 API、日志 key、配置键、错误码、命令或库名。

## 10. 测试与证据

1. 行为变化必须测试。
2. bug 修复原则上必须补回归测试。
3. public interface、schema、配置、CLI、协议、权限、审计、lease、fencing、消息格式变化必须覆盖相关调用或解析路径。
4. 主链路变化至少需要 smoke 或 integration 验证。
5. 测试必须区分证据等级：unit/mock、contract/stub、simulator、integration、e2e/field。
6. 不允许降低断言、删除失败测试、增加无条件 skip 或吞异常来制造通过。
7. 不能只跑单文件 passed 就声称全量通过。
8. 未执行的检查必须标记为未执行或 environment-pending，不得写成 passed。

## 11. 文档与需求状态

1. 代码、测试、配置、schema、脚本、报告与需求跟踪表必须保持一致。
2. 新增、删除、移动、重命名、职责变化文件必须触发目录树更新判断。
3. 需求状态只能基于当前真实证据更新。
4. 如果只有 mock/contract/simulator 证据，不得标为真实生产验证完成。
5. 如果发现状态高估，必须明确降级或标注 pending。
