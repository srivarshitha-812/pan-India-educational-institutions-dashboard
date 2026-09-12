"""
extract_aicte_national.py — AICTE National Approved Institute Extractor
=========================================================================
Uses the AICTE public API to extract all approved institutes nationally.

API: POST https://www.aicte-india.org/Approved_Institute_List?draw=N&start=0&length=100
Or: GET  https://facilities.aicte-india.org/dashboard/pages/admin-approvedist.php?start=0&length=100

Strategy:
  1. Probe AICTE API endpoints discovered via browser investigation
  2. Iterate with pagination (draw/start/length pattern — DataTables server-side)
  3. Preserve existing Telangana data, supplement missing states

Official IDs:
  - Permanent ID (aictePermId)
  - AISHE Code (aisheCode)

Rate-limit: 1 req/s (AICTE portals are rate-sensitive)

Output:
  data/raw/aicte/<state>_approved.json
  data/AICTE_INSTITUTIONS_2024_25.xlsx
  data/AICTE_PROGRAMMES_2024_25.xlsx
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
import re
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE, STATES_UTS,
    save_raw, load_raw, existing_states
)

SOURCE = "aicte"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Academic year context
ACADEMIC_YEAR = "2024-25"

# ── API Candidates (will try in order) ───────────────────────────────────────
# AICTE One Nation One Data API (known public endpoint)
ONOD_BASE = "https://www.aicte-india.org/bureaux/approvals/approved-institutions"

# AICTE Facilities/Dashboard API (DataTables server-side)
FACILITIES_BASE = "https://facilities.aicte-india.org"
FACILITIES_SEARCH = f"{FACILITIES_BASE}/dashboard/pages/admin-approvedist.php"

# AICTE API server
API_BASE = "https://api.aicte-india.org"

# Bureau of Approvals public report endpoint
BUREAU_URL = "https://www.aicte-india.org/bureau/reporting_online/approved.php"

session = RateLimitedSession(
    rps=1.0,
    max_retries=5,
    timeout=30,
    extra_headers={
        "Referer": "https://www.aicte-india.org/",
        "Origin": "https://www.aicte-india.org",
    }
)


def discover_api() -> dict | None:
    """
    Try multiple known AICTE endpoints to find the working one.
    Returns endpoint config dict or None.
    """
    candidates = [
        # ONOD / Approved Institute Search
        {
            "url": "https://www.aicte-india.org/approved-institutes",
            "method": "GET",
            "params": {"draw": 1, "start": 0, "length": 10},
            "name": "AICTE Approved Institutes (ONOD)"
        },
        # DataTables POST endpoint
        {
            "url": FACILITIES_SEARCH,
            "method": "POST",
            "body": b"draw=1&start=0&length=10",
            "extra_headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "name": "AICTE Facilities DataTables"
        },
        # API server
        {
            "url": f"{API_BASE}/approvedInstList",
            "method": "GET",
            "params": {"draw": 1, "start": 0, "length": 10},
            "name": "AICTE API Server"
        },
        # One Nation One Data open endpoint
        {
            "url": "https://onod.aicte-india.org/api/institution/list",
            "method": "GET",
            "params": {"page": 1, "limit": 10, "status": "active"},
            "name": "ONOD API"
        },
        # Facilities search directly
        {
            "url": "https://facilities.aicte-india.org/dashboard/pages/admin-approvedist.php",
            "method": "GET",
            "params": {"draw": 1, "start": 0, "length": 10},
            "name": "Facilities Search GET"
        },
    ]

    for c in candidates:
        print(f"  Trying: {c['name']} — {c['url']}")
        try:
            if c["method"] == "GET":
                status, data = session.get(c["url"], params=c.get("params"), as_json=True)
            else:
                body = c.get("body")
                extra = c.get("extra_headers")
                status, data = session.post(c["url"], data=body, extra_headers=extra, as_json=True)

            print(f"    Status: {status}, type: {type(data)}")
            if status == 200 and data:
                if isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:10]}")
                    # DataTables response has "data" key
                    if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        print(f"    SUCCESS — {len(data['data'])} records, total: {data.get('recordsTotal', '?')}")
                        return {"endpoint": c, "sample": data}
                    # Or "institutes" or "records"
                    for key in ("institutes", "records", "institutions", "results", "list"):
                        if key in data and isinstance(data[key], list) and data[key]:
                            print(f"    SUCCESS via key '{key}' — {len(data[key])} records")
                            return {"endpoint": c, "sample": data}
                elif isinstance(data, list) and len(data) > 0:
                    print(f"    SUCCESS — {len(data)} records in list")
                    return {"endpoint": c, "sample": data}
        except Exception as e:
            print(f"    Error: {e}")

    return None


def fetch_by_state(state_name: str, working_endpoint: dict) -> list[dict]:
    """
    Fetch all approved institutes for a given state using the working endpoint.
    Handles DataTables pagination.
    """
    ep = working_endpoint["endpoint"]
    all_records = []
    start = 0
    page_size = 100
    total = None

    while True:
        if ep["method"] == "GET":
            params = dict(ep.get("params", {}))
            params.update({"start": start, "length": page_size})
            # Add state filter if API supports it
            # Common param names: state, stateName, stateId, filterState
            for state_key in ("state", "stateName", "filterState"):
                params[state_key] = state_name
            status, data = session.get(ep["url"], params=params)
        else:
            # POST with form data
            from urllib.parse import urlencode
            body_params = {"draw": start // page_size + 1, "start": start, "length": page_size, "state": state_name}
            body = urlencode(body_params).encode()
            status, data = session.post(ep["url"], data=body,
                                        extra_headers=ep.get("extra_headers"))

        if status != 200 or not data:
            print(f"    [ERROR] status={status} at start={start}")
            break

        # Parse DataTables response
        if isinstance(data, dict):
            records = data.get("data") or data.get("institutes") or data.get("records") or []
            if total is None:
                total = data.get("recordsTotal") or data.get("total") or len(records)
        elif isinstance(data, list):
            records = data
            total = len(data)
        else:
            break

        all_records.extend(records)
        print(f"    start={start}, got={len(records)}, total_so_far={len(all_records)}, expected_total={total}")

        if len(records) < page_size or (total and len(all_records) >= total):
            break
        start += page_size

    return all_records


def main():
    print(f"[AICTE] National Extraction — {EXTRACTION_DATE}")
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_states = set(ckpt.get("done_states", []))

    # Check which states already have real data (non-empty arrays)
    already_done = existing_states(SOURCE)
    print(f"  States with existing data: {already_done}")
    print(f"  States from checkpoint: {done_states}")

    # Discover working API
    print("\n[AICTE] Discovering API endpoint...")
    working = discover_api()

    if not working:
        print("\n[AICTE] No working API endpoint found via direct probing.")
        print("  Recommendation: Use browser-based investigation to find the correct endpoint.")
        print("  Falling back to: check for bulk download at aicte-india.org/approvedInstList.xlsx")

        # Try bulk Excel download
        bulk_urls = [
            "https://www.aicte-india.org/approvedInstList.xlsx",
            "https://www.aicte-india.org/approved-institutes/approved-institute-list.xlsx",
            "https://www.aicte-india.org/bureaux/approvals/approved.xlsx",
        ]
        for url in bulk_urls:
            status, raw = session.get(url, as_json=False)
            print(f"  Bulk URL: {url} — status={status}")
            if status == 200 and raw and len(raw) > 10000:
                path = RAW_SOURCE_DIR / "aicte_bulk_download.xlsx"
                path.write_bytes(raw)
                print(f"  [SUCCESS] Bulk download saved: {path}")
                return

        print("\n[AICTE] API discovery FAILED. See SOURCE_RESEARCH/AICTE_SOURCE_RESEARCH.md")
        write_research_doc(None)
        return

    print(f"\n[AICTE] Working endpoint found: {working['endpoint']['name']}")

    # Extract per state (preserving Telangana)
    all_institutions = {}

    # Load existing Telangana data
    tg_data = load_raw(SOURCE, "telangana_approved")
    if tg_data:
        all_institutions["Telangana"] = tg_data
        done_states.add("Telangana")
        print(f"  Loaded existing Telangana data: {len(tg_data)} records")

    for state in STATES_UTS:
        state_key = state.lower().replace(" ", "_")
        if state in done_states or state_key in already_done:
            print(f"  [SKIP] {state} — already extracted")
            continue

        print(f"\n  [EXTRACT] {state}")
        try:
            records = fetch_by_state(state, working)
            if records:
                all_institutions[state] = records
                save_raw(SOURCE, f"{state_key}_approved", records)
                print(f"    Saved {len(records)} records for {state}")
            else:
                print(f"    0 records for {state} — saving empty")
                save_raw(SOURCE, f"{state_key}_approved", [])

            done_states.add(state)
            save_checkpoint(f"{SOURCE}_national", {
                "done_states": list(done_states),
                "working_endpoint": working["endpoint"]["name"],
            })

        except KeyboardInterrupt:
            print("  Interrupted — checkpoint saved")
            break
        except Exception as e:
            print(f"  [ERROR] {state}: {e}")

    # Build outputs
    total_institutions = sum(len(v) for v in all_institutions.values())
    print(f"\n[AICTE] Total institutions: {total_institutions}")

    build_excel(all_institutions)
    write_research_doc(working)


def build_excel(all_institutions: dict):
    """Build institution and programme Excel files."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("[WARN] openpyxl not installed")
        return

    inst_rows = []
    prog_rows = []

    for state, records in all_institutions.items():
        for r in records:
            # Normalize fields (different API responses may use different field names)
            inst_id = (r.get("aictePermId") or r.get("permanentId") or r.get("aicteId")
                      or r.get("permId") or r.get("perm_id") or "")
            aishe = (r.get("aisheCode") or r.get("aishe_code") or r.get("AISHE_CODE") or "")
            name = (r.get("instituteName") or r.get("name") or r.get("institute_name")
                   or r.get("collegeName") or "")
            address = (r.get("address") or r.get("instituteAddress") or "")
            district = (r.get("district") or r.get("districtName") or r.get("dist_name") or "")
            city = (r.get("city") or r.get("town") or "")
            pin = (r.get("pincode") or r.get("pin") or r.get("postalCode") or "")
            management = (r.get("management") or r.get("type_of_institution") or "")
            inst_type = (r.get("instituteType") or r.get("type") or r.get("programme_type") or "")
            affiliation = (r.get("affiliation") or r.get("university") or "")
            status = (r.get("approvalStatus") or r.get("status") or "Approved")

            inst_rows.append([
                inst_id, aishe, name, address, state, district, city, pin,
                management, inst_type, affiliation, "Approved", ACADEMIC_YEAR,
                "https://www.aicte-india.org/", EXTRACTION_DATE
            ])

            # Programmes
            for prog in (r.get("programmes") or r.get("courses") or []):
                prog_rows.append([
                    inst_id, name, state,
                    prog.get("name") or prog.get("programme") or "",
                    prog.get("level") or "",
                    prog.get("intake") or "",
                    ACADEMIC_YEAR, EXTRACTION_DATE
                ])

    # Institutions sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AICTE_Institutions"

    inst_headers = [
        "AICTE_Perm_ID", "AISHE_Code", "Institution_Name",
        "Address", "State", "District", "City", "PIN_Code",
        "Management", "Institution_Type", "Affiliation",
        "Approval_Status", "Academic_Year", "Source_URL", "Extraction_Date"
    ]
    hdr_fill = PatternFill("solid", fgColor="154360")
    hdr_font = Font(bold=True, color="FFFFFF")
    for col, h in enumerate(inst_headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font

    for i, row in enumerate(inst_rows, 2):
        for col, val in enumerate(row, 1):
            ws.cell(row=i, column=col, value=val)

    col_widths = [20, 15, 50, 40, 25, 20, 20, 10, 25, 30, 40, 15, 12, 40, 15]
    for col, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w

    inst_path = BASE / "data" / "AICTE_INSTITUTIONS_2024_25.xlsx"
    wb.save(inst_path)
    print(f"  Institutions Excel: {inst_path} ({len(inst_rows)} rows)")

    # Programmes sheet
    if prog_rows:
        wb2 = openpyxl.Workbook()
        ws2 = wb2.active
        ws2.title = "AICTE_Programmes"
        prog_headers = [
            "AICTE_Perm_ID", "Institution_Name", "State",
            "Programme_Name", "Level", "Approved_Intake",
            "Academic_Year", "Extraction_Date"
        ]
        for col, h in enumerate(prog_headers, 1):
            cell = ws2.cell(row=1, column=col, value=h)
            cell.fill = hdr_fill
            cell.font = hdr_font
        for i, row in enumerate(prog_rows, 2):
            for col, val in enumerate(row, 1):
                ws2.cell(row=i, column=col, value=val)

        prog_path = BASE / "data" / "AICTE_PROGRAMMES_2024_25.xlsx"
        wb2.save(prog_path)
        print(f"  Programmes Excel: {prog_path} ({len(prog_rows)} rows)")


def write_research_doc(working: dict | None):
    """Write source research document."""
    status_label = "API_FOUND_BUT_EXTRACTION_INCOMPLETE" if working else "NO_BULK_SOURCE"
    doc = f"""# AICTE Source Research

## Source Information
- **Source**: All India Council for Technical Education (AICTE)
- **Official URL**: https://www.aicte-india.org/
- **Domain**: Higher Technical Education (Engineering, Management, Pharmacy, Architecture, etc.)
- **Extraction Date**: {EXTRACTION_DATE}
- **Academic Year**: {ACADEMIC_YEAR}
- **Status**: {status_label}

## Endpoints Investigated

### Primary Portal
- https://www.aicte-india.org/approved-institutes
- https://facilities.aicte-india.org/dashboard/pages/admin-approvedist.php
- https://api.aicte-india.org/approvedInstList
- https://onod.aicte-india.org/api/institution/list

### Bulk Download Attempts
- https://www.aicte-india.org/approvedInstList.xlsx
- https://www.aicte-india.org/approved-institutes/approved-institute-list.xlsx

## API Discovery Result
{'Working endpoint: ' + working["endpoint"]["name"] if working else 'No working API endpoint found. Manual investigation via browser required.'}

## Official Identifiers
- **AICTE Permanent ID** (primary)
- **AISHE Code** (secondary cross-reference)

## Fields Available
AICTE_Perm_ID, AISHE_Code, Institution_Name, Address, State, District, City, PIN_Code,
Management, Institution_Type, Affiliation, Approval_Status, Academic_Year, Programmes

## Limitations
- AICTE API may require session cookie or specific headers from the browser portal
- The approved institutes list covers ~12,000 AICTE-approved institutions
- Only active/approved institutions in current year are shown by default
- Closed/withdrawn institutes require separate query with status filter

## Recommended Manual Step
If automated extraction fails:
1. Navigate to https://www.aicte-india.org/approved-institutes
2. Look for Excel/CSV export button
3. Download full approved institute list for 2024-25
"""
    doc_path = RESEARCH_DIR / "AICTE_SOURCE_RESEARCH.md"
    doc_path.write_text(doc, encoding="utf-8")
    print(f"  Research doc: {doc_path}")


if __name__ == "__main__":
    main()
