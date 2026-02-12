# Discovery Scripts

One-off tools for discovering and verifying auto24.ee search form parameters.

- `discover_params.py` — Extracts all form field names, types, and option values from the search page using Playwright.
- `test_url_params.py` — Tests specific URL parameters (brand IDs, fuel filter, transmission filter, pagination) against the live site.
- `url_test_results.json` — Output from the last test run (Feb 2026).

Run these if auto24.ee changes their search form and you need to re-verify parameter values.
