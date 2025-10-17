"""Diffing logic for job postings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .utils import deduplicate_jobs, normalize_job


@dataclass
class DiffResult:
    new_jobs: List[Dict[str, str]]
    removed_jobs: List[Dict[str, str]]


class DiffEngine:
    """Compare two job listing snapshots."""

    def diff(self, previous: Iterable[Dict[str, str]], current: Iterable[Dict[str, str]]) -> DiffResult:
        prev_map = {self._key(job): job for job in deduplicate_jobs(previous)}
        curr_map = {self._key(job): job for job in deduplicate_jobs(current)}

        new_keys = curr_map.keys() - prev_map.keys()
        removed_keys = prev_map.keys() - curr_map.keys()

        new_jobs = [curr_map[key] for key in new_keys]
        removed_jobs = [prev_map[key] for key in removed_keys]

        return DiffResult(new_jobs=new_jobs, removed_jobs=removed_jobs)

    @staticmethod
    def _key(job: Dict[str, str]) -> tuple[str, str]:
        normalized = normalize_job(job)
        return (normalized.get("title", ""), normalized.get("url", ""))
