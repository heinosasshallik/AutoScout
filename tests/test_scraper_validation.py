"""Canary tests that validate live parsing quality against auto24.ee.

These tests are designed to FAIL LOUDLY if auto24.ee changes their HTML structure
in a way that breaks our parser. They check that a reasonable percentage of
listings have critical fields populated.

Run with: pytest tests/test_scraper_validation.py -m integration
"""

import logging

import pytest

from autoscout.scraper import BRAND_IDS, Auto24Scraper

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)


@pytest.fixture
async def scraper():
    """Create a scraper instance, start and close the browser."""
    s = Auto24Scraper(headless=True, delay_min=2.0, delay_max=4.0)
    await s.start()
    yield s
    await s.close()


async def test_search_results_parsing_quality(scraper):
    """Validate that search results are parsing correctly.

    This test fetches real search results and checks that a high percentage
    have critical fields populated. If auto24.ee changes their HTML structure,
    this test should fail.
    """
    results = await scraper.search(brand_id=BRAND_IDS["toyota"], year_min=2010)
    assert len(results) >= 10, "Need at least 10 results for meaningful validation"

    # Check field population rates
    total = len(results)
    with_price = sum(1 for r in results if r.price_eur is not None)
    with_year = sum(1 for r in results if r.year is not None)
    with_mileage = sum(1 for r in results if r.mileage_km is not None)
    with_fuel = sum(1 for r in results if r.fuel_type)
    with_transmission = sum(1 for r in results if r.transmission)

    # Log parsing rates for visibility
    logger.info("Search results parsing quality:")
    logger.info(f"  Total results: {total}")
    logger.info(f"  With price: {with_price}/{total} ({with_price/total*100:.1f}%)")
    logger.info(f"  With year: {with_year}/{total} ({with_year/total*100:.1f}%)")
    logger.info(f"  With mileage: {with_mileage}/{total} ({with_mileage/total*100:.1f}%)")
    logger.info(f"  With fuel: {with_fuel}/{total} ({with_fuel/total*100:.1f}%)")
    logger.info(f"  With transmission: {with_transmission}/{total} ({with_transmission/total*100:.1f}%)")

    # Assert minimum thresholds (80% is reasonable - some listings may be incomplete)
    assert with_price / total >= 0.80, (
        f"Only {with_price}/{total} results have price. "
        "auto24.ee HTML may have changed!"
    )
    assert with_year / total >= 0.80, (
        f"Only {with_year}/{total} results have year. "
        "auto24.ee HTML may have changed!"
    )
    assert with_mileage / total >= 0.80, (
        f"Only {with_mileage}/{total} results have mileage. "
        "auto24.ee HTML may have changed!"
    )
    assert with_fuel / total >= 0.70, (
        f"Only {with_fuel}/{total} results have fuel type. "
        "auto24.ee HTML may have changed!"
    )
    assert with_transmission / total >= 0.70, (
        f"Only {with_transmission}/{total} results have transmission. "
        "auto24.ee HTML may have changed!"
    )


async def test_listing_page_parsing_quality(scraper):
    """Validate that listing detail pages are parsing correctly.

    This test fetches several real listing pages and checks that critical
    fields are populated. If auto24.ee changes their HTML structure,
    this test should fail.
    """
    # Get some listing IDs from search
    results = await scraper.search(brand_id=BRAND_IDS["toyota"], year_min=2010)
    assert len(results) >= 5, "Need at least 5 results to test listing parsing"

    # Fetch first 5 listings
    sample_size = min(5, len(results))
    listings = []
    for i in range(sample_size):
        listing = await scraper.get_listing(results[i].id)
        listings.append(listing)

    # Check field population rates
    total = len(listings)
    with_make = sum(1 for l in listings if l.make)
    with_model = sum(1 for l in listings if l.model)
    with_year = sum(1 for l in listings if l.year)
    with_price = sum(1 for l in listings if l.price_eur)
    with_mileage = sum(1 for l in listings if l.mileage_km)
    with_fuel = sum(1 for l in listings if l.fuel_type)
    with_transmission = sum(1 for l in listings if l.transmission)
    with_engine_cc = sum(1 for l in listings if l.engine_cc)
    with_power_kw = sum(1 for l in listings if l.power_kw)
    with_photos = sum(1 for l in listings if l.photo_urls and len(l.photo_urls) > 0)
    with_seller = sum(1 for l in listings if l.seller_name)
    with_location = sum(1 for l in listings if l.location)

    # Log parsing rates for visibility
    logger.info("Listing detail parsing quality:")
    logger.info(f"  Total listings: {total}")
    logger.info(f"  With make: {with_make}/{total} ({with_make/total*100:.1f}%)")
    logger.info(f"  With model: {with_model}/{total} ({with_model/total*100:.1f}%)")
    logger.info(f"  With year: {with_year}/{total} ({with_year/total*100:.1f}%)")
    logger.info(f"  With price: {with_price}/{total} ({with_price/total*100:.1f}%)")
    logger.info(f"  With mileage: {with_mileage}/{total} ({with_mileage/total*100:.1f}%)")
    logger.info(f"  With fuel: {with_fuel}/{total} ({with_fuel/total*100:.1f}%)")
    logger.info(f"  With transmission: {with_transmission}/{total} ({with_transmission/total*100:.1f}%)")
    logger.info(f"  With engine_cc: {with_engine_cc}/{total} ({with_engine_cc/total*100:.1f}%)")
    logger.info(f"  With power_kw: {with_power_kw}/{total} ({with_power_kw/total*100:.1f}%)")
    logger.info(f"  With photos: {with_photos}/{total} ({with_photos/total*100:.1f}%)")
    logger.info(f"  With seller: {with_seller}/{total} ({with_seller/total*100:.1f}%)")
    logger.info(f"  With location: {with_location}/{total} ({with_location/total*100:.1f}%)")

    # Critical fields should be present in 100% of listings
    assert with_make == total, (
        f"Only {with_make}/{total} listings have make. "
        "auto24.ee HTML may have changed!"
    )
    assert with_model == total, (
        f"Only {with_model}/{total} listings have model. "
        "auto24.ee HTML may have changed!"
    )
    assert with_year == total, (
        f"Only {with_year}/{total} listings have year. "
        "auto24.ee HTML may have changed!"
    )
    assert with_price == total, (
        f"Only {with_price}/{total} listings have price. "
        "auto24.ee HTML may have changed!"
    )

    # Important fields should be present in most listings (90%+)
    assert with_mileage / total >= 0.90, (
        f"Only {with_mileage}/{total} listings have mileage. "
        "auto24.ee HTML may have changed!"
    )
    assert with_fuel / total >= 0.90, (
        f"Only {with_fuel}/{total} listings have fuel type. "
        "auto24.ee HTML may have changed!"
    )
    assert with_transmission / total >= 0.90, (
        f"Only {with_transmission}/{total} listings have transmission. "
        "auto24.ee HTML may have changed!"
    )
    assert with_engine_cc / total >= 0.80, (
        f"Only {with_engine_cc}/{total} listings have engine displacement. "
        "auto24.ee HTML may have changed!"
    )
    assert with_power_kw / total >= 0.80, (
        f"Only {with_power_kw}/{total} listings have power. "
        "auto24.ee HTML may have changed!"
    )
    assert with_photos / total >= 0.90, (
        f"Only {with_photos}/{total} listings have photos. "
        "auto24.ee HTML may have changed!"
    )

    # Nice-to-have fields should be present in many listings (70%+)
    assert with_seller / total >= 0.70, (
        f"Only {with_seller}/{total} listings have seller name. "
        "auto24.ee HTML may have changed!"
    )
    assert with_location / total >= 0.70, (
        f"Only {with_location}/{total} listings have location. "
        "auto24.ee HTML may have changed!"
    )


async def test_photo_urls_are_accessible(scraper):
    """Verify that extracted photo URLs are valid and accessible.

    If auto24.ee changes their image URL structure, this will catch it.
    """
    results = await scraper.search(brand_id=BRAND_IDS["toyota"], year_min=2010)
    assert results, "Need at least one result"

    listing = await scraper.get_listing(results[0].id)
    assert listing.photo_urls, "Listing should have photos"
    assert len(listing.photo_urls) >= 3, "Typical listing should have at least 3 photos"

    # Check first photo URL structure
    first_photo = listing.photo_urls[0]
    assert first_photo.startswith("http"), f"Photo URL should be absolute: {first_photo}"
    # auto24.ee uses Baltic Classifieds Group CDN (img-bcg.eu)
    assert "img-bcg.eu" in first_photo or "auto24" in first_photo, (
        f"Photo URL doesn't match expected CDN pattern: {first_photo}. "
        "auto24.ee may have changed their image hosting!"
    )
