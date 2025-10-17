"""Utility helpers for the job monitor package."""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

DEFAULT_LOG_DIR = Path(os.getenv("JOB_ALERT_LOG_DIR", "logs"))
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging(name: str = "job_monitor", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a package-wide logger with rotation."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    log_path = DEFAULT_LOG_DIR / "job_monitor.log"
    handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=5)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def exponential_backoff(
    func: Callable[..., Any],
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    logger: Optional[logging.Logger] = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_error: Optional[Callable[[Exception, int], None]] = None,
    **kwargs: Any,
) -> Any:
    """Execute ``func`` with retry logic and exponential backoff."""

    attempt = 0
    delay = base_delay
    last_exc: Optional[Exception] = None
    logger = logger or configure_logging()

    while attempt <= retries:
        try:
            return func(**kwargs)
        except exceptions as exc:  # pragma: no cover - defensive logging branch
            last_exc = exc
            if on_error:
                on_error(exc, attempt)
            logger.warning("Attempt %s failed: %s", attempt + 1, exc)
            if attempt == retries:
                break
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            attempt += 1

    if last_exc:
        raise last_exc

    raise RuntimeError("exponential_backoff reached unreachable state")


def normalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize job fields for diffing and deduplication."""
    normalized = job.copy()
    normalized["title"] = job.get("title", "").strip().lower()
    normalized["url"] = job.get("url", "").strip().lower()
    return normalized


def deduplicate_jobs(jobs: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Deduplicate jobs by normalized title and URL."""
    seen: set[tuple[str, str]] = set()
    deduped: list[Dict[str, Any]] = []
    for job in jobs:
        normalized = normalize_job(job)
        key = (normalized.get("title", ""), normalized.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
