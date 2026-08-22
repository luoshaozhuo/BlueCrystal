# Observability Architecture

## 依赖方向

```text
应用 composition root
        │ 注入 app / scheduler / callable
        ▼
ObservabilityRuntime
        ├── LoggingBackend (structlog)
        ├── MetricsBackend (独立 Prometheus registry)
        ├── TracingBackend (独立 OTel TracerProvider)
        ├── AuditService (默认 SQLite，可替换 AuditStore)
        └── InstrumentationRegistry
                ├── FastAPIInstrumentation
                ├── APSchedulerInstrumentation
                ├── Worker wrapper
                └── future adapter
```

Backend 决定遥测数据连接到哪里，Instrumentation 决定从哪个执行边界产生事实。
Instrumentation 只能消费 Runtime 已启用能力，不直接创建 exporter 或全局 registry。

## 生命周期

`create_observability()` 只创建 backend；框架对象随后必须在宿主启动前安装。
`install` 阶段可以修改 route、middleware 和 listener；`start()` 只启动运行期资源，
不得再修改宿主结构。任一启动失败会逆序停止资源并卸载结构；`close()` 同样先停止
资源再逆序卸载并关闭 provider，重复关闭安全。关闭后的 Runtime 不允许再次启动或安装。
若 start 在获取部分资源后失败，Runtime 会先 stop 当前失败 adapter，再逆序 stop 先前
成功项并 uninstall 全部结构；清理失败作为异常 note 关联，首要 start 异常类型保持不变。

## 传播模型

`ObservationContext` 的 request、correlation、actor、job、execution 和扩展属性全部
可选，不假设 HTTP 是根。每个边界继承已有上下文；Worker 没有上游时生成新的
`execution_id`。作用域使用 ContextVar token reset，异常和 asyncio 取消都恢复父上下文。

长期周期任务不应永久恢复创建请求的父 span；创建链路应作为 link 或持久化关联信息，
每次周期执行创建新的 root execution。短期 `run_now` 才适合显式传播捕获上下文。

## 第三方优先原则

FastAPI 的 HTTP Trace/Metrics 直接委托第三方 instrumentation，基座中间件只补关联
上下文，避免重复 span 和指标。APScheduler 缺少等价覆盖时使用 listener；Worker
只包装执行边界。业务步骤日志始终由业务代码通过 `get_logger()` 产生。
