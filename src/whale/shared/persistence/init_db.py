"""shared persistence 数据库初始化入口。

本模块负责建表、重建只读视图和重置样例库。对于 PostgreSQL 这类可能连接到
常驻实例的后端，destructive reset 必须先通过安全库名护栏，避免误删默认库
或生产风格库。
"""

from __future__ import annotations

import argparse
from importlib import import_module

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from whale.shared.persistence import Base
from whale.shared.persistence.session import _db_url, engine

from whale.shared.persistence.template.protocol_view_defs import ensure_protocol_views

_SCADA_SERVER_VIEW_NAME = "v_scada_server"
_SAFE_RESET_MARKERS = ("test", "tmp", "ci", "local_dev_test")
_SCADA_SERVER_VIEW_SQL = f"""
CREATE VIEW {_SCADA_SERVER_VIEW_NAME} AS
SELECT
    ep.endpoint_id AS endpoint_id,
    ep.ied_id AS ied_id,
    ld.ld_instance_id AS ld_instance_id,
    ied.ied_name AS ied_name,
    asset.asset_code AS asset_code,
    asset.asset_name AS asset_name,
    ep.access_point_name AS access_point_name,
    ep.application_protocol AS application_protocol,
    ep.transport AS transport,
    ep.host AS host,
    ep.port AS port,
    ep.namespace_uri AS namespace_uri,
    ep.security_policy AS security_policy,
    ep.security_mode AS security_mode,
    ep.auth_type AS auth_type,
    ep.credential_ref AS credential_ref,
    ld.asset_instance_id AS asset_instance_id,
    ld.signal_profile_id AS signal_profile_id,
    ld.ld_name AS ld_name,
    ld.path_prefix AS path_prefix
FROM scada_communication_endpoint AS ep
JOIN scada_ied AS ied
    ON ied.ied_id = ep.ied_id
JOIN scada_ld_instance AS ld
    ON ld.endpoint_id = ep.endpoint_id
JOIN asset_instance AS asset
    ON asset.asset_instance_id = ld.asset_instance_id
"""


def init_db(force: bool = False) -> None:
    if force:
        reset_db()
        initialize_db()
        print("初始化完成。")
        return

    if _has_existing_schema():
        confirmation = input(_build_delete_confirmation_prompt()).strip()
        if confirmation != "delete":
            print("已取消初始化。")
            return
        reset_db()

    initialize_db()
    print("初始化完成。")


def initialize_db() -> None:
    import_module("whale.shared.persistence.orm")
    Base.metadata.create_all(bind=engine)
    ensure_shared_views(bind=engine)
    ensure_protocol_views(bind=engine)


def reset_db() -> None:
    import_module("whale.shared.persistence.orm")
    _assert_safe_reset_target()

    with engine.begin() as conn:
        if _db_url.get_dialect().name == "postgresql":
            views = conn.execute(text(
                "SELECT table_name FROM information_schema.views "
                "WHERE table_schema = 'public'"
            )).fetchall()
            for (v,) in views:
                if v.startswith("v_"):
                    conn.execute(text(f"DROP VIEW IF EXISTS {v} CASCADE"))
            # Clean up removed legacy tables that may still hold FKs into current tables.
            conn.execute(text("DROP TABLE IF EXISTS scada_ld_signal_override CASCADE"))
    Base.metadata.drop_all(bind=engine)

    if _db_url.get_dialect().name == "sqlite":
        engine.dispose()
        from pathlib import Path
        db_path = Path(str(_db_url.database))
        if db_path.exists():
            db_path.unlink()


def ensure_shared_views(*, bind: Engine) -> None:
    """Create the read-only shared SQL views required by the persistence layer."""
    with bind.begin() as conn:
        conn.execute(text(f"DROP VIEW IF EXISTS {_SCADA_SERVER_VIEW_NAME}"))
        conn.execute(text(_SCADA_SERVER_VIEW_SQL))


def _has_existing_schema() -> bool:
    inspector = inspect(engine)
    return bool(inspector.get_table_names())


def _build_delete_confirmation_prompt() -> str:
    return (
        f"数据库 {_db_url} 已包含数据表。"
        "此操作会清除所有数据并重建。"
        '输入 "delete" 后才会继续删除并重建：'
    )


def _assert_safe_reset_target() -> None:
    """阻止对不安全 PostgreSQL 目标执行 destructive reset。"""

    if _db_url.get_backend_name() != "postgresql":
        return

    database_name = (_db_url.database or "").strip().lower()
    rendered_url = _db_url.render_as_string(hide_password=True).lower()
    if any(marker in database_name or marker in rendered_url for marker in _SAFE_RESET_MARKERS):
        return

    raise RuntimeError(
        "拒绝对非测试 PostgreSQL 库执行 shared persistence reset。"
        f" 当前目标 database={_db_url.database!r}，要求库名或 URL 至少包含 "
        f"{_SAFE_RESET_MARKERS!r} 之一。请改用临时测试库。"
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize the shared persistence database.")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = _build_argument_parser().parse_args()
    if args.force:
        init_db(force=True)
        return 0
    if args.reset:
        reset_db()
    elif not args.non_interactive:
        init_db()
        return 0
    initialize_db()
    print("初始化完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
