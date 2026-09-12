"""
extract_ncte_national.py — NCTE Recognized Institution National Extractor
==========================================================================
NCTE (National Council for Teacher Education)

Portal: https://web.ncte.gov.in/page/recognized-institutions

Strategy:
  Backend is a REST API serving JSON data.
  Filters: State → District → Programme → Status
  
  Known working approach: POST/GET with state and district parameters
  The four Regional Committees: Eastern (ERC), Northern (NRC), Southern (SRC), Western (WRC)

Official identifier: NCTE Institution ID (numeric)

Output:
  data/raw/ncte/<state>_recognised.json
  data/NCTE_INSTITUTIONS_2025.xlsx
  data/NCTE_PROGRAMMES_2025.xlsx
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import urllib.parse
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE, STATES_UTS,
    save_raw, load_raw, existing_states
)

SOURCE = "ncte"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

NCTE_BASE = "https://web.ncte.gov.in"
NCTE_API = f"{NCTE_BASE}/ncteapp/recognisedInstitution"

session = RateLimitedSession(
    rps=1.0,
    max_retries=5,
    timeout=30,
    extra_headers={
        "Referer": "https://web.ncte.gov.in/page/recognized-institutions",
        "Origin": NCTE_BASE,
    }
)

# Regional Committee → State mapping
RC_STATE_MAP = {
    "ERC": ["West Bengal", "Bihar", "Jharkhand", "Odisha", "Sikkim", "Andaman and Nicobar Islands"],
    "NRC": ["Delhi", "Uttar Pradesh", "Uttarakhand", "Rajasthan", "Haryana", "Himachal Pradesh",
            "Punjab", "Chandigarh", "Jammu and Kashmir", "Ladakh"],
    "SRC": ["Andhra Pradesh", "Telangana", "Karnataka", "Kerala", "Tamil Nadu",
            "Puducherry", "Lakshadweep"],
    "WRC": ["Maharashtra", "Gujarat", "Goa", "Madhya Pradesh", "Chhattisgarh",
            "Dadra and Nagar Haveli and Daman and Diu"],
}
# States in ERC that aren't above
OTHER_STATES = ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram",
                "Nagaland", "Tripura", "Sikkim"]


def discover_ncte_api() -> list[dict]:
    """Try known NCTE API endpoint patterns."""
    candidates = [
        # Main recognized institution endpoint
        {"url": f"{NCTE_API}/getInstitutionList",
         "params": {"state": "Andhra Pradesh", "district": "", "programme": "", "status": "recognized", "page": 1, "size": 20}},
        {"url": f"{NCTE_API}/list",
         "params": {"state": "Andhra Pradesh", "page": 1, "size": 20}},
        {"url": f"{NCTE_BASE}/ncteapp/api/recognized-institution",
         "params": {"state": "Andhra Pradesh", "page": 1, "size": 20}},
        {"url": f"{NCTE_BASE}/api/recognized-institutions",
         "params": {"state": "Andhra Pradesh", "page": 1, "size": 20}},
        {"url": f"{NCTE_BASE}/ncteapp/recognisedInstitution/fetchInstitutionList",
         "params": {"state": "Andhra Pradesh", "status": 1, "page": 1, "size": 20}},
        # Try without subpath
        {"url": f"{NCTE_BASE}/ncteapp/fetchInstitutionList",
         "params": {"stateName": "Andhra Pradesh", "page": 0, "size": 20}},
    ]

    working = []
    for c in candidates:
        print(f"  Trying: {c['url']}")
        status, data = session.get(c["url"], params=c.get("params"))
        print(f"    Status: {status}, type: {type(data)}")

        if status == 200 and data:
            if isinstance(data, dict):
                for key in ("content", "data", "institutions", "list", "records", "result"):
                    if key in data and isinstance(data[key], list):
                        print(f"    [CANDIDATE] key='{key}', count={len(data[key])}")
                        if data[key]:
                            working.append({"url": c["url"], "params": c.get("params", {}),
                                           "data_key": key, "total_key": "totalElements"})
            elif isinstance(data, list) and data:
                print(f"    [CANDIDATE] list, count={len(data)}")
                working.append({"url": c["url"], "params": c.get("params", {}), "data_key": None})

    return working


def fetch_ncte_state(state_name: str, api_config: dict | None = None) -> list[dict]:
    """Fetch NCTE recognized institutions for a state."""
    if not api_config:
        return []

    all_records = []
    page = 0
    size = 100
    total = None

    while True:
        params = dict(api_config.get("params", {}))
        params.update({"state": state_name, "page": page, "size": size})

        status, data = session.get(api_config["url"], params=params)
        if status != 200 or not data:
            break

        data_key = api_config.get("data_key")
        if isinstance(data, dict):
            records = data.get(data_key, []) if data_key else []
            if not records:
                for k in ("content", "data", "institutions", "list"):
                    records = data.get(k, [])
                    if records:
                        break
            if total is None:
                total = (data.get("totalElements") or data.get("total") or
                         data.get("totalRecords") or data.get("totalCount"))
        elif isinstance(data, list):
            records = data
            total = len(data)
        else:
            break

        all_records.extend(records)
        print(f"    page={page}, got={len(records)}, total_so_far={len(all_records)}")

        if not records or len(records) < size:
            break
        if total and len(all_records) >= total:
            break
        page += 1

    return all_records


def scrape_ncte_html(state_name: str) -> list[dict]:
    """Fallback HTML scraping for NCTE portal."""
    url = f"{NCTE_BASE}/page/recognized-institutions"
    status, raw = session.get(url, params={"state": state_name}, as_json=False)
    if not raw:
        return []

    html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw

    # Look for JSON data in Angular/React embedded state
    json_m = re.search(r'"data"\s*:\s*(\[.*?\])', html, re.S)
    if json_m:
        try:
            return json.loads(json_m.group(1))
        except Exception:
            pass

    return []


def main():
    print(f"[NCTE] National Extraction — {EXTRACTION_DATE}")
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_states = set(ckpt.get("done_states", []))
    already_done = existing_states(SOURCE)

    all_institutions = {}
    all_programmes = []

    # Load existing Telangana data
    tg_data = load_raw(SOURCE, "telangana_recognised")
    if tg_data:
        all_institutions["Telangana"] = tg_data
        done_states.add("Telangana")
        print(f"  Loaded Telangana: {len(tg_data)} records")

    # Discover API
    print("\n[NCTE] Discovering API endpoint...")
    working_apis = discover_ncte_api()

    if not working_apis:
        print("  [WARN] No working API found — will try HTML scraping")

    api_config = working_apis[0] if working_apis else None

    for state in STATES_UTS:
        state_key = state.lower().replace(" ", "_")
        if state in done_states:
            print(f"  [SKIP] {state}")
            continue

        existing = load_raw(SOURCE, f"{state_key}_recognised")
        if existing:
            all_institutions[state] = existing
            done_states.add(state)
            print(f"  [EXISTING] {state}: {len(existing)} records")
            continue

        print(f"\n  [EXTRACT] {state}")

        if api_config:
            records = fetch_ncte_state(state, api_config)
        else:
            records = scrape_ncte_html(state)

        print(f"    Got {len(records)} records for {state}")

        if records:
            all_institutions[state] = records
            save_raw(SOURCE, f"{state_key}_recognised", records)
        else:
            save_raw(SOURCE, f"{state_key}_recognised", [])

        done_states.add(state)
        save_checkpoint(f"{SOURCE}_national", {"done_states": list(done_states)})

    # Flatten, separate institution-level and programme-level
    inst_map = {}  # ncte_id → institution dict
    prog_rows = []

    for state, records in all_institutions.items():
        for r in records:
            inst_id = (r.get("institutionId") or r.get("ncteId") or r.get("id") or
                       r.get("ncte_id") or "")
            inst_name = (r.get("institutionName") or r.get("name") or r.get("college_name") or "")
            programme = (r.get("programme") or r.get("programmeName") or r.get("course") or "")
            intake = r.get("intake") or r.get("sanctionedIntake") or ""

            key = str(inst_id) if inst_id else f"{state}_{inst_name}"

            if key not in inst_map:
                inst_map[key] = {
                    "ncte_id": str(inst_id),
                    "name": inst_name,
                    "address": r.get("address") or r.get("instituteAddress") or "",
                    "state": state,
                    "district": r.get("district") or r.get("districtName") or "",
                    "management": r.get("management") or r.get("managementType") or "",
                    "affiliation": r.get("affiliation") or r.get("affiliationUniversity") or "",
                    "recognition_status": r.get("recognitionStatus") or r.get("status") or "Recognised",
                    "recognition_order": r.get("recognitionOrderNo") or "",
                    "recognition_date": r.get("recognitionDate") or "",
                    "regional_committee": r.get("regionalCommittee") or r.get("rc") or "",
                }

            if programme:
                prog_rows.append({
                    "ncte_id": str(inst_id),
                    "institution_name": inst_name,
                    "state": state,
                    "programme": programme,
                    "intake": intake,
                    "status": r.get("recognitionStatus") or "Recognised",
                })

    institutions = list(inst_map.values())
    print(f"\n[NCTE] {len(institutions)} unique institutions, {len(prog_rows)} programme records")

    build_excel(institutions, prog_rows)
    write_research_doc(api_config, len(institutions))


def build_excel(institutions: list, programmes: list):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print("[WARN] openpyxl not installed")
        return

    # Institutions
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "NCTE_Institutions"
    headers = ["NCTE_ID", "Institution_Name", "Address", "State", "District",
               "Management", "Affiliation", "Recognition_Status", "Recognition_Order",
               "Recognition_Date", "Regional_Committee", "Academic_Year",
               "Source_URL", "Extraction_Date"]
    hdr_fill = PatternFill("solid", fgColor="7D3C98")
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = hdr_fill
        c.font = Font(bold=True, color="FFFFFF")

    for i, r in enumerate(institutions, 2):
        for col, val in enumerate([
            r.get("ncte_id", ""), r.get("name", ""), r.get("address", ""),
            r.get("state", ""), r.get("district", ""), r.get("management", ""),
            r.get("affiliation", ""), r.get("recognition_status", ""),
            r.get("recognition_order", ""), r.get("recognition_date", ""),
            r.get("regional_committee", ""), "2025",
            "https://web.ncte.gov.in/page/recognized-institutions", EXTRACTION_DATE
        ], 1):
            ws.cell(row=i, column=col, value=val)

    out = BASE / "data" / "NCTE_INSTITUTIONS_2025.xlsx"
    wb.save(out)
    print(f"  Institutions: {out} ({len(institutions)} rows)")

    # Programmes
    if programmes:
        wb2 = openpyxl.Workbook()
        ws2 = wb2.active
        ws2.title = "NCTE_Programmes"
        ph = ["NCTE_ID", "Institution_Name", "State", "Programme", "Intake", "Status",
              "Academic_Year", "Extraction_Date"]
        for col, h in enumerate(ph, 1):
            c = ws2.cell(row=1, column=col, value=h)
            c.fill = hdr_fill
            c.font = Font(bold=True, color="FFFFFF")
        for i, r in enumerate(programmes, 2):
            for col, val in enumerate([
                r.get("ncte_id", ""), r.get("institution_name", ""), r.get("state", ""),
                r.get("programme", ""), r.get("intake", ""), r.get("status", ""),
                "2025", EXTRACTION_DATE
            ], 1):
                ws2.cell(row=i, column=col, value=val)
        out2 = BASE / "data" / "NCTE_PROGRAMMES_2025.xlsx"
        wb2.save(out2)
        print(f"  Programmes: {out2} ({len(programmes)} rows)")


def write_research_doc(api_config: dict | None, count: int):
    status = "API_FOUND" if api_config else "NO_BULK_SOURCE"
    doc = f"""# NCTE Source Research

## Source Information
- **Source**: National Council for Teacher Education (NCTE)
- **Official URL**: https://web.ncte.gov.in/page/recognized-institutions
- **Domain**: Teacher Education Institutions
- **Extraction Date**: {EXTRACTION_DATE}
- **Status**: {status}

## Endpoints Investigated
- https://web.ncte.gov.in/ncteapp/recognisedInstitution/getInstitutionList
- https://web.ncte.gov.in/ncteapp/recognisedInstitution/list
- https://web.ncte.gov.in/ncteapp/api/recognized-institution
- https://web.ncte.gov.in/ncteapp/fetchInstitutionList
- https://web.ncte.gov.in/api/recognized-institutions

## API Status
{'Working endpoint: ' + api_config['url'] if api_config else 'No working JSON API found. NCTE portal appears to require browser-rendered JavaScript.'}

## Four Regional Committees
- **ERC** (Eastern): WB, Bihar, JH, Odisha, Sikkim, Andaman
- **NRC** (Northern): Delhi, UP, UK, Rajasthan, Haryana, HP, Punjab, JK, Ladakh
- **SRC** (Southern): AP, Telangana, Karnataka, Kerala, TN, Puducherry, Lakshadweep
- **WRC** (Western): Maharashtra, Gujarat, Goa, MP, Chhattisgarh, DNH&DD

## Official Identifier
- **NCTE Institution ID** (numeric)

## Fields Available
NCTE_ID, Institution_Name, Address, State, District, Programme, Intake,
Management, Affiliation, Recognition_Status, Recognition_Order, Regional_Committee

## Record Count
- Extracted: {count:,}
- Expected: ~16,000-18,000 (NCTE recognized TEIs across India)

## Limitations
- NCTE portal is Angular-based with server-side rendering
- API endpoint may require specific session headers
- Withdrawn/derecognized institutions need separate status filter
- Programme-level data requires deduplication at institution level
"""
    (RESEARCH_DIR / "NCTE_SOURCE_RESEARCH.md").write_text(doc, encoding="utf-8")
    print(f"  Research doc written")


if __name__ == "__main__":
    main()
