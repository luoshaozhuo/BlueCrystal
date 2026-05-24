# 验证路由规则

本文件说明不同改动完成后应运行哪些检查和测试。

## 1. 基本原则

1. 验证范围跟随改动影响。
2. 最小验证必须覆盖本轮风险。
3. 不默认全量测试。
4. 不默认长测或重回归。
5. 跳过验证必须说明原因和风险。

## 2. 工具不存在时的处理

如果仓库未配置 ruff、mypy、pytest、npm、cmake、bandit 等工具，不得虚构命令成功。

应改为：

1. 说明工具或脚本不存在。
2. 选择可执行的替代验证。
3. 明确未验证风险。

可选替代验证示例：

- Python：`python -m py_compile <changed-python-files>`。
- 局部 smoke 命令。
- 读取测试配置确认无可运行入口。
- 静态检查变更调用链。
- 运行已有最接近的测试文件。

## 3. Python 改动

优先考虑：

```bash
python -m py_compile <changed-python-files>
ruff check <changed-python-files-or-related-package>
mypy <affected-package-or-files>
pytest <affected-tests> -q
```

实际命令以仓库配置为准。

## 4. C / Native 改动

优先考虑：

```bash
# 根据仓库实际构建方式选择
cmake --build ...
make ...
pytest <native-or-adapter-related-tests> -q
```

如果涉及 stdout/stderr 或协议输出，必须运行相关协议或 adapter 测试。

## 5. TypeScript / 前端改动

优先考虑：

```bash
npm test -- <affected-tests>
npm run lint
npm run typecheck
```

实际命令以仓库配置为准。

## 6. Schema / ORM / Migration 改动

优先考虑：

```bash
pytest <schema/repository/config-related-tests> -q
pytest <affected-integration-tests> -q
```

并检查：

- migration 是否同步。
- 初始化脚本是否同步。
- example config 是否同步。
- 调用方是否同步。

## 7. 配置 / env / CLI 改动

优先考虑：

```bash
pytest <config-or-cli-tests> -q
```

必须覆盖：

- 未设置时默认值。
- 合法值。
- 非法值。
- 新旧配置优先级。
- 类型转换错误。

## 8. 测试代码改动

运行被修改的测试文件：

```bash
pytest <changed-test-files> -q
```

如果测试失败暴露生产逻辑问题，不得直接弱化测试，应判断是实现错还是测试错。

## 9. 文档改动

纯文档改动通常不需要代码验证。若文档含可执行命令、配置示例、接口契约，应验证示例是否仍然正确。

## 10. 安全检查

仅在涉及以下内容时优先运行安全检查，例如 Bandit 或仓库配置的安全工具：

- 命令执行。
- 文件读写。
- 外部输入。
- 网络访问。
- 认证鉴权。
- 密钥或凭证。
- 反序列化。
- 权限控制。

## 11. 重回归 / 长测

以下必须用户明确要求：

- heavy-regression。
- 长时间性能测试。
- 全量测试。
- 多轮容量测试。
- 发布前完整验证。
