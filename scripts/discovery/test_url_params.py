"""Test auto24.ee URL parameters by fetching real pages with Playwright.

Uses the project's scraper infrastructure (stealth mode, Cloudflare handling)
to verify brand IDs, sort orders, fuel filters, transmission filters, and
pagination parameters.
"""

import asyncio
import json
import logging
import re
import sys
from collections import Counter

from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, "/workspace/src")

from autoscout.scraper import Auto24Scraper
from autoscout.parser import parse_search_results, _text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def extract_summary(html: str) -> dict:
    """Extract a summary of search results from HTML for comparison."""
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("div.result-row")

    brands = []
    fuel_types = []
    transmissions = []
    titles = []
    prices = []
    years = []

    for row in rows:
        # Title / brand
        link = row.select_one("a.main") or row.select_one('a[href*="/vehicles/"]')
        if link:
            spans = link.find_all("span", recursive=False)
            if spans:
                brand_text = _text(spans[0])
                if brand_text:
                    brands.append(brand_text)
            title_text = _text(link)
            if title_text:
                titles.append(title_text)

        # Extra details
        extra = row.select_one("div.extra")
        if extra:
            fuel_el = extra.select_one("span.fuel")
            if fuel_el:
                ft = _text(fuel_el)
                if ft:
                    fuel_types.append(ft)

            trans_el = extra.select_one("span.transmission")
            if trans_el:
                tt = _text(trans_el)
                if tt:
                    transmissions.append(tt)

            year_el = extra.select_one("span.year")
            if year_el:
                yt = _text(year_el)
                if yt:
                    years.append(yt)

        # Price
        price_el = row.select_one("span.price")
        if price_el:
            pt = _text(price_el)
            if pt:
                prices.append(pt)

    # Check for pagination info
    total_text = None
    total_el = soup.select_one("span.result-count") or soup.select_one(".results-count")
    if total_el:
        total_text = _text(total_el)

    # Also look for "Found X vehicles" type text
    found_text = None
    for el in soup.select("div.search-summary, div.list-header, .result-header"):
        t = _text(el)
        if t:
            found_text = t
            break

    # Check page title for clues
    title_tag = soup.select_one("title")
    page_title = _text(title_tag) if title_tag else None

    # Sort order clue
    sort_el = soup.select_one("select.sort-select option[selected]")
    sort_text = _text(sort_el) if sort_el else None

    # Check if we got a Cloudflare challenge page
    is_cloudflare = False
    if page_title and "just a moment" in page_title.lower():
        is_cloudflare = True

    # Check if page has an error
    error_el = soup.select_one("div.error, div.alert, div.no-results")
    error_text = _text(error_el) if error_el else None

    return {
        "total_rows": len(rows),
        "brands": dict(Counter(brands)),
        "fuel_types": dict(Counter(fuel_types)),
        "transmissions": dict(Counter(transmissions)),
        "first_3_titles": titles[:3],
        "last_3_titles": titles[-3:] if len(titles) > 3 else [],
        "first_3_prices": prices[:3],
        "first_3_years": years[:3],
        "page_title": page_title,
        "is_cloudflare": is_cloudflare,
        "total_text": total_text,
        "found_text": found_text,
        "sort_selected": sort_text,
        "error_text": error_text,
        "html_length": len(html),
    }


async def run_test(scraper: Auto24Scraper, test_name: str, url: str) -> dict:
    """Fetch a URL and return a summary."""
    logger.info("=== %s ===", test_name)
    logger.info("URL: %s", url)
    try:
        html = await scraper.get_page(url)
        await asyncio.sleep(3)  # extra politeness between tests
        summary = extract_summary(html)
        logger.info("  Results: %d rows", summary["total_rows"])
        logger.info("  Brands: %s", summary["brands"])
        logger.info("  Fuel types: %s", summary["fuel_types"])
        logger.info("  Transmissions: %s", summary["transmissions"])
        logger.info("  Page title: %s", summary["page_title"])
        if summary["is_cloudflare"]:
            logger.warning("  *** CLOUDFLARE CHALLENGE PAGE ***")
        if summary["error_text"]:
            logger.warning("  Error text: %s", summary["error_text"])
        return {"test": test_name, "url": url, "status": "ok", **summary}
    except Exception as e:
        logger.error("  FAILED: %s", e)
        return {"test": test_name, "url": url, "status": "error", "error": str(e)}


async def main():
    results = {}

    async with Auto24Scraper(headless=True, delay_min=5, delay_max=8) as scraper:
        # Warm up - establish Cloudflare cookies
        logger.info("Warming up with main page...")
        await scraper.get_page("https://eng.auto24.ee/toyota")
        await asyncio.sleep(5)

        # ---- Test 1: Honda brand ID ----
        results["test1a_honda_b30"] = await run_test(
            scraper,
            "Test 1a: Honda b=30",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=30&ae=8&af=20",
        )
        await asyncio.sleep(6)

        results["test1b_honda_b1"] = await run_test(
            scraper,
            "Test 1b: Brand b=1",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=1&ae=8&af=20",
        )
        await asyncio.sleep(6)

        # ---- Test 2: Mazda brand ID ----
        results["test2a_mazda_b56"] = await run_test(
            scraper,
            "Test 2a: Mazda b=56",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=56&ae=8&af=20",
        )
        await asyncio.sleep(6)

        results["test2b_mazda_b6"] = await run_test(
            scraper,
            "Test 2b: Brand b=6",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=6&ae=8&af=20",
        )
        await asyncio.sleep(6)

        # ---- Test 3: ae parameter ----
        results["test3a_toyota_ae8"] = await run_test(
            scraper,
            "Test 3a: Toyota ae=8 (current)",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&ae=8&af=20",
        )
        await asyncio.sleep(6)

        results["test3b_toyota_a100_ae8"] = await run_test(
            scraper,
            "Test 3b: Toyota a=100 ae=8",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&a=100&ae=8&af=20",
        )
        await asyncio.sleep(6)

        results["test3c_toyota_ae1"] = await run_test(
            scraper,
            "Test 3c: Toyota ae=1",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&ae=1&af=20",
        )
        await asyncio.sleep(6)

        # ---- Test 4: Fuel filter ----
        results["test4_petrol"] = await run_test(
            scraper,
            "Test 4: Toyota petrol h[]=1",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&h%5B%5D=1&ae=8&af=20",
        )
        await asyncio.sleep(6)

        # ---- Test 5: Transmission filter ----
        results["test5_petrol_manual"] = await run_test(
            scraper,
            "Test 5: Toyota petrol manual h[]=1&i[]=1",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&h%5B%5D=1&i%5B%5D=1&ae=8&af=20",
        )
        await asyncio.sleep(6)

        # ---- Test 6: af=100 vs af=200 ----
        results["test6a_af100"] = await run_test(
            scraper,
            "Test 6a: Toyota af=100",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&ae=8&af=100",
        )
        await asyncio.sleep(6)

        results["test6b_af200"] = await run_test(
            scraper,
            "Test 6b: Toyota af=200",
            "https://eng.auto24.ee/kasutatud/nimekiri.php?b=13&ae=8&af=200",
        )

    # Print final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS SUMMARY")
    print("=" * 80)

    for key, res in results.items():
        print(f"\n--- {res['test']} ---")
        print(f"  URL: {res['url']}")
        print(f"  Status: {res['status']}")
        if res['status'] == 'ok':
            print(f"  Total rows: {res['total_rows']}")
            print(f"  Page title: {res['page_title']}")
            print(f"  Brands: {res['brands']}")
            print(f"  Fuel types: {res['fuel_types']}")
            print(f"  Transmissions: {res['transmissions']}")
            print(f"  First 3 titles: {res['first_3_titles']}")
            if res.get('first_3_years'):
                print(f"  First 3 years: {res['first_3_years']}")
            if res.get('is_cloudflare'):
                print(f"  *** CLOUDFLARE CHALLENGE - page not loaded ***")
            if res.get('error_text'):
                print(f"  Error: {res['error_text']}")
        else:
            print(f"  Error: {res.get('error', 'unknown')}")

    # Write JSON for detailed analysis
    with open("/workspace/scripts/url_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to /workspace/scripts/url_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
