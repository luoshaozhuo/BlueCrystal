"""Shared helpers for e2e tests — importable utilities and constants."""

from __future__ import annotations

import socket
import time
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
# Round 12: old tools/opcua_sim/ templates deleted.  E2E tests that need
# NodeSet / connection fixtures must be explicitly supplied at call time.
# These constants are kept as sentinels pointing to the starfish native
# directory; production E2E is expected to provide real configuration.
DEFAULT_NODESET_PATH = PROJECT_ROOT / "src" / "starfish" / "native" / "bin" / "OPCUANodeSet.xml"
DEFAULT_CONNECTIONS_PATH = (
    PROJECT_ROOT / "src" / "starfish" / "native" / "bin" / "OPCUA_client_connections.yaml"
)

# Infrastructure constants (match deploy/whale/ingest/docker-compose.ingest-dev.yaml)
PG_HOST = "127.0.0.1"
PG_PORT = 5432
PG_DB = "whale_ingest"
PG_USER = "whale"
PG_PASSWORD = "whale"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 16379

KAFKA_BOOTSTRAP_SERVER = "127.0.0.1:9092"


def get_free_port() -> int:
    """Return one currently available local TCP port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def ensure_src_on_path() -> None:
    """Add src/ to sys.path so whale.* imports resolve."""
    import sys

    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))


def seed_postgres_for_e2e(
    pg_session,
    *,
    substation_name: str | None = None,
    model_id: str | None = None,
    model_version: str = "v1",
    variable_keys: tuple[str, ...] = ("TotW", "Spd", "WS"),
    device_code: str = "WTG_01",
    endpoint: str | None = None,
    acquisition_mode: str = "ONCE",
) -> tuple[int, int]:
    """Update an existing acq_task row for e2e test parameters.

    The shared DB already has sample data with acq_task entries.
    This function finds the matching task (by task_name = f\"task_{device_code}\")
    and updates its acquisition_mode and endpoint for the test.

    Returns (task_id, 0).  The second element is kept for backwards
    compatibility; model_pk is no longer meaningful.
    """
    from whale.shared.persistence.orm.acquisition import AcquisitionTask

    task_name = f"task_{device_code}"

    # Try the ingest session first, then fall back to shared session
    from sqlalchemy import select as _select

    # Use the shared session_scope for acq_task access
    from whale.shared.persistence.session import session_scope as _shared_scope

    with _shared_scope() as session:
        task = session.execute(
            _select(AcquisitionTask).where(AcquisitionTask.task_name == task_name)
        ).scalar_one_or_none()

        if task is None:
            # Create a minimal task linked to existing asset/ied
            from whale.shared.persistence.orm.asset import AssetInstance, AssetType
            from whale.shared.persistence.orm.scada_ingest import (
                CommunicationEndpoint, IED, LDInstance,
            )

            asset = session.execute(
                _select(AssetInstance).where(AssetInstance.asset_code == device_code)
            ).scalar_one_or_none()

            if asset is None:
                # Find wind turbine asset type
                wt_type = session.execute(
                    _select(AssetType).where(AssetType.asset_type_name == "风力发电机")
                ).scalar_one_or_none()
                if wt_type is None:
                    raise LookupError("AssetType '风力发电机' not found")

                asset = AssetInstance(
                    asset_code=device_code,
                    asset_name=device_code,
                    asset_type_id=wt_type.asset_type_id,
                )
                session.add(asset)
                session.flush()

            ied = session.execute(
                _select(IED).where(IED.ied_name == "IED_WTG_OPCUA")
            ).scalar_one_or_none()
            if ied is None:
                raise LookupError("IED 'IED_WTG_OPCUA' not found")

            # Resolve endpoint parts
            from urllib.parse import urlsplit
            ep_url = endpoint or "opc.tcp://127.0.0.1:40001"
            parsed = urlsplit(ep_url)
            ep_host = parsed.hostname or "127.0.0.1"
            ep_port = parsed.port or 4840

            comm_ep = CommunicationEndpoint(
                ied_id=ied.ied_id,
                access_point_name="AP_E2E",
                application_protocol="OPC_UA",
                transport="TCP",
                host=ep_host,
                port=ep_port,
                namespace_uri="urn:windfarm:2wtg",
                security_policy="None",
                security_mode="None",
            )
            session.add(comm_ep)
            session.flush()

            ld = LDInstance(
                endpoint_id=comm_ep.endpoint_id,
                asset_instance_id=asset.asset_instance_id,
                ld_inst=device_code,
                path_prefix=device_code,
            )
            session.add(ld)
            session.flush()

            task = AcquisitionTask(
                task_name=task_name,
                ld_instance_id=ld.ld_instance_id,
                acquisition_mode=acquisition_mode,
                enabled=True,
            )
            session.add(task)
        else:
            task.acquisition_mode = acquisition_mode
            if endpoint is not None:
                # Update the CommunicationEndpoint through LDInstance chain
                ld = session.get(LDInstance, task.ld_instance_id)
                if ld is not None:
                    from urllib.parse import urlsplit
                    ep = session.get(CommunicationEndpoint, ld.endpoint_id)
                    if ep is not None:
                        parsed = urlsplit(endpoint)
                        ep.host = parsed.hostname or "127.0.0.1"
                        ep.port = parsed.port or 4840

        session.commit()
        return int(task.task_id), 0


def wait_for_redis(redis_client, timeout_seconds: float = 20.0) -> None:
    """Wait until Redis responds to ping or raise actionable error."""
    import pytest

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            if redis_client.ping():
                return
        except Exception:
            time.sleep(0.5)
            continue
        time.sleep(0.2)
    pytest.fail(
        f"Redis backend is not ready at {REDIS_HOST}:{REDIS_PORT}. "
        "Run `docker compose -f deploy/whale/ingest/docker-compose.ingest-dev.yaml up -d` first."
    )


def wait_for_kafka(timeout_seconds: float = 30.0) -> None:
    """Wait until Kafka metadata is queryable or raise actionable error."""
    import pytest

    try:
        from kafka import KafkaConsumer  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("E2E test requires `kafka-python` package.") from exc

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        consumer = None
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
                consumer_timeout_ms=1000,
                api_version_auto_timeout_ms=2000,
            )
            consumer.topics()
            return
        except Exception:
            time.sleep(0.5)
        finally:
            if consumer is not None:
                consumer.close()
    pytest.fail(
        f"Kafka backend is not ready at {KAFKA_BOOTSTRAP_SERVER}. "
        "Run `docker compose -f deploy/whale/ingest/docker-compose.ingest-dev.yaml up -d` first."
    )
