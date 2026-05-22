"""Tests for capacity progress bar rendering."""

from __future__ import annotations

import sys

import pytest

from tools.source_lab.access.common.progress import CapacityProgressBar


def test_progress_bar_uses_carriage_return_on_tty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

    progress = CapacityProgressBar("subscribe", total=4)
    progress.update(
        process_count=1,
        process_max=5,
        server_count=10,
        server_max=30,
        hz=5.0,
        hz_max=40.0,
        current=1,
    )
    progress.close()

    captured = capsys.readouterr()
    assert "\r" in captured.err
    assert "[capacity] subscribe" in captured.err
    assert "[source-lab]" not in captured.err
    assert captured.out == ""


def test_progress_bar_close_clears_rendered_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

    progress = CapacityProgressBar("polling", total=2)
    progress.update(
        process_count=3,
        process_max=5,
        server_count=20,
        server_max=30,
        hz=10.0,
        hz_max=40.0,
        current=1,
    )
    progress.close()

    err = capsys.readouterr().err
    assert err.endswith("\r")
    assert " " in err


def test_progress_bar_is_silent_on_non_tty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys.stderr, "isatty", lambda: False)

    progress = CapacityProgressBar("polling", total=3)
    progress.update(
        process_count=1,
        process_max=5,
        server_count=10,
        server_max=30,
        hz=5.0,
        hz_max=40.0,
        current=1,
    )
    progress.close()

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""
