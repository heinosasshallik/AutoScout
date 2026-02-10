"""Integration tests for autoscout.scraper — hits real auto24.ee.

These tests require network access and Playwright browsers installed.
Run with: pytest tests/test_scraper.py -m integration
"""

import pytest

from autoscout.scraper import Auto24Scraper, BRAND_IDS

pytestmark = pytest.mark.integration


@pytest.fixture
async def scraper():
    """Create a scraper instance, start and close the browser."""
    s = Auto24Scraper(headless=True, delay_min=2.0, delay_max=4.0)
    await s.start()
    yield s
    await s.close()


async def test_can_load_brand_page(scraper):
    """Verify we can get past Cloudflare and load a brand page."""
    html = await scraper.get_page("https://eng.auto24.ee/toyota")
    assert len(html) > 1000, "Page HTML seems too short"
    assert "Toyota" in html, "Page doesn't contain expected brand content"


async def test_search_returns_results(scraper):
    """Search for Toyota Corolla and verify we get results."""
    results = await scraper.search(brand_id=BRAND_IDS["toyota"], model_id=54)
    assert len(results) > 0, "Expected search results for Toyota Corolla"
    for item in results:
        assert item.id
        assert item.url
        assert item.id.isdigit()


async def test_get_listing_returns_data(scraper):
    """Fetch a specific listing and verify it parses."""
    # First search to find a listing ID
    results = await scraper.search(brand_id=BRAND_IDS["toyota"], model_id=54)
    assert results, "Need at least one result to test listing fetch"

    listing = await scraper.get_listing(results[0].id)
    assert listing.id == results[0].id
    assert listing.make is not None
    assert listing.raw_html


async def test_fetch_and_save_fixtures(scraper, tmp_path, monkeypatch):
    """Verify discovery mode works (fetch + save fixtures)."""
    import autoscout.scraper as scraper_mod

    monkeypatch.setattr(scraper_mod, "FIXTURES_DIR", tmp_path)

    await scraper.fetch_and_save_fixtures(brand_id=BRAND_IDS["toyota"], model_id=54)

    saved = list(tmp_path.glob("*.html"))
    assert len(saved) >= 1, "Expected at least one fixture file saved"
