# 编码、接口、类型与注释规则

## 1. 通用编码

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
3. 稳定多字段数据不应长期使用松散字典。
4. Python public function / method 应有参数和返回类型。
5. TypeScript 不滥用 `any`。
6. C / native 的 header、struct、return code、协议行都视为接口契约。
7. SQL schema、配置项、env、CLI 参数都视为数据契约。

## 3. Python

1. 遵循仓库 ruff、mypy、pytest 配置。
2. 默认遵循 PEP 8。
3. 避免无约束 `Any`、无解释 `type: ignore`。
4. `Optional` 使用前必须处理。
5. 异步代码必须注意取消、清理、超时。
6. public interface 有复杂语义时使用 Google-style docstring。

## 4. C / Native

1. 遵循仓库编译配置和当前风格。
2. 明确内存、句柄、资源所有权。
3. 检查返回值。
4. stdout 仅用于协议输出时，不得混入日志。
5. stderr 用于日志和诊断。
6. 修改 native runner 时必须考虑 Python adapter 和测试。

## 5. HTML / CSS / TypeScript

1. 遵循仓库 formatter、linter、tsconfig。
2. 组件职责清楚。
3. 样式与结构分离。
4. 修改交互行为时同步验证。

## 6. SQL / ORM / 配置

1. 不凭记忆推断字段。
2. 查询优先沿用仓库当前风格。
3. schema 变化必须说明兼容性。
4. 配置项变化必须检查默认值、示例、测试。

## 7. 注释与文档

1. 注释解释为什么，不重复做了什么。
2. public interface、复杂调度、协议、性能指标、异常边界应有必要注释。
3. 文档与实现不一致时必须修正文档。
