# ADR-20260530-010: shared_source production runner artifact boundary

## 状态

已采纳

## 背景

Round 10 复核发现 `src/whale/shared/source/` 下多个 production source client backend
默认把 native runner 路径指向 `tools/source_lab/native/build`。这虽然没有 Python import
层面的 `tools.source_lab` 污染，但会把工具模块的本地构建产物误当成 production runner
默认来源，导致：

1. `shared_source` 的独立交付边界被高估；
2. `source_lab` build path 被误写成 ingest production-ready 证据；
3. 缺失 runner 时错误提示没有区分 production artifact 与 dev/test fallback。

## 决策

对 `shared_source` native runner 路径解析采用双层边界：

1. production 优先：
   - 单 runner 显式环境变量；
   - `WHALE_SHARED_SOURCE_RUNNER_DIR`；
   - PATH / 约定安装目录。
2. `tools/source_lab/native/build` 只允许作为显式 dev/test fallback：
   - 必须设置 `WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1`；
   - fallback 证据等级仅为 dev/test，不计入 production-ready。
3. backend 缺失 runner 时错误消息必须明确：
   - 当前路径是否属于 dev/test fallback；
   - 生产环境应通过独立 runner artifact、PATH 或环境变量交付；
   - `shared_source` 不 import `tools.source_lab`。

## 影响

正向影响：

1. `shared_source` 与 `source_lab` native build 的职责边界可追溯。
2. ingest production-ready 结论不再依赖工具模块构建目录默认存在。
3. 测试和本地联调仍可通过显式环境变量或 dev fallback 继续使用 source_lab build。

保留约束：

1. 这次仅修正路径解析与证据边界，不新增新的 native artifact 打包链。
2. 若生产部署要真正收口，仍需独立的 runner artifact 交付/安装流程与现场验证。
