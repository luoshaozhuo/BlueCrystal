# 编码、接口、类型与注释规则

## 1. 基本原则

1. 优先清晰、直接、可读。
2. 保持当前模块局部风格。
3. 控制函数复杂度，必要时拆分阶段。
4. 不过度抽象。
5. 不隐藏关键业务逻辑。
6. 不静默吞异常。
7. 外部边界差异应隔离在 adapter、provider、repository 或相应边界层。
8. 不做无关格式化。
9. 不引入未经确认的新依赖。
10. 不恢复废弃文件。

## 2. 类型与接口

1. public interface 必须语义清楚。
2. 输入、输出、异常、side effect 变化必须同步调用方和测试。
3. 稳定多字段数据不应长期使用松散 dict。
4. Python public function / method 应有参数和返回类型。
5. SQL schema、配置项、env、CLI 参数都视为数据契约。

## 3. Python

1. 遵循仓库 ruff、mypy、pytest 配置。
2. 避免无约束 `Any`、无解释 `type: ignore`。
3. `Optional` 使用前必须处理。
4. 异步代码必须注意取消、清理、超时。
5. public interface 有复杂语义时使用 Google-style docstring。
6. 新增或修改的业务注释默认使用中文。
7. Google-style docstring 正文默认中文；Args / Returns / Raises 标题可保留英文。

## 4. SQL / ORM / 配置

1. 不凭记忆推断字段。
2. 查询优先沿用仓库当前风格。
3. schema 变化必须说明兼容性。
4. 配置项变化必须检查默认值、示例、测试。

## 5. 注释

1. 注释解释为什么，不重复做了什么。
2. public interface、复杂调度、协议、性能指标、异常边界应有必要注释。
3. 不给简单代码堆无意义注释。
