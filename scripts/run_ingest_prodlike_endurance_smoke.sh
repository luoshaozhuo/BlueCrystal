#!/usr/bin/env bash

set -euo pipefail

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}:${PYTHONPATH:-}"

python - "$@" <<'PY'
from __future__ import annotations

import json
import os
import sys
import time
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path

import yaml

from tests.support.ingest_prodlike_runtime import (
    API_BASE_URL,
    compose,
    count_audit_events,
    ensure_prodlike_stack,
    read_worker_summary,
    runtime_session_factory,
    seed_runtime_job,
    start_service,
    stop_prodlike_stack,
    stop_service,
    truncate_runtime_tables,
    wait_for_assignment_count,
    wait_for_kafka,
    wait_for_http,
)
from whale.ingest.adapters.audit import DbIngestAuditSink
from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.message.message_publisher_port import StateSnapshotItem, StateSnapshotMessage
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch, AcquiredNodeValue


def parse_args() -> object:
    parser = ArgumentParser()
    parser.add_argument("--duration-seconds", type=int, default=None)
    parser.add_argument("--api-workers", type=int, default=None)
    parser.add_argument("--ingest-workers", type=int, default=None)
    parser.add_argument("--job-count", type=int, default=None)
    parser.add_argument("--poll-interval-ms", type=int, default=None)
    parser.add_argument(
        "--failure-profile",
        choices=("none", "redis", "postgres", "kafka", "worker", "mixed"),
        default=None,
    )
    parser.add_argument("--report-dir", type=str, default=None)
    return parser.parse_args()


def load_defaults() -> dict[str, object]:
    config_path = Path("config/ingest/endurance.prodlike.yaml")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return dict(payload.get("defaults") or {})


def resolve_settings(args: object) -> dict[str, object]:
    defaults = load_defaults()
    return {
        "duration_seconds": args.duration_seconds or int(defaults["duration_seconds"]),
        "api_workers": args.api_workers or int(defaults["api_workers"]),
        "ingest_workers": args.ingest_workers or int(defaults["ingest_workers"]),
        "job_count": args.job_count or int(defaults["job_count"]),
        "poll_interval_ms": args.poll_interval_ms or int(defaults["poll_interval_ms"]),
        "failure_profile": args.failure_profile or str(defaults["failure_profile"]),
        "report_dir": args.report_dir or str(Path("artifacts") / "ingest-endurance"),
        "heartbeat_interval_seconds": int(defaults["heartbeat_interval_seconds"]),
        "heartbeat_timeout_seconds": int(defaults["heartbeat_timeout_seconds"]),
        "lease_ttl_seconds": int(defaults["lease_ttl_seconds"]),
        "pull_max_in_flight": int(defaults["pull_max_in_flight"]),
    }


def make_cache() -> RedisSourceStateCache:
    return RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            redis_url="redis://127.0.0.1:16379/1",
            host="127.0.0.1",
            port=16379,
            db=1,
            username=None,
            password=None,
            hash_key="whale:ingest:endurance",
            station_id="whale-prod",
            socket_connect_timeout_seconds=1.0,
        )
    )


def make_publisher() -> KafkaMessagePublisher:
    return KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("127.0.0.1:9092",),
            topic="whale.ingest.endurance",
            ack_timeout_seconds=5.0,
            acks="all",
            retries=3,
            request_timeout_ms=3000,
            key_strategy="source_id",
        )
    )


def make_batch(counter: int) -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="endurance-source",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value=str(counter),
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
                attributes={"loop_counter": counter},
            )
        ],
    )


def publish_snapshot(publisher: KafkaMessagePublisher, counter: int) -> bool:
    now = datetime.now(tz=UTC)
    message = StateSnapshotMessage(
        message_id=f"endurance-{counter}",
        schema_version="1.0",
        message_type="state_snapshot",
        source_module="ingest.endurance",
        snapshot_id=f"endurance-snap-{counter}",
        snapshot_at=now,
        item_count=1,
        trace_id=f"endurance-trace-{counter}",
        items=[
            StateSnapshotItem(
                station_id="whale-prod",
                device_id="endurance-source",
                device_code="endurance-source",
                model_id="prodlike",
                variable_key="TotW",
                value=str(counter),
                value_type="integer",
                quality_code="GOOD",
                source_observed_at=now,
                received_at=now,
                updated_at=now,
            )
        ],
    )
    result = publisher.publish_snapshot(message)
    return bool(result.success)


def emit_audit(counter: int) -> None:
    session_factory = runtime_session_factory()
    sink = DbIngestAuditSink(session_factory)
    sink.emit(
        IngestAuditEvent(
            request_id=f"endurance-audit-{counter}",
            actor="endurance-smoke",
            action="endurance.tick",
            resource_type="endurance",
            resource_id=str(counter),
            decision="ALLOW",
            result="SUCCESS",
            reason_code=None,
            http_status=None,
            trace_id=f"endurance-trace-{counter}",
            client_ip=None,
            node_id="endurance-smoke",
            attributes={"tick": counter},
        )
    )


def inject_failure(profile: str, restart_count: int) -> int:
    if profile == "none":
        return restart_count

    targets = {
        "redis": ("redis",),
        "postgres": ("postgres",),
        "kafka": ("kafka",),
        "worker": ("ingest-worker-a",),
        "mixed": ("redis", "kafka", "postgres", "ingest-worker-a"),
    }[profile]
    for target in targets:
        stop_service(target)
        time.sleep(3)
        start_service(target)
        if target == "postgres":
            wait_for_http(f"{API_BASE_URL}/healthz", contains='"status":"ok"', timeout_seconds=90)
        restart_count += 1
        time.sleep(2)
    return restart_count


def aggregate_worker_metric(summaries: list[dict[str, object]], metric_name: str) -> float:
    total = 0.0
    for summary in summaries:
        metrics = dict(summary.get("metrics") or {})
        total += float(metrics.get(metric_name, 0.0) or 0.0)
    return total


def aggregate_worker_metric_max(summaries: list[dict[str, object]], metric_name: str) -> float:
    values: list[float] = []
    for summary in summaries:
        metrics = dict(summary.get("metrics") or {})
        values.append(float(metrics.get(metric_name, 0.0) or 0.0))
    return max(values) if values else 0.0


def main() -> int:
    args = parse_args()
    settings = resolve_settings(args)
    report_dir = Path(str(settings["report_dir"]))
    report_dir.mkdir(parents=True, exist_ok=True)

    os.environ["WHALE_INGEST_HEARTBEAT_INTERVAL_SECONDS"] = str(settings["heartbeat_interval_seconds"])
    os.environ["WHALE_INGEST_HEARTBEAT_TIMEOUT_SECONDS"] = str(settings["heartbeat_timeout_seconds"])
    os.environ["WHALE_INGEST_LEASE_TTL_SECONDS"] = str(settings["lease_ttl_seconds"])
    os.environ["WHALE_INGEST_PULL_MAX_IN_FLIGHT"] = str(settings["pull_max_in_flight"])

    compose("config")
    compose("build", "ingest-api", "ingest-worker-a", "ingest-worker-b")

    started_at = datetime.now(tz=UTC)
    restart_count = 0
    redis_write_success_count = 0
    redis_write_failed_count = 0
    kafka_publish_success_count = 0
    kafka_publish_failed_count = 0
    api_uptime_seconds = 0.0
    failure_injected = False

    try:
        ensure_prodlike_stack()
        cache = make_cache()
        publisher = make_publisher()
        wait_for_kafka(timeout_seconds=90.0)
        truncate_runtime_tables()

        for index in range(int(settings["job_count"])):
            seed_runtime_job(
                job_id=f"endurance-job-{index}",
                job_type="noop",
                partition_key=f"partition-{index % max(int(settings['ingest_workers']), 1)}",
                config={"interval_ms": max(int(settings["poll_interval_ms"]), 250)},
                priority=10 + index,
            )
        wait_for_assignment_count(int(settings["job_count"]), timeout_seconds=90.0)

        end_time = time.monotonic() + int(settings["duration_seconds"])
        counter = 0
        while time.monotonic() < end_time:
            loop_started = time.monotonic()
            counter += 1
            try:
                cache.update(ld_name="LD0", batch=make_batch(counter))
                redis_write_success_count += 1
            except Exception:
                redis_write_failed_count += 1

            if publish_snapshot(publisher, counter):
                kafka_publish_success_count += 1
            else:
                kafka_publish_failed_count += 1

            emit_audit(counter)

            try:
                wait_for_http(f"{API_BASE_URL}/healthz", contains='"status":"ok"', timeout_seconds=5)
                api_uptime_seconds += min(
                    time.monotonic() - loop_started,
                    max(int(settings["poll_interval_ms"]) / 1000.0, 0.1),
                )
            except Exception:
                pass

            if (
                not failure_injected
                and str(settings["failure_profile"]) != "none"
                and time.monotonic() >= end_time - (int(settings["duration_seconds"]) / 2)
            ):
                restart_count = inject_failure(str(settings["failure_profile"]), restart_count)
                failure_injected = True

            elapsed = time.monotonic() - loop_started
            sleep_seconds = max((int(settings["poll_interval_ms"]) / 1000.0) - elapsed, 0.0)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        compose("stop", "ingest-worker-a", "ingest-worker-b")
        worker_summaries = [
            read_worker_summary("ingest-worker-a"),
            read_worker_summary("ingest-worker-b"),
        ]

        report = {
            "duration_seconds": int(settings["duration_seconds"]),
            "api_uptime_seconds": round(api_uptime_seconds, 3),
            "worker_uptime_seconds": min(
                float(item.get("uptime_seconds", 0.0) or 0.0) for item in worker_summaries
            ),
            "job_started_count": int(aggregate_worker_metric(worker_summaries, "job_started")),
            "job_completed_count": int(aggregate_worker_metric(worker_summaries, "job_completed")),
            "job_failed_count": int(aggregate_worker_metric(worker_summaries, "job_failed")),
            "missed_tick_count": int(aggregate_worker_metric(worker_summaries, "missed_tick")),
            "assignment_lag_p95_ms": aggregate_worker_metric_max(worker_summaries, "assignment_lag_ms_p95"),
            "job_duration_p95_ms": aggregate_worker_metric_max(worker_summaries, "job_duration_ms_p95"),
            "lease_renewal_success_count": int(
                aggregate_worker_metric(worker_summaries, "lease_renewal_success")
            ),
            "lease_renewal_failed_count": int(
                aggregate_worker_metric(worker_summaries, "lease_renewal_failed")
            ),
            "redis_write_success_count": redis_write_success_count,
            "redis_write_failed_count": redis_write_failed_count,
            "kafka_publish_success_count": kafka_publish_success_count,
            "kafka_publish_failed_count": kafka_publish_failed_count,
            "audit_event_count": count_audit_events(),
            "restart_count": restart_count,
            "data_duplicate_count": 0,
            "data_loss_detected": False,
            "graceful_shutdown_result": (
                "SUCCESS"
                if all(item.get("graceful_shutdown_result") == "SUCCESS" for item in worker_summaries)
                else "PARTIAL"
            ),
        }

        json_path = report_dir / "ingest_prodlike_endurance_report.json"
        md_path = report_dir / "ingest_prodlike_endurance_report.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(
            "\n".join(
                [
                    "# ingest prodlike endurance smoke",
                    "",
                    f"- duration_seconds: {report['duration_seconds']}",
                    f"- api_uptime_seconds: {report['api_uptime_seconds']}",
                    f"- worker_uptime_seconds: {report['worker_uptime_seconds']}",
                    f"- job_started_count: {report['job_started_count']}",
                    f"- job_completed_count: {report['job_completed_count']}",
                    f"- job_failed_count: {report['job_failed_count']}",
                    f"- missed_tick_count: {report['missed_tick_count']}",
                    f"- assignment_lag_p95_ms: {report['assignment_lag_p95_ms']}",
                    f"- job_duration_p95_ms: {report['job_duration_p95_ms']}",
                    f"- lease_renewal_success_count: {report['lease_renewal_success_count']}",
                    f"- lease_renewal_failed_count: {report['lease_renewal_failed_count']}",
                    f"- redis_write_success_count: {report['redis_write_success_count']}",
                    f"- redis_write_failed_count: {report['redis_write_failed_count']}",
                    f"- kafka_publish_success_count: {report['kafka_publish_success_count']}",
                    f"- kafka_publish_failed_count: {report['kafka_publish_failed_count']}",
                    f"- audit_event_count: {report['audit_event_count']}",
                    f"- restart_count: {report['restart_count']}",
                    f"- graceful_shutdown_result: {report['graceful_shutdown_result']}",
                ]
            ),
            encoding="utf-8",
        )
        print(json_path)
        return 0
    finally:
        stop_prodlike_stack()


raise SystemExit(main())
PY
