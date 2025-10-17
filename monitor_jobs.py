"""Entry point for running the job monitoring workflow."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List

from job_monitor.config import AppConfig, ConfigManager
from job_monitor.diff_engine import DiffEngine
from job_monitor.notifier import EmailNotifier, WebhookNotifier, send_notifications
from job_monitor.scraper import JobScraper, scrape_sites
from job_monitor.sheets import SheetsClient
from job_monitor.utils import configure_logging

logger = configure_logging(__name__)


def load_sites(config: AppConfig, sheets_client: SheetsClient) -> List[dict]:
    try:
        return sheets_client.get_sites()
    except Exception as exc:  # pragma: no cover - network heavy path
        logger.warning("Falling back to config sites due to sheets error: %s", exc)
        return [site.__dict__ for site in config.sites]


def main(config_path: Path = Path("config.json")) -> None:
    manager = ConfigManager(config_path)
    config = manager.load()

    sheets_client = SheetsClient(
        spreadsheet_url=config.sheets.spreadsheet_url,
        credentials_path=config.sheets.credentials_path,
        worksheet_name=config.sheets.worksheet_name,
    )

    sites = load_sites(config, sheets_client)
    logger.info("Loaded %s sites", len(sites))

    scraper = JobScraper()
    scrape_results = scrape_sites(sites, scraper)

    current_jobs = [job for result in scrape_results for job in result.jobs]
    previous_jobs: List[dict] = []

    diff_engine = DiffEngine()
    diff = diff_engine.diff(previous_jobs, current_jobs)

    checked_at = dt.datetime.utcnow().isoformat()

    email_notifier = EmailNotifier(config.notifications)
    slack_notifier = WebhookNotifier(config.notifications.slack_webhook) if config.notifications.slack_webhook else None
    discord_notifier = WebhookNotifier(config.notifications.discord_webhook) if config.notifications.discord_webhook else None

    if diff.new_jobs or diff.removed_jobs:
        sheets_client.append_jobs_snapshot(diff.new_jobs, notes="New jobs")
    send_notifications(
        email_notifier=email_notifier,
        slack_notifier=slack_notifier,
        discord_notifier=discord_notifier,
        new_jobs=diff.new_jobs,
        removed_jobs=diff.removed_jobs,
        checked_at=checked_at,
        user_name=config.user_name,
    )


if __name__ == "__main__":  # pragma: no cover - manual entry
    main()
