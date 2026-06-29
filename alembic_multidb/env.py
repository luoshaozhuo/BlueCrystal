"""BlueCrystal Alembic environment."""

from __future__ import annotations

import os
import sys
from importlib import import_module
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from alembic import context
from dotenv import dotenv_values
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_DOTENV = dotenv_values()


def _add_src_to_path() -> None:
    if config.config_file_name:
        repo_root = Path(config.config_file_name).resolve().parent
    else:
        repo_root = Path.cwd()

    src_dir = repo_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _database_names() -> list[str]:
    names = _split_csv(config.get_main_option("databases"))
    if not names:
        raise SystemExit("alembic.ini 中 [alembic] 必须配置 databases。")
    return names


def _required_option(section: str, option: str) -> str:
    value = config.get_section_option(section, option, default=None)
    if not value:
        raise SystemExit(f"alembic.ini 中 [{section}] 必须配置 {option}。")
    return value


def _resolve_url(section: str) -> str:
    env_name = _required_option(section, "db_url_env")
    url = os.environ.get(env_name) or _DOTENV.get(env_name, "")
    if not url:
        raise SystemExit(f"未读取到环境变量 {env_name}。")
    return url


def _import_object(spec: str) -> Any:
    module_name, sep, object_path = spec.partition(":")
    if not sep or not module_name or not object_path:
        raise SystemExit(f"无效 import 配置：{spec}，应为 module:object。")

    obj: Any = import_module(module_name)
    for attr in object_path.split("."):
        obj = getattr(obj, attr)
    return obj


def _load_metadata(section: str) -> Any:
    target_spec = _required_option(section, "target_metadata")
    orm_modules = _split_csv(_required_option(section, "orm_modules"))

    target = _import_object(target_spec)
    for module_name in orm_modules:
        import_module(module_name)

    return getattr(target, "metadata", target)


def _metadata_map() -> dict[str, Any]:
    _add_src_to_path()
    return {name: _load_metadata(name) for name in _database_names()}


def _render_as_batch(url: str) -> bool:
    return make_url(url).get_backend_name() == "sqlite"


def run_migrations_offline() -> None:
    metadata_map = _metadata_map()

    for name in _database_names():
        url = _resolve_url(name)
        context.configure(
            url=url,
            target_metadata=metadata_map[name],
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            render_as_batch=_render_as_batch(url),
            upgrade_token=f"{name}_upgrades",
            downgrade_token=f"{name}_downgrades",
        )
        with context.begin_transaction():
            context.run_migrations(engine_name=name)


def run_migrations_online() -> None:
    metadata_map = _metadata_map()

    for name in _database_names():
        url = _resolve_url(name)
        engine = create_engine(url, poolclass=pool.NullPool)

        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata_map[name],
                compare_type=True,
                render_as_batch=connection.dialect.name == "sqlite",
                upgrade_token=f"{name}_upgrades",
                downgrade_token=f"{name}_downgrades",
            )
            with context.begin_transaction():
                context.run_migrations(engine_name=name)

        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
