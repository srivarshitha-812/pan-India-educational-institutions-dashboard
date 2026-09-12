"""
extract_cisce.py — CISCE Affiliated School Extractor
=====================================================
CISCE uses server-side rendered HTML pages (Laravel/Blade).
Endpoint: GET https://locate.cisce.org/?page=N
Pages:    1 to ~331 (10 records per page, ~3310 total)
Auth:     None required
CAPTCHA:  None observed

Fields per record:
  - affiliation_code (e.g., AN001, AP005)
  - school_name
  - principal_name
  - address
  - city_town
  - district
  - state
  - pin_code
  - country
  - school_level (ICSE / ISC)
  - school_type (Boys / Girls / Co-ed.)
  - classification (Day / Residential / Day-Boarding)

Features:
  - Parses pre-downloaded HTML pages in data/raw/cisce/
  - Fetches remaining pages with RateLimitedSession (0.8 req/s)
  - Resumable from checkpoint
  - Deduplicates on affiliation_code
  - Generates data/CISCE_INSTITUTIONS_2025.xlsx and raw JSON
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import time
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from lib_extract import (
    RateLimitedSession, load_checkpoint, save_checkpoint,
    RAW_DIR, RESEARCH_DIR, EXTRACTION_DATE
)

SOURCE = "cisce"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://locate.cisce.org/"
TOTAL_PAGES = 332  # observed ~331-332 pages
RPS = 0.8  # safe 0.8 req/sec

session = RateLimitedSession(
    rps=RPS,
    max_retries=5,
    timeout=30,
    extra_headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://locate.cisce.org/",
    }
)


def parse_school_card(card_soup) -> dict | None:
    """Parse one school card BeautifulSoup tag."""
    # School code and name from <h6>
    h6 = card_soup.find("h6")
    if not h6:
        return None
    h6_text = h6.get_text(strip=True)
    parts = h6_text.split("-", 1)
    code = parts[0].strip() if len(parts) > 1 else ""
    name = parts[1].strip() if len(parts) > 1 else h6_text

    # Verify code looks like CISCE code (2-3 letters + 3-4 digits)
    if not re.match(r'^[A-Z]{2,3}\d{3,4}[A-Z]?$', code):
        # Fallback search
        m = re.search(r'\b([A-Z]{2,3}\d{3,4}[A-Z]?)\b', h6_text)
        if m:
            code = m.group(1)

    # Principal and address from <p class="mb-1">
    p = card_soup.find("p", class_="mb-1")
    p_lines = [s.strip() for s in p.stripped_strings] if p else []

    principal = p_lines[0] if len(p_lines) > 0 else ""
    address_line = ", ".join(p_lines[1:]) if len(p_lines) > 1 else ""

    # Parse address components from p_lines
    # Example p_lines:
    # ['Fr. BHARATHRAJA C', 'PORT BLAIR, South Andaman,', 'Andaman and Nicobar Islands,', '744103, India']
    city_town = ""
    district = ""
    state = ""
    pin_code = ""
    country = "India"

    # Search for 6-digit PIN
    pin_m = re.search(r'\b(\d{6})\b', address_line)
    if pin_m:
        pin_code = pin_m.group(1)

    # Geographic tokens
    if len(p_lines) >= 4:
        first_line_parts = [x.strip() for x in p_lines[1].rstrip(",").split(",")]
        if len(first_line_parts) >= 2:
            city_town = first_line_parts[0]
            district = first_line_parts[1]
        elif len(first_line_parts) == 1:
            city_town = first_line_parts[0]
        state = p_lines[2].rstrip(",").strip()
    elif len(p_lines) == 3:
        first_line_parts = [x.strip() for x in p_lines[1].rstrip(",").split(",")]
        if len(first_line_parts) >= 2:
            city_town = first_line_parts[0]
            district = first_line_parts[1]
        state = p_lines[2].rstrip(",").strip()
        # If state contains pin, split it
        if pin_code in state:
            state = re.sub(r'[\d,]+', '', state).strip()

    # Badges: levels, gender type, classification
    badges = [b.get_text(strip=True) for b in card_soup.find_all(class_="badge")]
    levels = [b for b in badges if b in ("ICSE", "ISC", "CVE")]
    school_level = "/".join(levels) if levels else "ICSE"
    
    types = [b for b in badges if b in ("Co-ed.", "Boys", "Girls")]
    school_type = types[0] if types else "Co-ed."
    
    classes = [b for b in badges if b in ("Day", "Residential", "Day/Residential", "Day/Boarding")]
    classification = classes[0] if classes else "Day"

    return {
        "affiliation_code": code,
        "school_name": name,
        "principal_name": principal,
        "address": address_line,
        "city_town": city_town,
        "district": district,
        "state": state,
        "pin_code": pin_code,
        "country": country,
        "school_level": school_level,
        "school_type": school_type,
        "classification": classification,
        "badges": badges,
    }


def extract_from_html(html_content: str) -> tuple[list[dict], int | None]:
    """Extract school records from page HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")
    cards = soup.find_all(class_="school-card")
    
    records = []
    for card in cards:
        rec = parse_school_card(card)
        if rec and rec.get("affiliation_code"):
            records.append(rec)

    # Check for total pages in pagination
    total_pages = None
    page_links = soup.find_all("a", href=re.compile(r'page=(\d+)'))
    for l in page_links:
        m = re.search(r'page=(\d+)', l["href"])
        if m:
            p_num = int(m.group(1))
            if total_pages is None or p_num > total_pages:
                total_pages = p_num

    return records, total_pages


def main():
    print(f"[CISCE] Starting extraction — {EXTRACTION_DATE}")
    
    # Check what pages already exist on disk in data/raw/cisce/
    saved_html_files = sorted(RAW_SOURCE_DIR.glob("cisce_page_*.html"))
    print(f"  Found {len(saved_html_files)} cached HTML files on disk.")
    
    records_by_code = {}
    done_pages = set()
    
    # First pass: parse all already-downloaded pages
    for f in saved_html_files:
        try:
            m = re.search(r'cisce_page_(\d+)\.html', f.name)
            p_num = int(m.group(1)) if m else None
            content = f.read_text(encoding="utf-8", errors="replace")
            recs, _ = extract_from_html(content)
            for r in recs:
                code = r["affiliation_code"]
                if code:
                    records_by_code[code] = r
            if p_num:
                done_pages.add(p_num)
        except Exception as ex:
            print(f"  Error reading {f.name}: {ex}")

    print(f"  Parsed {len(records_by_code)} unique schools from {len(done_pages)} cached pages.")
    
    actual_total = max(332, max(done_pages) if done_pages else 332)
    print(f"  Target total pages: {actual_total}")
    
    # Second pass: fetch any missing pages
    missing_pages = [p for p in range(1, actual_total + 1) if p not in done_pages]
    print(f"  Missing pages to fetch: {len(missing_pages)}")
    
    consecutive_empty = 0
    for page in missing_pages:
        print(f"  [PAGE {page}/{actual_total}] fetching from {BASE_URL}...")
        status, raw = session.get(BASE_URL, params={"page": page}, as_json=False)
        
        if status != 200 or not raw:
            print(f"    HTTP {status} — failed to fetch page {page}")
            consecutive_empty += 1
            if consecutive_empty > 10:
                print("    Too many consecutive errors, pausing live fetch.")
                break
            continue
            
        html_content = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        
        # Save raw HTML
        raw_path = RAW_SOURCE_DIR / f"cisce_page_{page:04d}.html"
        raw_path.write_text(html_content, encoding="utf-8")
        
        recs, found_total = extract_from_html(html_content)
        if found_total and found_total > actual_total:
            actual_total = found_total
            
        if recs:
            for r in recs:
                code = r["affiliation_code"]
                if code:
                    records_by_code[code] = r
            consecutive_empty = 0
            print(f"    {len(recs)} records extracted (total unique: {len(records_by_code)})")
        else:
            consecutive_empty += 1
            print(f"    0 records on page {page} (consecutive empty: {consecutive_empty})")
            if consecutive_empty > 5:
                print("    End of pagination reached.")
                break
                
        done_pages.add(page)
        save_checkpoint(SOURCE, {
            "done_pages": sorted(list(done_pages)),
            "total_records": len(records_by_code),
            "total_pages": actual_total,
        })

    all_records = list(records_by_code.values())
    print(f"\n[CISCE] Extraction complete: {len(all_records)} unique records from {len(done_pages)} pages")

    # Save consolidated raw JSON
    consolidated_path = RAW_SOURCE_DIR / "cisce_all_schools.json"
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f"  Raw JSON: {consolidated_path}")

    # Build Excel output
    build_excel(all_records)


def build_excel(records: list[dict]):
    """Build standardized Excel output."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("[WARN] openpyxl not available — skipping Excel output")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CISCE_Institutions"

    headers = [
        "Official_ID", "Institution_Name", "Principal_Name",
        "Address", "City_Town", "State", "District", "PIN_Code",
        "Country", "Board", "School_Level", "School_Type", "Classification",
        "Recognition_Status", "Academic_Year",
        "Source_URL", "Extraction_Date"
    ]

    hdr_fill = PatternFill("solid", fgColor="1F4E79")
    hdr_font = Font(bold=True, color="FFFFFF")
    for col, hdr in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=hdr)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    for i, r in enumerate(records, 2):
        row_data = [
            r.get("affiliation_code", ""),
            r.get("school_name", ""),
            r.get("principal_name", ""),
            r.get("address", ""),
            r.get("city_town", ""),
            r.get("state", ""),
            r.get("district", ""),
            r.get("pin_code", ""),
            r.get("country", "India"),
            "CISCE",
            r.get("school_level", "ICSE"),
            r.get("school_type", "Co-ed."),
            r.get("classification", "Day"),
            "Affiliated",
            "2025",
            "https://locate.cisce.org/",
            EXTRACTION_DATE,
        ]
        for col, val in enumerate(row_data, 1):
            ws.cell(row=i, column=col, value=val)

    col_widths = [15, 50, 30, 45, 20, 25, 20, 10, 12, 12, 15, 12, 15, 15, 12, 35, 15]
    for col, width in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

    out_path = BASE / "data" / "CISCE_INSTITUTIONS_2025.xlsx"
    wb.save(out_path)
    print(f"  Excel saved: {out_path} ({len(records)} rows)")


if __name__ == "__main__":
    main()
