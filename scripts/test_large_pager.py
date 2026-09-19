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
    
    # Find Rajasthan
    opts = page.query_selector_all("#cphBody_lbState option")
    raj_val = None
    for o in opts:
        if "RAJASTHAN" in o.inner_text().strip().upper():
            raj_val = o.get_attribute("value")
            break
    
    print(f"Rajasthan state value: {raj_val}")
    page.select_option("#cphBody_lbState", value=raj_val)
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
        print(f"Initial rows: {len(rows)}")
        last_row = rows[-1]
        pager_elements = last_row.query_selector_all("a, span")
        print("Pager on Page 1:", [el.inner_text().strip() for el in pager_elements])

        # Click page 10
        p10 = next((el for el in pager_elements if el.inner_text().strip() == "10"), None)
        if p10:
            print("\nClicking Page 10...")
            p10.click()
            time.sleep(2)
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            
            dg10 = page.query_selector("#cphBody_dgSearch")
            rows10 = dg10.query_selector_all("tr")
            pager10 = rows10[-1].query_selector_all("a, span")
            print("Pager on Page 10:", [el.inner_text().strip() for el in pager10])

            # Now look for '...' after page 10
            # Let's find forward '...'
            dots = [el for el in pager10 if el.inner_text().strip() == "..."]
            print(f"Found {len(dots)} '...' elements on Page 10")
            # The second '...' or the one after active span
            if dots:
                forward_dot = dots[-1]
                print("Clicking forward '...' to advance to Page 11-20...")
                forward_dot.click()
                time.sleep(2)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass
                
                dg11 = page.query_selector("#cphBody_dgSearch")
                rows11 = dg11.query_selector_all("tr")
                pager11 = rows11[-1].query_selector_all("a, span")
                print("Pager after clicking forward '...':", [el.inner_text().strip() for el in pager11])
    else:
        print("No dgSearch found")

    browser.close()
