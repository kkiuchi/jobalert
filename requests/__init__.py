from __future__ import annotations


class RequestException(Exception):
    """Generic request error."""


class Response:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 300):
            raise RequestException(f"HTTP {self.status_code}")


def get(url: str, timeout: int = 10, headers: dict | None = None) -> Response:  # pragma: no cover - stub
    raise RequestException("requests.get not implemented in stub")


def post(url: str, json: dict | None = None, timeout: int = 10) -> Response:  # pragma: no cover - stub
    return Response()
