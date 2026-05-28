# Python 中文注释与 Google-style Docstring 规则

本规则补充 `coding.md`，不削弱原规则。

## 1. 中文注释

1. 新增或修改的业务注释默认使用中文。
2. 第三方 API、协议字段、标准字段、日志 key、异常类名、CLI 参数、环境变量可保留英文。
3. 注释解释原因、边界、假设和风险，不重复代码表面行为。

## 2. Google-style docstring

以下对象必须有必要 Google-style docstring：

```text
public use case
public port / adapter
public service / repository
runtime / scheduler / worker
协议解析、外部 API 边界
复杂异常转换、重试、回滚、lease、fencing、audit、metrics
```

docstring 正文默认中文；`Args`、`Returns`、`Raises` 标题可保留英文。

## 3. 禁止事项

1. public interface 无类型标注。
2. 复杂 public interface 无 docstring。
3. 无解释 `type: ignore`。
4. 裸 `except`。
5. 静默吞异常。
