# Agent 反馈与报告规则

## 1. 编码阶段反馈

普通编码反馈只说明：

```text
1. 修改的文件和行为；
2. 必要的兼容性、迁移或使用说明；
3. 已知实现风险。
```

不输出检查状态、`NOT_RUN` 清单或例行检查命令提示。

## 2. 测试阶段 `/test` 反馈

```text
直接范围:
- staged files/symbols:
- excluded unstaged/untracked files:
- mixed-index files:

测试变更:
- ...

结果:
- PASS:
- FAIL:
- NOT_RUN:

证据:
- commands:
- relevant tests:

下一步:
- 无 / 返回编码阶段
```

## 3. 验证阶段 `/validate` 反馈

```text
影响范围:
- staged change roots:
- callers/dependents:
- contracts/wiring:
- mixed-index files:

结果:
- PASS:
- FAIL:
- NOT_RUN:

证据:
- commands:
- files and relationships:

结论:
- 通过 / 不通过
```

## 4. 全量测试 `/test-all` 反馈

```text
范围:
- current workspace
- include-heavy: yes/no

结果:
- PASS:
- FAIL:
- NOT_RUN:

证据:
- commands:
- suites:

结论:
- 全量通过 / 不通过 / 部分未执行
```

## 5. 证据规则

1. 只记录真实执行的命令和真实读取的文件。
2. `PASS`、`FAIL`、`NOT_RUN` 必须与真实结果一致。
3. 局部结果不得写成全量结果。
4. skipped、mock、fake、stub、health check、脚本存在或环境 pending 不得写成真实通过。

## 6. 报告与长期文档

只有用户明确要求时才写入 `ai_shared/reports/`、需求跟踪或 project_tree。不因编码、测试或验证阶段自动生成报告。
