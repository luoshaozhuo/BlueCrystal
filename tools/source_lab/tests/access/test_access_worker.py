"""Tests for runner-injected worker orchestration."""

from __future__ import annotations

import inspect

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

from tools.source_lab.access.polling import worker
from tools.source_lab.access.polling.metrics import WorkerRawStats
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.polling.worker import run_level_once, run_worker_level


class _FakeRunner:
    name = "fake_runner"

    def __init__(self) -> None:
        self.calls: list[tuple[int, tuple[RunnerEndpointPlan, ...], float, CapacityScanConfig]] = []

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        target_hz: float,
        config: CapacityScanConfig,
    ) -> WorkerRawStats:
        self.calls.append((worker_index, specs, target_hz, config))
        return WorkerRawStats(
            worker_index=worker_index,
            reader_count=len(specs),
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=tuple(((1.0, 1.1),) for _ in specs),
            max_observed_concurrent_reads=max(1, len(specs)),
        )


def _config(*, process_count: int = 1) -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=process_count,
    )


def _source(index: int) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=f"source-{index}",
            host="127.0.0.1",
            port=48000 + index,
            protocol="opcua",
        ),
        points=(SourcePointSpec(address="IED.LD.LN.DO"),),
    )


def test_worker_exports() -> None:
    assert callable(run_worker_level)
    assert callable(run_level_once)


def test_worker_depends_on_runner_protocol_not_open62541_module() -> None:
    names = run_level_once.__code__.co_names
    assert "run_serial_polling_worker" not in names
    assert "open62541_serial_polling" not in inspect.getsource(worker)


def test_run_level_once_process_count_one_uses_injected_runner(
    monkeypatch,
) -> None:
    runner = _FakeRunner()
    diagnostics_calls: list[int] = []

    monkeypatch.setattr(
        "tools.source_lab.access.polling.worker.print_worker_diagnostics",
        lambda config, worker_stats: diagnostics_calls.append(len(worker_stats)),
    )

    metrics = run_level_once(
        (_source(0),),
        target_hz=10.0,
        config=_config(process_count=1),
        runner=runner,
    )

    assert [(worker_index, len(specs), target_hz) for worker_index, specs, target_hz, _ in runner.calls] == [
        (0, 1, 10.0)
    ]
    assert diagnostics_calls == [1]
    assert metrics.worker_conc_sum == 1
    assert metrics.worker_conc_max == 1


def test_run_worker_level_forwards_arguments_to_runner() -> None:
    runner = _FakeRunner()
    specs = (RunnerEndpointPlan(global_index=0, source=_source(0), offset_ns=0),)

    stats = run_worker_level(
        specs,
        target_hz=10.0,
        worker_index=3,
        config=_config(),
        runner=runner,
    )

    assert stats.reader_count == 1
    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call[0] == 3
    assert call[1] == specs
    assert call[2] == 10.0


def test_run_level_once_partitions_sources_across_workers(monkeypatch) -> None:
    runner = _FakeRunner()
    submitted: list[tuple[int, int]] = []

    class _Future:
        def __init__(self, value: WorkerRawStats) -> None:
            self._value = value

        def result(self) -> WorkerRawStats:
            return self._value

    class _Executor:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def __enter__(self) -> "_Executor":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def submit(self, func, index, bucket, target_hz, config, runner_arg):
            submitted.append((index, len(bucket)))
            return _Future(func(index, bucket, target_hz, config, runner_arg))

    monkeypatch.setattr("tools.source_lab.access.polling.worker.ProcessPoolExecutor", _Executor)

    metrics = run_level_once(
        (_source(0), _source(1), _source(2)),
        target_hz=10.0,
        config=_config(process_count=2),
        runner=runner,
    )

    assert submitted == [(0, 2), (1, 1)]
    assert [(worker_index, len(specs)) for worker_index, specs, _, _ in runner.calls] == [(0, 2), (1, 1)]
    assert metrics.worker_conc_by_worker == (2, 1)
