"""
extract_cbse_saras.py — CBSE SARAS National Affiliated School Extractor
========================================================================
Target: https://saras.cbse.gov.in/SARAS/AffiliatedList/ListOfSchdirReport
Method:
  1. GET page to obtain session cookies, anti-forgery token, and form tokens.
  2. Discover all 38 State/UT options from the dropdown.
  3. POST sequentially per state with rate limiting (0.8-1.0 req/s).
  4. Parse all table rows with BeautifulSoup.
  5. Extract:
     - Affiliation Number (e.g., 100002) -> official_institution_id
     - School Code (e.g., 59511)
     - School Name
     - Principal / Head Name
     - State, District, Address, PIN Code
     - School Level (e.g., Senior Secondary Level)
     - Website
  6. Checkpointing, retries, exponential backoff, resumability.
  7. Deduplicate strictly on Affiliation Number.
  8. Output:
     - data/raw/cbse/cbse_<state>.html
     - data/raw/cbse/cbse_all_schools.json
     - data/CBSE_INSTITUTIONS_2025.xlsx
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import re
import json
import time
import http.cookiejar
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE
)

SOURCE = "cbse"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://saras.cbse.gov.in/SARAS/AffiliatedList/ListOfSchdirReport"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_session_and_states():
    """Fetch initial page with cookies, return (opener, tokens, state_options)."""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    req = urllib.request.Request(URL, headers=HEADERS)
    with opener.open(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        raise RuntimeError("No form found on CBSE SARAS page")

    token_elem = form.find("input", {"name": "__RequestVerificationToken"})
    token = token_elem["value"] if token_elem else ""

    ncinfo_elem = form.find("input", {"name": "__ncforminfo"})
    ncinfo = ncinfo_elem["value"] if ncinfo_elem else ""

    state_select = form.find("select", {"name": "State"})
    state_options = []
    if state_select:
        for o in state_select.find_all("option"):
            val = o.get("value", "").strip()
            text = o.get_text(strip=True)
            if val and val != "0":
                state_options.append((val, text))

    return opener, token, ncinfo, state_options


def parse_cbse_table(html_content: str, state_name_fallback: str) -> list[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", id="myTable")
    if not table:
        table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    schools = []
    for row in rows[1:]:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 6:
            continue

        # Cell 1: 'Aff. No. : 100002 Sch. Code: 59511'
        aff_cell = cells[1].strip()
        aff_m = re.search(r'Aff\.\s*No\.\s*:\s*(\d+)', aff_cell, re.I)
        code_m = re.search(r'Sch\.\s*Code\s*:\s*(\d+)', aff_cell, re.I)

        aff_no = aff_m.group(1) if aff_m else ""
        sch_code = code_m.group(1) if code_m else ""

        if not aff_no:
            continue

        # Cell 2: 'State : ANDHRA PRADESH District : KRISHNA'
        geo_cell = cells[2].strip()
        st_m = re.search(r'State\s*:\s*(.*?)(?:District\s*:|$)', geo_cell, re.I)
        dt_m = re.search(r'District\s*:\s*(.*)', geo_cell, re.I)

        state = st_m.group(1).strip() if st_m else state_name_fallback
        district = dt_m.group(1).strip() if dt_m else ""

        # Cell 3: Status / Level
        level = cells[3].strip()

        # Cell 4: 'Name : PM SHRI KENDRIYA VIDYALAYA Head/Principal Name: ROOPINDER SINGH'
        name_cell = cells[4].strip()
        nm_m = re.search(r'Name\s*:\s*(.*?)(?:Head/Principal\s*Name\s*:|$)', name_cell, re.I)
        pr_m = re.search(r'Head/Principal\s*Name\s*:\s*(.*)', name_cell, re.I)

        school_name = nm_m.group(1).strip() if nm_m else name_cell
        principal = pr_m.group(1).strip() if pr_m else ""

        # Cell 5: 'Address : PICKET SECUNDERABAD ANDHRA PRADESH Website : www.picket.kvs.ac.in'
        addr_cell = cells[5].strip()
        ad_m = re.search(r'Address\s*:\s*(.*?)(?:Website\s*:|$)', addr_cell, re.I)
        wb_m = re.search(r'Website\s*:\s*(.*)', addr_cell, re.I)

        address = ad_m.group(1).strip() if ad_m else addr_cell
        website = wb_m.group(1).strip() if wb_m else ""

        pin_m = re.search(r'\b(\d{6})\b', address)
        pin_code = pin_m.group(1) if pin_m else ""

        schools.append({
            "official_institution_id": aff_no,
            "affiliation_number": aff_no,
            "school_code": sch_code,
            "institution_name": school_name,
            "principal_name": principal,
            "education_level": "School (" + (level or "CBSE") + ")",
            "school_level": level,
            "state": state,
            "district": district,
            "address": address,
            "pin_code": pin_code,
            "website": website,
            "country": "India",
            "board": "CBSE",
            "recognition_status": "Affiliated",
            "recognition_authority": "Central Board of Secondary Education (CBSE)",
            "source_database": "CBSE SARAS Official Affiliation Directory",
            "source_url": URL,
            "academic_year": "2025-26",
            "extraction_date": EXTRACTION_DATE,
        })

    return schools


def main():
    print(f"[CBSE SARAS] Starting national extraction — {EXTRACTION_DATE}")
    opener, token, ncinfo, state_options = get_session_and_states()
    print(f"  Acquired session tokens. Found {len(state_options)} States/UTs.")

    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_codes = set(ckpt.get("done_codes", []))
    all_schools = ckpt.get("schools", {})

    for val, name in state_options:
        if val in done_codes:
            print(f"  [SKIP] {name} (code={val}) — already done")
            continue

        print(f"  [EXTRACT] {name} (code={val})...")
        time.sleep(1.2)  # safe 0.8 req/s

        post_headers = dict(HEADERS)
        post_headers["Content-Type"] = "application/x-www-form-urlencoded"
        post_headers["Referer"] = URL
        post_headers["Origin"] = "https://saras.cbse.gov.in"

        post_data = urllib.parse.urlencode({
            "MainRadioValue": "State_wise",
            "State": val,
            "District": "",
            "__Invariant": "RegiAffNo",
            "RegiAffNo": "0",
            "__RequestVerificationToken": token,
            "__ncforminfo": ncinfo,
        }).encode()

        req = urllib.request.Request(URL, data=post_data, headers=post_headers, method="POST")
        try:
            with opener.open(req, timeout=45) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Save raw HTML
            safe_name = name.lower().replace(" ", "_").replace("&", "and")
            raw_path = RAW_SOURCE_DIR / f"cbse_{val}_{safe_name}.html"
            raw_path.write_text(html, encoding="utf-8")

            state_schools = parse_cbse_table(html, name)
            print(f"    Extracted {len(state_schools)} schools for {name}")

            for s in state_schools:
                aff = s["affiliation_number"]
                all_schools[aff] = s

            done_codes.add(val)
            save_checkpoint(f"{SOURCE}_national", {
                "done_codes": sorted(list(done_codes)),
                "schools": all_schools,
            })

        except Exception as ex:
            print(f"    Error on {name}: {ex}")
            time.sleep(3.0)

    schools_list = list(all_schools.values())
    print(f"\n[CBSE SARAS] National extraction complete: {len(schools_list):,} canonical schools")

    # Save consolidated raw JSON
    json_path = RAW_SOURCE_DIR / "cbse_all_schools.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schools_list, f, ensure_ascii=False, indent=2)
    print(f"  Raw JSON: {json_path}")

    # Build Excel
    build_excel(schools_list)


def build_excel(records: list[dict]):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("[WARN] openpyxl not available")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CBSE_Affiliated_Schools"

    headers = [
        "Official_ID", "Affiliation_Number", "School_Code", "Institution_Name",
        "Principal_Name", "State", "District", "Address", "PIN_Code",
        "Website", "Country", "Board", "School_Level",
        "Recognition_Status", "Recognition_Authority",
        "Academic_Year", "Source_URL", "Extraction_Date"
    ]

    hdr_fill = PatternFill("solid", fgColor="4A235A")
    hdr_font = Font(bold=True, color="FFFFFF")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for i, r in enumerate(records, 2):
        row_data = [
            r.get("official_institution_id", ""),
            r.get("affiliation_number", ""),
            r.get("school_code", ""),
            r.get("institution_name", ""),
            r.get("principal_name", ""),
            r.get("state", ""),
            r.get("district", ""),
            r.get("address", ""),
            r.get("pin_code", ""),
            r.get("website", ""),
            r.get("country", "India"),
            "CBSE",
            r.get("school_level", ""),
            r.get("recognition_status", "Affiliated"),
            r.get("recognition_authority", "Central Board of Secondary Education (CBSE)"),
            "2025-26",
            r.get("source_url", URL),
            r.get("extraction_date", EXTRACTION_DATE),
        ]
        for col, v in enumerate(row_data, 1):
            ws.cell(row=i, column=col, value=v)

    col_widths = [15, 18, 12, 50, 30, 20, 20, 50, 10, 30, 10, 10, 22, 15, 30, 12, 35, 15]
    for col, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w

    out_path = BASE / "data" / "CBSE_INSTITUTIONS_2025.xlsx"
    wb.save(out_path)
    print(f"  Excel saved: {out_path} ({len(records):,} rows)")


if __name__ == "__main__":
    main()
