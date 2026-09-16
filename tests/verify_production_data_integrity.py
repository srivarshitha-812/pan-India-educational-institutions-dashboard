import json
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def verify_all():
    print("=" * 70)
    print("PRE-DEPLOYMENT PRODUCTION DATA INTEGRITY VERIFICATION")
    print("=" * 70)
    
    # 1. Final Institute Lists
    final_dir = BASE_DIR / "Final Institute Lists"
    expected_counts = {
        "Welcome to UGC, New Delhi, India.xlsx": 1301,
        "Medical Colleges.xlsx": 919,
        "Nursing Colleges.xlsx": 3633,
        "Architecture Colleges.xlsx": 404,
        "Rehabilitation Colleges.xlsx": 1055,
        "Ayurveda Colleges.xlsx": 650,
        "Homoeopathy Colleges.xlsx": 299,
        "Law Colleges.xlsx": 3074,
        "Pharmacy Colleges.xlsx": 6664,
        "Dental Colleges.xlsx": 330,
        "NCTE Teacher Education Colleges.xlsx": 17556,
    }
    
    total_final = 0
    print("\n--- 1. FINAL INSTITUTE LISTS ---")
    for fname, exp_count in expected_counts.items():
        fpath = final_dir / fname
        assert fpath.exists(), f"Missing Final List: {fname}"
        if "welcome to ugc" in fname.lower():
            df = pd.read_excel(fpath, skiprows=1)
        elif "ayurveda" in fname.lower():
            df = pd.read_excel(fpath, sheet_name="Combined")
        elif "dental" in fname.lower():
            df = pd.read_excel(fpath, sheet_name="Dental Colleges", skiprows=1)
        elif "ncte" in fname.lower():
            df = pd.read_excel(fpath, sheet_name="Institutions Roster")
        elif "homoeopathy" in fname.lower():
            df = pd.read_excel(fpath, skiprows=2)
        else:
            df = pd.read_excel(fpath)
        actual = len(df)
        print(f"  [OK] {fname:<40}: {actual:>5} records (Expected: {exp_count})")
        assert actual == exp_count, f"Count mismatch for {fname}: got {actual}, expected {exp_count}"
        total_final += actual
        
    print(f"  TOTAL RECORDS ACROSS FINAL LISTS: {total_final:>5} (Expected: 35,885)")
    assert total_final == 35885, f"Total mismatch: got {total_final}, expected 35885"
    
    # 2. UDISE+ Dataset
    print("\n--- 2. UDISE+ MASTER DATASET ---")
    udise_csv = BASE_DIR / "data" / "processed" / "UDISE_PLUS_2025_26_SCHOOLS.csv"
    assert udise_csv.exists(), "Missing UDISE+ CSV file"
    # Count lines efficiently without loading 640MB into pandas
    with open(udise_csv, "r", encoding="utf-8-sig") as f:
        udise_lines = sum(1 for _ in f) - 1 # exclude header
    print(f"  [OK] UDISE+ Schools CSV                 : {udise_lines:>10,} records (Expected: 1,466,682)")
    assert udise_lines == 1466682, f"UDISE+ count mismatch: got {udise_lines}, expected 1,466,682"
    
    # 3. Data Dictionary
    print("\n--- 3. DATA DICTIONARY ---")
    dict_json = BASE_DIR / "data" / "data_dictionary.json"
    dict_xlsx = BASE_DIR / "DATA_DICTIONARY.xlsx"
    assert dict_json.exists(), "Missing data_dictionary.json"
    assert dict_xlsx.exists(), "Missing DATA_DICTIONARY.xlsx"
    with open(dict_json, "r", encoding="utf-8") as f:
        ddata = json.load(f)
    field_count = ddata.get("total_fields", len(ddata.get("records", [])))
    print(f"  [OK] Data Dictionary documented fields : {field_count:>5} fields (Expected: >= 148)")
    assert field_count >= 148, f"Data Dictionary count mismatch: got {field_count}, expected >= 148"
    
    # 4. Database Integrity
    print("\n--- 4. PROCESSED SQLITE DATABASE ---")
    db_path = BASE_DIR / "data" / "processed" / "education_master.db"
    assert db_path.exists(), "Missing education_master.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  [OK] SQLite Database Tables             : {', '.join(tables)}")
    for tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
        cnt = cur.fetchone()[0]
        print(f"       - Table `{tbl}`: {cnt:,} rows")
    conn.close()
    
    print("\n" + "=" * 70)
    print(">>> ALL PRE-DEPLOYMENT DATA INTEGRITY CHECKS PASSED 100%! <<<")
    print("=" * 70)

if __name__ == "__main__":
    verify_all()
