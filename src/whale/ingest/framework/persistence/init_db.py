"""框架基础设施。

提供持久化、数据库初始化等底层能力。
"""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

from sqlalchemy import inspect

from whale.ingest.config import CONFIG, PostgresDatabaseConfig, SqliteDatabaseConfig
from whale.ingest.framework.persistence.session import engine
from whale.shared.persistence import Base
from whale.shared.persistence.init_db import ensure_shared_views


def init_db() -> None:
    """创建 ORM 表并可选加载示例数据。"""
    if _has_existing_schema():
        confirmation = input(_build_delete_confirmation_prompt()).strip()
        if confirmation != "delete":
            print("已取消初始化。")
            return
        reset_db()

    insert_sample_data = input("是否插入样例数据？(y/n)：").strip().lower()
    initialize_db(insert_sample_data=insert_sample_data == "y")
    print("已完成初始化。")


def initialize_db(*, insert_sample_data: bool) -> None:
    """创建 ORM 表并可选加载默认示例数据。"""
    import_module("whale.ingest.framework.persistence.orm")
    import_module("whale.shared.persistence.orm")
    Base.metadata.create_all(bind=engine)
    from whale.shared.persistence import Base as SharedBase
    SharedBase.metadata.create_all(bind=engine)
    ensure_shared_views(bind=engine)
    if insert_sample_data:
        load_default_sample_data()


def reset_db() -> None:
    """移除当前为配置的 ingest 数据库持久化的存储。"""
    import_module("whale.ingest.framework.persistence.orm")
    _clear_existing_storage()


def load_default_sample_data() -> None:
    """将内置示例数据模板加载到当前 ingest 数据库。"""
    from whale.shared.persistence.template.sample_data import generate_all_sample_data

    generate_all_sample_data()


def _resolve_database_path() -> Path:
    """返回具体的 SQLite 数据库路径。"""
    if not isinstance(CONFIG.database, SqliteDatabaseConfig):
        raise RuntimeError("Current ingest database backend is not sqlite.")
    database = CONFIG.database.database
    database_path = Path(database)
    if not database_path.is_absolute():
        database_path = (Path(__file__).resolve().parents[5] / database_path).resolve()
    return database_path


def _has_existing_schema() -> bool:
    """返回当前配置的数据库是否已包含表。"""
    inspector = inspect(engine)
    return bool(inspector.get_table_names())


def _clear_existing_storage() -> None:
    """移除配置数据库的已有存储 schema。"""
    if isinstance(CONFIG.database, SqliteDatabaseConfig):
        database_path = _resolve_database_path()
        engine.dispose()
        if database_path.exists():
            database_path.unlink()
        return

    raise RuntimeError(
        "Automatic database deletion is only supported for sqlite. "
        "Please clear the configured non-sqlite database manually."
    )


def _storage_display_name() -> str:
    """返回用户可读的配置存储目标描述。"""
    if isinstance(CONFIG.database, SqliteDatabaseConfig):
        return f"Database at {_resolve_database_path()}"
    assert isinstance(CONFIG.database, PostgresDatabaseConfig)
    return f"Database {CONFIG.database.backend}://{CONFIG.database.database}"


def _build_delete_confirmation_prompt() -> str:
    """返回本地化的删除确认提示。"""
    if isinstance(CONFIG.database, SqliteDatabaseConfig):
        return (
            f"{_storage_display_name()} 已包含数据表。"
            "此操作会永久删除当前整个数据库文件及其中的所有数据。"
            '输入 "delete" 后才会继续删除并重建：'
        )

    return (
        f"{_storage_display_name()} 已包含数据表。"
        "当前不会自动删除非 sqlite 数据库。"
        '如仍要继续确认流程，请输入 "delete"：'
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    """构造非交互式数据库初始化的命令行解析器。"""
    parser = argparse.ArgumentParser(description="Initialize the ingest persistence database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing configured storage before re-initializing.",
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Insert built-in sample acquisition data after creating tables.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without interactive prompts and fail fast on invalid operations.",
    )
    return parser


def main() -> int:
    """以交互或非交互模式运行 init-db 入口。"""
    args = _build_argument_parser().parse_args()

    if not args.non_interactive and not args.reset and not args.sample_data:
        init_db()
        return 0

    if args.reset:
        reset_db()
    initialize_db(insert_sample_data=args.sample_data)
    print("已完成初始化。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
