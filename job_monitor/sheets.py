"""Google Sheets helper utilities."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .utils import configure_logging

logger = configure_logging(__name__)


@dataclass
class SheetsRow:
    timestamp: str
    site: str
    title: str
    url: str
    notes: str = ""


class SheetsClient:
    """Abstraction around the Google Sheets API."""

    def __init__(self, spreadsheet_url: str, credentials_path: str, worksheet_name: str = "Job Monitor"):
        self.spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        self.worksheet_name = worksheet_name
        self.credentials_path = credentials_path
        self._service = None
        logger.debug("SheetsClient initialized for worksheet %s", worksheet_name)

    @staticmethod
    def _extract_spreadsheet_id(url: str) -> str:
        parts = url.split("/")
        if "spreadsheets" not in parts:
            raise ValueError("Invalid Google Sheets URL")
        try:
            index = parts.index("d")
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError("Unable to determine spreadsheet id") from exc
        return parts[index + 1]

    @property
    def service(self):
        if self._service is None:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = service_account.Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
            self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return self._service

    def get_sites(self) -> List[Dict[str, Any]]:
        logger.info("Fetching sites from sheet %s", self.worksheet_name)
        response = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{self.worksheet_name}!A2:D")
            .execute()
        )
        rows = response.get("values", [])
        sites = []
        for row in rows:
            if len(row) < 2:
                continue
            name, url = row[:2]
            keywords = row[2].split(",") if len(row) > 2 and row[2] else []
            max_pages = int(row[3]) if len(row) > 3 and row[3] else 1
            sites.append({"name": name, "url": url, "keywords": [k.strip() for k in keywords], "max_pages": max_pages})
        return sites

    def update_sites(self, sites: Iterable[Dict[str, Any]]) -> None:
        logger.info("Updating sheet with %s sites", len(list(sites)))
        rows = [[site["name"], site["url"], ", ".join(site.get("keywords", [])), site.get("max_pages", 1)] for site in sites]
        body = {"values": rows}
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.worksheet_name}!A2",
            valueInputOption="RAW",
            body=body,
        ).execute()

    def append_log(self, rows: Iterable[SheetsRow]) -> None:
        payload = [[row.timestamp, row.site, row.title, row.url, row.notes] for row in rows]
        if not payload:
            return
        body = {"values": payload}
        logger.info("Appending %s rows to sheet", len(payload))
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.worksheet_name}!F2",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

    def append_jobs_snapshot(self, jobs: List[Dict[str, Any]], notes: Optional[str] = None) -> None:
        timestamp = dt.datetime.utcnow().isoformat()
        rows = [
            SheetsRow(timestamp=timestamp, site=job.get("site", ""), title=job.get("title", ""), url=job.get("url", ""), notes=notes or "")
            for job in jobs
        ]
        self.append_log(rows)
