"""HTML parsing for auto24.ee search results and listing pages.

Uses BeautifulSoup to extract structured data from auto24.ee HTML.
Selectors are built against real HTML fixtures from February 2026.
If auto24 changes their markup, update the selectors here.

Search results page structure (nimekiri.php):
  div.result-row
    div.thumbnail > a[href="/vehicles/{ID}"]
    div.description
      div.title > a.main > span (make) + span.model + span.engine
      div.extra > span.year, span.mileage, span.fuel, span.transmission,
                  span.bodytype, span.drive
      div.finance > span.price

Listing page structure (/vehicles/{ID}):
  table.main-data > tr > td.label + td.field  (main properties)
  div.vImages > a.vImages__item > img  (photos)
  div.vEquipment  (equipment/description)
  div.vTechData  (technical specifications)
  address.seller  (seller info)
  div.other-info  (location, registration status)
"""

import logging
import re

from bs4 import BeautifulSoup, Tag

from autoscout.models import Listing, SearchResultItem

logger = logging.getLogger(__name__)

BASE_URL = "https://eng.auto24.ee"


def _text(el: Tag | None) -> str | None:
    """Extract stripped text from a BS4 element, or None."""
    if el is None:
        return None
    text = el.get_text(strip=True)
    return text if text else None


def _parse_price(text: str | None) -> int | None:
    """Parse price string like '€7700' or 'EUR 4000' or '5 900 €' into integer euros."""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    return int(digits)


def _parse_mileage(text: str | None) -> int | None:
    """Parse mileage like '178 000 km' or '343\xa0300\xa0km' into integer km."""
    if not text:
        return None
    # Replace non-breaking spaces and regular spaces, keep only digits
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    return int(digits)


def _parse_year(text: str | None) -> int | None:
    """Parse year from text, e.g. '2015' or '06/2012'."""
    if not text:
        return None
    match = re.search(r"((?:19|20)\d{2})", text)
    return int(match.group(1)) if match else None


def _parse_engine_cc(text: str | None) -> int | None:
    """Parse engine displacement like '1598 cm³' or '1.6 l' into cc."""
    if not text:
        return None
    # Try cm³ format first: "1598 cm³"
    match = re.search(r"(\d{3,5})\s*cm", text)
    if match:
        return int(match.group(1))
    # Try liter format: "1.6 l" or "1.6"
    match = re.search(r"(\d+\.\d+)\s*[Ll]?\b", text)
    if match:
        return int(float(match.group(1)) * 1000)
    return None


def _parse_power_kw(text: str | None) -> int | None:
    """Parse power like '97 kW' or '97kW' into kW integer."""
    if not text:
        return None
    match = re.search(r"(\d+)\s*kW", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_listing_id(url: str) -> str:
    """Extract listing ID from URL like '/vehicles/4275993'."""
    match = re.search(r"/vehicles/(\d+)", url)
    if match:
        return match.group(1)
    # Fallback: last numeric segment
    match = re.search(r"/(\d+)(?:[^/]*)?$", url)
    return match.group(1) if match else url.rstrip("/").split("/")[-1]


# ---------------------------------------------------------------------------
# Search results parsing
# ---------------------------------------------------------------------------

def parse_search_results(html: str) -> list[SearchResultItem]:
    """Parse a search results page (nimekiri.php) into SearchResultItems."""
    soup = BeautifulSoup(html, "lxml")
    items: list[SearchResultItem] = []

    rows = soup.select("div.result-row")

    for row in rows:
        item = _parse_result_row(row)
        if item:
            items.append(item)

    logger.info("Parsed %d search results from HTML", len(items))
    return items


def _parse_result_row(row: Tag) -> SearchResultItem | None:
    """Parse a single div.result-row into SearchResultItem."""
    # Find the main listing link: <a href="/vehicles/{ID}" class="main">
    link = row.select_one('a.main') or row.select_one('a[href*="/vehicles/"]')
    if not link:
        return None

    href = link.get("href", "")
    if not href.startswith("http"):
        href = BASE_URL + href

    listing_id = _extract_listing_id(href)

    # Title: combine make + model + engine from spans inside the main link
    # Structure: <a class="main"><span>Toyota</span> <span class="model">Corolla</span>
    #            <span class="engine">1.6 97kW</span></a>
    title_parts = []
    for span in link.find_all("span", recursive=False):
        text = _text(span)
        if text:
            title_parts.append(text)
    title = " ".join(title_parts) if title_parts else (_text(link) or "")

    # The .extra div has the detailed fields — prefer it over .title spans
    # because the .title has abbreviated versions (e.g., "P" vs "Petrol")
    extra = row.select_one("div.extra")

    # Price — from .finance > .price (in the description, not the title bar)
    price_el = row.select_one("div.finance span.price")
    if not price_el:
        price_el = row.select_one("span.price")
    price = _parse_price(_text(price_el))

    # Year — from .extra > span.year
    year_el = extra.select_one("span.year") if extra else None
    if not year_el:
        year_el = row.select_one("span.year")
    year = _parse_year(_text(year_el))

    # Mileage — from .extra > span.mileage
    mileage_el = extra.select_one("span.mileage") if extra else None
    if not mileage_el:
        mileage_el = row.select_one("span.mileage")
    mileage = _parse_mileage(_text(mileage_el))

    # Fuel type — from .extra > span.fuel (full text, not the abbreviated icon version)
    fuel_el = extra.select_one("span.fuel") if extra else None
    fuel_type = _text(fuel_el)

    # Transmission — from .extra > span.transmission (full text)
    trans_el = extra.select_one("span.transmission") if extra else None
    transmission = _text(trans_el)

    if not listing_id:
        return None

    return SearchResultItem(
        id=listing_id,
        url=href,
        title=title,
        price_eur=price,
        year=year,
        mileage_km=mileage,
        fuel_type=fuel_type,
        transmission=transmission,
    )


# ---------------------------------------------------------------------------
# Listing page parsing
# ---------------------------------------------------------------------------

def parse_listing(html: str, listing_id: str) -> Listing:
    """Parse a full listing page (/vehicles/{ID}) into a Listing model."""
    soup = BeautifulSoup(html, "lxml")
    url = f"{BASE_URL}/vehicles/{listing_id}"

    # Extract key-value pairs from the main data table
    details = _extract_main_data(soup)

    # Also extract technical specs for engine displacement etc.
    tech = _extract_tech_data(soup)

    # Photos from the image gallery
    photo_urls = _extract_photo_urls(soup)

    # Description — from equipment section (sellers put free text there)
    description = _extract_description(soup)

    # Seller info
    seller_name, seller_phone = _extract_seller_info(soup)

    # Seller type
    seller_type = _detect_seller_type(soup, details)

    # Location from other-info section
    location = _extract_location(soup)

    # Make and model from the page title/heading
    make, model = _extract_make_model(soup)

    # Engine text from main data (e.g., "1.6 97kW")
    engine_text = details.get("engine")

    return Listing(
        id=listing_id,
        url=url,
        make=make,
        model=model,
        year=_parse_year(details.get("initial reg")),
        price_eur=_parse_price(details.get("price")),
        mileage_km=_parse_mileage(details.get("mileage")),
        fuel_type=details.get("fuel"),
        transmission=details.get("transmission"),
        engine_cc=_parse_engine_cc(tech.get("displacement") or engine_text),
        power_kw=_parse_power_kw(tech.get("power") or engine_text),
        body_type=details.get("bodytype"),
        drivetrain=details.get("drive"),
        color=details.get("color"),
        location=location,
        seller_type=seller_type,
        seller_name=seller_name,
        seller_phone=seller_phone,
        description=description,
        photo_urls=photo_urls,
        raw_html=html,
    )


def _extract_main_data(soup: BeautifulSoup) -> dict[str, str]:
    """Extract key-value pairs from table.main-data.

    Structure: <table class="main-data"> <tr class="field-xxx">
               <td class="label"><span>Key</span></td>
               <td class="field"><span class="value">Value</span></td>
    """
    details: dict[str, str] = {}
    table = soup.select_one("table.main-data")
    if not table:
        return details

    for tr in table.select("tr"):
        label_td = tr.select_one("td.label")
        field_td = tr.select_one("td.field")
        if not label_td or not field_td:
            continue

        key = _text(label_td)
        # Get value from the .value span if present, otherwise from the td
        value_el = field_td.select_one("span.value")
        val = _text(value_el) if value_el else _text(field_td)

        if key and val:
            details[key.lower().rstrip(":")] = val

    return details


def _extract_tech_data(soup: BeautifulSoup) -> dict[str, str]:
    """Extract key-value pairs from the technical specifications section.

    Structure: div.vTechData > table.group > tr.item >
               td.label + td.value
    """
    tech: dict[str, str] = {}
    section = soup.select_one("div.vTechData")
    if not section:
        return tech

    for tr in section.select("tr.item"):
        label_td = tr.select_one("td.label")
        value_td = tr.select_one("td.value")
        if not label_td or not value_td:
            continue
        key = _text(label_td)
        val = _text(value_td)
        if key and val:
            tech[key.lower().rstrip(":")] = val

    return tech


def _extract_photo_urls(soup: BeautifulSoup) -> list[str]:
    """Extract full-size photo URLs from the listing gallery.

    Structure: div.vImages > a.vImages__item[href] > img
    The <a> href points to full-size images.
    """
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.select(".vImages a.vImages__item"):
        href = a.get("href", "")
        if href and href not in seen and not href.endswith((".svg", ".gif")):
            seen.add(href)
            urls.append(href)

    return urls


def _extract_description(soup: BeautifulSoup) -> str | None:
    """Extract free-text description from the equipment section.

    Sellers put additional info in the "Other equipment" group within
    div.vEquipment. We also check for a standalone description div.
    """
    # Look in equipment section for "Other equipment" items
    equip = soup.select_one("div.vEquipment")
    if equip:
        # Get all list items from equipment groups
        items = [_text(li) for li in equip.select("li.item")]
        # Filter to items that look like free text (longer than typical equipment names)
        descriptions = [t for t in items if t and len(t) > 30]
        if descriptions:
            return "\n".join(descriptions)

    return None


def _extract_seller_info(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extract seller name and phone from the seller section.

    Structure: address.seller > h2 (seller name)
    Phone is behind a JS trigger and not available in raw HTML.
    """
    seller = soup.select_one("address.seller")
    if not seller:
        return None, None

    # Seller name — the h2 inside address.seller
    name_el = seller.select_one("h2")
    name = _text(name_el)

    # Phone — usually hidden behind "Show phone number" JS trigger
    # We can't get it from static HTML, but check for a tel: link just in case
    phone_el = seller.select_one("a[href^='tel:']")
    phone = _text(phone_el) if phone_el else None

    return name, phone


def _detect_seller_type(soup: BeautifulSoup, details: dict[str, str]) -> str | None:
    """Determine if seller is private or dealer.

    Dealer listings typically have:
    - has-dlogo class on the result row
    - A dealer logo (div.dlogo) on the listing page
    - VAT information in the price field
    """
    # Check for dealer logo on listing page
    if soup.select_one("div.dlogo, .dealer-logo, [class*=dlogo]"):
        return "dealer"

    # Check the VAT span in the price row (separate from the value span)
    vat_el = soup.select_one("span.vat-value")
    if vat_el:
        vat_text = _text(vat_el) or ""
        vat_lower = vat_text.lower()
        if "no vat" in vat_lower or "0%" in vat_lower:
            return "private"
        if "vat" in vat_lower:
            return "dealer"

    # Fallback: check price field text itself
    price_val = details.get("price", "").lower()
    if "vat" in price_val and "no vat" not in price_val:
        return "dealer"
    if "no vat" in price_val:
        return "private"

    return None


def _extract_location(soup: BeautifulSoup) -> str | None:
    """Extract vehicle location from the other-info section."""
    info = soup.select_one("div.other-info")
    if not info:
        return None

    loc_el = info.select_one("div.-location")
    if loc_el:
        text = _text(loc_el)
        if text:
            # Strip prefix like "Location of a vehicle: "
            text = re.sub(r"^Location of a vehicle:\s*", "", text, flags=re.IGNORECASE)
            return text

    return None


def _extract_make_model(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extract make and model from the page heading or make-model span.

    The listing page has: <span class="-make">Toyota Corolla</span>
    Or the h1: "Toyota Corolla 1.6 97kW"
    """
    # Try the explicit make span
    make_el = soup.select_one("span.-make")
    if make_el:
        text = _text(make_el)
        if text:
            parts = text.split(None, 1)
            if len(parts) == 2:
                return parts[0], parts[1]
            return text, None

    # Fall back to h1 title
    h1 = soup.select_one("h1.commonSubtitle")
    if h1:
        text = _text(h1)
        if text:
            # Title format: "Toyota Corolla 1.6 97kW" — take first two words
            parts = text.split()
            if len(parts) >= 2:
                return parts[0], parts[1]
            return text, None

    return None, None
