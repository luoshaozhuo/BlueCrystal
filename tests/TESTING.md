# Testing Guide

## 测试分层与定位

`tools/source_lab/access` 的 capacity/profile 路径固定使用 `open62541_client_runner`，不提供 backend selector。

### Unit Tests（单元测试）

验证单个函数、类或模块的逻辑正确性。不依赖外部服务（数据库、网络、OPC UA 服务器），所有外部依赖使用 mock 或 fake。

- **目标**：快速、稳定、精确定位问题
- **运行频率**：每次提交、每次保存
- **标记**：`@pytest.mark.unit`
- **目录**：[tests/unit/](tests/unit/)

### Integration Tests（集成测试）

验证多个组件之间的交互是否正确。依赖真实的数据库连接、真实的 OPC UA 服务器启动/停止、真实的网络通信。不做 mock。

- **目标**：验证组件间接口和交互正确
- **依赖**：PostgreSQL、OPC UA 服务端、open62541 runner
- **标记**：`@pytest.mark.integration`
- **目录**：[tests/integration/](tests/integration/)

### E2E Tests（端到端测试）

验证从 OPC UA 数据采集到消息管道（Redis State Cache → Kafka Message Pipeline）的完整链路。

- **目标**：验证全链路数据流动正确
- **依赖**：Docker（PostgreSQL + Redis + Kafka）、OPC UA 模拟器、ingest 管道
- **标记**：`@pytest.mark.e2e`
- **目录**：[tests/e2e/](tests/e2e/)

### Performance Tests（性能测试）

性能测试是总称，包含以下三个子类型，分别验证系统在不同维度下的表现。

#### Endurance Tests（耐久测试 / 性能验证）

验证系统在稳态负载下是否达到预期性能指标。例如：90% 的请求响应时间不超过 1 秒、持续运行 N 小时零错误。

- **目标**：确认系统满足 SLA 或预期性能指标
- **特征**：固定负载、较长时间运行、关注延迟/吞吐量指标
- **标记**：`@pytest.mark.endurance`
- **目录**：[tests/performance/endurance/](tests/performance/endurance/)

#### Load Tests（负载测试）

对系统施加不同级别的负载（逐步增加用户数、数据量、并发度），观察系统表现，找出最佳运行状态或容量上限。

- **目标**：确定系统在什么负载级别下能平稳运行，找到拐点
- **特征**：阶梯式或持续高负载、关注吞吐量变化曲线、找上限
- **标记**：`@pytest.mark.load`
- **目录**：[tests/performance/load/](tests/performance/load/)

#### Stress Tests（压力测试）

主动将系统推向极限（超大规模数据、极端并发、资源耗尽），观察系统在超出设计容量时的行为：是优雅降级还是崩溃。

- **目标**：验证极端条件下的健壮性和恢复能力
- **特征**：超出正常容量、故意制造资源瓶颈、关注崩溃模式和恢复
- **标记**：`@pytest.mark.stress`
- **目录**：[tests/performance/stress/](tests/performance/stress/)

### 测试分层关系图

```
                         ┌──────────────┐
                         │   E2E Tests  │  ← 全链路，最慢，最真实
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼──────┐  ┌──────▼──────┐  ┌───────▼────────┐
    │  Endurance     │  │    Load     │  │    Stress      │
    │  (稳态验证)     │  │  (找上限)   │  │  (推向崩溃)     │
    └────────────────┘  └─────────────┘  └────────────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  Integration Tests  │  ← 组件交互，中等速度
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │    Unit Tests       │  ← 单一模块，最快，最稳定
                     └─────────────────────┘
```

---

## 运行测试

### 按目录

```bash
pytest                                          # 默认发现
pytest tests/unit/tools                         # 只跑 unit/tools
pytest tests/integration/tools                  # 只跑 integration/tools
pytest tests/e2e                                # 只跑 e2e
pytest tests/performance/load                   # 只跑 load 测试
```

### 按标记

```bash
pytest -m unit                                  # 所有单元测试
pytest -m integration                           # 所有集成测试
pytest -m e2e                                   # 所有端到端测试
pytest -m load                                  # 所有负载测试
pytest -m stress                                # 所有压力测试
pytest -m endurance                             # 所有耐久测试
```

### 按名称

```bash
pytest -k "10hz"                                # 名称含 "10hz" 的测试
pytest -k "from_database"                       # 名称含 "from_database" 的测试
```

---

## 常用参数

| 参数 | 作用 |
|------|------|
| `-v` | 详细输出，显示每个测试名称 |
| `-vv` | 更详细，适合调试 |
| `-q` | 简洁输出 |
| `-s` | 不捕获 print，调试时常用 |
| `-x` | 遇到第一个失败立即停止 |
| `--maxfail=N` | 最多 N 个失败后停止 |
| `-m <marker>` | 按 pytest marker 过滤 |
| `-k <expr>` | 按名称关键字过滤 |

---

## 环境依赖速查

| 测试层级 | PostgreSQL | Redis | Kafka | OPC UA Server | Docker |
|----------|-----------|-------|-------|---------------|--------|
| Unit | No | No | No | No | No |
| Integration | Yes (shared DB) | No | No | Yes | No |
| E2E | Yes | Yes | Yes | Yes | Yes |
| Performance | Yes | Yes | Yes | Yes | Yes |

### 启动 E2E / Performance 所需基础设施

```bash
docker compose -f docker-compose.ingest-dev.yaml up -d
python -m whale.shared.persistence.template.sample_data
```

---

## 负载测试

负载测试脚本位于 [tests/tmp/load_test.py](tmp/load_test.py)，为标准 Python 脚本，可直接调用：

```bash
python tests/tmp/load_test.py --turbines 30 --hz 10 --samples 3
```

参数说明：
- `--turbines N`: 最大风机数 (默认 30)
- `--hz HZ`: 采集频率 (默认 10)
- `--samples S`: 每轮采样数 (默认 3)

测试产物：
- `tests/tmp/load_test_report.md` — 测试报告
- `tests/tmp/charts/` — 图表（延迟箱线图、时间戳分布、缩放曲线、延迟分解）

### 最近测试结果 (2026-05-05)

**测试条件**: 30 台风机，10Hz 采集，每台 20 变量，3 轮采样

| 策略 | 单批次耗时 | P50 | P95 | 错误 |
|------|-----------|-----|-----|------|
| Sequential (one-by-one) | — | 6ms | 7ms | 0 |
| Async gather (all-at-once) | 148ms | 148ms | 148ms | 0 |
| ThreadPool (4 workers) | 207ms | 115ms | 200ms | 0 |
| ThreadPool (8 workers) | 202ms | 120ms | 200ms | 0 |
| ThreadPool-keep (16 workers) | 200ms | 155ms | 197ms | 0 |

**缩放结果** (ThreadPool-keep, 8 workers):

| 风机数 | P95 |
|--------|-----|
| 1 | 14ms |
| 5 | 32ms |
| 10 | 68ms |
| 15 | 104ms |
| 20 | 130ms |
| 25 | 163ms |
| 30 | 204ms |

**结论**:
- 单台机组全量 395 变量读取延迟 13ms（连接 5ms + 读取 6ms）
- 30 台风机全部满足 <1s 延迟要求，线性缩放
- ThreadPool(8 workers) 为最优策略
- 源时间戳抖动 <0.2ms，满足 1/5 周期要求
python -m whale.shared.persistence.template.sample_data
```

---

## conftest.py

[tests/conftest.py](tests/conftest.py) 被 pytest 自动加载，提供共享 fixture：

- `sample_nodeset_path` / `sample_opcua_connections_path` — OPC UA 模板路径
- `free_ports` — 分配空闲端口
- `local_opcua_connections_path` — 生成测试专用 localhost OPC UA 配置
- `opcua_server_runtime` / `opcua_sim_fleet` — 启动 OPC UA 模拟服务

`tests/e2e/conftest.py` 和 `tests/performance/load/conftest.py` 负责 Docker 基础设施（PostgreSQL / Redis / Kafka）的连接和表创建。
