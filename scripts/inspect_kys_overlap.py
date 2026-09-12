import sqlite3
import openpyxl
from pathlib import Path

def inspect_kys():
    conn = sqlite3.connect("data/processed/education_master.db")
    c = conn.cursor()
    
    rows = c.execute("SELECT institution_id, official_institution_id, name, education_level, district FROM pan_india_census WHERE source_database LIKE '%Know Your School%'").fetchall()
    print(f"Total KYS rows in pan_india_census: {len(rows)}")
    for r in rows[:10]:
        print(" ", r)
        
    # Check if these official_institution_ids exist in the 42,834 portal schools
    portal_ids = set(r[0] for r in c.execute("SELECT official_institution_id FROM pan_india_census WHERE source_database = 'UDISE+ / Telangana School Education Portal'").fetchall())
    print(f"Total portal schools official_institution_ids: {len(portal_ids)}")
    
    in_portal = [r for r in rows if r[1] in portal_ids]
    not_in_portal = [r for r in rows if r[1] not in portal_ids]
    print(f"KYS records whose official_institution_id ALREADY EXISTS in portal schools: {len(in_portal)}")
    print(f"KYS records whose official_institution_id is NOT in portal schools: {len(not_in_portal)}")
    
    conn.close()

if __name__ == "__main__":
    inspect_kys()
