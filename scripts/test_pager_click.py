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
    page.select_option("#cphBody_ddlScheme", value="1")
    time.sleep(1.5)
    page.select_option("#cphBody_lbState", value="6")  # Haryana
    time.sleep(1.5)
    page.click("#cphBody_btnSearch")
    time.sleep(2)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    
    # Inspect pager in #cphBody_dgSearch
    dg = page.query_selector("#cphBody_dgSearch")
    rows = dg.query_selector_all("tr")
    print(f"Initial page rows: {len(rows)}")
    
    pager_row = rows[-1]
    pager_links = pager_row.query_selector_all("a, span")
    print(f"Pager elements: {len(pager_links)}")
    for el in pager_links:
        tag = el.evaluate("e => e.tagName")
        text = el.inner_text().strip()
        href = el.get_attribute("href") or ""
        print(f"  <{tag}> text='{text}' href='{href[:60]}'")
    
    # Click page "2"
    page2_link = next((el for el in pager_links if el.inner_text().strip() == "2"), None)
    if page2_link:
        print("\nClicking page 2...")
        page2_link.click()
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        
        dg2 = page.query_selector("#cphBody_dgSearch")
        rows2 = dg2.query_selector_all("tr")
        print(f"Page 2 rows: {len(rows2)}")
        r1 = [c.inner_text().strip() for c in rows2[1].query_selector_all("td")]
        print(f"Page 2 Row 1: {r1[:5]}")
        
        # Check pager on page 2
        pager_row2 = rows2[-1]
        pager_links2 = pager_row2.query_selector_all("a, span")
        print("Pager on Page 2:")
        for el in pager_links2:
            tag = el.evaluate("e => e.tagName")
            text = el.inner_text().strip()
            print(f"  <{tag}> '{text}'")

    browser.close()
