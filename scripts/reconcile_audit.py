import sqlite3
import pandas as pd
from pathlib import Path

def run_reconciliation():
    conn = sqlite3.connect("data/processed/education_master.db")
    c = conn.cursor()
    
    print("=" * 70)
    print("1. STRICT TELANGANA RECONCILIATION AUDIT")
    print("=" * 70)
    
    # Check all records where state = 'Telangana'
    all_tg = c.execute("SELECT institution_id, official_institution_id, source_database, education_level, name FROM institutions WHERE lower(state) = 'telangana'").fetchall()
    print(f"Total Telangana records in master: {len(all_tg)}")
    
    # Group by id prefix and source_database
    sources = {}
    for inst_id, oid, src, lvl, name in all_tg:
        key = (src, lvl)
        sources[key] = sources.get(key, 0) + 1
        
    print("\n[Telangana Breakdown by Source & Level in Current Master]:")
    for (src, lvl), count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src:<55} | {lvl:<35} : {count:>6}")
        
    # Baseline breakdown:
    # Notice: CANONICAL-SC (42,834)
    #         CANONICAL-JC (1,744)
    #         CANONICAL-ST (370)
    #         DOST / Affiliated / Universities / etc:
    
    # Check new additions that were merged from national sources:
    print("\n[Reconciling the 897 New Records in Telangana]:")
    cbse_tg = c.execute("SELECT COUNT(*) FROM institutions WHERE lower(state) = 'telangana' AND institution_id LIKE 'IND_CBSE_%'").fetchone()[0]
    cisce_tg = c.execute("SELECT COUNT(*) FROM institutions WHERE lower(state) = 'telangana' AND institution_id LIKE 'IND_CISCE_%'").fetchone()[0]
    coa_tg = c.execute("SELECT COUNT(*) FROM institutions WHERE lower(state) = 'telangana' AND institution_id LIKE 'IND_COA_%'").fetchone()[0]
    rci_tg = c.execute("SELECT COUNT(*) FROM institutions WHERE lower(state) = 'telangana' AND institution_id LIKE 'IND_RCI_%'").fetchone()[0]
    nmc_tg = c.execute("SELECT COUNT(*) FROM institutions WHERE lower(state) = 'telangana' AND institution_id LIKE 'IND_NMC_%'").fetchone()[0]
    
    print(f"  CBSE schools added (IND_CBSE_*) : {cbse_tg:>5}")
    print(f"  CISCE schools added (IND_CISCE_*): {cisce_tg:>5}")
    print(f"  CoA colleges added (IND_COA_*)  : {coa_tg:>5}")
    print(f"  RCI institutes added (IND_RCI_*): {rci_tg:>5}")
    print(f"  NMC colleges added (IND_NMC_*)  : {nmc_tg:>5}")
    total_added = cbse_tg + cisce_tg + coa_tg + rci_tg + nmc_tg
    print(f"  ----------------------------------------")
    print(f"  Total newly added records       : {total_added:>5}")
    print(f"  Expected baseline               : 46,016")
    print(f"  Expected baseline + added (46,016 + {total_added}): {46016 + total_added}")
    print(f"  Current Telangana count in DB   : {len(all_tg)}")
    print(f"  Difference                      : {len(all_tg) - (46016 + total_added)}")
    
    print("\n" + "=" * 70)
    print("2. TELANGANA SCHOOL COUNT AUDIT (42,834 vs 42,876)")
    print("=" * 70)
    portal_schools = c.execute("SELECT COUNT(*) FROM institutions WHERE source_database = 'UDISE+ / Telangana School Education Portal'").fetchone()[0]
    kys_schools = c.execute("SELECT education_level, COUNT(*), MIN(official_institution_id), MAX(official_institution_id) FROM institutions WHERE source_database = 'UDISE+ / Know Your School' GROUP BY education_level").fetchall()
    
    print(f"  UDISE+ / Telangana School Education Portal records: {portal_schools}")
    print(f"  UDISE+ / Know Your School records breakdown:")
    for lvl, cnt, min_id, max_id in kys_schools:
        print(f"    - {lvl:<25}: {cnt:>3} records (IDs: {min_id} to {max_id})")
        
    kys_hsec = c.execute("SELECT COUNT(*) FROM institutions WHERE source_database = 'UDISE+ / Know Your School' AND education_level = 'Higher Secondary'").fetchone()[0]
    print(f"  Notice: Validated portal count ({portal_schools}) + KYS Higher Secondary ({kys_hsec}) = {portal_schools + kys_hsec}")
    print(f"  Explanation: Previous report mistakenly cited 42,876 by adding the 42 KYS Higher Secondary records to the 42,834 validated baseline.")
    
    print("\n" + "=" * 70)
    print("3. GEOGRAPHIC COVERAGE & OVERSEAS AUDIT")
    print("=" * 70)
    state_counts = c.execute("SELECT state, COUNT(*) FROM institutions GROUP BY state ORDER BY COUNT(*) DESC").fetchall()
    print(f"Total distinct state labels in current DB: {len(state_counts)}")
    for st, cnt in state_counts:
        print(f"  {st:<35}: {cnt:>6}")
        
    conn.close()

if __name__ == "__main__":
    run_reconciliation()
