from __future__ import annotations


class _SheetValues:
    def __init__(self, service):
        self._service = service

    def get(self, spreadsheetId: str, range: str):  # pylint: disable=unused-argument,redefined-builtin
        return self._service.stub

    def update(self, spreadsheetId: str, range: str, valueInputOption: str, body: dict):  # noqa: D401 - stub
        self._service.calls.append(("update", spreadsheetId, range, valueInputOption, body))
        return self

    def append(self, spreadsheetId: str, range: str, valueInputOption: str, insertDataOption: str, body: dict):
        self._service.calls.append(("append", spreadsheetId, range, valueInputOption, insertDataOption, body))
        return self

    def execute(self):
        return self._service.stub


class _Sheets:
    def __init__(self, service):
        self._service = service

    def values(self):
        return _SheetValues(self._service)


class _Spreadsheets:
    def __init__(self, service):
        self._service = service

    def values(self):
        return _Sheets(self._service)


class _Service:
    def __init__(self):
        self.calls = []
        self.stub = {"values": []}

    def spreadsheets(self):
        return self

    def values(self):
        return _SheetValues(self)

    def execute(self):
        return self.stub


def build(api_name: str, api_version: str, credentials=None, cache_discovery=False):  # noqa: D401 - stub
    return _Service()
