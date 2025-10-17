from __future__ import annotations

from unittest import mock

import pytest

from job_monitor.config import NotificationConfig
from job_monitor.notifier import EmailNotifier, format_job_summary, send_notifications, WebhookNotifier


@pytest.fixture
def notification_config():
    return NotificationConfig(
        sender="alerts@example.com",
        recipient="user@example.com",
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="alerts@example.com",
        password="secret",
    )


def test_email_notifier_send(notification_config):
    notifier = EmailNotifier(notification_config)
    with mock.patch("smtplib.SMTP") as smtp_mock:
        notifier.send("Subject", "Body")
        smtp_mock.assert_called_once_with("smtp.example.com", 587)
        instance = smtp_mock.return_value.__enter__.return_value
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("alerts@example.com", "secret")
        instance.sendmail.assert_called()


def test_format_job_summary_includes_removed(sample_jobs):
    summary = format_job_summary(sample_jobs, sample_jobs[:1], "2025-01-01T00:00:00", "Alex")
    assert "Hi Alex" in summary
    assert "Roles no longer listed" in summary


def test_send_notifications_triggers_webhooks(notification_config, sample_jobs):
    email_notifier = EmailNotifier(notification_config)
    with mock.patch.object(email_notifier, "send") as email_mock:
        with mock.patch("requests.post") as request_mock:
            slack = WebhookNotifier("https://hooks.slack.com")
            discord = WebhookNotifier("https://discord.com")
            send_notifications(
                email_notifier=email_notifier,
                slack_notifier=slack,
                discord_notifier=discord,
                new_jobs=sample_jobs,
                removed_jobs=[],
                checked_at="2025-01-01T00:00:00",
                user_name="Alex",
            )
    email_mock.assert_called_once()
    assert request_mock.call_count == 2
