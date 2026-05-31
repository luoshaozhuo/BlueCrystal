# 验证路由规则

## 1. 基本原则

1. 验证范围跟随真实变更影响。
2. 最小验证必须覆盖本轮风险。
3. 不默认全量测试、长测或重回归。
4. 跳过验证必须说明原因和风险。
5. 工具不存在时不得虚构通过，必须说明替代验证和风险。

## 2. 按变更类型选择验证

```text
源码行为变化：
- 语法/编译检查
- lint/static analysis
- type-check（如适用）
- affected unit/integration tests

配置/env/CLI/API/schema 变化：
- 配置解析测试
- schema 或 migration 兼容性验证
- 文档/示例同步检查
- 相关集成或 smoke 测试

协议/消息/文件格式变化：
- parser/serializer contract tests
- backward/forward compatibility tests
- 真实依赖或 simulator/integration 证据等级说明

安全/权限/审计/lease/fencing 变化：
- deny/conflict/failure path tests
- audit/metrics evidence
- concurrency 或 failover 测试（如可负担）

文档/规则/报告变化：
- 路径、格式、规则一致性检查
- 通常不需要代码测试，但必须说明
```

## 3. 语言命令参考

执行命令以仓库配置为准；可参考 `quality-gate.md` 的语言门禁清单。

## 4. 分类规则

失败必须分类为：

```text
本轮引入
既有失败
环境失败
flaky
依赖缺失
验证命令错误
未执行 / environment-pending
```

## 5. 收口规则

1. 存在本轮引入 failed 时不得收口。
2. 存在 environment-pending 时不得写成通过。
3. 如果只运行局部测试，最终反馈必须说明局部范围。
4. 如果只有 mock/contract/simulator 证据，不得写成真实 e2e/field 通过。
