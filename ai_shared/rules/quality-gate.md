# 质量门禁规则

## 1. 生效边界

质量门禁不在普通编码阶段自动执行。只在用户显式调用 `/test`、`/validate` 或 `/test-all` 时，按对应范围选择命令。

## 2. 阶段门禁

### `/test`

仅选择 staged diff 直接修改代码的必要测试；需要支持测试执行时，可对直接文件执行最小 syntax/compile 检查。

### `/validate`

对 staged 修改及其真实引用/依赖范围选择：

```text
1. syntax/compile；
2. lint/static analysis；
3. type-check；
4. 直接和受影响测试；
5. 契约、配置、schema、安全、审计和生产路径边界专项检查。
```

### `/test-all`

对当前整个工作区执行仓库定义的全仓 syntax/compile、lint、type-check 和全部常规自动化测试。

## 3. 结果分类

检查或测试结果只使用 `PASS`、`FAIL`、`NOT_RUN`。失败必须分类为本次变更引入、既有失败、环境失败、flaky、依赖缺失或验证命令错误。

## 4. 收口规则

1. 存在本次变更引入的 `FAIL` 时不得写成通过。
2. 必需项为 `NOT_RUN` 时不得写成通过，除非用户明确调整范围。
3. 未执行项不得写成 `PASS`，局部验证不得写成全量验证。
4. `project-tree-update` 和 `project-tree-reset` 不属于质量门禁。

## 5. 禁止事项

不允许无说明的类型/lint 抑制、裸 catch/except/rescue、静默吞异常、fake OK，或把 skipped、mock、health check、脚本存在写成真实通过。
