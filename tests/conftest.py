from __future__ import annotations

import pytest


@pytest.fixture
def sample_html() -> str:
    return """
    <html>
        <body>
            <a href="https://example.com/job1">Backend Engineer</a>
            <a href="https://example.com/job2">Data Scientist</a>
            <a href="/job3">Marketing Manager</a>
            <a href="https://example.com/next">Next Page</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_jobs():
    return [
        {"site": "Example", "title": "Backend Engineer", "url": "https://example.com/job1"},
        {"site": "Example", "title": "Data Scientist", "url": "https://example.com/job2"},
    ]
