import time
import json
from playwright.sync_api import sync_playwright

NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
        ignore_https_errors=True
    )
    page = context.new_page()
    page.set_default_timeout(90000)
    
    print("Navigating to search page...")
    t0 = time.time()
    page.goto(NCVT_SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    print(f"Loaded in {round(time.time() - t0, 2)}s")
    
    # Select Annual
    print("Selecting Scheme: Annual (1)...")
    page.select_option("#cphBody_ddlScheme", value="1")
    time.sleep(2)
    
    # Select State: Rajasthan (value 8)
    print("Selecting State: RAJASTHAN (8)...")
    page.select_option("#cphBody_lbState", value="8")
    time.sleep(2)
    
    # Click Search with no_wait_after=True
    print("Clicking search with no_wait_after=True...")
    t1 = time.time()
    page.click("#cphBody_btnSearch", no_wait_after=True)
    
    print("Waiting for #cphBody_dgSearch...")
    page.wait_for_selector("#cphBody_dgSearch", timeout=90000)
    print(f"Grid appeared in {round(time.time() - t1, 2)}s!")
    
    # Count rows
    dg = page.query_selector("#cphBody_dgSearch")
    rows = dg.query_selector_all("tr")
    print(f"Grid has {len(rows)} rows on page 1")
    
    last_row = rows[-1]
    pager_links = last_row.query_selector_all("a, span")
    print(f"Pager links text: {[el.inner_text().strip() for el in pager_links]}")
    
    browser.close()
    print("Test successful!")
