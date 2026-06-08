# BlueCrystal - 能源数据统一平台

## 项目概述
渐进式开发的能源数据平台，从Level 0数据流开始，逐步构建统一数据底座。

## 开发原则
1. **渐进式**：从最简单用例开始
2. **最简方案**：不过度设计
3. **阶段性重构**：功能稳定后优化架构
4. **测试驱动**：确保迭代可靠性

## 快速开始
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行代码检查
flake8 src/
black --check src/
mypy src/

# 运行测试
pytest
```

## 编码规范
- PEP 8标准
- Black格式化（行宽100）
- Google风格文档字符串
- 全面使用类型提示

## 项目结构
```
BlueCrystal/
├── src/whale/          # 核心代码（whale 模块名保留）
├── tests/              # 测试
├── docs/               # 文档
└── config/             # 配置
```

## 配置说明
- `CODEBUDDY.md`：项目级配置和约束
- `.codebuddy/`：CodeBuddy规则和模板
- `pyproject.toml`：Python工具链配置

## init_db

PYTHONPATH=src python -m whale.shared.persistence.template.sample_data

## Ingest 开发基础设施

本仓库提供了一套本地开发/测试用的基础设施编排：

```bash
docker compose -f docker-compose.ingest-dev.yaml up -d
```

它会启动：

- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`
- Kafka: `127.0.0.1:9092`

建议先复制环境变量模板，再按需要调整：

```bash
cp .env.ingest.example .env.ingest.local
```

如果想一键重建开发基础设施、初始化数据库并写入样本数据、再启动 ingest：

```bash
bash scripts/run_ingest_dev.sh
```

这个脚本会按顺序执行：

- 加载 `.env.ingest.local`（不存在时回退到 `.env.ingest.example`）
- 删除旧的开发容器和 volume（统一 recreate）
- 根据 `database/state_cache/message` 后端组合按需启动容器
	- `sqlite` 不启动容器（使用本地文件数据库）
	- `postgresql` 启动 `postgres`
	- `redis` state cache 或 `redis_streams` message 启动 `redis`
	- `kafka` message 启动 `kafka`
- `sqlite` 默认文件路径为 `.data/ingest/whale.ingest.db`
- 非交互式执行 `init_db` 并写入样本数据
- 启动 ingest

如果只想手动启动 ingest，也可以先导出环境变量：

```bash
set -a
source .env.ingest.local
set +a
PYTHONPATH=src python -m whale.ingest
```

如果要停止本地基础设施：

```bash
docker compose -f docker-compose.ingest-dev.yaml down
```
