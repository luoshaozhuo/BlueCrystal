# Observability Integration Runtime

这是面向 FastAPI、APScheduler 和业务 Worker 的强约定可观测性接入层。
三类 instrumentation 可以任意组合，也可以全部缺席；新增框架 adapter 实现
`Instrumentation` 的 `install/start/stop/uninstall` 两阶段生命周期。

## 使用方式

```python
from observability import create_observability, get_logger

runtime = create_observability("observability.yaml")
runtime.instrument_fastapi(app)          # 可选
runtime.instrument_apscheduler(scheduler)  # 可选
runner = runtime.instrument_worker("data.import", business_runner)

await runtime.start()
logger = get_logger(__name__)
# 应用关闭时：await runtime.close()
```

需要一次注入可选对象时，也可以使用根入口
`install_observability(config, app=app, scheduler=scheduler)`。

`instrument_fastapi()` 等结构安装必须在宿主应用启动前完成；`start()` 只启动运行期
资源，不会在 FastAPI lifespan 中新增 route 或 middleware。

YAML 是部署入口，并严格解析为 `ObservabilityConfig`。稳定字段拒绝未知键；
`provider_options`、`exporter_options` 和 instrumentation 的 `options` 保留第三方
原生参数。FastAPI app、scheduler 和 callable 是运行对象，只能由 Python 注入。

## 能力边界

- HTTP span 使用 OpenTelemetry FastAPI instrumentation。
- HTTP RED Metrics 使用 `prometheus-fastapi-instrumentator`。
- APScheduler 通过 listener 补足调度事件；显式管理操作可使用
  `observability.instrumentation.observe_scheduler_action` 记录 Trace 与 Audit。
- Worker wrapper 只记录执行 span、指标和关联上下文，不接管业务日志。
- 业务通过 `get_logger()` 获取自动注入 request/job/execution/trace 字段的 logger。
- Audit 默认使用 SQLite，并保留小型 `AuditStore` Protocol 替换点。

每个 Runtime 独占 Prometheus registry 和 OTel `TracerProvider`，模块导入不会注册
全局 collector、设置全局 tracer provider 或自动修改 root logger。

## 运行完整示例

默认示例不依赖外部 Collector：结构化业务日志和 OTel console span 写到进程
标准输出，Prometheus 指标由 `GET /metrics` 暴露，审计记录写入仓库
`/tmp/observability-example-audit.sqlite3`。YAML 中 SQLite 相对路径统一以 YAML
文件所在目录为基准；可通过 `OBSERVABILITY_EXAMPLE_AUDIT_PATH` 覆盖持久化位置。

示例明确把 `X-Actor` 当作演示主体，因此同一 request context 中的声明式 HTTP
Audit 与 scheduler 管理 Audit 都能关联 actor。通用 FastAPI adapter 默认不信任
任何主体 header；生产代码必须向 `runtime.instrument_fastapi(...,
actor_resolver=...)` 注入从认证 session、token 或网关可信声明解析主体的 resolver，
不能直接照搬示例 header 作为身份认证。

```bash
python -m observability.example_app

# 直接运行经过 instrumentation 的业务 Worker
curl -H 'x-request-id: demo-request' -H 'x-actor: operator' \
  -X POST 'http://127.0.0.1:8000/tasks/7/run'
# 观察代表性业务失败日志、失败 span 与 Audit
curl -X POST 'http://127.0.0.1:8000/tasks/8/run?fail=true'

# 创建一次性真实 APScheduler 任务，并立即触发
curl -H 'x-actor: scheduler-operator' -X POST \
  'http://127.0.0.1:8000/schedules/demo-job?task_id=9&delay_seconds=60'
curl -H 'x-actor: scheduler-operator' -X POST \
  'http://127.0.0.1:8000/schedules/demo-job/run-now'

curl 'http://127.0.0.1:8000/metrics'
curl 'http://127.0.0.1:8000/audit?operation=schedule.run_now&limit=10'
curl 'http://127.0.0.1:8000/health'
```

部署时可用 `OBSERVABILITY_CONFIG_PATH=/path/to/observability.yaml` 替换默认 YAML；
`OBSERVABILITY_EXAMPLE_HOST`、`OBSERVABILITY_EXAMPLE_PORT` 和
`OBSERVABILITY_EXAMPLE_RELOAD=true` 分别控制监听地址、端口与 Uvicorn reload。

APScheduler listener 只证明 scheduler 启停、提交和执行结果等技术事实，并输出
对应 metrics/log；被调度的 Worker wrapper 负责执行 span 与指标，显式
create/run-now/pause/resume/remove 管理操作由 `observe_scheduler_action` 负责
trace/audit。示例不会把 listener 事件夸大为操作者审计。
