"""Tests for autoscout.parser against HTML fixtures."""

import pytest

from autoscout.parser import (
    _extract_listing_id,
    _parse_engine_cc,
    _parse_mileage,
    _parse_power_kw,
    _parse_price,
    _parse_year,
    parse_listing,
    parse_search_results,
)


# --- Unit tests for parsing helpers (always run, no fixtures needed) ---


class TestParsePrice:
    def test_euro_sign_suffix(self):
        assert _parse_price("5 900 €") == 5900

    def test_euro_sign_prefix(self):
        assert _parse_price("€5,900") == 5900

    def test_euro_entity(self):
        """auto24 uses €7700 which becomes €7700 after BS4 parsing."""
        assert _parse_price("€7700") == 7700

    def test_eur_prefix(self):
        """Listing pages use 'EUR 4000' format."""
        assert _parse_price("EUR 4000") == 4000

    def test_eur_with_nbsp(self):
        assert _parse_price("EUR\xa04000") == 4000

    def test_plain_number(self):
        assert _parse_price("12000") == 12000

    def test_with_spaces(self):
        assert _parse_price("15 000") == 15000

    def test_with_comma(self):
        assert _parse_price("€11,299") == 11299

    def test_none(self):
        assert _parse_price(None) is None

    def test_empty(self):
        assert _parse_price("") is None

    def test_no_digits(self):
        assert _parse_price("Price on request") is None


class TestParseMileage:
    def test_with_spaces_and_km(self):
        assert _parse_mileage("212 000 km") == 212000

    def test_with_nbsp(self):
        """auto24 uses non-breaking spaces: '343\xa0300\xa0km'."""
        assert _parse_mileage("343\xa0300\xa0km") == 343300

    def test_plain_number(self):
        assert _parse_mileage("150000") == 150000

    def test_none(self):
        assert _parse_mileage(None) is None

    def test_empty(self):
        assert _parse_mileage("") is None


class TestParseYear:
    def test_plain_year(self):
        assert _parse_year("2015") == 2015

    def test_with_month_slash(self):
        """auto24 listing pages use '06/2012' format."""
        assert _parse_year("06/2012") == 2012

    def test_in_text(self):
        assert _parse_year("First reg. 2012") == 2012

    def test_none(self):
        assert _parse_year(None) is None

    def test_no_year(self):
        assert _parse_year("no info") is None


class TestParseEngineCc:
    def test_cm3_format(self):
        """auto24 tech specs: '1598 cm³'."""
        assert _parse_engine_cc("1598 cm³") == 1598

    def test_liter_format(self):
        """auto24 tech specs: '1.6 l'."""
        assert _parse_engine_cc("1.6 l") == 1600

    def test_liter_with_L(self):
        assert _parse_engine_cc("2.0L") == 2000

    def test_engine_field_format(self):
        """Main data engine field: '1.6 97kW' — extract displacement."""
        assert _parse_engine_cc("1.6 97kW") == 1600

    def test_none(self):
        assert _parse_engine_cc(None) is None


class TestParsePowerKw:
    def test_kw_format(self):
        assert _parse_power_kw("97 kW") == 97

    def test_kw_no_space(self):
        assert _parse_power_kw("97kW") == 97

    def test_from_engine_field(self):
        """Main data engine field: '1.6 97kW'."""
        assert _parse_power_kw("1.6 97kW") == 97

    def test_none(self):
        assert _parse_power_kw(None) is None


class TestExtractListingId:
    def test_vehicles_url(self):
        assert _extract_listing_id("/vehicles/4275993") == "4275993"

    def test_full_url(self):
        assert _extract_listing_id("https://eng.auto24.ee/vehicles/4275993") == "4275993"

    def test_with_fragment(self):
        assert _extract_listing_id("/vehicles/4275993#loan=60") == "4275993"


# --- Integration tests against real HTML fixtures ---


class TestParseSearchResults:
    def test_returns_nonempty_list(self, search_results_html):
        results = parse_search_results(search_results_html)
        assert len(results) > 0, "Expected at least one search result"

    def test_items_have_id_and_url(self, search_results_html):
        results = parse_search_results(search_results_html)
        for item in results:
            assert item.id, f"Missing ID in result: {item}"
            assert item.url, f"Missing URL in result: {item}"
            assert "auto24" in item.url

    def test_ids_are_numeric(self, search_results_html):
        results = parse_search_results(search_results_html)
        for item in results:
            assert item.id.isdigit(), f"ID should be numeric: {item.id}"

    def test_items_have_title(self, search_results_html):
        results = parse_search_results(search_results_html)
        titled = [r for r in results if r.title]
        assert len(titled) == len(results), "All results should have titles"

    def test_titles_contain_make(self, search_results_html):
        results = parse_search_results(search_results_html)
        for item in results:
            assert "Toyota" in item.title or "Corolla" in item.title, (
                f"Expected Toyota/Corolla in title: {item.title}"
            )

    def test_items_have_price(self, search_results_html):
        results = parse_search_results(search_results_html)
        priced = [r for r in results if r.price_eur is not None]
        assert len(priced) > 0, "Expected at least some results with prices"

    def test_prices_are_reasonable(self, search_results_html):
        results = parse_search_results(search_results_html)
        for item in results:
            if item.price_eur is not None:
                assert 100 < item.price_eur < 200_000, (
                    f"Price {item.price_eur} seems unreasonable for {item.title}"
                )

    def test_items_have_year(self, search_results_html):
        results = parse_search_results(search_results_html)
        with_year = [r for r in results if r.year is not None]
        assert len(with_year) > 0, "Expected at least some results with year"
        for item in with_year:
            assert 1990 < item.year < 2030, f"Year {item.year} out of range"

    def test_items_have_mileage(self, search_results_html):
        results = parse_search_results(search_results_html)
        with_mileage = [r for r in results if r.mileage_km is not None]
        assert len(with_mileage) > 0, "Expected at least some results with mileage"

    def test_items_have_fuel_type(self, search_results_html):
        results = parse_search_results(search_results_html)
        with_fuel = [r for r in results if r.fuel_type is not None]
        assert len(with_fuel) > 0, "Expected at least some results with fuel type"

    def test_items_have_transmission(self, search_results_html):
        results = parse_search_results(search_results_html)
        with_trans = [r for r in results if r.transmission is not None]
        assert len(with_trans) > 0, "Expected at least some results with transmission"


class TestParseListing:
    def test_returns_listing(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.id == "4244561"

    def test_has_make_and_model(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.make == "Toyota"
        assert listing.model == "Corolla"

    def test_has_year(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.year == 2012

    def test_has_price(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.price_eur == 4000

    def test_has_mileage(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.mileage_km == 178000

    def test_has_fuel_type(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.fuel_type == "petrol"

    def test_has_transmission(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.transmission == "manual"

    def test_has_body_type(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.body_type == "sedan"

    def test_has_drivetrain(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.drivetrain is not None
        assert "front" in listing.drivetrain.lower()

    def test_has_color(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.color == "silver"

    def test_has_engine_cc(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.engine_cc == 1598

    def test_has_power_kw(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.power_kw == 97

    def test_has_photos(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert len(listing.photo_urls) >= 3

    def test_photo_urls_are_valid(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        for url in listing.photo_urls:
            assert url.startswith("http"), f"Photo URL should be absolute: {url}"

    def test_has_location(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.location is not None
        assert "Estonia" in listing.location

    def test_has_seller_name(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.seller_name is not None

    def test_seller_type_detected(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        # This listing has "no VAT accrue" -> private
        assert listing.seller_type == "private"

    def test_has_raw_html(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.raw_html == listing_html
        assert len(listing.raw_html) > 1000

    def test_url_format(self, listing_html):
        listing = parse_listing(listing_html, "4244561")
        assert listing.url == "https://eng.auto24.ee/vehicles/4244561"
