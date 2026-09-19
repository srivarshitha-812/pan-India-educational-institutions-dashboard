"""
recovery_ncvt.py — Re-collect states that had ElementHandle.click stale DOM errors.
Uses page.locator() text selectors instead of stored ElementHandle references,
which go stale when ASP.NET UpdatePanel re-renders the pager grid.
"""
import sys
import re
import json
import time
import traceback
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"
EXTRACTION_DATE = str(date.today())
CHECKPOINT_DIR = BASE / "data" / "checkpoints"
RAW_DIR = BASE / "data" / "raw" / "ncvt"

# States to re-collect (remove from checkpoint done_states first)
FAILED_STATES = {"ODISHA", "PUNJAB", "RAJASTHAN", "TAMIL NADU", "TELANGANA", "UTTAR PRADESH", "WEST BENGAL"}


def clean_cell(text: str) -> str:
    text = re.sub(r'[\u00a0\u200b\t\r\n]', ' ', text or "")
    return re.sub(r'\s+', ' ', text).strip()


def load_checkpoint() -> dict:
    ckpt_file = CHECKPOINT_DIR / "ncvt_national_checkpoint.json"
    with open(ckpt_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(ckpt: dict):
    ckpt_file = CHECKPOINT_DIR / "ncvt_national_checkpoint.json"
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)


def save_raw_state(state_label: str, records: list):
    slug = re.sub(r'[^a-z0-9]+', '_', state_label.lower()).strip('_')
    raw_file = RAW_DIR / f"{slug}_itis.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def collect_state(page, state_val: str, state_label: str) -> tuple[list, int, str, str]:
    """Collect all ITIs for one state using locator-based pager clicks."""
    state_records = []
    page_count = 0
    status = "SUCCESS"
    error_msg = ""

    try:
        page.goto(NCVT_SEARCH_URL, wait_until="networkidle", timeout=35000)
        time.sleep(1.2)

        page.select_option("#cphBody_ddlScheme", value="1")  # Annual
        time.sleep(1.5)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        page.select_option("#cphBody_lbState", value=state_val)
        time.sleep(1.8)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        page.click("#cphBody_btnSearch")
        time.sleep(2.5)
        try:
            page.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass

        # Check grid
        dg = page.query_selector("#cphBody_dgSearch")
        if not dg:
            body_text = page.inner_text("body")
            if re.search(r'(no\s+record|0\s+record)', body_text, re.IGNORECASE):
                print(f"    No records for {state_label}")
            else:
                print(f"    [WARN] No grid found for {state_label}")
                status = "NO_GRID"
            return state_records, page_count, status, error_msg

        current_page_num = 1
        max_pages = 100  # Safety cap

        while current_page_num <= max_pages:
            page_count += 1

            # Re-query the grid fresh from page each iteration
            dg = page.query_selector("#cphBody_dgSearch")
            if not dg:
                print(f"    Grid lost at page {current_page_num}")
                break

            rows = dg.query_selector_all("tr")
            if len(rows) < 2:
                break

            header_cells = [clean_cell(c.inner_text()) for c in rows[0].query_selector_all("th, td")]

            # Detect pager row: last row contains numeric link/spans
            last_row = rows[-1]
            pager_els = last_row.query_selector_all("a, span")
            is_pager_row = any(el.inner_text().strip().isdigit() for el in pager_els)

            data_rows = rows[1:-1] if is_pager_row else rows[1:]

            # Extract records
            page_recs = []
            for r in data_rows:
                cells = [clean_cell(c.inner_text()) for c in r.query_selector_all("td")]
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
                print(f"    [PAGER] No pager row — end of data.")
                break

            # Determine active page using fresh DOM query
            # Active page is shown as <span> (not <a>)
            pager_inner = last_row.inner_text()
            
            # Get active page from fresh DOM span
            active_page = current_page_num
            pager_spans = last_row.query_selector_all("span")
            for sp in pager_spans:
                txt = sp.inner_text().strip()
                if txt.isdigit():
                    active_page = int(txt)
                    break

            target_page = active_page + 1
            target_str = str(target_page)

            # KEY FIX: Use page.locator() with text selector — re-queries live DOM each time
            # This avoids the stale ElementHandle issue
            
            # First try direct page link
            next_locator = page.locator(f"#cphBody_dgSearch tr:last-child a")
            
            # Find the right link by text among pager links
            pager_links = page.locator("#cphBody_dgSearch tr:last-child a")
            count = pager_links.count()
            
            found_next = False
            for i in range(count):
                link = pager_links.nth(i)
                txt = link.inner_text().strip()
                if txt == target_str:
                    print(f"    [PAGER] Clicking page {target_str}...")
                    link.click()
                    time.sleep(2.5)
                    try:
                        page.wait_for_load_state("networkidle", timeout=25000)
                    except Exception:
                        pass
                    time.sleep(0.8)
                    current_page_num += 1
                    found_next = True
                    break

            if not found_next:
                # Look for forward '...' or '>>' among pager links
                for i in range(count):
                    link = pager_links.nth(i)
                    txt = link.inner_text().strip()
                    if txt in ("...", ">>"):
                        print(f"    [PAGER] Advancing window via '{txt}' for page {target_str}...")
                        link.click()
                        time.sleep(2.5)
                        try:
                            page.wait_for_load_state("networkidle", timeout=25000)
                        except Exception:
                            pass
                        time.sleep(0.8)
                        # After window advance, look for target_str again
                        pager_links2 = page.locator("#cphBody_dgSearch tr:last-child a")
                        count2 = pager_links2.count()
                        for j in range(count2):
                            link2 = pager_links2.nth(j)
                            txt2 = link2.inner_text().strip()
                            if txt2 == target_str:
                                print(f"    [PAGER] Clicking page {target_str} after window advance...")
                                link2.click()
                                time.sleep(2.5)
                                try:
                                    page.wait_for_load_state("networkidle", timeout=25000)
                                except Exception:
                                    pass
                                time.sleep(0.8)
                                current_page_num += 1
                                found_next = True
                                break
                        break

            if not found_next:
                print(f"    [PAGER] End of pages at page {active_page}.")
                break

    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        print(f"    [ERROR] {state_label}: {e}")
        traceback.print_exc()

    return state_records, page_count, status, error_msg


def run_recovery():
    from playwright.sync_api import sync_playwright

    # Step 1: Patch checkpoint — remove failed states from done_states
    ckpt = load_checkpoint()
    done_states = set(ckpt.get("done_states", []))
    
    # Remove failed states so they get re-collected
    for s in FAILED_STATES:
        done_states.discard(s)
    ckpt["done_states"] = list(done_states)
    save_checkpoint(ckpt)
    print(f"[RECOVERY] Removed {len(FAILED_STATES)} states from done_states")
    print(f"[RECOVERY] States to re-collect: {sorted(FAILED_STATES)}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            slow_mo=50
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.set_default_timeout(40000)

        # Get state list
        print("\n[RECOVERY] Loading portal to get state list...")
        page.goto(NCVT_SEARCH_URL, wait_until="networkidle", timeout=40000)
        time.sleep(2)

        opts = page.query_selector_all("#cphBody_lbState option")
        state_list = []
        for o in opts:
            val = o.get_attribute("value") or ""
            lbl = clean_cell(o.inner_text())
            if val not in ("-1", "") and not lbl.startswith("-"):
                state_list.append((val, lbl))

        # Re-load checkpoint (may have been updated during initial pass)
        ckpt = load_checkpoint()
        done_states = set(ckpt.get("done_states", []))
        all_records_by_state = ckpt.get("all_records_by_state", {})
        audit_log = ckpt.get("audit_log", [])

        for state_idx, (state_val, state_label) in enumerate(state_list, 1):
            if state_label not in FAILED_STATES:
                continue  # Only recovery targets
            if state_label in done_states:
                print(f"[SKIP] {state_label} already done in checkpoint")
                continue

            print(f"\n[RECOVERY {state_idx}/38] >>> {state_label} (Code: {state_val})")
            start = time.time()

            state_records, page_count, status, error_msg = collect_state(page, state_val, state_label)
            elapsed = round(time.time() - start, 1)
            
            print(f"    Result: {len(state_records)} ITIs in {elapsed}s across {page_count} pages ({status})")

            # Save raw
            save_raw_state(state_label, state_records)
            all_records_by_state[state_label] = state_records

            if status == "SUCCESS" or len(state_records) > 0:
                done_states.add(state_label)

            # Update audit log (replace any existing FAILED entry)
            audit_log = [e for e in audit_log if e.get("state") != state_label]
            audit_log.append({
                "state": state_label,
                "state_code": state_val,
                "pages_fetched": page_count,
                "records_collected": len(state_records),
                "elapsed_seconds": elapsed,
                "status": status,
                "error": error_msg,
                "timestamp": EXTRACTION_DATE,
            })

            ckpt["done_states"] = list(done_states)
            ckpt["all_records_by_state"] = all_records_by_state
            ckpt["audit_log"] = audit_log
            ckpt["total_records_collected"] = sum(len(r) for r in all_records_by_state.values())
            save_checkpoint(ckpt)

        browser.close()

    ckpt = load_checkpoint()
    total = ckpt.get("total_records_collected", 0)
    done = ckpt.get("done_states", [])
    print(f"\n=======================================================")
    print(f"[RECOVERY] Complete! {len(done)} states done, {total} total raw records")
    print(f"=======================================================")


if __name__ == "__main__":
    run_recovery()
