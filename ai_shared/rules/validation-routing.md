# 验证路由规则

## 1. 基本原则

1. 验证范围跟随改动影响。
2. 最小验证必须覆盖本轮风险。
3. 不默认全量测试。
4. 不默认长测或重回归。
5. 跳过验证必须说明原因和风险。

## 2. Python 改动

优先执行：

```bash
python -m py_compile <changed-python-files>
ruff check <changed-python-files-or-related-package>
mypy <affected-package-or-files>
pytest <affected-tests> -q
```

工具不存在时不得虚构通过，必须说明替代验证和风险。

## 3. 分类规则

失败必须分类为：

```text
本轮引入
既有失败
环境失败
flaky
依赖缺失
验证命令错误
```

## 4. 收口规则

存在本轮引入 failed 时不得收口。

存在环境 pending 时不得写成通过。
