"""Notification helpers for email and webhooks."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Iterable, List, Optional

import requests

from .config import NotificationConfig
from .utils import configure_logging

logger = configure_logging(__name__)


class EmailNotifier:
    """Send email notifications about job updates."""

    def __init__(self, config: NotificationConfig):
        self.config = config

    def build_message(self, subject: str, body: str) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.config.sender
        message["To"] = self.config.recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        return message

    def send(self, subject: str, body: str) -> None:
        message = self.build_message(subject, body)
        logger.info("Sending email to %s", self.config.recipient)
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.username, self.config.password)
            server.sendmail(self.config.sender, [self.config.recipient], message.as_string())


class WebhookNotifier:
    """Send webhook notifications to Slack or Discord."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, text: str) -> None:
        logger.info("Posting webhook notification")
        response = requests.post(self.webhook_url, json={"text": text}, timeout=10)
        response.raise_for_status()


def format_job_summary(new_jobs: Iterable[Dict[str, str]], removed_jobs: Iterable[Dict[str, str]], checked_at: str, user_name: str) -> str:
    lines: List[str] = [f"Hi {user_name},", "", "Here are the latest job updates:"]

    new_jobs_list = list(new_jobs)
    removed_jobs_list = list(removed_jobs)

    if new_jobs_list:
        lines.append("")
        lines.append("New positions:")
        for job in new_jobs_list:
            lines.append(f"- {job.get('site', 'Unknown')}: {job.get('title')} -> {job.get('url')}")
    else:
        lines.append("")
        lines.append("No new positions found.")

    if removed_jobs_list:
        lines.append("")
        lines.append("Roles no longer listed:")
        for job in removed_jobs_list:
            lines.append(f"- {job.get('site', 'Unknown')}: {job.get('title')} -> {job.get('url')}")

    lines.append("")
    lines.append(f"Checked at: {checked_at}")
    return "\n".join(lines)


def send_notifications(
    *,
    email_notifier: EmailNotifier,
    slack_notifier: Optional[WebhookNotifier],
    discord_notifier: Optional[WebhookNotifier],
    new_jobs: Iterable[Dict[str, str]],
    removed_jobs: Iterable[Dict[str, str]],
    checked_at: str,
    user_name: str,
) -> None:
    summary = format_job_summary(new_jobs, removed_jobs, checked_at, user_name)
    subject = f"New Job Postings – {checked_at.split('T')[0]}"
    email_notifier.send(subject, summary)

    webhook_text = summary
    if slack_notifier:
        slack_notifier.send(webhook_text)
    if discord_notifier:
        discord_notifier.send(webhook_text)
