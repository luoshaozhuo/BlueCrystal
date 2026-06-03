"""Whale 主平台 E2E 测试包。

所属生命周期阶段：跨模块联调期验证（docker-compose/simulator 全链路）或
准生产依赖验证期（真实 Kafka/PG/Redis/S3/TDengine 等外部服务）。
使用 docker-compose 或受控环境进行端到端闭环验证。
物理目录不等于单一生命周期阶段；测试文件头或 ai_shared/memory/test_index.md
是权威分类来源。
"""

