import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
        ignore_https_errors=True
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(1)

    print("--- cphBody_ddlScheme options ---")
    opts = page.query_selector_all("#cphBody_ddlScheme option")
    for o in opts:
        print(f"Value: '{o.get_attribute('value')}', Text: '{o.inner_text().strip()}'")

    # Select Annual (assuming value is '1' or 'Annual' or whatever it is)
    # Let's see all values and try selecting each one
    annual_opt = next((o for o in opts if "ANNUAL" in o.inner_text().upper()), None)
    if annual_opt:
        val = annual_opt.get_attribute("value")
        print(f"\nSelecting Annual (value={val})...")
        page.select_option("#cphBody_ddlScheme", value=val)
        time.sleep(1.5)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        # Select Goa (state 30)
        print("Selecting Goa (state 30)...")
        page.select_option("#cphBody_lbState", value="30")
        time.sleep(1.5)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        # Select North Goa (district 585)
        print("Selecting North Goa (585)...")
        page.select_option("#cphBody_lbDistrict", value="585")
        time.sleep(1.0)

        # Click Search
        print("Clicking Search...")
        page.click("#cphBody_btnSearch")
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.screenshot(path=str(BASE / "data" / "raw" / "ncvt" / "test_annual_search.png"), full_page=True)
        print("Screenshot saved to test_annual_search.png")

        # Check tables
        tables = page.query_selector_all("table")
        print(f"Tables found: {len(tables)}")
        for i, t in enumerate(tables):
            rows = t.query_selector_all("tr")
            if len(rows) >= 2:
                hdr = [c.inner_text().strip() for c in rows[0].query_selector_all("th, td")]
                if any(kw in " ".join(hdr).lower() for kw in ["iti", "code", "name", "trade", "address"]):
                    print(f"Table[{i}] id={t.get_attribute('id')}: {len(rows)} rows")
                    print(f"  Header: {hdr[:10]}")
                    if len(rows) > 1:
                        r1 = [c.inner_text().strip() for c in rows[1].query_selector_all("td")]
                        print(f"  Row 1:  {r1[:10]}")

    browser.close()
