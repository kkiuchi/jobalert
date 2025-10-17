"""Web scraping utilities for job listings."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

from .utils import configure_logging, deduplicate_jobs

logger = configure_logging(__name__)


@dataclass
class ScrapeResult:
    site: str
    jobs: List[Dict[str, str]]
    errors: List[str]


class JobScraper:
    """Scrape job postings from configured sites."""

    def __init__(self, *, delay: float = 1.0, timeout: int = 10, max_retries: int = 3):
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch_site(self, site: Dict[str, any]) -> ScrapeResult:
        url = site["url"]
        keywords = [kw.lower() for kw in site.get("keywords", [])]
        max_pages = int(site.get("max_pages", 1))
        logger.info("Scraping %s", url)
        jobs: List[Dict[str, str]] = []
        errors: List[str] = []
        next_url: Optional[str] = url
        pages_visited = 0

        while next_url and pages_visited < max_pages:
            try:
                response = self._request(next_url)
            except requests.RequestException as exc:
                errors.append(f"Failed to fetch {next_url}: {exc}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            page_jobs = self._parse_jobs(soup, site["name"], keywords)
            jobs.extend(page_jobs)
            pages_visited += 1
            next_url = self._find_next_page(soup)
            if next_url:
                time.sleep(self.delay)

        return ScrapeResult(site=site["name"], jobs=deduplicate_jobs(jobs), errors=errors)

    def _request(self, url: str) -> requests.Response:
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                logger.warning("Request to %s failed (%s/%s): %s", url, attempt + 1, self.max_retries, exc)
                if attempt + 1 == self.max_retries:
                    raise
                time.sleep(self.delay * (attempt + 1))
        raise RuntimeError("Unreachable")

    def _parse_jobs(self, soup: BeautifulSoup, site_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        jobs: List[Dict[str, str]] = []
        for link in soup.select("a"):
            title = (link.get_text() or "").strip()
            href = link.get("href", "").strip()
            if not title or not href:
                continue
            lower_title = title.lower()
            if keywords and not any(keyword in lower_title for keyword in keywords):
                continue
            if href.startswith("/"):
                href = href
            jobs.append({"site": site_name, "title": title, "url": href})
        return jobs

    def _find_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        next_link = soup.find("a", string=lambda text: text and "next" in text.lower())
        if not next_link:
            return None
        return next_link.get("href")


def scrape_sites(sites: Iterable[Dict[str, any]], scraper: Optional[JobScraper] = None) -> List[ScrapeResult]:
    scraper = scraper or JobScraper()
    results = []
    for site in sites:
        result = scraper.fetch_site(site)
        results.append(result)
    return results
