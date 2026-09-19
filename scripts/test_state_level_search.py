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
    
    print("--- Test 1: Goa at State Level (no district selected) ---")
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(1)
    page.select_option("#cphBody_ddlScheme", value="1")  # Annual
    time.sleep(1.5)
    page.select_option("#cphBody_lbState", value="30")   # Goa
    time.sleep(1.5)
    page.click("#cphBody_btnSearch")
    time.sleep(2)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    
    dg = page.query_selector("#cphBody_dgSearch")
    if dg:
        rows = dg.query_selector_all("tr")
        print(f"State-level Goa search SUCCESS! Found #cphBody_dgSearch with {len(rows)} rows (including header)")
        # Check last row for pagination
        last_row = rows[-1]
        links = last_row.query_selector_all("a")
        print(f"Links in last row: {[l.inner_text().strip() for l in links]}")
    else:
        print("No dgSearch found for state-level Goa")
        body_text = page.inner_text("body")
        print("Body excerpt:", body_text[:300])

    print("\n--- Test 2: Goa with Semester (value=0) ---")
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(1)
    page.select_option("#cphBody_ddlScheme", value="0")  # Semester
    time.sleep(1.5)
    page.select_option("#cphBody_lbState", value="30")   # Goa
    time.sleep(1.5)
    page.click("#cphBody_btnSearch")
    time.sleep(2)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    
    dg2 = page.query_selector("#cphBody_dgSearch")
    if dg2:
        rows2 = dg2.query_selector_all("tr")
        print(f"Semester Goa search SUCCESS! Found {len(rows2)} rows")
    else:
        print("No dgSearch found for Semester Goa")

    print("\n--- Test 3: Delhi at State Level (to check pagination) ---")
    # Delhi state value: let's find it
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(1)
    page.select_option("#cphBody_ddlScheme", value="1")
    time.sleep(1.5)
    
    # Find Delhi value from state options
    opts = page.query_selector_all("#cphBody_lbState option")
    delhi_val = None
    for o in opts:
        if "DELHI" in o.inner_text().strip().upper():
            delhi_val = o.get_attribute("value")
            break
    
    print(f"Delhi state value: {delhi_val}")
    if delhi_val:
        page.select_option("#cphBody_lbState", value=delhi_val)
        time.sleep(1.5)
        page.click("#cphBody_btnSearch")
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        
        dg3 = page.query_selector("#cphBody_dgSearch")
        if dg3:
            rows3 = dg3.query_selector_all("tr")
            print(f"Delhi search SUCCESS! Rows: {len(rows3)}")
            last_row = rows3[-1]
            links = last_row.query_selector_all("a")
            print(f"Pager links in last row: {[l.inner_text().strip() for l in links]}")
            # print first 3 data rows
            for r in rows3[:4]:
                cells = [c.inner_text().strip() for c in r.query_selector_all("th, td")]
                print("  Row:", cells)
        else:
            print("No dgSearch found for Delhi")

    browser.close()
