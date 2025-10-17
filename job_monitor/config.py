"""Configuration management for the job monitor system."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import configure_logging, load_json, save_json


CONFIG_PATH = Path("config.json")
BACKUP_DIR = Path("data") / "config_backups"

logger = configure_logging(__name__)


class ConfigError(RuntimeError):
    """Raised when configuration validation fails."""


@dataclass
class SiteConfig:
    """Represents a monitored site configuration."""

    name: str
    url: str
    keywords: List[str] = field(default_factory=list)
    max_pages: int = 1


@dataclass
class NotificationConfig:
    sender: str
    recipient: str
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None


@dataclass
class SheetsConfig:
    spreadsheet_url: str
    credentials_path: str
    worksheet_name: str = "Job Monitor"


@dataclass
class AppConfig:
    user_name: str
    notifications: NotificationConfig
    sheets: SheetsConfig
    sites: List[SiteConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_name": self.user_name,
            "notifications": self.notifications.__dict__,
            "sheets": self.sheets.__dict__,
            "sites": [site.__dict__ for site in self.sites],
        }


SCHEMA = {
    "user_name": str,
    "notifications": dict,
    "sheets": dict,
    "sites": list,
}


class ConfigManager:
    """Loads, validates, and persists configuration data."""

    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        logger.debug("ConfigManager initialized with path %s", self.path)

    def load(self) -> AppConfig:
        if not self.path.exists():
            raise ConfigError(f"Config file {self.path} does not exist")
        data = load_json(self.path)
        logger.debug("Loaded config data: %s", data)
        self._validate_schema(data)
        notifications = NotificationConfig(**data["notifications"])
        sheets = SheetsConfig(**data["sheets"])
        sites = [SiteConfig(**site) for site in data.get("sites", [])]
        return AppConfig(
            user_name=data["user_name"],
            notifications=notifications,
            sheets=sheets,
            sites=sites,
        )

    def save(self, config: AppConfig) -> None:
        payload = config.to_dict()
        logger.debug("Saving config: %s", payload)
        self._validate_schema(payload)
        self._backup_existing()
        save_json(self.path, payload)

    def _backup_existing(self) -> None:
        if self.path.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = BACKUP_DIR / f"config_backup_{self.path.stat().st_mtime_ns}.json"
            shutil.copy2(self.path, backup_path)
            logger.info("Backed up config to %s", backup_path)

    @staticmethod
    def _validate_schema(payload: Dict[str, Any]) -> None:
        missing = [key for key in SCHEMA if key not in payload]
        if missing:
            raise ConfigError(f"Config missing keys: {missing}")
        for key, expected_type in SCHEMA.items():
            if not isinstance(payload.get(key), expected_type):
                raise ConfigError(f"Config key '{key}' must be {expected_type.__name__}")


def ensure_default_config(path: Path = CONFIG_PATH) -> None:
    """Create an empty config placeholder if none exists."""
    if path.exists():
        return
    default = {
        "user_name": "",
        "notifications": {
            "sender": "",
            "recipient": "",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "use_tls": True,
        },
        "sheets": {
            "spreadsheet_url": "",
            "credentials_path": "",
            "worksheet_name": "Job Monitor",
        },
        "sites": [],
    }
    save_json(path, default)
    logger.info("Created default config at %s", path)
