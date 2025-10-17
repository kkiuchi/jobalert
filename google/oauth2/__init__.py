from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class _Credentials:
    scopes: List[str]

    @classmethod
    def from_service_account_file(cls, _: str, scopes: List[str]):
        return cls(scopes=scopes)


class service_account:  # pylint: disable=invalid-name
    Credentials = _Credentials
