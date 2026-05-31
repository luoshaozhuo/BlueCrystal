# 质量门禁规则

## 1. changed-files-gate

每个 agent 开始工作前必须使用 `changed-files-gate` 获取真实变更范围。不得只依赖上一个 agent 的口头说明。

## 2. 通用门禁

修改代码时，必须优先执行或说明未执行原因：

```text
1. 语法或编译检查；
2. lint / static analysis；
3. type-check（如果该语言或仓库启用）；
4. affected tests；
5. 与边界、安全、审计、配置、schema 相关的专项检查。
```

## 3. 语言门禁参考

实际命令以仓库配置为准：

```text
Python: py_compile/compileall, ruff/flake8/pylint, mypy/pyright, pytest
TypeScript/JavaScript: tsc --noEmit, eslint, npm/pnpm/yarn test
Go: go test ./..., go vet ./..., golangci-lint
Java/Kotlin: mvn/gradle test, checkstyle/spotbugs/PMD/detekt
C/C++: cmake --build, ctest, clang-tidy/cppcheck, compiler warnings
Rust: cargo check, cargo clippy, cargo test
Shell: bash -n, shellcheck
SQL/migration: migration dry-run, schema compatibility tests
```

## 4. 文档门禁

新增、删除、移动、重命名文件，或文件职责变化时，必须触发 `project-tree-update` 判断。该判断写在 agent/project-steward 流程中，不再单独作为 project-tree-read skill。

## 5. 失败分类

失败必须分类为：

```text
本轮引入
既有失败
环境失败
flaky
依赖缺失
验证命令错误
未执行 / environment-pending
```

存在本轮引入 failed 时不得收口。存在环境 pending 时不得写成通过。

## 6. 禁止事项

1. 不允许无说明的类型、lint 或静态分析抑制指令。
2. 不允许裸 catch / except / rescue。
3. 不允许静默吞异常。
4. 不允许把未执行的工具写成通过。
5. 不允许把 skipped、mock、fake、health check、脚本存在、单文件 passed 写成真实闭环。
