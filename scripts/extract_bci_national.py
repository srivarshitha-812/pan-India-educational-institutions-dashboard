"""
extract_bci_national.py — BCI National Approved Law Colleges Extractor
=======================================================================
Bar Council of India (BCI) approved law colleges.

Strategy:
  1. Check BCI website for downloadable list or JSON API
  2. The BCI website typically publishes state-wise lists in HTML/PDF
  3. Preserve existing Telangana data (already extracted)
  4. Extract national list using HTML scraping or JSON API if found

Known BCI college count: ~1,500-1,700 approved law colleges nationwide

Official identifier: BCI approval number or institution code
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
    save_raw, load_raw, existing_states
)

SOURCE = "bci"
RAW_SOURCE_DIR = RAW_DIR / SOURCE
RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

session = RateLimitedSession(
    rps=1.0, max_retries=5, timeout=30,
    extra_headers={
        "Referer": "https://www.barcouncilofindia.org/",
        "Accept": "text/html,application/xhtml+xml,*/*",
    }
)


def parse_bci_table(html_content: str, state_name: str) -> list[dict]:
    """Parse HTML table from BCI page."""
    records = []
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.S | re.I)

    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S | re.I)
        if len(cells) < 2:
            continue
        def c(x):
            return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', htmlmod.unescape(x))).strip()
        cc = [c(cell) for cell in cells]

        # Skip header rows
        if any(h in (cc[0] + (cc[1] if len(cc) > 1 else "")).lower()
               for h in ["s.no", "name", "college", "sl."]):
            continue
        if not cc[0] or len(cc) < 2:
            continue

        records.append({
            "sr_no": cc[0],
            "institution_name": cc[1] if len(cc) > 1 else "",
            "state": state_name or (cc[2] if len(cc) > 2 else ""),
            "district": cc[3] if len(cc) > 3 else "",
            "address": cc[4] if len(cc) > 4 else "",
            "course": cc[5] if len(cc) > 5 else "LL.B",
            "approval_status": "Approved",
        })
    return records


def main():
    print(f"[BCI] National Extraction — {EXTRACTION_DATE}")
    ckpt = load_checkpoint(f"{SOURCE}_national")
    done = set(ckpt.get("done", []))

    all_records = []

    # Load existing Telangana data
    tg_data = load_raw(SOURCE, "telangana_approved_law")
    if tg_data:
        for r in tg_data:
            r["state"] = r.get("state") or "Telangana"
        all_records.extend(tg_data)
        done.add("Telangana")
        print(f"  Loaded Telangana: {len(tg_data)} records")

    # Try BCI website pages
    bci_pages = [
        ("https://www.barcouncilofindia.org/legal-education/approved-law-colleges", ""),
        ("https://www.barcouncilofindia.org/LE/ApprovedColleges.aspx", ""),
        ("https://www.barcouncilofindia.org/approved-law-colleges", ""),
    ]

    for url, state_hint in bci_pages:
        print(f"\n  Trying: {url}")
        status, raw = session.get(url, as_json=False)
        print(f"    Status: {status}")

        if status == 200 and raw:
            html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            (RAW_SOURCE_DIR / f"bci_national_page.html").write_text(html[:100000], encoding="utf-8")
            print(f"    Page size: {len(html)} chars")

            records = parse_bci_table(html, state_hint)
            if records:
                all_records.extend(records)
                print(f"    Parsed {len(records)} records")

            # Also look for state-wise links
            state_links = re.findall(
                r'href="([^"]*(?:law|legal|college|institute)[^"]*)"[^>]*>([^<]*(?:Pradesh|Bengal|Maharashtra|Karnataka)[^<]*)<',
                html, re.I
            )
            print(f"    State links found: {len(state_links)}")
            for link, link_text in state_links[:5]:
                print(f"      {link_text}: {link}")

    # Try state-wise BCI pages
    BCI_STATE_URLS = {
        "Andhra Pradesh": "https://www.barcouncilofindia.org/legal-education/approved-law-colleges/andhra-pradesh",
        "Maharashtra": "https://www.barcouncilofindia.org/legal-education/approved-law-colleges/maharashtra",
        "Tamil Nadu": "https://www.barcouncilofindia.org/legal-education/approved-law-colleges/tamil-nadu",
    }

    for state, url in BCI_STATE_URLS.items():
        if state in done:
            continue
        print(f"\n  Trying {state}: {url}")
        status, raw = session.get(url, as_json=False)
        if status == 200 and raw:
            html = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            records = parse_bci_table(html, state)
            if records:
                all_records.extend(records)
                done.add(state)
                print(f"    {len(records)} records for {state}")

    # Deduplicate
    seen = set()
    deduped = []
    for r in all_records:
        key = (r.get("institution_name", "").upper().strip(),
               r.get("state", ""), r.get("district", ""))
        if key[0] and key not in seen:
            seen.add(key)
            deduped.append(r)
        elif not key[0]:
            deduped.append(r)

    print(f"\n[BCI] Total: {len(deduped)} unique institutions")

    # Save raw
    out_json = RAW_SOURCE_DIR / "bci_national_all.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    # Build Excel
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BCI_Institutions"
        headers = ["BCI_ID", "Institution_Name", "Address", "State", "District",
                   "Course", "Intake", "Approval_Status", "Affiliation",
                   "Academic_Year", "Source_URL", "Extraction_Date"]
        hdr_fill = PatternFill("solid", fgColor="784212")
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=col, value=h)
            c.fill = hdr_fill
            c.font = Font(bold=True, color="FFFFFF")
        for i, r in enumerate(deduped, 2):
            vals = [
                r.get("bciId", r.get("aicteId", r.get("sr_no", ""))),
                r.get("name", r.get("institution_name", "")),
                r.get("address", ""),
                r.get("state", ""),
                r.get("district", ""),
                r.get("programme", r.get("course", "LL.B")),
                r.get("intake", ""),
                r.get("approval_status", "Approved"),
                r.get("affiliation", ""),
                "2025",
                "https://www.barcouncilofindia.org/",
                EXTRACTION_DATE
            ]
            for col, val in enumerate(vals, 1):
                ws.cell(row=i, column=col, value=val)

        out_path = BASE / "data" / "BCI_INSTITUTIONS_2025.xlsx"
        wb.save(out_path)
        print(f"  Excel: {out_path} ({len(deduped)} rows)")
    except ImportError:
        print("[WARN] openpyxl not installed")

    # Research doc
    doc = f"""# BCI Source Research

## Source Information
- **Source**: Bar Council of India (BCI)
- **Official URL**: https://www.barcouncilofindia.org/
- **Domain**: Legal Education Institutions
- **Extraction Date**: {EXTRACTION_DATE}
- **Status**: {'PARTIAL' if len(deduped) > 0 else 'NO_BULK_SOURCE'}

## Endpoints Investigated
- https://www.barcouncilofindia.org/legal-education/approved-law-colleges
- https://www.barcouncilofindia.org/LE/ApprovedColleges.aspx
- State-specific pages (Andhra Pradesh, Maharashtra, Tamil Nadu)

## API Discovery
No public JSON API found. BCI website uses primarily static HTML.

## Official Identifier
BCI does not publish a standardized institution code in public lists.
Institutions are identified by name + affiliation university + state.
Where available, AICTE Permanent ID serves as the official cross-reference.

## Fields Available
Institution_Name, State, District, Address, Programme (LL.B/LL.M), Intake, Affiliation

## Record Counts
- Extracted: {len(deduped):,} (including existing Telangana data)
- Expected: ~1,500-1,700 approved law colleges nationwide

## Limitations
- BCI does not maintain a single downloadable institution list
- State Bar Councils maintain separate lists for state-affiliated law colleges  
- Complete national coverage requires scraping each state page or state bar council
- No CAPTCHA observed, but page structure may vary by state
- BCI website primarily serves as a regulatory body, not a data portal

## Notes
- BCI regulates LL.B (3-year and 5-year integrated) and LL.M programmes
- Approved college count changes annually as BCI inspects and approves/withdraws
"""
    (RESEARCH_DIR / "BCI_SOURCE_RESEARCH.md").write_text(doc, encoding="utf-8")
    print(f"  Research doc: {RESEARCH_DIR / 'BCI_SOURCE_RESEARCH.md'}")


if __name__ == "__main__":
    main()
