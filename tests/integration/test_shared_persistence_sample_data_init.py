"""共享持久化样例初始化 PostgreSQL 集成测试。

证据等级：L4 integration。
本测试通过真实 `python -m whale.shared.persistence.template.sample_data` 子进程
在安全创建的 PostgreSQL 临时测试库上执行 `init_db + sample_data`，验证 shared
persistence 输入基线已真实落到 PostgreSQL，而不是继续由 SQLite 冒充最终验收。
它不证明真实协议驱动、simulator 或现场设备连通性。
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from tests.support.scada_sample_db import postgres_scada_sample_db

_EXPECTED_MATRIX = {
    ("OPC_UA", "READ"),
    ("OPC_UA", "SUBSCRIBE"),
    ("MODBUS", "TCP_READ"),
    ("MODBUS", "RTU_READ"),
    ("IEC101", "INTERROGATION"),
    ("IEC101", "SPONTANEOUS"),
    ("IEC104", "INTERROGATION"),
    ("IEC104", "SPONTANEOUS"),
    ("IEC61850", "MMS_READ"),
    ("IEC61850", "REPORT"),
    ("IEC61850", "GOOSE"),
    ("IEC61850", "SV"),
    ("MQTT", "SUBSCRIBE"),
    ("HTTP_REST", "REQUEST"),
    ("BECKHOFF_ADS", "ADS_READ_WRITE"),
    ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
}


@contextmanager
def _postgres_engine() -> Iterator[Engine]:
    """创建一份安全 PostgreSQL 样例库并返回查询 engine。"""

    try:
        with postgres_scada_sample_db() as sample_db:
            engine = create_engine(sample_db.database_url, pool_pre_ping=True)
            try:
                yield engine
            finally:
                engine.dispose()
    except RuntimeError as exc:
        _skip_if_environment_unavailable(exc)


def _skip_if_environment_unavailable(exc: RuntimeError) -> None:
    """只在 PostgreSQL 环境确实不可用时转成 skip。"""

    message = str(exc)
    if (
        "requires env vars" in message
        or "test environment unavailable" in message
    ):
        pytest.skip(f"environment-pending: shared persistence PostgreSQL test env unavailable: {message}")
    raise exc


def _distinct_matrix(engine: Engine, sql: str) -> set[tuple[str, str]]:
    """执行 protocol-service 去重查询。"""

    with engine.connect() as conn:
        return {tuple(row) for row in conn.execute(text(sql)).fetchall()}


@pytest.mark.integration
def test_sample_data_module_initializes_safe_postgres_db_with_full_protocol_matrix() -> None:
    """在安全 PostgreSQL 临时库上执行样例初始化，并验证 16 组协议服务全量落库。"""

    with _postgres_engine() as engine:
        endpoint_matrix = _distinct_matrix(
            engine,
            """
            SELECT application_protocol, service_type
            FROM scada_communication_endpoint
            ORDER BY application_protocol, service_type
            """,
        )
        endpoint_param_matrix = _distinct_matrix(
            engine,
            """
            SELECT DISTINCT ep.application_protocol, ep.service_type
            FROM scada_endpoint_param_value AS epv
            JOIN scada_communication_endpoint AS ep
                ON ep.endpoint_id = epv.endpoint_id
            ORDER BY ep.application_protocol, ep.service_type
            """,
        )
        signal_param_matrix = _distinct_matrix(
            engine,
            """
            SELECT DISTINCT def.application_protocol, def.service_type
            FROM scada_signal_profile_item_param_value AS spv
            JOIN scada_signal_param_def AS def
                ON def.param_def_id = spv.param_def_id
            ORDER BY def.application_protocol, def.service_type
            """,
        )

        with engine.connect() as conn:
            protocol_counts = conn.execute(
                text(
                    """
                    SELECT application_protocol, COUNT(*)
                    FROM scada_communication_endpoint
                    GROUP BY application_protocol
                    ORDER BY application_protocol
                    """
                )
            ).fetchall()
            endpoint_count = conn.execute(
                text("SELECT COUNT(*) FROM scada_communication_endpoint")
            ).scalar_one()
            shared_profile_count = conn.execute(
                text("SELECT COUNT(DISTINCT signal_profile_id) FROM scada_ld_instance")
            ).scalar_one()
            endpoint_param_coverage = conn.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT endpoint_id)
                    FROM scada_endpoint_param_value
                    """
                )
            ).scalar_one()
            signal_param_coverage = conn.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT application_protocol || ':' || service_type)
                    FROM (
                        SELECT DISTINCT def.application_protocol, def.service_type
                        FROM scada_signal_profile_item_param_value AS spv
                        JOIN scada_signal_param_def AS def
                            ON def.param_def_id = spv.param_def_id
                    ) AS matrix
                    """
                )
            ).scalar_one()
            ads_services = {
                tuple(row)
                for row in conn.execute(
                    text(
                        """
                        SELECT application_protocol, service_type
                        FROM scada_communication_endpoint
                        WHERE application_protocol = 'BECKHOFF_ADS'
                        ORDER BY service_type
                        """
                    )
                ).fetchall()
            }

    assert endpoint_matrix == _EXPECTED_MATRIX
    assert endpoint_param_matrix == _EXPECTED_MATRIX
    assert signal_param_matrix == _EXPECTED_MATRIX
    assert endpoint_count == 16
    assert len(protocol_counts) > 1
    assert protocol_counts != [("OPC_UA", 16)]
    assert shared_profile_count == 1
    assert endpoint_param_coverage == 16
    assert signal_param_coverage == 16
    assert ads_services == {
        ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
        ("BECKHOFF_ADS", "ADS_READ_WRITE"),
    }
