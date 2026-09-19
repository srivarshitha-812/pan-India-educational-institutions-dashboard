"""
collect_ncvt_playwright.py — Complete National NCVET/DGT ITI & Vocational Institutions Collection
Traverses all 38 States & UTs via the official NCVT MIS portal (https://ncvtmis.gov.in/Pages/ITI/Search.aspx).
Uses verified Playwright headless automation with ASP.NET ViewState handling and multi-page DataGrid pagination.
"""

import os
import sys
import re
import json
import time
import traceback
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

SOURCE = "ncvt"
NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"
EXTRACTION_DATE = str(date.today())
CHECKPOINT_DIR = BASE / "data" / "checkpoints"
RAW_DIR = BASE / "data" / "raw" / "ncvt"

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def clean_cell(text: str) -> str:
    """Clean whitespace and non-breaking spaces from table cell."""
    text = re.sub(r'[\u00a0\u200b\t\r\n]', ' ', text or "")
    return re.sub(r'\s+', ' ', text).strip()


def load_checkpoint() -> dict:
    ckpt_file = CHECKPOINT_DIR / f"{SOURCE}_national_checkpoint.json"
    if ckpt_file.exists():
        try:
            with open(ckpt_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "source": SOURCE,
        "extraction_date": EXTRACTION_DATE,
        "done_states": [],
        "all_records_by_state": {},
        "audit_log": [],
        "total_records_collected": 0,
    }


def save_checkpoint(ckpt: dict):
    ckpt_file = CHECKPOINT_DIR / f"{SOURCE}_national_checkpoint.json"
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)


def save_raw_state(state_label: str, records: list):
    slug = re.sub(r'[^a-z0-9]+', '_', state_label.lower()).strip('_')
    raw_file = RAW_DIR / f"{slug}_itis.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def collect_national(headless: bool = True):
    from playwright.sync_api import sync_playwright

    ckpt = load_checkpoint()
    done_states = set(ckpt.get("done_states", []))
    all_records_by_state = ckpt.get("all_records_by_state", {})
    audit_log = ckpt.get("audit_log", [])

    print(f"=== NCVET / DGT ITI National Collection ===")
    print(f"Extraction Date: {EXTRACTION_DATE}")
    print(f"Previously completed states: {len(done_states)}")
    total_prev = sum(len(recs) for recs in all_records_by_state.values())
    print(f"Previously collected records: {total_prev}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            slow_mo=50
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.set_default_timeout(35000)

        # 1. Fetch initial page and state options
        print("\nLoading NCVT MIS ITI Search portal...")
        page.goto(NCVT_SEARCH_URL, wait_until="networkidle", timeout=40000)
        time.sleep(2)

        state_select = page.query_selector("#cphBody_lbState")
        if not state_select:
            print("[FATAL] Could not find state dropdown (#cphBody_lbState)")
            browser.close()
            return

        opts = state_select.query_selector_all("option")
        state_list = []
        for o in opts:
            val = o.get_attribute("value") or ""
            lbl = clean_cell(o.inner_text())
            if val not in ("-1", "") and not lbl.startswith("-"):
                state_list.append((val, lbl))

        print(f"Found {len(state_list)} States/UTs in official directory.")

        # 2. Iterate each state
        for state_idx, (state_val, state_label) in enumerate(state_list, 1):
            if state_label in done_states:
                rec_count = len(all_records_by_state.get(state_label, []))
                print(f"[{state_idx}/{len(state_list)}] [SKIP] {state_label} (already collected {rec_count} ITIs)")
                continue

            print(f"\n[{state_idx}/{len(state_list)}] >>> Processing: {state_label} (Code: {state_val})")
            state_start_time = time.time()
            state_records = []
            page_count = 0
            status = "SUCCESS"
            error_msg = ""

            try:
                # Fresh page navigation for clean ViewState
                page.goto(NCVT_SEARCH_URL, wait_until="networkidle", timeout=35000)
                time.sleep(1.0)

                # Select Exam System = Annual ('1')
                page.select_option("#cphBody_ddlScheme", value="1")
                time.sleep(1.2)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass

                # Select State
                page.select_option("#cphBody_lbState", value=state_val)
                time.sleep(1.5)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass

                # Click Search
                search_btn = page.query_selector("#cphBody_btnSearch")
                if not search_btn:
                    search_btn = page.query_selector("input[type='submit'][value='Search']")
                if not search_btn:
                    raise RuntimeError("Search button not found on page")

                search_btn.click()
                time.sleep(2.0)
                try:
                    page.wait_for_load_state("networkidle", timeout=25000)
                except Exception:
                    pass

                # Check if results grid appeared
                dg = page.query_selector("#cphBody_dgSearch")
                if not dg:
                    # Check for "No records found" or 0 records
                    body_text = page.inner_text("body")
                    if re.search(r'(no\s+record|0\s+record)', body_text, re.IGNORECASE):
                        print(f"    No records found for {state_label} (0 ITIs).")
                    else:
                        print(f"    [WARN] No dgSearch grid found for {state_label}.")
                        status = "NO_GRID"
                else:
                    # Paginate through all pages for this state
                    current_page_num = 1
                    while True:
                        page_count += 1
                        dg = page.query_selector("#cphBody_dgSearch")
                        if not dg:
                            break

                        rows = dg.query_selector_all("tr")
                        if len(rows) < 2:
                            break

                        header_cells = [clean_cell(c.inner_text()) for c in rows[0].query_selector_all("th, td")]

                        # Check if last row is pager row
                        last_row = rows[-1]
                        pager_links = last_row.query_selector_all("a, span")
                        is_pager_row = any(el.inner_text().strip().isdigit() for el in pager_links)

                        if is_pager_row:
                            data_rows = rows[1:-1]
                        else:
                            data_rows = rows[1:]

                        # Extract ITI records
                        page_recs = []
                        for r in data_rows:
                            cells = [clean_cell(c.inner_text()) for c in r.query_selector_all("td")]
                            # Valid ITI row has at least 3 cells and valid code (starts with 2 letters or length >= 6)
                            if len(cells) >= 3 and cells[1] and not cells[1].isdigit() and len(cells[1]) >= 4:
                                rec = {
                                    "id": cells[0] if len(cells) > 0 else "",
                                    "iti_code": cells[1] if len(cells) > 1 else "",
                                    "name": cells[2] if len(cells) > 2 else "",
                                    "management_type": cells[3] if len(cells) > 3 else "",
                                    "location": cells[4] if len(cells) > 4 else "",
                                    "address": cells[5] if len(cells) > 5 else "",
                                    "district": cells[6] if len(cells) > 6 else "",
                                    "state": cells[7] if len(cells) > 7 else state_label,
                                    "trades": cells[8] if len(cells) > 8 else "",
                                    "seats": cells[9] if len(cells) > 9 else "",
                                    "trainees": cells[10] if len(cells) > 10 else "",
                                    "scheme": cells[11] if len(cells) > 11 else "",
                                    "file_ref_no": cells[12] if len(cells) > 12 else "",
                                    "final_grading": cells[13] if len(cells) > 13 else "",
                                    "instructor_count": cells[14] if len(cells) > 14 else "",
                                    "source_url": NCVT_SEARCH_URL,
                                    "extraction_date": EXTRACTION_DATE,
                                }
                                page_recs.append(rec)

                        state_records.extend(page_recs)
                        print(f"    Page {current_page_num}: {len(page_recs)} ITIs (Subtotal: {len(state_records)})")

                        if not is_pager_row:
                            break

                        # Find active page number
                        active_span = next(
                            (el for el in pager_links if el.evaluate("e => e.tagName") == "SPAN" and el.inner_text().strip().isdigit()),
                            None
                        )
                        active_page = int(active_span.inner_text().strip()) if active_span else current_page_num
                        target_page = active_page + 1

                        # Look for target page link
                        target_link = next((el for el in pager_links if el.inner_text().strip() == str(target_page)), None)

                        if not target_link:
                            # Check for forward '...' or '>>'
                            span_idx = -1
                            for idx, el in enumerate(pager_links):
                                if el == active_span:
                                    span_idx = idx
                                    break
                            forward_dots = [
                                el for idx, el in enumerate(pager_links)
                                if idx > span_idx and el.inner_text().strip() in ("...", ">>")
                            ]
                            if forward_dots:
                                target_link = forward_dots[0]
                                print(f"    [PAGER] Advancing page window via '{target_link.inner_text().strip()}' for page {target_page}...")

                        if not target_link:
                            print(f"    [PAGER] End of pages reached at page {active_page}.")
                            break

                        # Click next page
                        target_link.click()
                        time.sleep(1.8)
                        try:
                            page.wait_for_load_state("networkidle", timeout=25000)
                        except Exception:
                            pass
                        time.sleep(0.5)
                        current_page_num += 1

            except Exception as e:
                status = "FAILED"
                error_msg = str(e)
                print(f"    [ERROR] Failed to collect {state_label}: {e}")
                traceback.print_exc()

            elapsed = round(time.time() - state_start_time, 1)
            print(f"    Result for {state_label}: {len(state_records)} ITIs in {elapsed}s across {page_count} pages ({status})")

            # Save state raw data
            save_raw_state(state_label, state_records)

            all_records_by_state[state_label] = state_records
            if status == "SUCCESS" or len(state_records) > 0:
                done_states.add(state_label)

            audit_log.append({
                "state": state_label,
                "state_code": state_val,
                "pages_fetched": page_count,
                "records_collected": len(state_records),
                "elapsed_seconds": elapsed,
                "status": status,
                "error": error_msg,
                "timestamp": str(date.today()),
            })

            # Checkpoint save after every single state
            ckpt["done_states"] = list(done_states)
            ckpt["all_records_by_state"] = all_records_by_state
            ckpt["audit_log"] = audit_log
            ckpt["total_records_collected"] = sum(len(r) for r in all_records_by_state.values())
            save_checkpoint(ckpt)

        browser.close()

    total_collected = sum(len(r) for r in all_records_by_state.values())
    print(f"\n=======================================================")
    print(f"[NCVT] Collection finished for {len(done_states)} states!")
    print(f"[NCVT] Total ITI records collected: {total_collected}")
    print(f"=======================================================")


if __name__ == "__main__":
    collect_national(headless=True)
