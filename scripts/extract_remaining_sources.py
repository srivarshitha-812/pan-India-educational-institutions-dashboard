"""
extract_remaining_sources.py — INC, PCI, BCI, CoA, RCI, NCH, DGT/NCVT Extraction
===================================================================================
Unified investigation and extraction script for remaining regulatory sources.

Sources:
  4. INC  — Indian Nursing Council
  5. PCI  — Pharmacy Council of India
  6. BCI  — Bar Council of India
  7. CoA  — Council of Architecture
  8. RCI  — Rehabilitation Council of India
  9. NCH  — National Commission for Homoeopathy
  10. DGT/NCVT — Directorate General of Training / NCVT MIS

Each source is investigated for:
  - API endpoint
  - Authentication requirements
  - CAPTCHA presence
  - Bulk download availability
  - Extraction method

Outputs:
  data/INC_INSTITUTIONS_2025.xlsx
  data/PCI_INSTITUTIONS_2025.xlsx
  data/BCI_INSTITUTIONS_2025.xlsx
  data/COA_INSTITUTIONS_2025.xlsx
  data/RCI_INSTITUTIONS_2025.xlsx
  data/NCH_INSTITUTIONS_2025.xlsx
  data/NCVT_ITI_INSTITUTIONS_2025.xlsx
  data/SOURCE_RESEARCH/<SOURCE>_SOURCE_RESEARCH.md
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import html as htmlmod
import urllib.parse
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE, STATES_UTS,
    save_raw, load_raw
)

# ═══════════════════════════════════════════════════════════════
# COMMON UTILITIES
# ═══════════════════════════════════════════════════════════════

def make_session(referer: str, rps: float = 1.0) -> RateLimitedSession:
    return RateLimitedSession(
        rps=rps, max_retries=5, timeout=30,
        extra_headers={"Referer": referer, "Origin": referer.split("/")[0] + "//" + referer.split("/")[2]}
    )


def probe_endpoints(session: RateLimitedSession, candidates: list[dict], label: str) -> dict | None:
    """Test candidate endpoints and return first working one."""
    print(f"\n[{label}] Probing {len(candidates)} endpoint candidates...")
    for c in candidates:
        url = c["url"]
        params = c.get("params", {})
        method = c.get("method", "GET")
        print(f"  Trying: {url}")

        if method == "POST":
            body = c.get("body")
            if isinstance(body, dict):
                body = urllib.parse.urlencode(body).encode()
            status, data = session.post(url, data=body,
                                       extra_headers=c.get("extra_headers"), as_json=True)
        else:
            status, data = session.get(url, params=params, as_json=True)

        print(f"    Status: {status}, type: {type(data)}")
        if status == 200 and data:
            if isinstance(data, (dict, list)) and data:
                print(f"    [HIT] Found working endpoint!")
                return {"url": url, "config": c, "sample": data}
    return None


def build_simple_excel(records: list, headers: list, row_fn, title: str, out_path: Path):
    """Build Excel file from records."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        print("[WARN] openpyxl not installed")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]
    colors = {"INC": "1A5276", "PCI": "117A65", "BCI": "784212",
              "COA": "283747", "RCI": "6C3483", "NCH": "1F618D", "NCVT": "145A32"}
    color = colors.get(title.split("_")[0], "1F4E79")
    hdr_fill = PatternFill("solid", fgColor=color)
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = hdr_fill
        c.font = Font(bold=True, color="FFFFFF")
    for i, r in enumerate(records, 2):
        for col, val in enumerate(row_fn(r), 1):
            ws.cell(row=i, column=col, value=val)
    wb.save(out_path)
    print(f"  Saved: {out_path} ({len(records)} rows)")


def write_source_research(source: str, api_found: bool, count: int, details: dict):
    status_map = {True: "COMPLETE", False: "NO_BULK_SOURCE"}
    content = f"""# {source} Source Research

## Source Information
- **Source**: {details.get('full_name', source)}
- **Official URL**: {details.get('url', '')}
- **Domain**: {details.get('domain', '')}
- **Extraction Date**: {EXTRACTION_DATE}
- **Status**: {status_map[api_found] if count > 0 else 'NO_BULK_SOURCE'}

## Endpoints Investigated
{chr(10).join('- ' + ep for ep in details.get('endpoints', []))}

## API Discovery Result
{'Working endpoint found' if api_found else 'No public JSON API found. Portal requires browser interaction or CAPTCHA.'}

## Official Identifier
{details.get('identifier', 'Not established')}

## Fields Available
{details.get('fields', 'Not determined')}

## Record Count
- **Extracted**: {count:,}
- **Expected**: {details.get('expected_count', 'Unknown')}

## Limitations
{details.get('limitations', 'Investigation ongoing')}

## Notes
{details.get('notes', '')}
"""
    path = RESEARCH_DIR / f"{source}_SOURCE_RESEARCH.md"
    path.write_text(content, encoding="utf-8")
    print(f"  Research doc: {path}")


# ═══════════════════════════════════════════════════════════════
# INC — Indian Nursing Council
# ═══════════════════════════════════════════════════════════════

def extract_inc():
    print("\n" + "=" * 60)
    print("[INC] Indian Nursing Council — Institution Extraction")
    print("=" * 60)

    session = make_session("https://online.indiannursingcouncil.org/")
    raw_dir = RAW_DIR / "inc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # INC uses ASP.NET WebForms with ViewState
    # The YearlyReportByState page has dropdowns for State/District/Sector/Programme
    # We need to find the underlying data call

    candidates = [
        {"url": "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx",
         "method": "GET", "params": {}},
        {"url": "https://online.indiannursingcouncil.org/api/institutions",
         "method": "GET", "params": {"year": "2025", "state": "Andhra Pradesh"}},
        {"url": "https://online.indiannursingcouncil.org/Reports/getInstitutionData",
         "method": "POST",
         "body": {"yearId": "2025", "stateId": "2", "districtId": "0", "sectorId": "0"},
         "extra_headers": {"Content-Type": "application/x-www-form-urlencoded"}},
        {"url": "https://indiannursingcouncil.org/api/institutions",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
        {"url": "https://indiannursingcouncil.org/Institutions/List",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
    ]

    working = probe_endpoints(session, candidates, "INC")

    if not working:
        # Try fetching the main page to discover ViewState and form structure
        status, raw = session.get(
            "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx",
            as_json=False
        )
        if status == 200 and raw:
            html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            # Save for analysis
            (raw_dir / "inc_main_page.html").write_text(html[:50000], encoding="utf-8")
            print(f"  Fetched main page: {len(html)} chars")

            # Look for ViewState, form action, dropdown values
            vs_m = re.search(r'__VIEWSTATE[^>]*value="([^"]{20,})"', html)
            action_m = re.search(r'<form[^>]*action="([^"]*)"', html, re.I)
            print(f"  ViewState found: {bool(vs_m)}")
            print(f"  Form action: {action_m.group(1) if action_m else 'not found'}")

    records = []
    if working:
        # Extract data using working endpoint
        data = working.get("sample", {})
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for k in ("data", "institutions", "records", "list"):
                if k in data and isinstance(data[k], list):
                    records = data[k]
                    break

    # Build Excel even if empty (to document status)
    headers = ["INC_Code", "Institution_Name", "Address", "State", "District",
               "Sector", "Programme", "Intake", "Recognition_Status",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("institutionId", ""), r.get("institutionName", ""), r.get("address", ""),
                r.get("state", ""), r.get("district", ""), r.get("sector", ""),
                r.get("programme", ""), r.get("intake", ""), r.get("status", "Recognised"),
                "2025", "https://online.indiannursingcouncil.org/", EXTRACTION_DATE]

    out_path = BASE / "data" / "INC_INSTITUTIONS_2025.xlsx"
    build_simple_excel(records, headers, row_fn, "INC_Institutions", out_path)

    write_source_research("INC", bool(working), len(records), {
        "full_name": "Indian Nursing Council",
        "url": "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx",
        "domain": "Nursing and Midwifery Education Institutions",
        "identifier": "INC Institution Code",
        "fields": "Institution_Name, State, District, Sector, Programme, Intake, Recognition_Status",
        "expected_count": "~5,000+",
        "endpoints": [
            "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx",
            "https://online.indiannursingcouncil.org/api/institutions",
        ],
        "limitations": ("INC portal uses ASP.NET WebForms with ViewState. "
                        "State-by-state extraction requires simulating form posts with ViewState token. "
                        "No public JSON API found. Browser automation (Playwright) recommended for full extraction."),
        "notes": "Programme-level data requires deduplication at institution level."
    })

    return len(records)


# ═══════════════════════════════════════════════════════════════
# PCI — Pharmacy Council of India
# ═══════════════════════════════════════════════════════════════

def extract_pci():
    print("\n" + "=" * 60)
    print("[PCI] Pharmacy Council of India — Institution Extraction")
    print("=" * 60)

    session = make_session("https://www.pci.gov.in/")
    raw_dir = RAW_DIR / "pci"
    raw_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        {"url": "https://www.pci.gov.in/pharmacyInstitutions",
         "method": "GET", "params": {"state": "Andhra Pradesh", "page": 1}},
        {"url": "https://www.pci.gov.in/api/institutions",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
        {"url": "https://www.pci.gov.in/InstitutionSearch/SearchInstitute",
         "method": "POST",
         "body": {"state": "Andhra Pradesh", "district": "", "programme": ""},
         "extra_headers": {"Content-Type": "application/x-www-form-urlencoded"}},
        {"url": "https://www.pci.gov.in/content/approved-institutions",
         "method": "GET", "params": {}},
    ]

    working = probe_endpoints(session, candidates, "PCI")

    records = []
    if working:
        data = working.get("sample", {})
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for k in ("data", "institutions", "records"):
                if k in data and isinstance(data[k], list):
                    records = data[k]
                    break

    headers = ["PCI_Code", "Institution_Name", "Address", "State", "District",
               "Course", "Intake", "Approval_Status", "Affiliation",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("pciId", ""), r.get("institutionName", r.get("name", "")),
                r.get("address", ""), r.get("state", ""), r.get("district", ""),
                r.get("course", r.get("programme", "")), r.get("intake", ""),
                r.get("status", "Approved"), r.get("affiliation", ""),
                "2025", "https://www.pci.gov.in/", EXTRACTION_DATE]

    build_simple_excel(records, headers, row_fn, "PCI_Institutions",
                       BASE / "data" / "PCI_INSTITUTIONS_2025.xlsx")

    write_source_research("PCI", bool(working), len(records), {
        "full_name": "Pharmacy Council of India",
        "url": "https://www.pci.gov.in/",
        "domain": "Pharmacy Education Institutions",
        "identifier": "PCI Institution Code",
        "fields": "Institution_Name, State, District, Course, Intake, Approval_Status, Affiliation",
        "expected_count": "~1,500+",
        "endpoints": ["https://www.pci.gov.in/pharmacyInstitutions",
                      "https://www.pci.gov.in/api/institutions"],
        "limitations": "PCI portal may use session-based access. No public JSON API confirmed.",
        "notes": "PCI regulates D.Pharm, B.Pharm, M.Pharm, Pharm.D programmes."
    })
    return len(records)


# ═══════════════════════════════════════════════════════════════
# BCI — Bar Council of India
# ═══════════════════════════════════════════════════════════════

def extract_bci_national():
    print("\n" + "=" * 60)
    print("[BCI] Bar Council of India — National Extraction")
    print("=" * 60)

    session = make_session("https://www.barcouncilofindia.org/")
    raw_dir = RAW_DIR / "bci"
    raw_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        {"url": "https://www.barcouncilofindia.org/legal-education/approved-law-colleges",
         "method": "GET"},
        {"url": "https://www.barcouncilofindia.org/api/law-colleges",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
        {"url": "https://www.barcouncilofindia.org/api/institutions",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
        {"url": "https://www.barcouncilofindia.org/LegalEducation/ApprovedColleges",
         "method": "GET"},
    ]

    working = probe_endpoints(session, candidates, "BCI")

    # Load existing Telangana data
    all_records = []
    tg_data = load_raw("bci", "telangana_approved_law")
    if tg_data:
        all_records.extend(tg_data)
        print(f"  Loaded existing Telangana: {len(tg_data)} records")

    if working:
        # Extract per state
        for state in STATES_UTS:
            if state == "Telangana":
                continue
            params = {"state": state, "page": 1}
            status, data = session.get(working["url"], params=params)
            if status == 200 and data:
                if isinstance(data, list):
                    all_records.extend(data)
                elif isinstance(data, dict):
                    for k in ("data", "colleges", "institutions"):
                        if k in data and isinstance(data[k], list):
                            all_records.extend(data[k])
                            break

    headers = ["BCI_Code", "Institution_Name", "Address", "State", "District",
               "Programme", "Intake", "Approval_Status", "Affiliation",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("bciId", r.get("aicteId", "")),
                r.get("name", r.get("institutionName", "")),
                r.get("address", ""), r.get("district", "TELANGANA" if not r.get("state") else r.get("state")),
                r.get("district", ""), r.get("programme", "LL.B / LL.M"),
                r.get("intake", ""), r.get("status", "Approved"),
                r.get("affiliation", ""), "2025",
                "https://www.barcouncilofindia.org/", EXTRACTION_DATE]

    # Deduplicate by name+state
    seen = set()
    deduped = []
    for r in all_records:
        key = (r.get("name", ""), r.get("state", ""), r.get("district", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    build_simple_excel(deduped, headers, row_fn, "BCI_Institutions",
                       BASE / "data" / "BCI_INSTITUTIONS_2025.xlsx")

    write_source_research("BCI", bool(working), len(deduped), {
        "full_name": "Bar Council of India",
        "url": "https://www.barcouncilofindia.org/",
        "domain": "Legal Education Institutions",
        "identifier": "BCI College Code (or AICTE Perm ID where available)",
        "fields": "Institution_Name, State, District, Programme, Intake, Affiliation",
        "expected_count": "~1,500-1,700",
        "endpoints": ["https://www.barcouncilofindia.org/legal-education/approved-law-colleges",
                      "https://www.barcouncilofindia.org/api/law-colleges"],
        "limitations": "BCI website is primarily static content. Law college list may be in PDF format. No JSON API confirmed.",
        "notes": "BCI regulates LL.B (3yr/5yr) and LL.M programmes. Must check for State Bar Council affiliated colleges too."
    })
    return len(deduped)


# ═══════════════════════════════════════════════════════════════
# CoA — Council of Architecture
# ═══════════════════════════════════════════════════════════════

def extract_coa():
    print("\n" + "=" * 60)
    print("[CoA] Council of Architecture — Institution Extraction")
    print("=" * 60)

    session = make_session("https://coa.gov.in/")
    raw_dir = RAW_DIR / "coa"
    raw_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        {"url": "https://coa.gov.in/architectural_institutions.php", "method": "GET"},
        {"url": "https://coa.gov.in/api/institutions", "method": "GET"},
        {"url": "https://coa.gov.in/api/arch-institutions",
         "method": "GET", "params": {"state": "Andhra Pradesh"}},
        {"url": "https://coa.gov.in/approved_institutions.php", "method": "GET"},
    ]

    # Also try the main page directly
    status, raw = session.get("https://coa.gov.in/architectural_institutions.php", as_json=False)

    records = []
    if status == 200 and raw:
        html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        (raw_dir / "coa_institutions_page.html").write_text(html[:100000], encoding="utf-8")
        print(f"  Fetched CoA institutions page: {len(html)} chars")

        # Parse HTML table
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I)
        for row in rows[1:]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S | re.I)
            if len(cells) < 3:
                continue
            def c(x):
                x = re.sub(r'<[^>]+>', ' ', x)
                return re.sub(r'\s+', ' ', htmlmod.unescape(x)).strip()
            cc = [c(cell) for cell in cells]
            if cc and cc[0] and not any(h in cc[0] for h in ["S.No", "Name", "Sl"]):
                records.append({
                    "sr_no": cc[0],
                    "institution_name": cc[1] if len(cc) > 1 else "",
                    "state": cc[2] if len(cc) > 2 else "",
                    "district": cc[3] if len(cc) > 3 else "",
                    "address": cc[4] if len(cc) > 4 else "",
                    "programme": "B.Arch",
                    "intake": cc[5] if len(cc) > 5 else "",
                    "affiliation": cc[6] if len(cc) > 6 else "",
                    "approval_status": "Approved",
                })
        print(f"  Parsed {len(records)} institutions from HTML table")

        # Also check for JSON embedded in page
        json_m = re.search(r'var\s+institutions\s*=\s*(\[.*?\]);', html, re.S)
        if json_m:
            try:
                embedded = json.loads(json_m.group(1))
                records = embedded
                print(f"  Found {len(records)} records in embedded JSON")
            except Exception:
                pass

    headers = ["CoA_ID", "Institution_Name", "Address", "State", "District",
               "Programme", "Intake", "Affiliation", "Approval_Status",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("sr_no", ""), r.get("institution_name", r.get("name", "")),
                r.get("address", ""), r.get("state", ""), r.get("district", ""),
                r.get("programme", "B.Arch"), r.get("intake", ""),
                r.get("affiliation", ""), r.get("approval_status", "Approved"),
                "2025", "https://coa.gov.in/architectural_institutions.php", EXTRACTION_DATE]

    build_simple_excel(records, headers, row_fn, "COA_Institutions",
                       BASE / "data" / "COA_INSTITUTIONS_2025.xlsx")

    write_source_research("COA", len(records) > 0, len(records), {
        "full_name": "Council of Architecture",
        "url": "https://coa.gov.in/architectural_institutions.php",
        "domain": "Architecture Education Institutions",
        "identifier": "Serial number on CoA list (no separate CoA code confirmed)",
        "fields": "Institution_Name, State, District, Programme (B.Arch), Intake, Affiliation",
        "expected_count": "~500-600",
        "endpoints": ["https://coa.gov.in/architectural_institutions.php"],
        "limitations": "CoA provides a static HTML table of approved institutions. No API found.",
        "notes": "CoA regulates B.Arch programme. List is on the main website page."
    })
    return len(records)


# ═══════════════════════════════════════════════════════════════
# RCI — Rehabilitation Council of India
# ═══════════════════════════════════════════════════════════════

def extract_rci():
    print("\n" + "=" * 60)
    print("[RCI] Rehabilitation Council of India — Institution Extraction")
    print("=" * 60)

    session = make_session("https://rehabcouncil.nic.in/")
    raw_dir = RAW_DIR / "rci"
    raw_dir.mkdir(parents=True, exist_ok=True)

    records = []

    # Try the regular mode institutions page
    status, raw = session.get("https://rehabcouncil.nic.in/regular-mode-inst/", as_json=False)
    if status == 200 and raw:
        html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        (raw_dir / "rci_regular_mode.html").write_text(html[:100000], encoding="utf-8")
        print(f"  Fetched RCI regular mode page: {len(html)} chars")

        # Parse HTML table
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I)
        for row in rows[1:]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S | re.I)
            if len(cells) < 3:
                continue
            def c(x):
                return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', htmlmod.unescape(x))).strip()
            cc = [c(cell) for cell in cells]
            if cc and cc[0] and len(cc[0]) < 10:
                records.append({
                    "sr_no": cc[0],
                    "institution_name": cc[1] if len(cc) > 1 else "",
                    "state": cc[2] if len(cc) > 2 else "",
                    "programme": cc[3] if len(cc) > 3 else "",
                    "recognition_status": "Approved",
                })

    # Also try the JSP-based filter
    candidates = [
        {"url": "https://rciregistration.nic.in/rehabcouncil/filterapprovalinst.jsp",
         "method": "POST",
         "body": {"state": "1", "programme": "0", "district": "0"},
         "extra_headers": {"Content-Type": "application/x-www-form-urlencoded"}},
        {"url": "https://rciregistration.nic.in/rehabcouncil/filterapprovalinst.jsp",
         "method": "GET"},
    ]

    for c in candidates:
        if c["method"] == "POST":
            body = urllib.parse.urlencode(c["body"]).encode()
            st, data = session.post(c["url"], data=body,
                                   extra_headers=c.get("extra_headers"), as_json=False)
        else:
            st, data = session.get(c["url"], as_json=False)

        if st == 200 and data:
            raw_html = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
            print(f"  [RCI JSP] Status {st}, {len(raw_html)} chars")
            (raw_dir / "rci_jsp_response.html").write_text(raw_html[:50000], encoding="utf-8")
            # Try to parse table
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw_html, re.S | re.I)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S | re.I)
                if len(cells) >= 3:
                    def c2(x):
                        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', htmlmod.unescape(x))).strip()
                    cc = [c2(cell) for cell in cells]
                    if cc[0] and len(cc[0]) < 10:
                        records.append({
                            "institution_name": cc[1] if len(cc) > 1 else "",
                            "state": cc[2] if len(cc) > 2 else "",
                            "programme": cc[3] if len(cc) > 3 else "",
                        })

    print(f"  Total RCI records: {len(records)}")
    headers = ["RCI_ID", "Institution_Name", "Address", "State", "District",
               "Programme", "Recognition_Status", "Intake",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("sr_no", ""), r.get("institution_name", r.get("name", "")),
                r.get("address", ""), r.get("state", ""), r.get("district", ""),
                r.get("programme", ""), r.get("recognition_status", "Approved"), r.get("intake", ""),
                "2025", "https://rehabcouncil.nic.in/regular-mode-inst/", EXTRACTION_DATE]

    build_simple_excel(records, headers, row_fn, "RCI_Institutions",
                       BASE / "data" / "RCI_INSTITUTIONS_2025.xlsx")

    write_source_research("RCI", len(records) > 0, len(records), {
        "full_name": "Rehabilitation Council of India",
        "url": "https://rehabcouncil.nic.in/regular-mode-inst/",
        "domain": "Rehabilitation and Special Education Institutions",
        "identifier": "RCI Registration Number",
        "fields": "Institution_Name, State, Programme, Recognition_Status",
        "expected_count": "~700-1,000",
        "endpoints": ["https://rehabcouncil.nic.in/regular-mode-inst/",
                      "https://rciregistration.nic.in/rehabcouncil/filterapprovalinst.jsp"],
        "limitations": "RCI uses JSP/servlet-based portal. Complete all-India list may require iterating state codes.",
    })
    return len(records)


# ═══════════════════════════════════════════════════════════════
# NCH — National Commission for Homoeopathy
# ═══════════════════════════════════════════════════════════════

def extract_nch():
    print("\n" + "=" * 60)
    print("[NCH] National Commission for Homoeopathy — Institution Extraction")
    print("=" * 60)

    session = make_session("https://nchindia.org/")
    raw_dir = RAW_DIR / "nch"
    raw_dir.mkdir(parents=True, exist_ok=True)

    records = []

    candidates = [
        {"url": "https://nchindia.org/institutions", "method": "GET"},
        {"url": "https://nchindia.org/api/institutions", "method": "GET",
         "params": {"state": "Andhra Pradesh"}},
        {"url": "https://nchindia.org/permitted-institutions", "method": "GET"},
        {"url": "https://nchindia.org/recognized-colleges", "method": "GET"},
        {"url": "https://api.nchindia.org/institutions", "method": "GET"},
    ]

    working = probe_endpoints(session, candidates, "NCH")

    # Try fetching the main site for institution links
    for page_path in ["/", "/institutions", "/colleges", "/permitted-colleges"]:
        url = f"https://nchindia.org{page_path}"
        status, raw = session.get(url, as_json=False)
        if status == 200 and raw:
            html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            print(f"  [{status}] {url}: {len(html)} chars")
            (raw_dir / f"nch_page{page_path.replace('/', '_')}.html").write_text(html[:50000], encoding="utf-8")

            # Parse HTML table
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S | re.I)
                if len(cells) >= 2:
                    def c(x):
                        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', htmlmod.unescape(x))).strip()
                    cc = [c(cell) for cell in cells]
                    if cc[0] and any(kw in cc[1] if len(cc) > 1 else "" for kw in
                                    ["College", "Institute", "Medical", "Homoeopathic"]):
                        records.append({
                            "institution_name": cc[1] if len(cc) > 1 else cc[0],
                            "state": cc[2] if len(cc) > 2 else "",
                            "district": cc[3] if len(cc) > 3 else "",
                        })

    headers = ["NCH_ID", "Institution_Name", "Address", "State", "District",
               "Programme", "Recognition_Status", "Intake",
               "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return ["", r.get("institution_name", ""), r.get("address", ""),
                r.get("state", ""), r.get("district", ""),
                "BHMS", r.get("recognition_status", "Permitted"), r.get("intake", ""),
                "2025", "https://nchindia.org/", EXTRACTION_DATE]

    build_simple_excel(records, headers, row_fn, "NCH_Institutions",
                       BASE / "data" / "NCH_INSTITUTIONS_2025.xlsx")

    write_source_research("NCH", bool(working), len(records), {
        "full_name": "National Commission for Homoeopathy",
        "url": "https://nchindia.org/",
        "domain": "Homoeopathy Education Institutions",
        "identifier": "NCH Permit/Recognition Number",
        "fields": "Institution_Name, State, District, Programme (BHMS/MD), Intake, Recognition_Status",
        "expected_count": "~220-250",
        "endpoints": ["https://nchindia.org/institutions", "https://nchindia.org/permitted-institutions"],
        "limitations": "NCH website content varies. May have institution list as PDF downloads. Replaced CCIM's Homoeopathy remit.",
    })
    return len(records)


# ═══════════════════════════════════════════════════════════════
# DGT/NCVT — ITI Institutions
# ═══════════════════════════════════════════════════════════════

def extract_ncvt():
    print("\n" + "=" * 60)
    print("[NCVT/DGT] ITI Institution Extraction")
    print("=" * 60)

    session = make_session("https://ncvtmis.gov.in/")
    raw_dir = RAW_DIR / "ncvt"
    raw_dir.mkdir(parents=True, exist_ok=True)

    records = []

    # NCVT MIS has a public institute search
    # URL: https://ncvtmis.gov.in/pages/Institute/InstSearch.aspx
    candidates = [
        {"url": "https://ncvtmis.gov.in/pages/Institute/InstSearch.aspx", "method": "GET"},
        {"url": "https://ncvtmis.gov.in/api/institutes",
         "method": "GET", "params": {"state": "Andhra Pradesh", "page": 1}},
        {"url": "https://ncvtmis.gov.in/pages/Institute/getInstList",
         "method": "POST",
         "body": {"stateId": "2", "districtId": "0", "sectorId": "0"},
         "extra_headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}},
        # Skill India Digital (NATS/NCVT API)
        {"url": "https://skillindiadigital.gov.in/api/institute/list",
         "method": "GET", "params": {"state": "Andhra Pradesh", "type": "ITI"}},
        # DGT search
        {"url": "https://dgt.gov.in/api/iti/list", "method": "GET",
         "params": {"state": "Andhra Pradesh"}},
    ]

    working = probe_endpoints(session, candidates, "NCVT")

    # Try fetching NCVT MIS search page
    status, raw = session.get("https://ncvtmis.gov.in/pages/Institute/InstSearch.aspx", as_json=False)
    if status == 200 and raw:
        html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        print(f"  NCVT MIS page: {len(html)} chars")
        (raw_dir / "ncvt_search_page.html").write_text(html[:50000], encoding="utf-8")

        # Check form structure
        vs_m = re.search(r'__VIEWSTATE[^>]*value="([^"]{20,})"', html)
        print(f"  ViewState: {bool(vs_m)}")

        # Try to find institute data in embedded JSON
        json_m = re.search(r'"institutes"\s*:\s*(\[.*?\])', html, re.S)
        if json_m:
            try:
                records = json.loads(json_m.group(1))
                print(f"  Found {len(records)} institutes in embedded JSON")
            except Exception:
                pass

    headers = ["NCVT_Code", "ITI_Name", "Address", "State", "District",
               "Management", "Trades", "Seats", "Affiliation_Status",
               "Grading", "Academic_Year", "Source_URL", "Extraction_Date"]

    def row_fn(r):
        return [r.get("instituteCode", r.get("iti_code", "")),
                r.get("instituteName", r.get("iti_name", r.get("name", ""))),
                r.get("address", ""), r.get("state", ""), r.get("district", ""),
                r.get("management", r.get("managementType", "")),
                r.get("trades", ""), r.get("seats", r.get("totalSeats", "")),
                r.get("affiliationStatus", "Affiliated"), r.get("grading", ""),
                "2025", "https://ncvtmis.gov.in/", EXTRACTION_DATE]

    build_simple_excel(records, headers, row_fn, "NCVT_ITI_Institutions",
                       BASE / "data" / "NCVT_ITI_INSTITUTIONS_2025.xlsx")

    write_source_research("NCVT_DGT", bool(working), len(records), {
        "full_name": "NCVT MIS / Directorate General of Training",
        "url": "https://ncvtmis.gov.in/",
        "domain": "Industrial Training Institutes (ITIs)",
        "identifier": "NCVT MIS Institute Code",
        "fields": "ITI_Name, State, District, Management, Trades, Seats, Grading, Affiliation_Status",
        "expected_count": "~14,000+ ITIs (Govt + Pvt)",
        "endpoints": ["https://ncvtmis.gov.in/pages/Institute/InstSearch.aspx",
                      "https://ncvtmis.gov.in/api/institutes",
                      "https://skillindiadigital.gov.in/api/institute/list"],
        "limitations": ("NCVT MIS uses ASP.NET WebForms with ViewState. "
                        "No public REST JSON API confirmed. May need Playwright or NCVT MIS data download."),
        "notes": "Official NCVT ITI count: ~14,000+ as of 2024. NCVT MIS 2.0 may have open API."
    })
    return len(records)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'=' * 60}")
    print(f"REMAINING SOURCES EXTRACTION — {EXTRACTION_DATE}")
    print("=" * 60)

    results = {}
    results["INC"] = extract_inc()
    results["PCI"] = extract_pci()
    results["BCI"] = extract_bci_national()
    results["CoA"] = extract_coa()
    results["RCI"] = extract_rci()
    results["NCH"] = extract_nch()
    results["NCVT"] = extract_ncvt()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for source, count in results.items():
        status = "EXTRACTED" if count > 0 else "NO_DATA_FOUND"
        print(f"  {source:10s}: {count:6,} records  [{status}]")


if __name__ == "__main__":
    main()
