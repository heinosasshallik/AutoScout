#!/usr/bin/env python3
"""Discover all search form parameters on auto24.ee.

Uses Playwright with stealth mode to bypass Cloudflare, then extracts
all form field names, types, and option values from the search form.
"""

import asyncio
import json
import logging

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

URLS = [
    "https://eng.auto24.ee/kasutatud/nimekiri.php",
    "https://www.auto24.ee/kasutatud/nimekiri.php",
]


async def extract_form_fields(page) -> dict:
    """Extract all form fields from the page using JavaScript."""
    return await page.evaluate("""() => {
        const results = {forms: [], allInputs: [], allSelects: [], allCheckboxes: [], allRadios: [], allHiddens: []};

        // Get all forms
        const forms = document.querySelectorAll('form');
        forms.forEach((form, fi) => {
            const formInfo = {
                index: fi,
                action: form.action,
                method: form.method,
                id: form.id,
                name: form.name,
                className: form.className,
                fields: []
            };

            // All inputs
            form.querySelectorAll('input, select, textarea').forEach(el => {
                const field = {
                    tag: el.tagName.toLowerCase(),
                    name: el.name,
                    id: el.id,
                    type: el.type || '',
                    value: el.value || '',
                    className: el.className,
                    placeholder: el.placeholder || '',
                };

                if (el.tagName === 'SELECT') {
                    field.options = [];
                    el.querySelectorAll('option').forEach(opt => {
                        field.options.push({
                            value: opt.value,
                            text: opt.textContent.trim(),
                            selected: opt.selected
                        });
                    });
                }

                // For labels
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) field.label = label.textContent.trim();
                }

                // Look for parent label or nearby text
                const parentLabel = el.closest('label');
                if (parentLabel) {
                    field.parentLabel = parentLabel.textContent.trim().substring(0, 100);
                }

                // Get previous sibling text
                const prev = el.previousElementSibling;
                if (prev && (prev.tagName === 'LABEL' || prev.tagName === 'SPAN' || prev.tagName === 'DIV')) {
                    field.prevText = prev.textContent.trim().substring(0, 100);
                }

                formInfo.fields.push(field);
            });

            results.forms.push(formInfo);
        });

        // Also get all inputs/selects outside forms
        document.querySelectorAll('input:not(form input), select:not(form select)').forEach(el => {
            const field = {
                tag: el.tagName.toLowerCase(),
                name: el.name,
                id: el.id,
                type: el.type || '',
                value: el.value || '',
                className: el.className,
            };
            if (el.tagName === 'SELECT') {
                field.options = [];
                el.querySelectorAll('option').forEach(opt => {
                    field.options.push({value: opt.value, text: opt.textContent.trim()});
                });
            }
            results.allInputs.push(field);
        });

        return results;
    }""")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = await context.new_page()

        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        for url in URLS:
            logger.info(f"\n{'='*80}")
            logger.info(f"Fetching: {url}")
            logger.info(f"{'='*80}")

            try:
                resp = await page.goto(url, wait_until="commit", timeout=30_000)
                logger.info(f"Status: {resp.status if resp else 'None'}")

                # Wait for Cloudflare if needed
                title = await page.title()
                if "just a moment" in title.lower():
                    logger.info("Cloudflare challenge detected, waiting...")
                    for _ in range(15):
                        await asyncio.sleep(2)
                        title = await page.title()
                        if "just a moment" not in title.lower():
                            logger.info(f"Resolved! Title: {title}")
                            break

                await asyncio.sleep(3)
                title = await page.title()
                logger.info(f"Page title: {title}")

                # Extract form fields
                data = await extract_form_fields(page)

                # Pretty print
                print(f"\n\n=== FORM FIELDS FROM {url} ===\n")
                for form in data["forms"]:
                    print(f"\nFORM #{form['index']}: action={form['action']}, method={form['method']}, id={form['id']}, class={form['className']}")
                    print(f"  Fields ({len(form['fields'])}):")
                    for f in form["fields"]:
                        desc = f"    {f['tag']} name='{f['name']}' type='{f.get('type','')}' id='{f['id']}' class='{f['className']}'"
                        if f.get('label'):
                            desc += f" label='{f['label']}'"
                        if f.get('prevText'):
                            desc += f" prev='{f['prevText']}'"
                        if f.get('parentLabel'):
                            desc += f" parentLabel='{f['parentLabel']}'"
                        if f.get('placeholder'):
                            desc += f" placeholder='{f['placeholder']}'"
                        print(desc)

                        if 'options' in f and f['options']:
                            for opt in f['options']:
                                sel = " [SELECTED]" if opt.get('selected') else ""
                                print(f"      option: value='{opt['value']}' text='{opt['text']}'{sel}")

                if data.get("allInputs"):
                    print(f"\n  Inputs outside forms ({len(data['allInputs'])}):")
                    for f in data["allInputs"]:
                        print(f"    {f['tag']} name='{f['name']}' type='{f.get('type','')}' id='{f['id']}'")
                        if 'options' in f and f['options']:
                            for opt in f['options']:
                                print(f"      option: value='{opt['value']}' text='{opt['text']}'")

                # Also dump the raw JSON for later analysis
                print(f"\n\n=== RAW JSON for {url} ===")
                print(json.dumps(data, indent=2, ensure_ascii=False))

            except Exception as e:
                logger.error(f"Failed for {url}: {e}")

            await asyncio.sleep(5)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
