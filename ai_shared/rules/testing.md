# 测试规则：什么时候写测试，写什么测试

本文件用于指导 coding agent 判断什么时候需要新增、修改、运行测试。

## 1. 总原则

1. 行为变化必须测试。
2. bug 修复原则上必须补回归测试。
3. public interface、schema、配置、CLI、协议变化必须覆盖相关调用或解析路径。
4. 主链路变化至少需要 smoke 或 integration 验证。
5. 纯文档变化通常不需要代码测试，但必须说明原因。
6. 不允许把“能运行不报错”当作有效测试。
7. 不允许降低断言、删除失败测试或吞异常来制造通过。
8. 编码与测试应同轮完成。

## 2. 必须新增或修改测试的情况

| 改动类型 | 测试要求 |
|---|---|
| 新增功能 | 正常路径、关键边界、主要异常路径 |
| 修复 bug | 回归测试，证明 bug 不再复现 |
| 修改业务行为 | 修改或新增行为测试 |
| 修改错误处理 | 异常路径、错误转换、降级行为 |
| 修改 public interface | 调用方或接口契约测试 |
| 修改 schema / ORM | repository、migration、初始化或查询路径 |
| 修改配置 / env / CLI | 默认值、合法值、非法值、缺省值、优先级 |
| 修改协议 / native runner | 协议输出、adapter 解析、stdout/stderr 边界 |
| 修改调度 / 异步 / 并发 | 时序、取消、超时、失败隔离 |
| 修改性能指标 | 指标定义、字段命名、报告输出 |
| 重构但声称行为不变 | 运行已有行为测试，必要时补保护性测试 |

## 3. 可以不新增测试的情况

以下情况可以不新增测试，但必须在反馈中说明：

- 只改注释或纯说明文档。
- 只改格式且无行为变化。
- 只改非执行性示例。
- 目标文件已有测试覆盖，且本轮不改变可观察行为。
- 用户明确要求只做方案、文档整理或 prompt 生成。

## 4. 测试类型选择

| 场景 | 优先测试类型 |
|---|---|
| 纯函数、解析、映射、计算 | unit |
| use case 与 port / adapter 协作 | unit + integration |
| 协议 adapter 与本地 fake server | integration |
| CLI 启动与参数解析 | unit + smoke |
| 主流程最小闭环 | smoke / e2e |
| 数据库 repository | unit / integration |
| native runner | native build + integration |
| 性能容量 | performance，仅用户要求或任务指定 |
| 回归 bug | regression，可放入对应 unit/integration/e2e |

## 5. 测试代码质量

1. 测试命名表达行为。
2. 使用 Arrange / Act / Assert。
3. 一个测试聚焦一个主要行为。
4. fixture 表达领域概念，不隐藏关键行为。
5. mock 优先使用依赖注入，少 patch 全局对象。
6. 测试数据小而明确。
7. 异步测试必须清理后台任务。
8. 性能测试必须输出可诊断指标。

## 6. 测试失败处理顺序

1. 先判断失败是否由本轮修改引入。
2. 再判断失败属于实现错误、测试过期、环境问题还是既有失败。
3. 如果是实现错误，优先修实现。
4. 如果是测试过期，必须说明行为变化依据后再改测试。
5. 如果是环境问题，必须报告原因，不得伪造通过。
6. 如果是既有失败，必须说明与本轮关系。
7. 不得简单删除失败测试或削弱断言。

## 7. 性能测试要求

性能测试不能只输出 pass/fail。应尽量区分：

- read call duration。
- tick duration。
- client period。
- jitter。
- miss rate。
- achievement ratio。
- error rate。
- post-processing duration。
- server update period。
