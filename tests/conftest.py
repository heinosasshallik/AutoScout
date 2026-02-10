"""Shared pytest fixtures for autoscout tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


def load_fixture(name: str) -> str:
    """Load an HTML fixture file by name."""
    path = FIXTURES_DIR / name
    if not path.exists():
        pytest.skip(f"Fixture {name} not found — run scraper discovery mode first")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def search_results_html() -> str:
    """Load the search results HTML fixture."""
    return load_fixture("search_results.html")


@pytest.fixture
def listing_html() -> str:
    """Load the listing_4244561.html fixture."""
    return load_fixture("listing_4244561.html")
