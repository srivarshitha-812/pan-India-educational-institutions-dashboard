import sqlite3
import pandas as pd
from pathlib import Path

def main():
    db_path = Path("data/processed/education_master.db")
    if not db_path.exists():
        print("Database not found!")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    total = c.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
    unique_ids = c.execute("SELECT COUNT(DISTINCT official_institution_id) FROM institutions").fetchone()[0]
    
    print("=" * 60)
    print("PAN-INDIA MASTER CENSUS VERIFICATION AUDIT")
    print("=" * 60)
    print(f"Total Canonical Records: {total:,}")
    print(f"Unique Official IDs:    {unique_ids:,}")
    print(f"ID Uniqueness Rate:     {100.0 * unique_ids / total:.4f}%")
    print(f"Duplicate IDs:          {total - unique_ids}")
    
    col_names = [d[1] for d in c.execute("PRAGMA table_info(institutions)").fetchall()]
    print(f"Table columns: {col_names[:10]}... (total {len(col_names)})")
    
    source_col = 'source_name' if 'source_name' in col_names else ('source_system' if 'source_system' in col_names else ('source_portal' if 'source_portal' in col_names else ('source' if 'source' in col_names else None)))
    if not source_col:
        for col in col_names:
            if 'source' in col.lower() or 'portal' in col.lower():
                source_col = col
                break
    
    print(f"\n[SOURCE BREAKDOWN] (using column: {source_col})")
    if source_col:
        sources = c.execute(f"SELECT {source_col}, COUNT(*) FROM institutions GROUP BY {source_col} ORDER BY 2 DESC").fetchall()
        for s, cnt in sources:
            print(f"  {s:<25}: {cnt:>8,}")
        
    print("\n[GEOGRAPHY BREAKDOWN]")
    ts_cnt = c.execute("SELECT COUNT(*) FROM institutions WHERE state = 'Telangana'").fetchone()[0]
    other_states_cnt = total - ts_cnt
    num_states = c.execute("SELECT COUNT(DISTINCT state) FROM institutions WHERE state IS NOT NULL AND state != ''").fetchone()[0]
    print(f"  Telangana Preserved Records : {ts_cnt:>8,}")
    print(f"  Supplemented States/UTs     : {other_states_cnt:>8,}")
    print(f"  Total States/UTs Covered    : {num_states:>8}")
    
    print("\n[TOP 15 STATES/UTS BY RECORD COUNT]")
    states = c.execute("SELECT state, COUNT(*) FROM institutions GROUP BY state ORDER BY 2 DESC LIMIT 15").fetchall()
    for st, cnt in states:
        print(f"  {st:<30}: {cnt:>8,}")
        
    print("\n[FILE EXISTENCE & SIZES]")
    for p in [
        "data/processed/education_master.db",
        "data/processed/master_institutions.csv",
        "data/processed/PAN_INDIA_EDUCATIONAL_INSTITUTES.xlsx",
        "data/PAN_INDIA_SOURCE_COVERAGE_REPORT.xlsx",
        "data/PAN_INDIA_SOURCE_COVERAGE_REPORT.md",
        "data/CBSE_INSTITUTIONS_2025.xlsx",
        "data/CISCE_INSTITUTIONS_2025.xlsx",
        "data/RCI_INSTITUTIONS_2025.xlsx",
        "data/COA_INSTITUTIONS_2025.xlsx",
        "data/NMC_COURSES_2026_27.xlsx"
    ]:
        f = Path(p)
        if f.exists():
            mb = f.stat().st_size / (1024 * 1024)
            print(f"  [OK] {p:<50}: {mb:>7.2f} MB")
        else:
            print(f"  [MISSING] {p}")

if __name__ == "__main__":
    main()
