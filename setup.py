"""Interactive setup wizard for the job alert system."""
from __future__ import annotations

import getpass
from pathlib import Path
from typing import List

from job_monitor.config import AppConfig, ConfigManager, NotificationConfig, SheetsConfig, SiteConfig
from job_monitor.notifier import EmailNotifier
from job_monitor.sheets import SheetsClient
from job_monitor.utils import configure_logging

logger = configure_logging(__name__)


def prompt(text: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if secret:
        value = getpass.getpass(f"{text}{suffix}: ")
    else:
        value = input(f"{text}{suffix}: ")
    if not value and default:
        return default
    return value


def collect_sites() -> List[SiteConfig]:
    sites: List[SiteConfig] = []
    while True:
        add_more = prompt("Add a site? (y/n)", default="n").lower()
        if add_more != "y":
            break
        name = prompt("Site name")
        url = prompt("Site URL")
        keywords_raw = prompt("Comma separated keywords (optional)", default="")
        keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()]
        max_pages_raw = prompt("Max pages to follow", default="1")
        max_pages = int(max_pages_raw)
        sites.append(SiteConfig(name=name, url=url, keywords=keywords, max_pages=max_pages))
    return sites


def run_setup(config_path: Path = Path("config.json")) -> None:
    print("Job Alert System Setup")
    user_name = prompt("Your name")
    recipient = prompt("Alert recipient email")
    sender = prompt("Sender email", default=recipient)
    smtp_server = prompt("SMTP server", default="smtp.gmail.com")
    smtp_port = int(prompt("SMTP port", default="587"))
    username = prompt("SMTP username", default=sender)
    password = prompt("SMTP password", secret=True)
    use_tls = prompt("Use TLS? (y/n)", default="y").lower() == "y"

    slack_webhook = prompt("Slack webhook URL (optional)", default="")
    slack_webhook = slack_webhook or None
    discord_webhook = prompt("Discord webhook URL (optional)", default="")
    discord_webhook = discord_webhook or None

    spreadsheet_url = prompt("Google Sheets URL")
    credentials_path = prompt("Google credentials JSON path")
    worksheet_name = prompt("Worksheet name", default="Job Monitor")

    sites = collect_sites()

    notifications = NotificationConfig(
        sender=sender,
        recipient=recipient,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        use_tls=use_tls,
        slack_webhook=slack_webhook,
        discord_webhook=discord_webhook,
    )
    sheets = SheetsConfig(spreadsheet_url=spreadsheet_url, credentials_path=credentials_path, worksheet_name=worksheet_name)

    config = AppConfig(user_name=user_name, notifications=notifications, sheets=sheets, sites=sites)

    manager = ConfigManager(config_path)
    manager.save(config)
    print(f"Configuration saved to {config_path}")

    email_notifier = EmailNotifier(notifications)
    test_subject = "Job Alert System Setup"
    test_body = "Setup complete. This is a test notification."
    try:
        email_notifier.send(test_subject, test_body)
        print("Test email sent successfully.")
    except Exception as exc:
        logger.warning("Unable to send test email: %s", exc)

    try:
        sheets_client = SheetsClient(spreadsheet_url=spreadsheet_url, credentials_path=credentials_path, worksheet_name=worksheet_name)
        sheets_client.update_sites([site.__dict__ for site in sites])
        print("Google Sheets updated with initial sites.")
    except Exception as exc:
        logger.warning("Unable to update Google Sheets: %s", exc)

    cron_command = f"0 8 * * * /usr/bin/python {Path.cwd() / 'monitor_jobs.py'}"
    print("Setup complete! Suggested cron command:")
    print(cron_command)


if __name__ == "__main__":  # pragma: no cover - interactive
    run_setup()
