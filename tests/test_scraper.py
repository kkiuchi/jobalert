
from __future__ import annotations

from types import SimpleNamespace

from job_monitor.scraper import JobScraper


def test_scraper_parses_jobs(sample_html):
    scraper = JobScraper()
    scraper._request = lambda url: SimpleNamespace(text=sample_html)  # type: ignore[attr-defined]
    scraper._find_next_page = lambda soup: None  # type: ignore[attr-defined]

    result = scraper.fetch_site({"name": "Example", "url": "https://example.com", "keywords": []})
    assert len(result.jobs) == 4
    assert any(job["title"] == "Backend Engineer" for job in result.jobs)


def test_scraper_filters_keywords(sample_html):
    scraper = JobScraper()
    scraper._request = lambda url: SimpleNamespace(text=sample_html)  # type: ignore[attr-defined]
    scraper._find_next_page = lambda soup: None  # type: ignore[attr-defined]

    result = scraper.fetch_site({"name": "Example", "url": "https://example.com", "keywords": ["data"]})
    assert len(result.jobs) == 1
    assert result.jobs[0]["title"] == "Data Scientist"
