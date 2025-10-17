"""CLI for managing monitored job sites."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from job_monitor.config import AppConfig, ConfigManager, SiteConfig
from job_monitor.sheets import SheetsClient
from job_monitor.utils import configure_logging

logger = configure_logging(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage job monitor sites")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new site")
    add_parser.add_argument("name")
    add_parser.add_argument("url")
    add_parser.add_argument("--keywords", nargs="*", default=[])
    add_parser.add_argument("--max-pages", type=int, default=1)

    update_parser = subparsers.add_parser("update", help="Update an existing site")
    update_parser.add_argument("name")
    update_parser.add_argument("--url")
    update_parser.add_argument("--keywords", nargs="*")
    update_parser.add_argument("--max-pages", type=int)

    remove_parser = subparsers.add_parser("remove", help="Remove a site")
    remove_parser.add_argument("name")

    subparsers.add_parser("list", help="List configured sites")

    parser.add_argument("--config", type=Path, default=Path("config.json"))
    return parser.parse_args()


def load_config(path: Path) -> AppConfig:
    manager = ConfigManager(path)
    return manager.load()


def save_config(config: AppConfig, path: Path) -> None:
    manager = ConfigManager(path)
    manager.save(config)


def sync_sheets(config: AppConfig) -> None:
    sheets = SheetsClient(
        spreadsheet_url=config.sheets.spreadsheet_url,
        credentials_path=config.sheets.credentials_path,
        worksheet_name=config.sheets.worksheet_name,
    )
    sheets.update_sites([site.__dict__ for site in config.sites])


def command_add(config: AppConfig, args: argparse.Namespace) -> None:
    config.sites.append(SiteConfig(name=args.name, url=args.url, keywords=args.keywords, max_pages=args.max_pages))
    logger.info("Added site %s", args.name)


def command_list(config: AppConfig, _: argparse.Namespace) -> None:
    for site in config.sites:
        print(f"{site.name}: {site.url} (keywords: {', '.join(site.keywords)})")


def command_update(config: AppConfig, args: argparse.Namespace) -> None:
    for site in config.sites:
        if site.name == args.name:
            if args.url:
                site.url = args.url
            if args.keywords is not None:
                site.keywords = args.keywords
            if args.max_pages is not None:
                site.max_pages = args.max_pages
            logger.info("Updated site %s", args.name)
            return
    raise ValueError(f"Site {args.name} not found")


def command_remove(config: AppConfig, args: argparse.Namespace) -> None:
    before = len(config.sites)
    config.sites = [site for site in config.sites if site.name != args.name]
    if len(config.sites) == before:
        raise ValueError(f"Site {args.name} not found")
    logger.info("Removed site %s", args.name)


COMMANDS = {
    "add": command_add,
    "list": command_list,
    "update": command_update,
    "remove": command_remove,
}


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    command = COMMANDS[args.command]
    command(config, args)
    if args.command != "list":
        save_config(config, args.config)
        try:
            sync_sheets(config)
        except Exception as exc:  # pragma: no cover - network heavy path
            logger.warning("Unable to sync sheets: %s", exc)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
