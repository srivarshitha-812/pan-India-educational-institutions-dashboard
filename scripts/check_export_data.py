import sqlite3
import pandas as pd
from pathlib import Path

def check():
    conn = sqlite3.connect("data/processed/education_master.db")
    c = conn.cursor()
    
    # 1. Telangana in pan_india_census
    tg_count = c.execute("SELECT COUNT(1) FROM pan_india_census WHERE state = 'Telangana'").fetchone()[0]
    tg_uniq_inst = c.execute("SELECT COUNT(DISTINCT institution_id) FROM pan_india_census WHERE state = 'Telangana'").fetchone()[0]
    tg_uniq_oid = c.execute("SELECT COUNT(DISTINCT official_institution_id) FROM pan_india_census WHERE state = 'Telangana'").fetchone()[0]
    
    print("=== TELANGANA CHECK IN pan_india_census ===")
    print(f"Total rows: {tg_count}")
    print(f"Unique institution_id: {tg_uniq_inst}")
    print(f"Unique official_institution_id: {tg_uniq_oid}")
    
    # Check source breakdown for Telangana
    sources = c.execute("SELECT source_database, COUNT(1) FROM pan_india_census WHERE state = 'Telangana' GROUP BY source_database ORDER BY COUNT(1) DESC").fetchall()
    print("\nSource Breakdown for Telangana:")
    for s, cnt in sources:
        print(f"  {s:<60}: {cnt:>6}")
        
    # Check if any KYS records exist
    kys_cnt = c.execute("SELECT COUNT(1) FROM pan_india_census WHERE state = 'Telangana' AND source_database LIKE '%Know Your School%'").fetchone()[0]
    print(f"\nKYS records in Telangana slice: {kys_cnt}")
    
    # Check if any newly added IND_NMC_ records exist
    nmc_new = c.execute("SELECT COUNT(1) FROM pan_india_census WHERE state = 'Telangana' AND institution_id LIKE 'IND_NMC_%'").fetchone()[0]
    print(f"Newly added IND_NMC_* in Telangana slice: {nmc_new}")
    
    # Check legacy medical in Telangana baseline
    med_baseline = c.execute("SELECT source_database, COUNT(1) FROM pan_india_census WHERE state = 'Telangana' AND (source_database LIKE '%Medical%' OR source_database LIKE '%KNRUHS%') GROUP BY source_database").fetchall()
    print(f"Legacy Medical in Telangana baseline: {med_baseline}")
    
    # 2. CoA Check
    coa_p = Path("data/COA_INSTITUTIONS_2025.xlsx")
    if coa_p.exists():
        df_coa = pd.read_excel(coa_p)
        print("\n=== COA CHECK ===")
        print(f"COA_INSTITUTIONS_2025.xlsx rows: {len(df_coa)}")
        print(f"Unique Official_ID: {df_coa['Official_ID'].nunique()}")
        print(f"Columns: {list(df_coa.columns)}")
        
    # 3. RCI Check
    rci_p = Path("data/RCI_INSTITUTIONS_2025.xlsx")
    if rci_p.exists():
        df_rci = pd.read_excel(rci_p)
        print("\n=== RCI CHECK ===")
        print(f"RCI_INSTITUTIONS_2025.xlsx rows: {len(df_rci)}")
        print(f"Unique Official_ID: {df_rci['Official_ID'].nunique()}")
        print(f"Columns: {list(df_rci.columns)}")
        
    conn.close()

if __name__ == "__main__":
    check()
