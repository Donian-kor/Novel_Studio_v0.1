from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from novel_studio.jobs.worker import Job, JobCancelled

def test_job_cancel_before_run_emits_only_cancelled() -> None:
    events: list[str] = []
    called = False

    def work() -> None:
        nonlocal called
        called = True

    job = Job(work)
    job.signals.cancelled.connect(lambda: events.append("cancelled"))
    job.signals.finished.connect(lambda _result: events.append("finished"))
    job.cancel()
    job.run()

    assert called is False
    assert events == ["cancelled"]


def test_job_cancelled_exception_never_emits_finished() -> None:
    events: list[str] = []

    def work() -> None:
        raise JobCancelled()

    job = Job(work)
    job.signals.cancelled.connect(lambda: events.append("cancelled"))
    job.signals.finished.connect(lambda _result: events.append("finished"))
    job.run()

    assert events == ["cancelled"]

