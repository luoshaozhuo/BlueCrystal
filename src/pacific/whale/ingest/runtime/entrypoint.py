"""ingest 启动入口。

组合 FastAPI 应用和服务组件，启动 ingest 全栈运行时。
负责资源生命周期（数据库连接池、消息客户端、调度器）的初始化和清理。
"""

from __future__ import annotations

from pacific.whale.ingest.runtime.cli import app


def main() -> int:
    """运行 ingest 运行时 CLI。"""

    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
