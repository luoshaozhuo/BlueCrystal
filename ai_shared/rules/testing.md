# 测试规则

## 1. 基本原则

1. 行为变化必须测试。
2. bug 修复原则上必须补回归测试。
3. public interface、schema、配置、CLI、协议、权限、审计、lease、fencing、消息格式变化必须覆盖相关调用或解析路径。
4. 主链路变化至少需要 smoke 或 integration 验证。
5. 纯文档变化通常不需要代码测试，但必须说明原因。
6. 不默认全量测试、长测或重回归；验证范围跟随变更影响。

## 2. 证据等级

测试结论必须说明证据等级：

```text
L1 unit/mock：只证明本地逻辑。
L2 contract/stub：只证明接口约束。
L3 simulator：证明仿真环境闭环。
L4 integration：证明真实依赖或受控依赖闭环。
L5 e2e/field：证明端到端或现场真实闭环。
```

不得把低等级证据写成高等级证据。

## 3. 禁止事项

1. 不允许把“能运行不报错”当作有效测试。
2. 不允许降低断言、删除失败测试或吞异常来制造通过。
3. 不允许把 skipped、mock、fake、health check 写成真实通过。
4. 不允许只跑单文件 passed 就声称全量通过。
5. 不允许新增无条件 skip 掩盖缺陷。
6. 不允许把测试工具能力写成生产能力。

## 4. 测试职责

1. code-implementer 负责补充或修改相关测试。
2. test-validator 负责独立验证和失败分类。
3. project-steward 只记录已验证事实，不得创造测试结论。
