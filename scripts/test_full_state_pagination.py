import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

def test_haryana_pagination():
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

        all_records = []
        page_num = 1

        while True:
            dg = page.query_selector("#cphBody_dgSearch")
            if not dg:
                print("No dgSearch found")
                break

            rows = dg.query_selector_all("tr")
            if len(rows) < 2:
                break

            # Headers
            header_cells = [c.inner_text().strip() for c in rows[0].query_selector_all("th, td")]
            
            # Check if last row is pager
            last_row = rows[-1]
            last_cells = last_row.query_selector_all("td")
            has_pager = False
            pager_elements = []
            
            # If the last row contains span/a with numbers or '...', it's a pager row
            pager_links = last_row.query_selector_all("a, span")
            if any(el.inner_text().strip().isdigit() or el.inner_text().strip() == '...' for el in pager_links):
                has_pager = True
                pager_elements = pager_links
                data_rows = rows[1:-1]
            else:
                data_rows = rows[1:]

            # Extract data
            page_records = []
            for r in data_rows:
                cells = [c.inner_text().strip() for c in r.query_selector_all("td")]
                if len(cells) >= 3 and cells[1]:  # ITI Code exists
                    rec = dict(zip(header_cells, cells))
                    page_records.append(rec)

            all_records.extend(page_records)
            print(f"Page {page_num}: extracted {len(page_records)} ITIs (Total so far: {len(all_records)})")

            if not has_pager:
                print("No pager row found — single page only.")
                break

            # Find active page from <span>
            active_span = next((el for el in pager_elements if el.evaluate("e => e.tagName") == "SPAN" and el.inner_text().strip().isdigit()), None)
            current_active = int(active_span.inner_text().strip()) if active_span else page_num
            target_page = current_active + 1

            # Look for target_page link
            target_link = next((el for el in pager_elements if el.inner_text().strip() == str(target_page)), None)
            
            if not target_link:
                # Look for forward '...' link
                # A forward '...' appears after current_active in the pager list
                span_idx = -1
                for idx, el in enumerate(pager_elements):
                    if el == active_span:
                        span_idx = idx
                        break
                dots_link = None
                for idx, el in enumerate(pager_elements):
                    if idx > span_idx and el.inner_text().strip() == "...":
                        dots_link = el
                        break
                if dots_link:
                    target_link = dots_link
                    print(f"Advancing pager window via '...' for page {target_page}...")

            if not target_link:
                print(f"No further pages found after page {current_active}. Done!")
                break

            # Click next link
            print(f"Clicking link for page {target_page} (text='{target_link.inner_text().strip()}')...")
            target_link.click()
            time.sleep(1.5)
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            time.sleep(1.0)
            page_num += 1

        print(f"\nHaryana collection finished! Total ITIs: {len(all_records)}")
        unique_codes = {r.get('ITI Code') for r in all_records}
        print(f"Unique ITI Codes: {len(unique_codes)}")

        browser.close()

if __name__ == "__main__":
    test_haryana_pagination()
