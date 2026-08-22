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
