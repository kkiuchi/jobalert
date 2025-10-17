from __future__ import annotations

from html.parser import HTMLParser
from typing import Callable, List, Optional


class _Link:
    def __init__(self, text: str, href: str):
        self._text = text
        self._href = href

    def get_text(self) -> str:
        return self._text

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if key == "href":
            return self._href
        return default


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: List[_Link] = []
        self._current_href: Optional[str] = None
        self._collect_text = False
        self._text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag == "a":
            self._collect_text = True
            self._current_href = dict(attrs).get("href", "")

    def handle_endtag(self, tag: str):
        if tag == "a" and self._collect_text:
            text = "".join(self._text_parts).strip()
            self.links.append(_Link(text, self._current_href or ""))
            self._collect_text = False
            self._text_parts = []
            self._current_href = None

    def handle_data(self, data: str):
        if self._collect_text:
            self._text_parts.append(data)


class BeautifulSoup:
    def __init__(self, markup: str, parser: str = "html.parser"):
        self._parser = _Parser()
        self._parser.feed(markup)

    def select(self, selector: str):
        if selector == "a":
            return self._parser.links
        raise NotImplementedError("Only 'a' selector is supported in stub")

    def find(self, selector: str, string: Callable[[str], bool]):
        if selector != "a":
            return None
        for link in self._parser.links:
            text = link.get_text()
            if string(text):
                return link
        return None
