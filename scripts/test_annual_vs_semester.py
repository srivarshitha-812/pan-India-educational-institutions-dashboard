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
    
    # Test Delhi Annual vs Semester
    # Delhi state value: 7
    def get_codes_for_scheme(scheme_val):
        page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
        time.sleep(1)
        page.select_option("#cphBody_ddlScheme", value=scheme_val)
        time.sleep(1.5)
        page.select_option("#cphBody_lbState", value="7") # Delhi
        time.sleep(1.5)
        page.click("#cphBody_btnSearch")
        time.sleep(2)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        
        dg = page.query_selector("#cphBody_dgSearch")
        if not dg:
            return []
        rows = dg.query_selector_all("tr")
        codes = []
        for r in rows[1:]:
            cells = r.query_selector_all("td")
            if len(cells) >= 3:
                c = cells[1].inner_text().strip()
                if c and c.isalnum():
                    codes.append(c)
        return codes

    annual_codes = get_codes_for_scheme("1")
    semester_codes = get_codes_for_scheme("0")
    
    print(f"Delhi Annual ITIs: {len(annual_codes)}")
    print(f"Delhi Semester ITIs: {len(semester_codes)}")
    
    set_a = set(annual_codes)
    set_s = set(semester_codes)
    
    only_annual = set_a - set_s
    only_semester = set_s - set_a
    overlap = set_a & set_s
    
    print(f"Overlap: {len(overlap)}")
    print(f"Only in Annual: {len(only_annual)}")
    print(f"Only in Semester: {len(only_semester)}")
    if only_semester:
        print(f"Sample only in Semester: {list(only_semester)[:5]}")
    if only_annual:
        print(f"Sample only in Annual: {list(only_annual)[:5]}")

    browser.close()
