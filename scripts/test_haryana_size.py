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
    
    # Test Haryana
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(1)
    page.select_option("#cphBody_ddlScheme", value="1")
    time.sleep(1.5)
    
    opts = page.query_selector_all("#cphBody_lbState option")
    haryana_val = None
    for o in opts:
        if "HARYANA" in o.inner_text().strip().upper():
            haryana_val = o.get_attribute("value")
            break
    
    print(f"Haryana state value: {haryana_val}")
    page.select_option("#cphBody_lbState", value=haryana_val)
    time.sleep(1.5)
    page.click("#cphBody_btnSearch")
    time.sleep(2)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    
    dg = page.query_selector("#cphBody_dgSearch")
    if dg:
        rows = dg.query_selector_all("tr")
        print(f"Haryana search SUCCESS! Rows: {len(rows)}")
        # Check if there is a pager row
        for r_idx in [0, 1, -2, -1]:
            if abs(r_idx) < len(rows):
                r = rows[r_idx]
                cells = [c.inner_text().strip() for c in r.query_selector_all("th, td")]
                print(f"  Row[{r_idx}]: {cells[:8]}")
    else:
        print("No dgSearch for Haryana")

    browser.close()
