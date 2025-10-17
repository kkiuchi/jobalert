from __future__ import annotations

from job_monitor.diff_engine import DiffEngine


def test_diff_engine_detects_new_and_removed(sample_jobs):
    previous = sample_jobs
    current = sample_jobs + [{"site": "Example", "title": "ML Engineer", "url": "https://example.com/ml"}]
    engine = DiffEngine()
    diff = engine.diff(previous, current)

    assert len(diff.new_jobs) == 1
    assert diff.new_jobs[0]["title"] == "ML Engineer"
    assert not diff.removed_jobs


def test_diff_engine_detects_removed(sample_jobs):
    previous = sample_jobs
    current = sample_jobs[:-1]
    engine = DiffEngine()
    diff = engine.diff(previous, current)

    assert len(diff.removed_jobs) == 1
    assert diff.removed_jobs[0]["title"] == "Data Scientist"
