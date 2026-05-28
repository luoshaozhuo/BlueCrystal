# 测试规则

## 1. 必测场景

1. 行为变化必须测试。
2. bug 修复原则上必须补回归测试。
3. public interface、schema、配置、CLI、协议变化必须覆盖相关调用或解析路径。
4. 主链路变化至少需要 smoke 或 integration 验证。
5. 纯文档变化通常不需要代码测试，但必须说明原因。

## 2. 禁止事项

1. 不允许把“能运行不报错”当作有效测试。
2. 不允许降低断言、删除失败测试或吞异常来制造通过。
3. 不允许把 skipped、mock、fake、health check 写成真实通过。
4. 不允许只跑单文件 passed 就声称全量通过。

## 3. 测试职责

1. code-implementer 负责补充或修改相关测试。
2. test-validator 负责独立验证和失败分类。
3. project-steward 只记录已验证事实，不得创造测试结论。
