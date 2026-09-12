"""
extract_rci_states.py — RCI State-by-State Extraction
=====================================================
Target: https://rciregistration.nic.in/rehabcouncil/instapproval_statewise.jsp
Method: POST with statewise=<State Name>
Extracts:
  - RCI Institute Code (e.g., AP004, DL001) -> official_institution_id
  - Institution Name
  - Address, State, District, PIN Code
  - Approved Programmes & Duration (aggregated to 1 physical institution)

All 35 States/UTs are queried sequentially at safe rate (0.8-1.0 req/s).
Checkpointed, resumable, deduplicated on RCI Institute Code.
Generates:
  - data/raw/rci/rci_<state>.html
  - data/raw/rci/rci_all_institutions.json
  - data/RCI_INSTITUTIONS_2025.xlsx
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import re
import json
import urllib.parse
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE
)

SOURCE = "rci"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

POST_URL = "https://rciregistration.nic.in/rehabcouncil/instapproval_statewise.jsp"

session = RateLimitedSession(
    rps=0.8,
    max_retries=5,
    timeout=30,
    extra_headers={
        "Referer": "https://rciregistration.nic.in/rehabcouncil/filterapprovalinst.jsp",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Origin": "https://rciregistration.nic.in",
    }
)

# 35 States/UTs discovered in RCI dropdown
RCI_STATES = [
    "Andaman and Nicobar",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]


def parse_state_page(html_content: str, state_name: str) -> list[dict]:
    """Parse table rows from RCI state response HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []

    # Target data table
    table = tables[0]
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    institutions_map = {}

    for row in rows[1:]:  # skip header
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 4:
            continue

        # Columns: SL.No. (0), Institute Code (1), Institute Name & Address (2), State (3), Approved Programme (4), Duration (5)
        inst_code = cells[1].strip()
        raw_name_addr = cells[2].strip()
        state = cells[3].strip() if len(cells) > 3 else state_name
        prog = cells[4].strip() if len(cells) > 4 else ""
        duration = cells[5].strip() if len(cells) > 5 else ""

        if not inst_code or inst_code == "Institute Code":
            continue

        # Split Name and Address
        if "Address :" in raw_name_addr:
            parts = raw_name_addr.split("Address :", 1)
            inst_name = parts[0].strip()
            address = parts[1].strip()
        elif "Address:" in raw_name_addr:
            parts = raw_name_addr.split("Address:", 1)
            inst_name = parts[0].strip()
            address = parts[1].strip()
        else:
            inst_name = raw_name_addr
            address = ""

        # Extract PIN code
        pin_code = ""
        pin_m = re.search(r'\b(\d{6})\b', address)
        if pin_m:
            pin_code = pin_m.group(1)

        prog_entry = f"{prog} ({duration})" if duration else prog

        if inst_code in institutions_map:
            # Aggregate programme to same institution (1 physical inst = 1 record)
            if prog_entry and prog_entry not in institutions_map[inst_code]["programmes"]:
                institutions_map[inst_code]["programmes"].append(prog_entry)
        else:
            institutions_map[inst_code] = {
                "official_institution_id": inst_code,
                "rci_code": inst_code,
                "institution_name": inst_name,
                "address": address,
                "state": state or state_name,
                "pin_code": pin_code,
                "country": "India",
                "education_level": "Higher Education / Rehabilitation",
                "institution_type": "Special Education / Rehabilitation Training Institute",
                "recognition_status": "Approved",
                "recognition_authority": "Rehabilitation Council of India (RCI)",
                "programmes": [prog_entry] if prog_entry else [],
                "source_database": "Rehabilitation Council of India (RCI) National Register",
                "source_url": POST_URL,
                "extraction_date": EXTRACTION_DATE,
            }

    return list(institutions_map.values())


def main():
    print(f"[RCI] Starting national extraction — {EXTRACTION_DATE}")
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done_states = set(ckpt.get("done_states", []))
    all_insts = ckpt.get("institutions", {})

    for state_name in RCI_STATES:
        if state_name in done_states:
            print(f"  [SKIP] {state_name} — already completed")
            continue

        print(f"  [EXTRACT] {state_name}...")
        body = urllib.parse.urlencode({
            "statewise": state_name,
            "Submit": "Submit",
        }).encode()

        status, raw = session.post(POST_URL, data=body, as_json=False)

        if status != 200 or not raw:
            print(f"    HTTP {status} on {state_name}")
            continue

        html_content = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)

        # Save raw HTML
        safe_name = state_name.lower().replace(" ", "_")
        raw_path = RAW_SOURCE_DIR / f"rci_{safe_name}.html"
        raw_path.write_text(html_content, encoding="utf-8")

        state_records = parse_state_page(html_content, state_name)
        print(f"    Extracted {len(state_records)} unique institutions for {state_name}")

        for r in state_records:
            code = r["official_institution_id"]
            if code in all_insts:
                # Merge programmes if duplicate code across queries
                for p in r["programmes"]:
                    if p not in all_insts[code]["programmes"]:
                        all_insts[code]["programmes"].append(p)
            else:
                all_insts[code] = r

        done_states.add(state_name)
        save_checkpoint(f"{SOURCE}_national", {
            "done_states": sorted(list(done_states)),
            "institutions": all_insts,
        })

    institutions_list = list(all_insts.values())
    print(f"\n[RCI] Complete: {len(institutions_list)} canonical institutions across {len(done_states)} States/UTs")

    # Save consolidated raw JSON
    json_path = RAW_SOURCE_DIR / "rci_all_institutions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(institutions_list, f, ensure_ascii=False, indent=2)
    print(f"  Raw JSON: {json_path}")

    # Build Excel
    build_excel(institutions_list)


def build_excel(records: list[dict]):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("[WARN] openpyxl not available")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RCI_Approved_Institutions"

    headers = [
        "Official_ID", "RCI_Code", "Institution_Name",
        "Address", "State", "District", "PIN_Code", "Country",
        "Education_Level", "Institution_Type",
        "Approved_Programmes", "Recognition_Status", "Recognition_Authority",
        "Academic_Year", "Source_URL", "Extraction_Date"
    ]

    hdr_fill = PatternFill("solid", fgColor="6C3483")
    hdr_font = Font(bold=True, color="FFFFFF")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for i, r in enumerate(records, 2):
        row_data = [
            r.get("official_institution_id", ""),
            r.get("rci_code", ""),
            r.get("institution_name", ""),
            r.get("address", ""),
            r.get("state", ""),
            r.get("district", ""),
            r.get("pin_code", ""),
            r.get("country", "India"),
            r.get("education_level", "Higher Education / Rehabilitation"),
            r.get("institution_type", "Special Education / Rehabilitation Training Institute"),
            "; ".join(r.get("programmes", [])),
            r.get("recognition_status", "Approved"),
            r.get("recognition_authority", "Rehabilitation Council of India (RCI)"),
            "2025",
            r.get("source_url", POST_URL),
            r.get("extraction_date", EXTRACTION_DATE),
        ]
        for col, v in enumerate(row_data, 1):
            ws.cell(row=i, column=col, value=v)

    col_widths = [15, 15, 45, 45, 20, 20, 10, 10, 25, 30, 40, 15, 25, 12, 35, 15]
    for col, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w

    out_path = BASE / "data" / "RCI_INSTITUTIONS_2025.xlsx"
    wb.save(out_path)
    print(f"  Excel saved: {out_path} ({len(records)} rows)")


if __name__ == "__main__":
    main()
