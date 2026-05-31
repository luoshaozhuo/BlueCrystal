# heavy-regression

## 1. 目的

用户明确要求时运行重回归、长测或发布前验证。

## 2. 触发条件

必须用户明确要求，或 handoff 明确指定。

禁止使用：
- 普通小改动默认触发。
- 未说明耗时、环境依赖和风险就直接运行。

## 3. 操作步骤

1. 列出验证矩阵。
2. 标注每项预计耗时、环境依赖、失败影响。
3. 等待 prompt 或用户授权范围内执行。
4. 执行后按 passed / failed / skipped / pending / environment-failed 分类。
5. 不把局部通过写成全量通过。

## 4. 输出格式

```text
skill result:
- skill: heavy-regression
- matrix:
- commands run:
- passed:
- failed:
- skipped:
- pending:
- environment:
- risk:
```
