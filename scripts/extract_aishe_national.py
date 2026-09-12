"""
extract_aishe_national.py — AISHE HE Directory National Extractor
===================================================================
AISHE (All India Survey on Higher Education) HE Directory

API: https://dashboard.aishe.gov.in/hedirectory
Backend JSON endpoint to be discovered via investigation.

Known data from existing Telangana extraction:
  - aisheCode, name, level, type, category, management
  - district, address, pincode, yearEstablished
  - website, email, phone, courses, approvalAuthority

Strategy:
  1. Load existing Telangana data (valid)
  2. Discover API for remaining states
  3. Extract per-state with pagination
  4. Merge and deduplicate by aisheCode
  5. Build Excel output

Official identifier: AISHE Code (e.g., U-0496 for universities, C-XXXXX for colleges)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import urllib.request
import urllib.error
import urllib.parse
import time
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE, STATES_UTS,
    save_raw, load_raw, existing_states
)

SOURCE = "aishe"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

ACADEMIC_YEAR = "2022-23"  # Latest published AISHE year

# ── API candidates ────────────────────────────────────────────────────────────
DASHBOARD_BASE = "https://dashboard.aishe.gov.in"
AISHE_BASE = "https://aishe.gov.in"

session = RateLimitedSession(
    rps=1.0,
    max_retries=5,
    timeout=30,
    extra_headers={
        "Referer": f"{DASHBOARD_BASE}/hedirectory",
        "Origin": DASHBOARD_BASE,
    }
)


def discover_aishe_api() -> dict | None:
    """Probe known AISHE dashboard API endpoints."""
    print("[AISHE] Discovering API endpoint...")

    candidates = [
        # Dashboard REST endpoints
        {"url": f"{DASHBOARD_BASE}/api/hedirectory", "params": {"page": 1, "size": 10}},
        {"url": f"{DASHBOARD_BASE}/api/institutions", "params": {"page": 1, "size": 10}},
        {"url": f"{DASHBOARD_BASE}/api/directory/list", "params": {"page": 1, "size": 10}},
        {"url": f"{DASHBOARD_BASE}/hedirectory/api/getInstList", "params": {"stateId": 1}},
        {"url": f"{DASHBOARD_BASE}/api/getInstList", "params": {"state": "Andhra Pradesh"}},

        # AISHE main site
        {"url": f"{AISHE_BASE}/api/institutions", "params": {"state": "Andhra Pradesh", "page": 1}},
        {"url": f"{AISHE_BASE}/api/hedirectory", "params": {"state": "Andhra Pradesh"}},
        {"url": f"{AISHE_BASE}/getInstitutionList", "params": {"state": "Andhra Pradesh"}},

        # Common patterns
        {"url": f"{DASHBOARD_BASE}/api/v1/institutions", "params": {"stateCode": "28", "page": 1}},
        {"url": f"{DASHBOARD_BASE}/api/inst/list", "params": {"state": "Andhra Pradesh", "year": "2022-23"}},
    ]

    for c in candidates:
        print(f"  Trying: {c['url']}")
        status, data = session.get(c["url"], params=c.get("params"), as_json=True)
        print(f"    Status: {status}, type: {type(data)}")

        if status == 200 and data:
            if isinstance(data, dict):
                # Look for institution array in common keys
                for key in ("data", "institutions", "records", "list", "content", "results", "items"):
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        sample = data[key][0]
                        print(f"    [HIT] key='{key}', count={len(data[key])}, fields={list(sample.keys())[:8] if isinstance(sample, dict) else '?'}")
                        return {"url": c["url"], "params": c.get("params", {}), "data_key": key, "total_key": "total", "sample": data}
            elif isinstance(data, list) and len(data) > 0:
                print(f"    [HIT] list, count={len(data)}, fields={list(data[0].keys())[:8] if isinstance(data[0], dict) else '?'}")
                return {"url": c["url"], "params": c.get("params", {}), "data_key": None, "sample": data}

    return None


def fetch_state_page(api_config: dict, state_name: str, page: int, size: int = 100) -> tuple[list, int | None]:
    """Fetch one page of institutions for a state."""
    params = dict(api_config.get("params", {}))
    params.update({
        "state": state_name,
        "page": page,
        "size": size,
    })

    status, data = session.get(api_config["url"], params=params, as_json=True)
    if status != 200 or not data:
        return [], None

    data_key = api_config.get("data_key")
    if data_key and isinstance(data, dict):
        records = data.get(data_key, [])
        total = data.get("total") or data.get("totalRecords") or data.get("totalElements")
        return records, total
    elif isinstance(data, list):
        return data, len(data)
    return [], None


def scrape_html_directory(state_name: str) -> list[dict]:
    """
    Fallback: Scrape the AISHE HE Directory HTML page by state.
    Uses the visible web page if JSON API is unavailable.
    """
    print(f"  [HTML FALLBACK] Scraping HTML for {state_name}...")
    url = f"{DASHBOARD_BASE}/hedirectory"
    params = {"state": state_name, "page": 1}

    status, raw = session.get(url, params=params, as_json=False)
    if status != 200 or not raw:
        return []

    html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw

    # Look for JSON data embedded in the page (common in Angular/React SSR)
    json_m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.S)
    if not json_m:
        json_m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.S | re.I)

    if json_m:
        try:
            embedded = json.loads(json_m.group(1))
            # Search for institution array in embedded state
            def find_institutions(obj, depth=0):
                if depth > 5:
                    return []
                if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                    if any(k in obj[0] for k in ("aisheCode", "name", "instituteName", "code")):
                        return obj
                if isinstance(obj, dict):
                    for v in obj.values():
                        result = find_institutions(v, depth + 1)
                        if result:
                            return result
                return []

            insts = find_institutions(embedded)
            if insts:
                print(f"    Found {len(insts)} institutions in embedded JSON")
                return insts
        except Exception:
            pass

    # Parse HTML table
    records = []
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I)
    for row in rows[1:]:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S | re.I)
        if len(cells) < 3:
            continue
        def c(x):
            x = re.sub(r'<[^>]+>', ' ', x)
            return re.sub(r'\s+', ' ', x).strip()
        cc = [c(cell) for cell in cells]
        if cc and re.match(r'[UC]-\d+', cc[0]):
            records.append({
                "aisheCode": cc[0],
                "name": cc[1] if len(cc) > 1 else "",
                "level": cc[2] if len(cc) > 2 else "",
                "state": state_name,
            })

    return records


def main():
    print(f"[AISHE] National Extraction — {EXTRACTION_DATE}")
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_states = set(ckpt.get("done_states", []))

    # Load existing states with real data
    already_done = existing_states(SOURCE)
    print(f"  States with existing data: {already_done}")

    # Always preserve Telangana
    all_institutions = {}
    tg_data = load_raw(SOURCE, "telangana_directory")
    if tg_data and isinstance(tg_data, list) and len(tg_data) > 0:
        all_institutions["Telangana"] = tg_data
        done_states.add("Telangana")
        print(f"  Loaded existing Telangana data: {len(tg_data)} records")

    # Discover working API
    working_api = discover_aishe_api()

    if not working_api:
        print("\n[AISHE] No REST JSON API found — falling back to HTML scraping")

    for state in STATES_UTS:
        state_key = state.lower().replace(" ", "_")
        if state in done_states:
            print(f"  [SKIP] {state} — already extracted")
            continue

        # Check if existing raw file has real data
        existing = load_raw(SOURCE, f"{state_key}_directory")
        if existing and isinstance(existing, list) and len(existing) > 0:
            all_institutions[state] = existing
            done_states.add(state)
            print(f"  [EXISTING] {state}: {len(existing)} records")
            continue

        print(f"\n  [EXTRACT] {state}")

        if working_api:
            # API-based extraction with pagination
            state_records = []
            page = 1
            total = None

            while True:
                records, found_total = fetch_state_page(working_api, state, page)
                if found_total is not None and total is None:
                    total = found_total
                if not records:
                    break
                state_records.extend(records)
                if total and len(state_records) >= total:
                    break
                if len(records) < 100:
                    break
                page += 1

            print(f"    API returned {len(state_records)} records for {state}")
        else:
            # HTML scraping fallback
            state_records = scrape_html_directory(state)
            print(f"    HTML scraping returned {len(state_records)} records for {state}")

        if state_records:
            all_institutions[state] = state_records
            save_raw(SOURCE, f"{state_key}_directory", state_records)
        else:
            print(f"    [WARN] 0 records for {state}")
            save_raw(SOURCE, f"{state_key}_directory", [])

        done_states.add(state)
        save_checkpoint(f"{SOURCE}_national", {"done_states": list(done_states)})

    # Flatten and deduplicate by aisheCode
    all_flat = []
    seen_codes = set()
    for state, records in all_institutions.items():
        for r in records:
            code = r.get("aisheCode") or r.get("code") or ""
            if code and code in seen_codes:
                continue
            if code:
                seen_codes.add(code)
            r["_state"] = state
            all_flat.append(r)

    print(f"\n[AISHE] Total: {len(all_flat)} institutions ({len(seen_codes)} unique AISHE codes)")

    # Save consolidated JSON
    out_json = RAW_SOURCE_DIR / "aishe_national_all.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_flat, f, ensure_ascii=False, indent=2)

    build_excel(all_flat)
    write_research_doc(working_api, len(all_flat), len(seen_codes))


def build_excel(records: list[dict]):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print("[WARN] openpyxl not installed")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AISHE_Institutions"

    headers = [
        "AISHE_Code", "Institution_Name", "Level", "Type", "Category",
        "Management", "State", "District", "Address", "PIN_Code",
        "Year_Established", "Website", "Email", "Phone",
        "Courses", "Approval_Authority", "Academic_Year", "Source_URL", "Extraction_Date"
    ]

    hdr_fill = PatternFill("solid", fgColor="0B3D91")
    hdr_font = Font(bold=True, color="FFFFFF")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font

    for i, r in enumerate(records, 2):
        row_data = [
            r.get("aisheCode") or r.get("code", ""),
            r.get("name") or r.get("instituteName", ""),
            r.get("level", ""),
            r.get("type") or r.get("institutionType", ""),
            r.get("category", ""),
            r.get("management", ""),
            r.get("_state") or r.get("state", ""),
            r.get("district", ""),
            r.get("address", ""),
            r.get("pincode") or r.get("pin", ""),
            r.get("yearEstablished", ""),
            r.get("website", ""),
            r.get("email", ""),
            r.get("phone", ""),
            r.get("courses", ""),
            r.get("approvalAuthority", ""),
            ACADEMIC_YEAR,
            "https://dashboard.aishe.gov.in/hedirectory",
            EXTRACTION_DATE,
        ]
        for col, val in enumerate(row_data, 1):
            ws.cell(row=i, column=col, value=val)

    col_widths = [15, 55, 20, 30, 30, 25, 25, 20, 40, 10, 12, 40, 30, 15, 50, 30, 10, 45, 15]
    for col, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w

    out_path = BASE / "data" / "AISHE_INSTITUTIONS_2022_23.xlsx"
    wb.save(out_path)
    print(f"  Excel saved: {out_path} ({len(records)} rows)")


def write_research_doc(working_api: dict | None, total: int, unique_codes: int):
    status = "API_FOUND" if working_api else "HTML_EXTRACTION"
    doc = f"""# AISHE Source Research

## Source Information
- **Source**: All India Survey on Higher Education (AISHE)
- **Managing Authority**: Ministry of Education, Govt. of India
- **Official Portal**: https://aishe.gov.in/
- **HE Directory**: https://dashboard.aishe.gov.in/hedirectory
- **Domain**: All Higher Education Institutions (Universities, Colleges, Standalone)
- **Latest Published Year**: 2022-23 (survey data with AY lag)
- **Extraction Date**: {EXTRACTION_DATE}
- **Status**: {status}

## API Discovery Result
{'API endpoint found: ' + working_api['url'] if working_api else 'No JSON API found — used HTML scraping'}

## Endpoints Investigated
- https://dashboard.aishe.gov.in/api/hedirectory
- https://dashboard.aishe.gov.in/api/institutions
- https://dashboard.aishe.gov.in/hedirectory/api/getInstList
- https://aishe.gov.in/api/institutions
- (+ 6 other variants)

## Official Identifier
- **AISHE Code** (U-XXXX for universities, C-XXXXX for colleges)

## Fields Available
AISHE_Code, Institution_Name, Level (University/College/Standalone),
Type (State Public/Private/Central/Deemed), Category (Affiliating/Unitary/etc.),
Management, State, District, Address, PIN_Code, Year_Established,
Website, Email, Phone, Courses, Approval_Authority

## Record Counts
- **Total institutions**: {total:,}
- **Unique AISHE codes**: {unique_codes:,}

## Levels Covered
- Universities (U-codes)
- Colleges (C-codes)
- Standalone Institutions

## Limitations
- AISHE data has a 1-2 year lag (latest = 2022-23, not 2025-26)
- HE Directory is the most current version but may not reflect all 2025-26 changes
- Some institutions may appear in AISHE but not yet in the HE Directory (newer registrations)
- Affiliated colleges may require separate college-level query per university
"""
    (RESEARCH_DIR / "AISHE_SOURCE_RESEARCH.md").write_text(doc, encoding="utf-8")
    print(f"  Research doc written")


if __name__ == "__main__":
    main()
