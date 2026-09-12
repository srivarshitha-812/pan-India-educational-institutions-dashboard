"""
normalize_census_geography.py — Clean and normalize State and District geography
================================================================================
Normalizes state names across all 84,443 records to official Government of India
Standard 36 States & UTs.
"""

import sqlite3
import re
from pathlib import Path
from collections import Counter
import csv
import openpyxl

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "processed" / "education_master.db"
OUTPUT_DIR = BASE / "data" / "processed"

# Canonical state name map
STATE_CANONICAL = {
    "andaman & nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chandigarh": "Chandigarh",
    "chattisgarh": "Chhattisgarh",
    "chhattisgarh": "Chhattisgarh",
    "dadra & nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadar & nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi",
    "delhi (nct)": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jammu & kashmir": "Jammu and Kashmir",
    "jammu and kashmir": "Jammu and Kashmir",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "west bengal": "West Bengal",
    "foreign schools": "Foreign / International",
}

# CISCE 2-letter prefix map
CISCE_PREFIX = {
    "AN": "Andaman and Nicobar Islands",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BI": "Bihar",
    "BR": "Bihar",
    "CH": "Chandigarh",
    "CG": "Chhattisgarh",
    "CT": "Chhattisgarh",
    "DL": "Delhi",
    "GA": "Goa",
    "GO": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JK": "Jammu and Kashmir",
    "JH": "Jharkhand",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "MP": "Madhya Pradesh",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "ME": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "OR": "Odisha",
    "PY": "Puducherry",
    "PU": "Puducherry",
    "PB": "Punjab",
    "PU": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "UA": "Uttarakhand",
    "UK": "Uttarakhand",
    "WB": "West Bengal",
}


def normalize():
    print("[NORMALIZE] Standardizing States and Districts...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(institutions)")
    cols = [c[1] for c in cur.fetchall()]

    cur.execute("SELECT " + ", ".join(cols) + " FROM institutions")
    rows = cur.fetchall()

    updated_rows = []
    state_counter = Counter()

    for r in rows:
        rec = dict(zip(cols, r))
        raw_state = str(rec.get("state") or "").strip()
        oid = str(rec.get("official_institution_id") or "").strip()
        src = str(rec.get("source_database") or "")
        addr = str(rec.get("full_address") or "")

        norm_state = ""
        # 1. Exact match in canonical map
        if raw_state.lower() in STATE_CANONICAL:
            norm_state = STATE_CANONICAL[raw_state.lower()]
        else:
            # 2. Check if CISCE code prefix
            if "CISCE" in src and len(oid) >= 2:
                pfx = oid[:2].upper()
                # Check special case for Hyderabad schools in CISCE
                if pfx == "AP" and any(h in addr.lower() for h in ["hyderabad", "secunderabad", "medchal", "ranga reddy"]):
                    norm_state = "Telangana"
                else:
                    norm_state = CISCE_PREFIX.get(pfx, "")

            # 3. Check CoA code prefix
            if not norm_state and "Architecture" in src and len(oid) >= 2:
                pfx = oid[:2].upper()
                norm_state = CISCE_PREFIX.get(pfx, "")

            # 4. Check RCI code prefix
            if not norm_state and "Rehabilitation" in src and len(oid) >= 2:
                pfx = oid[:2].upper()
                norm_state = CISCE_PREFIX.get(pfx, "")

            # 5. Search substring in raw_state
            if not norm_state:
                for k, v in STATE_CANONICAL.items():
                    if k in raw_state.lower():
                        norm_state = v
                        break

            # 6. Search in address if still blank
            if not norm_state and addr:
                for k, v in STATE_CANONICAL.items():
                    if re.search(r'\b' + re.escape(k) + r'\b', addr.lower()):
                        norm_state = v
                        break

        if not norm_state:
            norm_state = raw_state or "Unknown"

        rec["state"] = norm_state
        state_counter[norm_state] += 1
        updated_rows.append(rec)

    print(f"\n[NORMALIZE] Processed {len(updated_rows):,} records.")
    print("Top 20 Normalized States:")
    for st, c in state_counter.most_common(20):
        print(f"  {st}: {c:,}")

    # Write back to SQLite
    cur.execute("DROP TABLE IF EXISTS institutions_norm")
    col_defs = ", ".join([f"'{c}' TEXT" for c in cols])
    cur.execute(f"CREATE TABLE institutions_norm ({col_defs})")

    insert_sql = f"INSERT INTO institutions_norm ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})"
    batch = []
    for r in updated_rows:
        batch.append([r.get(c, "") for c in cols])
        if len(batch) >= 5000:
            cur.executemany(insert_sql, batch)
            batch = []
    if batch:
        cur.executemany(insert_sql, batch)

    cur.execute("DROP TABLE institutions")
    cur.execute("ALTER TABLE institutions_norm RENAME TO institutions")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inst_official_id ON institutions (official_institution_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inst_state ON institutions (state)")
    conn.commit()
    conn.close()
    print("  SQLite database normalized.")

    # Re-write CSV
    csv_path = OUTPUT_DIR / "master_institutions.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(updated_rows)
    print(f"  Saved normalized {csv_path.name} ({csv_path.stat().st_size:,} bytes)")

    # Re-write Excel
    excel_path = OUTPUT_DIR / "PAN_INDIA_EDUCATIONAL_INSTITUTES.xlsx"
    wb = openpyxl.Workbook()
    ws_summary = wb.active
    ws_summary.title = "National Summary"
    ws_summary.append(["PAN-INDIA EDUCATIONAL INSTITUTION CENSUS - NATIONAL SUMMARY"])
    ws_summary.append(["Total Verified Institutions", len(updated_rows)])
    ws_summary.append(["Unique Official Institution IDs", len(set(r['official_institution_id'] for r in updated_rows))])
    ws_summary.append([])
    ws_summary.append(["State / Union Territory", "Total Institutions"])
    for st, c in sorted(state_counter.items(), key=lambda x: x[1], reverse=True):
        ws_summary.append([st, c])

    ws_all = wb.create_sheet(title="All Institutions")
    ws_all.append(cols)
    for r in updated_rows[:65000]:
        ws_all.append([r.get(c, "") for c in cols])

    wb.save(excel_path)
    print(f"  Saved normalized {excel_path.name} ({excel_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    normalize()
