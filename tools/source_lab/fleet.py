"""Simulator fleet lifecycle helpers for source_lab tests and profiles."""

from __future__ import annotations

import asyncio
import math
import multiprocessing
import os
import queue
import random
import time
import traceback
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from multiprocessing import queues, synchronize
from typing import Any

from tools.source_lab.factory import build_simulator
from tools.source_lab.model import SimulatedPoint, SimulatedSource, UpdateConfig

_STARTUP_TIMEOUT_SECONDS = 10.0
_READY_POLL_SECONDS = 0.05
_START_CONCURRENCY_DEFAULT = 8
_START_STAGGER_MS_DEFAULT = 0


def _resolve_startup_timeout_seconds() -> float:
    """Resolve fleet startup timeout from environment with safe fallback."""

    raw_value = os.environ.get("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S")
    if raw_value is None or raw_value.strip() == "":
        return _STARTUP_TIMEOUT_SECONDS

    try:
        resolved = float(raw_value)
    except ValueError:
        return _STARTUP_TIMEOUT_SECONDS

    if resolved <= 0:
        return _STARTUP_TIMEOUT_SECONDS

    return resolved


def _resolve_start_concurrency() -> int:
    """Resolve startup concurrency cap from environment with safe fallback."""

    raw_value = os.environ.get("SOURCE_SIM_FLEET_START_CONCURRENCY")
    if raw_value is None or raw_value.strip() == "":
        return _START_CONCURRENCY_DEFAULT

    try:
        resolved = int(raw_value)
    except ValueError:
        return _START_CONCURRENCY_DEFAULT

    return resolved if resolved > 0 else _START_CONCURRENCY_DEFAULT


def _resolve_start_stagger_ms() -> int:
    """Resolve startup stagger milliseconds from environment with safe fallback."""

    raw_value = os.environ.get("SOURCE_SIM_FLEET_START_STAGGER_MS")
    if raw_value is None or raw_value.strip() == "":
        return _START_STAGGER_MS_DEFAULT

    try:
        resolved = int(raw_value)
    except ValueError:
        return _START_STAGGER_MS_DEFAULT

    return resolved if resolved >= 0 else _START_STAGGER_MS_DEFAULT


def _normalize_point_data_type(raw_data_type: str) -> str:
    normalized = raw_data_type.strip().upper()
    if normalized in {"BOOL", "BOOLEAN"}:
        return "BOOLEAN"
    if normalized in {
        "INT8",
        "INT16",
        "INT32",
        "INT64",
        "INT8U",
        "INT16U",
        "INT32U",
        "UINT8",
        "UINT16",
        "UINT32",
    }:
        return "INT32"
    if normalized in {"FLOAT", "FLOAT32", "FLOAT64", "DOUBLE"}:
        return "FLOAT64"
    if normalized in {"DATETIME", "TIMESTAMP"}:
        return "DATETIME"
    if normalized in {"STRING", "VISSTRING255", "TEXT"}:
        return "STRING"
    return "FLOAT64"


def _select_points_for_update(
    points: Sequence[SimulatedPoint],
    update_config: UpdateConfig,
) -> tuple[SimulatedPoint, ...]:
    total = len(points)
    if total == 0:
        return ()

    if update_config.update_count is not None:
        selected_count = min(total, update_config.update_count)
    else:
        selected_count = math.floor(total * update_config.update_ratio)

    return tuple(points[:selected_count])


def _build_random_value(
    rng: random.Random,
    data_type: str,
) -> str | int | float | bool:
    normalized_data_type = _normalize_point_data_type(data_type)
    if normalized_data_type == "BOOLEAN":
        return rng.choice([True, False])
    if normalized_data_type == "INT32":
        return rng.randint(0, 100)
    if normalized_data_type == "STRING":
        return rng.choice(["foo", "bar", "baz"])
    if normalized_data_type == "DATETIME":
        return datetime.now(tz=UTC).isoformat()
    return rng.uniform(0.0, 100.0)


def _build_update_writes(
    points: Sequence[SimulatedPoint],
    rng: random.Random,
) -> dict[str, str | int | float | bool]:
    writes: dict[str, str | int | float | bool] = {}
    for point in points:
        writes[point.key] = _build_random_value(rng, point.data_type)
    return writes


def _drain_command_queue(
    command_queue: queues.Queue[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if command_queue is None:
        return []
    commands: list[dict[str, Any]] = []
    while True:
        try:
            commands.append(command_queue.get_nowait())
        except queue.Empty:
            return commands


async def _drain_command_queue_async(
    command_queue: queues.Queue[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_drain_command_queue, command_queue)


def _run_simulator_process(
    source: SimulatedSource,
    update_config: UpdateConfig,
    stop_event: synchronize.Event,
    ready_event: synchronize.Event,
    error_queue: queues.Queue[str],
    command_queue: queues.Queue[dict[str, Any]] | None = None,
    response_queue: queues.Queue[dict[str, Any]] | None = None,
) -> None:
    """[deprecated] Old synchronous SourceSimulator subprocess.

    No longer the default path. Replaced by ``_run_facade_process``.
    """

    try:
        with build_simulator(source) as simulator:
            ready_event.set()

            update_points = _select_points_for_update(source.points, update_config)
            rng = random.Random(
                f"{source.connection.name}:{source.connection.host}:{source.connection.port}"
            )
            next_update_at = time.monotonic() + update_config.interval_seconds

            while not stop_event.is_set():
                for command in _drain_command_queue(command_queue):
                    request_id = str(command.get("request_id", ""))
                    action = str(command.get("action", ""))
                    if action != "update_values":
                        if response_queue is not None:
                            response_queue.put(
                                {
                                    "request_id": request_id,
                                    "ok": False,
                                    "message": f"unsupported action: {action}",
                                }
                            )
                        continue

                    try:
                        simulator.writes(dict(command.get("values", {})))
                        if response_queue is not None:
                            response_queue.put(
                                {
                                    "request_id": request_id,
                                    "ok": True,
                                    "message": "",
                                }
                            )
                    except Exception as exc:
                        if response_queue is not None:
                            response_queue.put(
                                {
                                    "request_id": request_id,
                                    "ok": False,
                                    "message": str(exc),
                                }
                            )

                if not update_config.enabled:
                    stop_event.wait(0.1)
                    continue

                now = time.monotonic()
                if now >= next_update_at:
                    writes = _build_update_writes(update_points, rng)
                    if writes:
                        simulator.writes(writes)

                    next_update_at += update_config.interval_seconds
                    while next_update_at <= now:
                        next_update_at += update_config.interval_seconds

                wait_seconds = min(0.05, max(0.0, next_update_at - time.monotonic()))
                stop_event.wait(wait_seconds)
    except Exception as exc:
        error_queue.put(
            (
                f"Simulator process failed for source={source.connection.name} "
                f"endpoint={source.connection.host}:{source.connection.port}: {exc}\n"
                f"{traceback.format_exc()}"
            )
        )


def _run_facade_process(
    source: SimulatedSource,
    update_config: UpdateConfig,
    stop_event: synchronize.Event,
    ready_event: synchronize.Event,
    error_queue: queues.Queue[str],
    command_queue: queues.Queue[dict[str, Any]] | None = None,
    response_queue: queues.Queue[dict[str, Any]] | None = None,
) -> None:
    """Run one facade-managed simulator in its own subprocess."""

    try:

        async def _run() -> None:
            from tools.source_lab.protocols.registry import create_server_simulator

            facade = create_server_simulator(source.connection.protocol, source)
            await facade.load_points([point for point in source.points])  # type: ignore[arg-type]
            result = await facade.start()
            if result.status.name != "OK":
                raise RuntimeError(
                    f"facade start failed for {source.connection.name}: "
                    f"{result.status.name} {result.message}"
                )

            ready_event.set()

            update_points = _select_points_for_update(source.points, update_config)
            rng = random.Random(
                f"{source.connection.name}:{source.connection.host}:{source.connection.port}"
            )
            next_update_at = time.monotonic() + update_config.interval_seconds

            while not stop_event.is_set():
                for command in await _drain_command_queue_async(command_queue):
                    request_id = str(command.get("request_id", ""))
                    action = str(command.get("action", ""))
                    if action != "update_values":
                        if response_queue is not None:
                            response_queue.put(
                                {
                                    "request_id": request_id,
                                    "ok": False,
                                    "message": f"unsupported action: {action}",
                                }
                            )
                        continue

                    result = await facade.update_values(dict(command.get("values", {})))
                    if response_queue is not None:
                        response_queue.put(
                            {
                                "request_id": request_id,
                                "ok": result.status.name == "OK",
                                "message": result.message,
                            }
                        )

                if not update_config.enabled:
                    await asyncio.sleep(0.1)
                    continue

                now = time.monotonic()
                if now >= next_update_at:
                    writes = _build_update_writes(update_points, rng)
                    if writes:
                        await facade.update_values(writes)
                    next_update_at += update_config.interval_seconds
                    while next_update_at <= now:
                        next_update_at += update_config.interval_seconds

                wait_seconds = min(0.05, max(0.0, next_update_at - time.monotonic()))
                await asyncio.sleep(wait_seconds)

            await facade.stop()

        asyncio.run(_run())
    except Exception as exc:
        error_queue.put(
            (
                f"Facade process failed for source={source.connection.name} "
                f"endpoint={source.connection.host}:{source.connection.port}: {exc}\n"
                f"{traceback.format_exc()}"
            )
        )


@dataclass
class SourceSimulatorFleet:
    """Build, start and stop one homogeneous simulator fleet."""

    sources: tuple[SimulatedSource, ...]
    update_config: UpdateConfig
    startup_timeout_seconds: float = 10.0
    join_timeout_seconds: float = 5.0
    start_concurrency: int = _START_CONCURRENCY_DEFAULT
    start_stagger_ms: int = _START_STAGGER_MS_DEFAULT
    use_facade: bool = True
    _processes: list[multiprocessing.Process | None] = field(
        init=False, repr=False, default_factory=list
    )
    _stop_events: list[synchronize.Event | None] = field(
        init=False, repr=False, default_factory=list
    )
    _ready_events: list[synchronize.Event | None] = field(
        init=False, repr=False, default_factory=list
    )
    _command_queues: list[queues.Queue[dict[str, Any]] | None] = field(
        init=False, repr=False, default_factory=list
    )
    _response_queues: list[queues.Queue[dict[str, Any]] | None] = field(
        init=False, repr=False, default_factory=list
    )
    _error_queue: queues.Queue[str] | None = field(init=False, repr=False, default=None)

    @classmethod
    def create(
        cls,
        sources: Sequence[SimulatedSource],
        *,
        update_config: UpdateConfig | None = None,
        startup_timeout_seconds: float | None = None,
        start_concurrency: int | None = None,
        start_stagger_ms: int | None = None,
        use_facade: bool | None = None,
    ) -> "SourceSimulatorFleet":
        """Build one fleet from externally prepared simulated sources."""

        resolved_config = update_config or UpdateConfig()
        resolved_timeout = (
            startup_timeout_seconds
            if startup_timeout_seconds is not None
            else _resolve_startup_timeout_seconds()
        )
        resolved_start_concurrency = (
            start_concurrency if start_concurrency is not None else _resolve_start_concurrency()
        )
        resolved_start_stagger_ms = (
            start_stagger_ms if start_stagger_ms is not None else _resolve_start_stagger_ms()
        )
        resolved_use_facade = use_facade if use_facade is not None else True
        source_list = tuple(sources)

        if not source_list:
            raise ValueError("A fleet must contain at least one source")

        protocols = {
            source.connection.protocol.strip().lower().replace("_", "").replace("-", "")
            for source in source_list
        }
        if len(protocols) > 1:
            raise ValueError("A fleet can only contain one protocol")

        return cls(
            sources=source_list,
            update_config=resolved_config,
            startup_timeout_seconds=resolved_timeout,
            start_concurrency=resolved_start_concurrency,
            start_stagger_ms=resolved_start_stagger_ms,
            use_facade=resolved_use_facade,
        )

    def start(self) -> "SourceSimulatorFleet":
        self._ensure_slots()
        try:
            self._start_processes()
        except Exception:
            self.stop()
            raise
        return self

    def stop(self) -> None:
        if not self._processes:
            self._close_error_queue()
            return

        alive_processes: list[str] = []
        for index in range(len(self.sources)):
            process = self._processes[index]
            if process is None:
                continue
            self._stop_process_slot(index)
            lingering = self._processes[index]
            if lingering is not None and lingering.is_alive():
                alive_processes.append(lingering.name)

        self._close_error_queue()
        self._close_control_queues()

        if alive_processes:
            raise RuntimeError(
                "Failed to stop simulator process(es): "
                + ", ".join(alive_processes)
            )

    def start_source(self, source_id: str | int) -> None:
        self._ensure_slots()
        index = self._resolve_source_index(source_id)
        process = self._processes[index]
        if process is not None and process.is_alive():
            return

        startup_deadline = time.monotonic() + self.startup_timeout_seconds
        self._start_process_slot(index)
        self._wait_until_ready(pending_indices={index}, deadline=startup_deadline)

    def stop_source(self, source_id: str | int) -> None:
        self._ensure_slots()
        self._stop_process_slot(self._resolve_source_index(source_id))

    def restart_source(self, source_id: str | int) -> None:
        index = self._resolve_source_index(source_id)
        self.stop_source(index)
        self.start_source(index)

    def status_source(self, source_id: str | int) -> str:
        self._ensure_slots()
        index = self._resolve_source_index(source_id)
        process = self._processes[index]
        if process is None:
            return "stopped"
        if process.is_alive():
            return "running"
        if process.exitcode not in (None, 0):
            return "failed"
        return "stopped"

    def update_source_values(
        self,
        source_id: str | int,
        values: dict[str, str | int | float | bool | None],
    ) -> None:
        self._ensure_slots()
        index = self._resolve_source_index(source_id)
        process = self._processes[index]
        command_queue = self._command_queues[index]
        response_queue = self._response_queues[index]
        if process is None or command_queue is None or response_queue is None or not process.is_alive():
            raise RuntimeError(f"source is not running: {source_id}")

        request_id = f"{index}-{time.time_ns()}"
        command_queue.put(
            {
                "action": "update_values",
                "request_id": request_id,
                "values": values,
            }
        )

        deadline = time.monotonic() + self.join_timeout_seconds
        while time.monotonic() < deadline:
            try:
                response = response_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if response.get("request_id") != request_id:
                continue
            if not response.get("ok", False):
                raise RuntimeError(str(response.get("message", "update failed")))
            return
        raise TimeoutError(f"timed out waiting update ack for source: {source_id}")

    def __enter__(self) -> "SourceSimulatorFleet":
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()

    def _start_processes(self) -> None:
        self._ensure_slots()
        if self._error_queue is None:
            self._error_queue = multiprocessing.get_context().Queue()
        startup_deadline = time.monotonic() + self.startup_timeout_seconds
        startup_window: set[int] = set()

        for index, _source in enumerate(self.sources):
            process = self._processes[index]
            if process is not None and process.is_alive():
                continue

            self._start_process_slot(index)
            startup_window.add(index)
            if self.start_stagger_ms > 0:
                time.sleep(self.start_stagger_ms / 1000.0)

            if self.start_concurrency > 0 and len(startup_window) >= self.start_concurrency:
                self._wait_until_ready(
                    pending_indices=startup_window,
                    deadline=startup_deadline,
                )
                startup_window.clear()

        if startup_window:
            self._wait_until_ready(
                pending_indices=startup_window,
                deadline=startup_deadline,
            )

        self._wait_until_ready(deadline=startup_deadline)

    def _start_process_slot(self, index: int) -> None:
        context = multiprocessing.get_context()
        if self._error_queue is None:
            self._error_queue = context.Queue()
        process_target = _run_facade_process if self.use_facade else _run_simulator_process
        stop_event = context.Event()
        ready_event = context.Event()
        command_queue = context.Queue()
        response_queue = context.Queue()
        process = context.Process(
            target=process_target,
            name=f"source-simulator-{index + 1}",
            args=(
                self.sources[index],
                self.update_config,
                stop_event,
                ready_event,
                self._error_queue,
                command_queue,
                response_queue,
            ),
        )
        process.start()
        self._processes[index] = process
        self._stop_events[index] = stop_event
        self._ready_events[index] = ready_event
        self._command_queues[index] = command_queue
        self._response_queues[index] = response_queue

    def _stop_process_slot(self, index: int) -> None:
        process = self._processes[index]
        stop_event = self._stop_events[index]
        if process is None or stop_event is None:
            return

        stop_event.set()
        if process.pid is not None:
            process.join(timeout=self.join_timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join(timeout=self.join_timeout_seconds)
            if process.is_alive():
                process.kill()
                process.join(timeout=self.join_timeout_seconds)
        if process.pid is not None and not process.is_alive():
            process.close()

        command_queue = self._command_queues[index]
        response_queue = self._response_queues[index]
        if command_queue is not None:
            command_queue.close()
            command_queue.join_thread()
        if response_queue is not None:
            response_queue.close()
            response_queue.join_thread()

        self._processes[index] = None
        self._stop_events[index] = None
        self._ready_events[index] = None
        self._command_queues[index] = None
        self._response_queues[index] = None

    def _wait_until_ready(
        self,
        *,
        pending_indices: set[int] | None = None,
        deadline: float | None = None,
    ) -> None:
        timeout_seconds = self.startup_timeout_seconds
        resolved_deadline = (
            deadline if deadline is not None else (time.monotonic() + timeout_seconds)
        )
        pending = (
            set(pending_indices)
            if pending_indices is not None
            else set(range(len(self._ready_events)))
        )

        while pending:
            startup_errors = self._drain_startup_errors()
            if startup_errors:
                raise RuntimeError("Failed to start simulator fleet:\n" + "\n".join(startup_errors))

            for index in tuple(pending):
                ready_event = self._ready_events[index]
                process = self._processes[index]
                if ready_event is None or process is None:
                    pending.remove(index)
                    continue
                if ready_event.is_set():
                    pending.remove(index)
                    continue
                if not process.is_alive():
                    source = self.sources[index]
                    raise RuntimeError(
                        "Simulator process exited before ready: "
                        f"name={process.name} exitcode={process.exitcode} "
                        f"source={source.connection.name} "
                        f"endpoint={source.connection.host}:{source.connection.port}"
                    )

            if not pending:
                break

            remaining_seconds = resolved_deadline - time.monotonic()
            if remaining_seconds <= 0:
                pending_list = sorted(pending)
                alive_process_count = sum(
                    1 for process in self._processes if process is not None and process.is_alive()
                )
                pending_sources = [
                    f"{self.sources[index].connection.name}@"
                    f"{self.sources[index].connection.host}:{self.sources[index].connection.port}"
                    for index in pending_list[:20]
                ]
                raise RuntimeError(
                    "Timed out waiting for simulator fleet readiness: "
                    f"timeout_seconds={timeout_seconds}, "
                    f"total_sources={len(self.sources)}, "
                    f"pending_count={len(pending)}, "
                    f"pending_indices={pending_list[:20]}, "
                    f"pending_sources={pending_sources}, "
                    f"alive_process_count={alive_process_count}"
                )

            for index in tuple(pending):
                ready_event = self._ready_events[index]
                if ready_event is None:
                    pending.remove(index)
                    continue
                if ready_event.wait(timeout=min(_READY_POLL_SECONDS, remaining_seconds)):
                    pending.remove(index)

    def _resolve_source_index(self, source_id: str | int) -> int:
        if isinstance(source_id, int):
            if 0 <= source_id < len(self.sources):
                return source_id
            raise IndexError(f"source index out of range: {source_id}")

        for index, source in enumerate(self.sources):
            if source.connection.name == source_id:
                return index
        raise KeyError(f"source not found: {source_id}")

    def _ensure_slots(self) -> None:
        target_size = len(self.sources)
        while len(self._processes) < target_size:
            self._processes.append(None)
            self._stop_events.append(None)
            self._ready_events.append(None)
            self._command_queues.append(None)
            self._response_queues.append(None)

    def _drain_startup_errors(self) -> list[str]:
        if self._error_queue is None:
            return []

        errors: list[str] = []
        while True:
            try:
                errors.append(self._error_queue.get_nowait())
            except queue.Empty:
                return errors

    def _close_error_queue(self) -> None:
        if self._error_queue is None:
            return
        self._error_queue.close()
        self._error_queue.join_thread()
        self._error_queue = None

    def _close_control_queues(self) -> None:
        for command_queue in self._command_queues:
            if command_queue is not None:
                command_queue.close()
                command_queue.join_thread()
        for response_queue in self._response_queues:
            if response_queue is not None:
                response_queue.close()
                response_queue.join_thread()
        self._command_queues.clear()
        self._response_queues.clear()
        self._processes.clear()
        self._stop_events.clear()
        self._ready_events.clear()
