"""Playwright-based scraper for auto24.ee."""

import asyncio
import logging
import random
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, Response, async_playwright

from autoscout.models import Listing, SearchResultItem
from autoscout.parser import parse_listing, parse_search_results

logger = logging.getLogger(__name__)

BASE_URL = "https://eng.auto24.ee"
FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"

# Default delay range between requests (seconds)
DELAY_MIN = 5.0
DELAY_MAX = 10.0

# Max seconds to wait for Cloudflare challenge to resolve
CLOUDFLARE_TIMEOUT = 30.0

# Known brand IDs (b= parameter in nimekiri.php)
BRAND_IDS = {
    "toyota": 13,
    "lexus": 35,
    "honda": 30,
    "mazda": 56,
}


class Auto24Scraper:
    """Drives Playwright to scrape auto24.ee listings.

    URL structure (discovered from real site, Feb 2026):
      Search results:  /kasutatud/nimekiri.php?b=13&f1=2007&f2=2020
      Individual listing: /vehicles/{ID}
      Brand page: /{brand_name}  (e.g., /toyota)

    Parameters for nimekiri.php:
      b   = brand ID (13=Toyota, 35=Lexus, 30=Honda, 56=Mazda)
      bw  = model ID (54=Corolla, 82=Yaris, etc.)
      f1  = year min
      f2  = year max
      ae  = vehicle type (8=used passenger cars)
      ak  = pagination offset (0, 50, 100, ...)
      af  = results per page (50, 200)
    """

    def __init__(
        self,
        headless: bool = True,
        delay_min: float = DELAY_MIN,
        delay_max: float = DELAY_MAX,
    ) -> None:
        self.headless = headless
        self.delay_min = delay_min
        self.delay_max = delay_max
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        """Launch browser and create a persistent context."""
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        self._page = await self._context.new_page()
        logger.info("Browser started (headless=%s)", self.headless)

    async def close(self) -> None:
        """Shut down browser and Playwright."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._pw = None
        logger.info("Browser closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    async def _delay(self) -> None:
        """Random polite delay between requests."""
        wait = random.uniform(self.delay_min, self.delay_max)
        logger.debug("Waiting %.1fs before next request", wait)
        await asyncio.sleep(wait)

    async def _wait_for_cloudflare(self, page: Page) -> None:
        """If Cloudflare challenge is shown, wait for it to resolve."""
        try:
            title = await page.title()
            if "just a moment" not in title.lower():
                return

            logger.info("Cloudflare challenge detected, waiting for resolution...")
            for _ in range(int(CLOUDFLARE_TIMEOUT / 2)):
                await asyncio.sleep(2)
                title = await page.title()
                if "just a moment" not in title.lower():
                    logger.info("Cloudflare challenge resolved")
                    return

            logger.warning("Cloudflare wait timed out after %.0fs", CLOUDFLARE_TIMEOUT)
        except Exception:
            logger.warning("Cloudflare wait failed (page may have crashed)")

    async def get_page(self, url: str) -> str:
        """Navigate to URL, handle Cloudflare, return page HTML.

        Uses response body capture as a fallback — some heavy pages crash
        the renderer on systems with limited /dev/shm, but we can still
        capture the HTTP response body before the crash.
        """
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")

        logger.info("Fetching %s", url)

        # Set up response capture in case the page crashes during rendering
        captured: dict[str, str] = {}

        async def _capture(response: Response) -> None:
            if response.request.resource_type == "document" and response.url == url:
                try:
                    body = await response.body()
                    captured["html"] = body.decode("utf-8", errors="replace")
                except Exception:
                    pass

        self._page.on("response", _capture)

        try:
            resp = await self._page.goto(url, wait_until="commit", timeout=30_000)
            status = resp.status if resp else None

            if status == 403:
                # Likely Cloudflare — wait for challenge to resolve
                await self._wait_for_cloudflare(self._page)

            # Try to get content from the live page
            try:
                await asyncio.sleep(3)
                html = await self._page.content()
                logger.info("Got %d bytes from %s", len(html), url)
                return html
            except Exception:
                # Page crashed during rendering — use captured response
                if "html" in captured:
                    logger.info(
                        "Page crashed but captured %d bytes from response",
                        len(captured["html"]),
                    )
                    return captured["html"]
                raise
        finally:
            self._page.remove_listener("response", _capture)

    async def search(
        self,
        brand_id: int | None = None,
        model_id: int | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        offset: int = 0,
    ) -> list[SearchResultItem]:
        """Fetch one page of search results and parse them.

        URL: /kasutatud/nimekiri.php?b=BRAND&bw=MODEL&f1=YEAR_MIN&f2=YEAR_MAX&ae=8&ak=OFFSET
        """
        params = ["ae=8"]  # ae=8 = used passenger cars
        if brand_id is not None:
            params.append(f"b={brand_id}")
        if model_id is not None:
            params.append(f"bw={model_id}")
        if year_min is not None:
            params.append(f"f1={year_min}")
        if year_max is not None:
            params.append(f"f2={year_max}")
        if offset > 0:
            params.append(f"ak={offset}")

        query = "&".join(params)
        url = f"{BASE_URL}/kasutatud/nimekiri.php?{query}"

        html = await self.get_page(url)
        await self._delay()
        return parse_search_results(html)

    async def search_all_pages(
        self,
        brand_id: int | None = None,
        model_id: int | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        max_pages: int = 10,
        results_per_page: int = 50,
    ) -> list[SearchResultItem]:
        """Fetch all pages of search results up to max_pages."""
        all_results: list[SearchResultItem] = []
        for page_nr in range(max_pages):
            offset = page_nr * results_per_page
            results = await self.search(
                brand_id=brand_id,
                model_id=model_id,
                year_min=year_min,
                year_max=year_max,
                offset=offset,
            )
            if not results:
                logger.info("No results at offset %d, stopping pagination", offset)
                break
            all_results.extend(results)
            logger.info(
                "Offset %d: %d results (total: %d)",
                offset,
                len(results),
                len(all_results),
            )
        return all_results

    async def get_listing(self, listing_id: str) -> Listing:
        """Fetch an individual listing page and parse it."""
        url = f"{BASE_URL}/vehicles/{listing_id}"
        html = await self.get_page(url)
        await self._delay()
        return parse_listing(html, listing_id)

    async def save_fixture(self, html: str, name: str) -> Path:
        """Save HTML to tests/fixtures/ for offline parser development."""
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        path = FIXTURES_DIR / name
        path.write_text(html, encoding="utf-8")
        logger.info("Saved fixture: %s (%d bytes)", path, len(html))
        return path

    async def fetch_and_save_fixtures(
        self,
        brand_id: int | None = None,
        model_id: int | None = None,
    ) -> None:
        """Discovery mode: fetch search results + a listing, save as fixtures."""
        logger.info("=== Discovery mode: fetching fixtures ===")

        # Warm up with a lightweight page to establish Cloudflare cookies
        logger.info("Warming up with brand page...")
        await self.get_page(f"{BASE_URL}/toyota")
        await self._delay()

        # Fetch search results
        params = ["ae=8"]
        if brand_id is not None:
            params.append(f"b={brand_id}")
        if model_id is not None:
            params.append(f"bw={model_id}")
        query = "&".join(params)
        url = f"{BASE_URL}/kasutatud/nimekiri.php?{query}"

        html = await self.get_page(url)
        await self.save_fixture(html, "search_results.html")

        # Parse and fetch first listing
        results = parse_search_results(html)
        if results:
            first = results[0]
            logger.info("Fetching first listing: %s (%s)", first.id, first.title)
            await self._delay()
            listing_html = await self.get_page(first.url)
            await self.save_fixture(listing_html, f"listing_{first.id}.html")
        else:
            logger.warning("No search results found to fetch a listing fixture")

        logger.info("=== Discovery mode complete ===")
