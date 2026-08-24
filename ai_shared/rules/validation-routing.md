# 验证路由规则

## 1. 规则定位

本规则只在用户显式调用 `/validate` 或 `/test-all` 时生效。普通编码不读取、不执行本规则。

## 2. `/validate` 影响范围

1. 以 Git index 为唯一范围基线，通过 `git diff --cached` 和 `git diff --cached --name-only` 获取 staged 变更起点。
2. `git diff` 只用于识别 mixed staged/unstaged 文件；untracked 内容不纳入范围起点。
3. 从 staged hunks 提取修改的函数、方法、类、模块、public interface、配置、schema、消息和文件契约。
4. 扩大到真实的 import、调用方、实现类、上下游契约、配置/schema 消费方、composition root、注册表、adapter、repository、scheduler、worker 及其测试。
5. 文本搜索只用于发现候选文件，不能替代真实 import、调用、类型和装配关系判断。

## 3. `/validate` 必跑集合

根据真实影响范围选择：

```text
1. staged diff 直接对应的测试；
2. 引用方、依赖方、实现方和装配路径的测试；
3. 影响范围内的 syntax/compile、lint 和 type-check；
4. 受影响的契约、schema、配置和生产路径边界检查。
```

只有真实影响范围需要时才运行 integration、contract 或 smoke，不得自动扩大为全仓测试。

## 4. `/test-all` 全量范围

1. 不再根据 diff 裁剪。
2. 对当前整个工作区执行仓库定义的全仓 syntax/compile、lint、type-check、unit、integration 及常规 smoke/regression 集合。
3. 默认不执行 performance、长稳、真实外部依赖或完整部署演练。
4. 只有用户显式指定 `include-heavy` 时才加入高成本项，执行前必须列出预计成本和环境依赖。

## 5. 结果和收口

1. 结果只允许 `PASS`、`FAIL`、`NOT_RUN`。
2. 必跑项存在 `FAIL` 或未经用户调整范围的 `NOT_RUN` 时，不得写成通过。
3. 局部结果不得写成全量结果。
4. mock、fake、stub、simulator、health check 或脚本存在不得写成生产真实闭环。
5. 混合 staged/unstaged 文件必须在结果中标注 `MIXED_INDEX_FILE`，说明命令运行于完整工作区。
