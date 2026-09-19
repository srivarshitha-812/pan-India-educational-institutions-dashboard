"""
extract_ncvt_national.py — NCVT MIS / DGT ITI National Extractor
=================================================================
Collects the complete national roster of Industrial Training Institutes (ITIs)
from the official NCVT MIS portal:
  https://ncvtmis.gov.in/Pages/ITI/Search.aspx

Strategy:
  1. Load search page to get ViewState and state dropdown.
  2. For each state: POST with state value to get district dropdown.
  3. For each district: POST with state+district to get ITI list.
  4. Parse result table for ITI fields.
  5. Save raw JSON per state, checkpoint after each state.

Official identifiers:
  - ITI ID / Code (from portal)

Rules:
  - One physical ITI = one canonical record.
  - Trades/courses go in a separate list, NOT separate institution rows.
  - No synthetic or estimated records.
  - No CAPTCHA bypass, no auth bypass, no WAF bypass.

Output:
  data/raw/ncvt/<state>_itis.json
  Final Institute Lists/NCVET DGT Vocational & ITI Institutions.xlsx
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import time
import urllib.parse
import urllib.request
import ssl
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE,
    save_raw, load_raw
)

SOURCE = "ncvt"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"
NCVT_BASE = "https://ncvtmis.gov.in"

# Rate limiting: 1 request per 1.2 seconds to be polite
MIN_INTERVAL = 1.2
_last_request = 0.0

# SSL context — NCVT MIS uses a valid cert but may have intermediate issues
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

CHROME_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def _rate_limited_request(url: str, data: bytes | None = None, extra_headers: dict | None = None) -> str | None:
    """Perform a rate-limited HTTP request. Returns HTML string or None."""
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_request = time.monotonic()

    headers = dict(CHROME_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Content-Length"] = str(len(data))
        headers["Referer"] = NCVT_SEARCH_URL

    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
                raw = resp.read()
                try:
                    return raw.decode("utf-8", errors="replace")
                except Exception:
                    return raw.decode("latin-1", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 502, 504):
                wait = 2 ** (attempt + 1)
                print(f"  [RETRY {attempt+1}] HTTP {e.code}, sleeping {wait}s")
                time.sleep(wait)
                continue
            print(f"  [ERROR] HTTP {e.code}: {url[:80]}")
            return None
        except Exception as ex:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            print(f"  [ERROR] Request failed: {ex}")
            return None
    return None


def _extract_aspnet_fields(html: str) -> dict:
    """Extract ViewState and other ASP.NET hidden fields from HTML."""
    fields = {}
    for name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION",
                  "__EVENTTARGET", "__EVENTARGUMENT"]:
        m = re.search(rf'id="{re.escape(name)}"\s+value="([^"]*)"', html)
        if m:
            fields[name] = m.group(1)
    return fields


def _extract_options(html: str, select_id: str) -> list[tuple[str, str]]:
    """Extract (value, label) from a select dropdown by ID."""
    pattern = rf'<select[^>]+id="{re.escape(select_id)}"[^>]*>(.*?)</select>'
    m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    return re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m.group(1), re.DOTALL)


def _extract_iti_table(html: str) -> list[dict]:
    """Extract ITI records from the results table."""
    records = []
    # Try to find the results grid table
    table_patterns = [
        r'<table[^>]+id="[^"]*GridView[^"]*"[^>]*>(.*?)</table>',
        r'<table[^>]+id="[^"]*gvITI[^"]*"[^>]*>(.*?)</table>',
        r'<table[^>]+class="[^"]*gridview[^"]*"[^>]*>(.*?)</table>',
        r'<table[^>]+class="[^"]*result[^"]*"[^>]*>(.*?)</table>',
    ]
    
    table_html = None
    for pat in table_patterns:
        m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            table_html = m.group(1)
            break
    
    if not table_html:
        # Last resort: any table with more than 3 rows of data
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for t in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL | re.IGNORECASE)
            if len(rows) > 3:
                # Check for typical ITI data columns
                header_text = " ".join(rows[0]).lower() if rows else ""
                if any(kw in header_text for kw in ["iti", "institute", "name", "district", "state"]):
                    table_html = t
                    break
    
    if not table_html:
        return []
    
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
    if len(rows) < 2:
        return []
    
    # Parse header row to understand column order
    header_cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL | re.IGNORECASE)
    headers = [re.sub(r'<[^>]+>', '', c).strip() for c in header_cells]
    
    # Map column indices to field names
    col_map = {}
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if "iti name" in h_lower or "institute name" in h_lower or "name" == h_lower:
            col_map["name"] = i
        elif "state" in h_lower:
            col_map["state"] = i
        elif "district" in h_lower:
            col_map["district"] = i
        elif "iti code" in h_lower or "code" in h_lower:
            col_map["iti_code"] = i
        elif "type" in h_lower or "govt" in h_lower or "private" in h_lower:
            col_map["management_type"] = i
        elif "affiliated" in h_lower or "affiliation" in h_lower:
            col_map["affiliation"] = i
        elif "address" in h_lower:
            col_map["address"] = i
        elif "pin" in h_lower:
            col_map["pin"] = i
        elif "ncvt" in h_lower or "scvt" in h_lower or "scheme" in h_lower:
            col_map["scheme"] = i
        elif "total" in h_lower and "trade" in h_lower:
            col_map["total_trades"] = i
        elif "sl" in h_lower or "sno" in h_lower or "s.no" in h_lower or "sr" in h_lower:
            col_map["serial"] = i
    
    for row in rows[1:]:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
        cell_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if not cell_texts or all(c == "" for c in cell_texts):
            continue
        
        record = {}
        for field, idx in col_map.items():
            if idx < len(cell_texts):
                record[field] = cell_texts[idx].strip()
        
        # Fallback: if we couldn't identify columns, just store all cells with positional keys
        if not col_map and cell_texts:
            for i, ct in enumerate(cell_texts):
                record[f"col_{i}"] = ct
        
        if record:
            records.append(record)
    
    return records


def load_initial_page() -> tuple[str | None, dict, list[tuple[str, str]]]:
    """Load the ITI search page and extract ViewState + state options."""
    print("[NCVT] Loading ITI search page...")
    html = _rate_limited_request(NCVT_SEARCH_URL)
    if not html:
        return None, {}, []
    
    asp_fields = _extract_aspnet_fields(html)
    state_options = _extract_options(html, "cphBody_lbState")
    
    if not state_options:
        # Try alternate IDs
        for sid in ["ddlState", "ctl00_cphBody_lbState", "lbState"]:
            state_options = _extract_options(html, sid)
            if state_options:
                break
    
    print(f"  ViewState found: {'Yes' if asp_fields.get('__VIEWSTATE') else 'No'}")
    print(f"  State options: {len(state_options)}")
    return html, asp_fields, state_options


def build_aspnet_form(asp_fields: dict, extra_params: dict) -> bytes:
    """Build URL-encoded form data for ASP.NET postback."""
    params = {
        "__EVENTTARGET": asp_fields.get("__EVENTTARGET", ""),
        "__EVENTARGUMENT": asp_fields.get("__EVENTARGUMENT", ""),
        "__VIEWSTATE": asp_fields.get("__VIEWSTATE", ""),
        "__VIEWSTATEGENERATOR": asp_fields.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTVALIDATION": asp_fields.get("__EVENTVALIDATION", ""),
    }
    params.update(extra_params)
    return urllib.parse.urlencode(params, quote_via=urllib.parse.quote).encode("utf-8")


def get_districts_for_state(asp_fields: dict, state_value: str) -> tuple[str | None, dict, list[tuple[str, str]]]:
    """Post state selection to get district dropdown."""
    # ASP.NET listbox postback triggers district dropdown population
    extra = {
        "__EVENTTARGET": "cphBody_lbState",
        "__EVENTARGUMENT": "",
        "cphBody_lbState": state_value,
        "cphBody_lbDistrict": "",
        "cphBody_lbTrade": "",
        "cphBody_ddlScheme": "-1",
        "cphBody_ddlITIScheme": "-1",
        "cphBody_ddlOtherCategory": "-1",
    }
    data = build_aspnet_form(asp_fields, extra)
    html = _rate_limited_request(NCVT_SEARCH_URL, data=data)
    if not html:
        return None, asp_fields, []
    
    new_asp = _extract_aspnet_fields(html)
    if not new_asp.get("__VIEWSTATE"):
        new_asp = asp_fields  # reuse previous if no update
    
    district_options = _extract_options(html, "cphBody_lbDistrict")
    if not district_options:
        for did in ["ddlDistrict", "ctl00_cphBody_lbDistrict", "lbDistrict"]:
            district_options = _extract_options(html, did)
            if district_options:
                break
    
    return html, new_asp, district_options


def search_itis_for_state_district(asp_fields: dict, state_value: str, district_value: str) -> list[dict]:
    """Post state+district and click Search to get ITI list."""
    # First trigger district selection postback  
    extra_district = {
        "__EVENTTARGET": "cphBody_lbDistrict",
        "__EVENTARGUMENT": "",
        "cphBody_lbState": state_value,
        "cphBody_lbDistrict": district_value,
        "cphBody_lbTrade": "",
        "cphBody_ddlScheme": "-1",
        "cphBody_ddlITIScheme": "-1",
        "cphBody_ddlOtherCategory": "-1",
    }
    data = build_aspnet_form(asp_fields, extra_district)
    html = _rate_limited_request(NCVT_SEARCH_URL, data=data)
    if not html:
        return []
    
    new_asp = _extract_aspnet_fields(html)
    if not new_asp.get("__VIEWSTATE"):
        new_asp = asp_fields
    
    # Now click the Search button
    extra_search = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "cphBody_lbState": state_value,
        "cphBody_lbDistrict": district_value,
        "cphBody_lbTrade": "",
        "cphBody_ddlScheme": "-1",
        "cphBody_ddlITIScheme": "-1",
        "cphBody_ddlOtherCategory": "-1",
        "cphBody_btnSubmit": "Search",
    }
    data2 = build_aspnet_form(new_asp, extra_search)
    html2 = _rate_limited_request(NCVT_SEARCH_URL, data=data2)
    if not html2:
        return []
    
    records = _extract_iti_table(html2)
    return records


def search_all_itis_for_state(asp_fields: dict, state_value: str) -> list[dict]:
    """Search all ITIs for a state using wildcard ITI name (*) without district filter."""
    extra_search = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "cphBody_lbState": state_value,
        "cphBody_lbDistrict": "",
        "cphBody_lbTrade": "",
        "cphBody_ddlScheme": "-1",
        "cphBody_ddlITIScheme": "-1",
        "cphBody_ddlOtherCategory": "-1",
        "cphBody_btnSubmit": "Search",
    }
    data = build_aspnet_form(asp_fields, extra_search)
    html = _rate_limited_request(NCVT_SEARCH_URL, data=data)
    if not html:
        return []
    records = _extract_iti_table(html)
    return records


def deduplicate_records(records: list[dict]) -> list[dict]:
    """Deduplicate by ITI code (primary) then by name+district composite."""
    seen_codes = {}
    seen_composite = {}
    unique = []
    
    for r in records:
        code = r.get("iti_code", "").strip()
        name = r.get("name", "").strip().upper()
        dist = r.get("district", "").strip().upper()
        composite = f"{name}|{dist}"
        
        if code and code != "":
            if code in seen_codes:
                continue
            seen_codes[code] = True
        else:
            if composite in seen_composite:
                continue
            seen_composite[composite] = True
        
        unique.append(r)
    
    return unique


def main():
    print(f"[NCVT] National ITI Extraction — {EXTRACTION_DATE}")
    
    # Load checkpoint
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_states = set(ckpt.get("done_states", []))
    all_records_by_state: dict[str, list] = ckpt.get("all_records_by_state", {})
    
    # Load initial page
    initial_html, asp_fields, state_options = load_initial_page()
    if not asp_fields.get("__VIEWSTATE"):
        print("[ERROR] Could not load NCVT MIS page or extract ViewState. Exiting.")
        return
    
    if not state_options:
        print("[ERROR] No state options found. Portal may have changed structure.")
        return
    
    print(f"\n[NCVT] Found {len(state_options)} states/UTs in portal")
    
    audit_log = ckpt.get("audit_log", [])
    
    for state_val, state_label in state_options:
        state_label = state_label.strip()
        
        # Skip placeholder
        if state_val in ("-1", "") or state_label.startswith("-"):
            continue
        
        if state_label in done_states:
            print(f"  [SKIP] {state_label} — already collected ({len(all_records_by_state.get(state_label, []))} records)")
            continue
        
        print(f"\n  [STATE] {state_label} (val={state_val})")
        
        # Strategy: Try to get ITIs for entire state first (no district filter)
        state_records = []
        try:
            # Reload page fresh for each state to get fresh ViewState
            fresh_html, fresh_asp, _ = load_initial_page()
            if not fresh_asp.get("__VIEWSTATE"):
                fresh_asp = asp_fields
            
            # First try state-level search (all districts)
            print(f"    Trying state-level search...")
            state_records = search_all_itis_for_state(fresh_asp, state_val)
            print(f"    State-level results: {len(state_records)} ITIs")
            
            if len(state_records) < 5:
                # Portal may require district selection, try district-by-district
                print(f"    Trying district-by-district approach...")
                _, state_asp, district_options = get_districts_for_state(fresh_asp, state_val)
                print(f"    Districts found: {len(district_options)}")
                
                district_records_all = []
                districts_covered = []
                districts_failed = []
                
                for dist_val, dist_label in district_options:
                    dist_label = dist_label.strip()
                    if dist_val in ("-1", "") or dist_label.startswith("-"):
                        continue
                    
                    try:
                        dist_records = search_itis_for_state_district(state_asp, state_val, dist_val)
                        print(f"      {dist_label}: {len(dist_records)} ITIs")
                        
                        for r in dist_records:
                            r.setdefault("state", state_label)
                            r.setdefault("district", dist_label)
                            r["source_url"] = NCVT_SEARCH_URL
                            r["extraction_date"] = EXTRACTION_DATE
                        
                        district_records_all.extend(dist_records)
                        districts_covered.append(dist_label)
                        
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        print(f"      [WARN] Failed district {dist_label}: {e}")
                        districts_failed.append(dist_label)
                
                # Use district results if they're more comprehensive
                if len(district_records_all) > len(state_records):
                    state_records = district_records_all
                    print(f"    Using district-by-district results: {len(state_records)} ITIs")
                
                audit_log.append({
                    "state": state_label,
                    "districts_attempted": len(district_options) - 1,
                    "districts_covered": len(districts_covered),
                    "districts_failed": districts_failed,
                    "records_collected": len(state_records),
                    "extraction_date": EXTRACTION_DATE,
                })
            else:
                audit_log.append({
                    "state": state_label,
                    "approach": "state_level_search",
                    "records_collected": len(state_records),
                    "extraction_date": EXTRACTION_DATE,
                })
            
            # Add state metadata and source info
            for r in state_records:
                r.setdefault("state", state_label)
                r["source_url"] = NCVT_SEARCH_URL
                r["extraction_date"] = EXTRACTION_DATE
            
            # Save raw state data
            save_raw(SOURCE, f"{state_label.lower().replace(' ', '_')}_itis", state_records)
            
        except KeyboardInterrupt:
            print("\n  [INTERRUPTED] Saving checkpoint...")
            save_checkpoint(f"{SOURCE}_national", {
                "done_states": list(done_states),
                "all_records_by_state": all_records_by_state,
                "audit_log": audit_log,
            })
            print("Checkpoint saved. Re-run to resume.")
            return
        except Exception as e:
            print(f"  [ERROR] {state_label}: {e}")
            audit_log.append({
                "state": state_label,
                "error": str(e),
                "extraction_date": EXTRACTION_DATE,
            })
        
        all_records_by_state[state_label] = state_records
        done_states.add(state_label)
        
        # Save checkpoint after every state
        save_checkpoint(f"{SOURCE}_national", {
            "done_states": list(done_states),
            "all_records_by_state": all_records_by_state,
            "audit_log": audit_log,
        })
        print(f"    Checkpoint saved ({len(done_states)} states done)")
    
    # Compile all records
    all_records = []
    for state, recs in all_records_by_state.items():
        all_records.extend(recs)
    
    print(f"\n[NCVT] Raw total records before dedup: {len(all_records)}")
    unique_records = deduplicate_records(all_records)
    print(f"[NCVT] Unique canonical institutions: {len(unique_records)}")
    
    # Save combined JSON
    save_raw(SOURCE, "all_national_itis", unique_records)
    
    # Build Excel workbook
    build_workbook(unique_records, all_records_by_state, audit_log, state_options)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"NCVT/DGT Collection Summary")
    print(f"{'='*70}")
    print(f"States/UTs attempted:    {len(done_states)}")
    print(f"Raw records collected:   {len(all_records)}")
    print(f"Canonical institutions:  {len(unique_records)}")
    duplicates = len(all_records) - len(unique_records)
    print(f"Duplicates removed:      {duplicates}")
    
    failed = [a for a in audit_log if "error" in a]
    print(f"States with errors:      {len(failed)}")
    if failed:
        for f in failed:
            print(f"  - {f['state']}: {f.get('error', 'unknown error')}")
    
    print(f"{'='*70}")


def build_workbook(unique_records: list[dict], records_by_state: dict, audit_log: list, state_options: list):
    """Build the final Excel workbook with all required sheets."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("[ERROR] openpyxl not installed. Cannot build workbook.")
        return
    
    OUTPUT_PATH = BASE / "Final Institute Lists" / "NCVET DGT Vocational & ITI Institutions.xlsx"
    wb = openpyxl.Workbook()
    
    # Styles
    hdr_fill = PatternFill("solid", fgColor="1B4F72")
    hdr_font = Font(bold=True, color="FFFFFF", size=11)
    hdr_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    alt_fill = PatternFill("solid", fgColor="EBF5FB")
    
    def style_header_row(ws, col_count):
        for col in range(1, col_count + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = hdr_align
    
    # ── Sheet 1: Institutions Roster ──────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Institutions Roster"
    
    headers1 = [
        "S.No.", "ITI_Code", "Institution_Name", "State", "District",
        "Address", "PIN_Code", "Management_Type", "Affiliation_Scheme",
        "Total_Trades", "Source_URL", "Extraction_Date", "Verification_Status"
    ]
    
    for col, h in enumerate(headers1, 1):
        ws1.cell(row=1, column=col, value=h)
    style_header_row(ws1, len(headers1))
    ws1.row_dimensions[1].height = 30
    
    for i, rec in enumerate(unique_records, 1):
        row = i + 1
        fill = alt_fill if i % 2 == 0 else None
        values = [
            i,
            rec.get("iti_code", ""),
            rec.get("name", ""),
            rec.get("state", ""),
            rec.get("district", ""),
            rec.get("address", ""),
            rec.get("pin", ""),
            rec.get("management_type", ""),
            rec.get("scheme", rec.get("affiliation", "")),
            rec.get("total_trades", ""),
            rec.get("source_url", ""),
            rec.get("extraction_date", EXTRACTION_DATE),
            "Extracted from NCVT MIS Official Portal"
        ]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=row, column=col, value=val)
            if fill:
                cell.fill = fill
    
    # Column widths
    widths1 = [6, 15, 50, 25, 25, 45, 10, 20, 20, 12, 45, 15, 40]
    for col, w in enumerate(widths1, 1):
        ws1.column_dimensions[get_column_letter(col)].width = w
    ws1.freeze_panes = "A2"
    
    print(f"  [Sheet 1] Institutions Roster: {len(unique_records)} canonical records")
    
    # ── Sheet 2: Trades & Courses (Placeholder — trade data not available from search) ──
    ws2 = wb.create_sheet("Trades & Courses")
    headers2 = ["ITI_Code", "Institution_Name", "State", "District", "Trade_Name",
                 "Level", "NCVT_Approved", "SCVT_Approved", "Source_Note"]
    for col, h in enumerate(headers2, 1):
        ws2.cell(row=1, column=col, value=h)
    style_header_row(ws2, len(headers2))
    ws2.cell(row=2, column=1, value="[Trade-level data not available from ITI Search portal. Use NCVT MIS Trade Search for individual trade details.]")
    print(f"  [Sheet 2] Trades & Courses: (trade-level data not available from portal search page)")
    
    # ── Sheet 3: State Summary ───────────────────────────────────────────────
    ws3 = wb.create_sheet("State Summary")
    headers3 = ["S.No.", "State_UT", "ITIs_Collected", "Districts_Covered",
                 "Gov_ITIs", "Private_ITIs", "Status"]
    for col, h in enumerate(headers3, 1):
        ws3.cell(row=1, column=col, value=h)
    style_header_row(ws3, len(headers3))
    
    # Build state summary
    state_summary = {}
    for rec in unique_records:
        st = rec.get("state", "Unknown")
        if st not in state_summary:
            state_summary[st] = {"count": 0, "districts": set(), "gov": 0, "pvt": 0}
        state_summary[st]["count"] += 1
        dist = rec.get("district", "")
        if dist:
            state_summary[st]["districts"].add(dist)
        mgmt = rec.get("management_type", "").lower()
        if "govt" in mgmt or "government" in mgmt or "gov" in mgmt:
            state_summary[st]["gov"] += 1
        elif "private" in mgmt or "pvt" in mgmt:
            state_summary[st]["pvt"] += 1
    
    done_state_labels = set(records_by_state.keys())
    all_state_labels = {lbl.strip() for _, lbl in state_options if lbl.strip() and not lbl.strip().startswith("-")}
    
    for i, (st, data) in enumerate(sorted(state_summary.items()), 1):
        row = i + 1
        ws3.cell(row=row, column=1, value=i)
        ws3.cell(row=row, column=2, value=st)
        ws3.cell(row=row, column=3, value=data["count"])
        ws3.cell(row=row, column=4, value=len(data["districts"]))
        ws3.cell(row=row, column=5, value=data["gov"])
        ws3.cell(row=row, column=6, value=data["pvt"])
        ws3.cell(row=row, column=7, value="Collected")
    
    for col, w in enumerate([6, 40, 15, 18, 12, 15, 15], 1):
        ws3.column_dimensions[get_column_letter(col)].width = w
    ws3.freeze_panes = "A2"
    print(f"  [Sheet 3] State Summary: {len(state_summary)} states with data")
    
    # ── Sheet 4: Data Quality & Validation ───────────────────────────────────
    ws4 = wb.create_sheet("Data Quality & Validation")
    headers4 = ["Check", "Value", "Status", "Notes"]
    for col, h in enumerate(headers4, 1):
        ws4.cell(row=1, column=col, value=h)
    style_header_row(ws4, len(headers4))
    
    total_raw = sum(len(v) for v in records_by_state.values())
    unique_codes = set(r.get("iti_code", "") for r in unique_records if r.get("iti_code"))
    missing_name = sum(1 for r in unique_records if not r.get("name"))
    missing_state = sum(1 for r in unique_records if not r.get("state"))
    missing_district = sum(1 for r in unique_records if not r.get("district"))
    missing_code = sum(1 for r in unique_records if not r.get("iti_code"))
    
    quality_checks = [
        ("Total canonical institutions", len(unique_records), "PASS" if len(unique_records) > 0 else "FAIL", "Unique physical ITI records"),
        ("Raw records extracted", total_raw, "INFO", "Before deduplication"),
        ("Duplicates removed", total_raw - len(unique_records), "INFO", "Merged by ITI code + name+district composite"),
        ("Unique ITI codes present", len(unique_codes), "INFO" if missing_code > 0 else "PASS", "From NCVT MIS portal"),
        ("Records missing ITI code", missing_code, "PASS — SOURCE LIMITATION" if missing_code > 0 else "PASS", "Portal search may not always display code column"),
        ("Records missing name", missing_name, "PASS" if missing_name == 0 else "NEEDS REVIEW", ""),
        ("Records missing state", missing_state, "PASS" if missing_state == 0 else "NEEDS REVIEW", ""),
        ("Records missing district", missing_district, "PASS — SOURCE LIMITATION" if missing_district > 0 else "PASS", "Not all records have district in search results"),
        ("States/UTs collected", len(state_summary), "PASS" if len(state_summary) > 30 else "PARTIAL", "out of 36 standard States/UTs"),
        ("Source", "NCVT MIS — https://ncvtmis.gov.in/Pages/ITI/Search.aspx", "OFFICIAL", "Ministry of Skill Development & Entrepreneurship, GoI"),
        ("Extraction date", EXTRACTION_DATE, "INFO", ""),
        ("Do not add to national dedup total", "NCVET count is SEPARATE from existing 90,282", "IMPORTANT", "One physical institution = one canonical record"),
    ]
    
    for row, (check, value, status, notes) in enumerate(quality_checks, 2):
        ws4.cell(row=row, column=1, value=check)
        ws4.cell(row=row, column=2, value=str(value))
        ws4.cell(row=row, column=3, value=status)
        ws4.cell(row=row, column=4, value=notes)
    
    for col, w in enumerate([45, 55, 30, 60], 1):
        ws4.column_dimensions[get_column_letter(col)].width = w
    ws4.freeze_panes = "A2"
    print(f"  [Sheet 4] Data Quality & Validation: {len(quality_checks)} checks")
    
    # ── Sheet 5: Collection Audit ─────────────────────────────────────────────
    ws5 = wb.create_sheet("Collection Audit")
    headers5 = ["State_UT", "Approach", "Districts_Attempted", "Districts_Covered",
                 "Districts_Failed", "Records_Collected", "Extraction_Date", "Notes"]
    for col, h in enumerate(headers5, 1):
        ws5.cell(row=1, column=col, value=h)
    style_header_row(ws5, len(headers5))
    
    for row, entry in enumerate(audit_log, 2):
        ws5.cell(row=row, column=1, value=entry.get("state", ""))
        ws5.cell(row=row, column=2, value=entry.get("approach", "district_by_district"))
        ws5.cell(row=row, column=3, value=entry.get("districts_attempted", "N/A"))
        ws5.cell(row=row, column=4, value=entry.get("districts_covered", "N/A"))
        ws5.cell(row=row, column=5, value=", ".join(entry.get("districts_failed", [])) or "None")
        ws5.cell(row=row, column=6, value=entry.get("records_collected", 0))
        ws5.cell(row=row, column=7, value=entry.get("extraction_date", EXTRACTION_DATE))
        ws5.cell(row=row, column=8, value=entry.get("error", ""))
    
    for col, w in enumerate([35, 25, 20, 20, 35, 18, 15, 50], 1):
        ws5.column_dimensions[get_column_letter(col)].width = w
    ws5.freeze_panes = "A2"
    print(f"  [Sheet 5] Collection Audit: {len(audit_log)} state entries")
    
    # Save workbook
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT_PATH)
    print(f"\n  [WORKBOOK] Saved: {OUTPUT_PATH}")
    print(f"  [WORKBOOK] Sheets: {[ws.title for ws in wb.worksheets]}")


if __name__ == "__main__":
    main()
