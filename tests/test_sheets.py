from __future__ import annotations

from job_monitor.sheets import SheetsClient


def create_client():
    url = "https://docs.google.com/spreadsheets/d/abc123/edit"
    client = SheetsClient(spreadsheet_url=url, credentials_path="creds.json", worksheet_name="Jobs")
    client._service = DummyService()  # type: ignore[attr-defined]
    return client


class DummyValues:
    def __init__(self, service):
        self.service = service
        self.response = {"values": [["Example", "https://example.com", "data, python", "2"]]}

    def get(self, spreadsheetId, range):  # noqa: D401 - stub
        self.service.calls.append(("get", spreadsheetId, range))
        return self

    def update(self, *args, **kwargs):
        self.service.calls.append(("update", args, kwargs))
        return self

    def append(self, *args, **kwargs):
        self.service.calls.append(("append", args, kwargs))
        return self

    def execute(self):
        return self.response


class DummySheets:
    def __init__(self, service):
        self.service = service

    def values(self):
        return DummyValues(self.service)


class DummyService:
    def __init__(self):
        self.calls = []

    def spreadsheets(self):
        return DummySheets(self)


def test_get_sites_parses_rows():
    client = create_client()
    sites = client.get_sites()
    assert sites[0]["name"] == "Example"
    assert sites[0]["keywords"] == ["data", "python"]
    assert sites[0]["max_pages"] == 2


def test_update_sites_records_calls():
    client = create_client()
    client.update_sites([
        {"name": "Example", "url": "https://example.com", "keywords": ["data"], "max_pages": 1}
    ])
    assert any(call[0] == "update" for call in client._service.calls)  # type: ignore[attr-defined]


def test_append_jobs_snapshot_appends_rows(sample_jobs):
    client = create_client()
    client.append_jobs_snapshot(sample_jobs, notes="New")
    assert any(call[0] == "append" for call in client._service.calls)  # type: ignore[attr-defined]
