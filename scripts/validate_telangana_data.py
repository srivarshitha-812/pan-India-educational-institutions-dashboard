"""
validate_telangana_data.py
Thoroughly validate the existing Telangana datasets using openpyxl & sqlite3 directly.
Checks:
1. TELANGANA_ALL_EDUCATIONAL_INSTITUTIONS_FINAL.xlsx
2. education_master.db (Telangana slice)
3. Duplication check on official_institution_id
4. Completeness of mandatory fields
5. Breakdown by education level, management, and regulatory source
"""
import sqlite3
import openpyxl
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def validate_excel():
    excel_path = BASE / "data" / "processed" / "TELANGANA_ALL_EDUCATIONAL_INSTITUTIONS_FINAL.xlsx"
    if not excel_path.exists():
        print(f"[FAIL] {excel_path} does not exist!")
        return
    print(f"[EXCEL] Loading {excel_path.name} ({excel_path.stat().st_size:,} bytes)...")
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    
    rows_iter = ws.iter_rows(values_only=True)
    headers = next(rows_iter)
    h_map = {h: idx for idx, h in enumerate(headers)}
    print(f"  Headers ({len(headers)}): {headers}")
    
    id_idx = h_map.get("official_institution_id", h_map.get("Official Institution ID"))
    name_idx = h_map.get("name", h_map.get("Institution Name"))
    level_idx = h_map.get("education_level", h_map.get("Education Level"))
    src_idx = h_map.get("source_database", h_map.get("Source Database"))
    dist_idx = h_map.get("district", h_map.get("District"))
    
    total_count = 0
    id_counter = Counter()
    level_counter = Counter()
    src_counter = Counter()
    dist_counter = Counter()
    null_ids = 0
    null_names = 0
    
    for row in rows_iter:
        total_count += 1
        oid = row[id_idx] if id_idx is not None else None
        name = row[name_idx] if name_idx is not None else None
        level = row[level_idx] if level_idx is not None else None
        src = row[src_idx] if src_idx is not None else None
        dist = row[dist_idx] if dist_idx is not None else None
        
        if oid is None or str(oid).strip() == "":
            null_ids += 1
        else:
            id_counter[str(oid).strip()] += 1
            
        if name is None or str(name).strip() == "":
            null_names += 1
            
        if level:
            level_counter[str(level).strip()] += 1
        if src:
            src_counter[str(src).strip()] += 1
        if dist:
            dist_counter[str(dist).strip()] += 1

    wb.close()
    
    unique_ids = len(id_counter)
    dupe_ids = {k: v for k, v in id_counter.items() if v > 1}
    
    print(f"\n[EXCEL VALIDATION SUMMARY]")
    print(f"  Total records: {total_count:,}")
    print(f"  Unique Official IDs: {unique_ids:,}")
    print(f"  Null Official IDs: {null_ids:,}")
    print(f"  Duplicate Official IDs: {len(dupe_ids):,}")
    print(f"  Null Institution Names: {null_names:,}")
    
    print(f"\n  [Breakdown by Education Level]:")
    for k, v in level_counter.most_common():
        print(f"    - {k}: {v:,}")
        
    print(f"\n  [Breakdown by Source Database]:")
    for k, v in src_counter.most_common():
        print(f"    - {k}: {v:,}")
        
    print(f"\n  Districts represented: {len(dist_counter)} districts")
    print(f"  Sample top districts: {dist_counter.most_common(5)}")

def validate_db():
    db_path = BASE / "data" / "processed" / "education_master.db"
    if not db_path.exists():
        print(f"[FAIL] {db_path} does not exist!")
        return
    print(f"\n[SQLITE] Querying {db_path.name}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM institutions WHERE lower(state) = 'telangana'")
    tg_cnt = cur.fetchone()[0]
    print(f"  Telangana records in DB: {tg_cnt:,}")
    
    cur.execute("""
        SELECT source_database, count(*) 
        FROM institutions 
        WHERE lower(state) = 'telangana'
        GROUP BY source_database 
        ORDER BY count(*) DESC
    """)
    print("  Telangana DB sources:")
    for s, c in cur.fetchall():
        print(f"    - {s}: {c:,}")
        
    cur.execute("""
        SELECT official_institution_id, count(*) 
        FROM institutions 
        WHERE lower(state) = 'telangana' AND official_institution_id IS NOT NULL AND official_institution_id != ''
        GROUP BY official_institution_id 
        HAVING count(*) > 1
    """)
    db_dupes = cur.fetchall()
    print(f"  Duplicate official IDs in Telangana DB slice: {len(db_dupes)}")
    conn.close()

if __name__ == "__main__":
    validate_excel()
    validate_db()
