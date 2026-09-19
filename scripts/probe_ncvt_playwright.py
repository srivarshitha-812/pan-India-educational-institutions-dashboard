"""
probe_ncvt_playwright.py — Quick Playwright test on one state (Goa)
to validate the page interaction and inspect actual table structure.
"""
import sys, os, re, time, json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"


def clean(text):
    text = re.sub(r'[\u00a0\u200b]', ' ', text or "")
    return re.sub(r'\s+', ' ', text).strip()


print("=== NCVT MIS Playwright Probe (Goa) ===")

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.6613.84 Safari/537.36"
        ),
        ignore_https_errors=True,
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page.set_default_timeout(30000)

    print("1. Loading search page...")
    page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
    time.sleep(2)

    # Print all select IDs
    selects = page.query_selector_all("select")
    print(f"   Selects found: {len(selects)}")
    for s in selects:
        print(f"   - id={s.get_attribute('id')}, name={s.get_attribute('name')}")

    # State select
    state_select = page.query_selector("#cphBody_lbState")
    if not state_select:
        print("[ERROR] State select not found")
        browser.close()
        sys.exit(1)

    opts = state_select.query_selector_all("option")
    state_list = [(o.get_attribute("value"), clean(o.inner_text())) for o in opts]
    print(f"   States: {len(state_list)}")

    # Find Goa
    goa = next(((v, l) for v, l in state_list if "GOA" in l.upper()), None)
    print(f"   Target state: {goa}")

    print("2. Selecting Goa...")
    state_select.select_option(value=goa[0])
    time.sleep(2)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    time.sleep(1)

    # Check districts
    dist_select = page.query_selector("#cphBody_lbDistrict")
    districts = []
    if dist_select:
        dist_opts = dist_select.query_selector_all("option")
        districts = [(o.get_attribute("value"), clean(o.inner_text())) for o in dist_opts]
        districts = [(v, l) for v, l in districts if v not in ("-1", "") and not l.startswith("-")]
    print(f"   Districts for Goa: {len(districts)} — {districts}")

    print("3. Clicking Search (no district filter)...")
    search_btn = page.query_selector("#cphBody_btnSearch")
    if not search_btn:
        search_btn = page.query_selector("input[type='submit']")
    if not search_btn:
        search_btn = page.query_selector("input[value='Search']")
    print(f"   Search button: {search_btn.get_attribute('id') if search_btn else 'NOT FOUND'}")

    if search_btn:
        search_btn.click()
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        time.sleep(2)

    # Capture screenshot
    screenshot_path = BASE / "data" / "raw" / "ncvt" / "probe_goa_results.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"   Screenshot saved: {screenshot_path}")

    # Inspect all elements on results page
    all_selects = page.query_selector_all("select")
    print(f"   Post-search selects: {len(all_selects)}")
    
    all_tables = page.query_selector_all("table")
    print(f"   Tables found: {len(all_tables)}")
    
    for i, t in enumerate(all_tables):
        rows = t.query_selector_all("tr")
        if len(rows) < 2:
            continue
        header_cells = rows[0].query_selector_all("th, td")
        hdr = [clean(c.inner_text()) for c in header_cells]
        row1_cells = rows[1].query_selector_all("td")
        row1 = [clean(c.inner_text()) for c in row1_cells]
        print(f"   Table[{i}] id={t.get_attribute('id')}: {len(rows)} rows")
        print(f"     Header: {hdr}")
        if row1:
            print(f"     Row 1:  {row1}")

    # Look for any GridView or result grid
    gridview_id = None
    for t in all_tables:
        tid = t.get_attribute("id") or ""
        if "grid" in tid.lower() or "gv" in tid.lower() or "result" in tid.lower():
            gridview_id = tid
            rows = t.query_selector_all("tr")
            print(f"\n   GridView found: id={tid}, rows={len(rows)}")
            for r in rows[:5]:
                cells = r.query_selector_all("th, td")
                print(f"     {[clean(c.inner_text()) for c in cells]}")

    # Look for "no records" / "no data" text
    body_text = page.inner_text("body")
    no_rec_m = re.search(r'(no\s+record|no\s+data|0\s+record|\d+ record)', body_text, re.IGNORECASE)
    if no_rec_m:
        print(f"\n   Record count message: '{no_rec_m.group(0)}'")

    # Try district-by-district for Goa
    if districts:
        for dist_val, dist_label in districts[:2]:  # Test first 2 districts
            print(f"\n4. Testing district: {dist_label}")
            page.goto(NCVT_SEARCH_URL, wait_until="networkidle")
            time.sleep(1.5)
            page.select_option("#cphBody_lbState", value=goa[0])
            time.sleep(1.5)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            
            dist_sel = page.query_selector("#cphBody_lbDistrict")
            if dist_sel:
                dist_sel.select_option(value=dist_val)
                time.sleep(1.2)
            
            sbtn = page.query_selector("#cphBody_btnSearch")
            if not sbtn:
                sbtn = page.query_selector("input[type='submit'][value='Search']")
            if sbtn:
                sbtn.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except Exception:
                    pass
                time.sleep(1.5)
            
            tables2 = page.query_selector_all("table")
            print(f"   Tables after district search: {len(tables2)}")
            for t in tables2:
                rows2 = t.query_selector_all("tr")
                if len(rows2) >= 2:
                    hdr2 = [clean(c.inner_text()) for c in rows2[0].query_selector_all("th, td")]
                    r1 = [clean(c.inner_text()) for c in rows2[1].query_selector_all("td")]
                    if any(kw in " ".join(hdr2).lower() for kw in ["name", "iti", "code", "district"]):
                        print(f"   [OK] Data table id={t.get_attribute('id')}: {len(rows2)} rows")
                        print(f"     Header: {hdr2}")
                        if r1:
                            print(f"     Row 1:  {r1}")
                        print(f"     Header: {hdr2}")
                        if r1:
                            print(f"     Row 1:  {r1}")
            
            screenshot_path2 = BASE / "data" / "raw" / "ncvt" / f"probe_goa_{dist_label.lower().replace(' ', '_')}.png"
            page.screenshot(path=str(screenshot_path2), full_page=True)
            print(f"   Screenshot: {screenshot_path2}")

    context.close()
    browser.close()
    print("\nProbe complete.")
