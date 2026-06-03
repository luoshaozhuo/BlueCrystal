"""Whale 主平台 integration 测试包。

所属生命周期阶段：模块集成期验证（无外部服务依赖的集成测试）或
跨模块联调期验证（docker-compose/simulator 全链路测试）。
使用 SQLite/TestClient/in-memory/临时文件等轻量依赖进行集成闭环验证。
不依赖真实 PostgreSQL/Kafka/Redis/S3/TDengine 等准生产外部服务
（这些属于准生产依赖验证期，由 ``l5`` marker 或测试说明指定）。
物理目录 ``tests/integration/`` 不等于单一生命周期阶段；测试文件头
或 ``ai_shared/memory/test_index.md`` 才是权威分类来源。
"""

