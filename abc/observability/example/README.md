# Observability examples

三个示例共享一个 OpenTelemetry Collector。先从仓库根目录启动 Collector：

```bash
docker compose \
  --env-file abc/observability/example/collector.env \
  -f abc/observability/config/docker-compose.collector.yaml \
  up -d
```

Collector 接收宿主机 `127.0.0.1:64317` 上的 OTLP/gRPC 数据，并将三个示例的
trace 统一写入：

```text
abc/observability/example/output/collector/traces.jsonl
```

然后可以分别运行：

```bash
python -m observability.example.fastapi_scheduler_worker
python -m observability.example.scheduler_worker
python -m observability.example.worker
```

三个应用通过不同的 `service.instance.id` 区分来源，应用日志与 SQLite 审计文件仍
分别保存在各自的 `output/<示例名>/` 目录中。

停止共享 Collector：

```bash
docker compose \
  --env-file abc/observability/example/collector.env \
  -f abc/observability/config/docker-compose.collector.yaml \
  down
```
