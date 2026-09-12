import openpyxl
import sqlite3
import pandas as pd
from pathlib import Path
from collections import Counter

BASE = Path("data")

def audit_sources():
    print("=" * 80)
    print("DETAILED SOURCE-BY-SOURCE AUDIT FOR 12 REGULATORY SOURCES")
    print("=" * 80)
    
    sources = [
        ("AISHE", BASE / "AISHE_INSTITUTIONS_2022_23.xlsx", "AISHE_Code", "2022-23"),
        ("AICTE", None, "AICTE_Permanent_ID", "2024-25"),
        ("NCTE", BASE / "NCTE_INSTITUTIONS_2025.xlsx", "NCTE_ID", "2025"),
        ("INC", BASE / "INC_INSTITUTIONS_2025.xlsx", "INC_Code", "2025"),
        ("PCI", BASE / "PCI_INSTITUTIONS_2025.xlsx", "PCI_Code", "2025"),
        ("BCI", BASE / "BCI_INSTITUTIONS_2025.xlsx", "BCI_Centre_Code", "2025"),
        ("CoA", BASE / "COA_INSTITUTIONS_2025.xlsx", "Official_ID", "2025-26"),
        ("RCI", BASE / "RCI_INSTITUTIONS_2025.xlsx", "Official_ID", "2025"),
        ("NCH", BASE / "NCH_INSTITUTIONS_2025.xlsx", "NCH_Permit_No", "2025"),
        ("DGT/NCVT", BASE / "NCVT_ITI_INSTITUTIONS_2025.xlsx", "MIS_Code", "2025"),
        ("CBSE SARAS", BASE / "CBSE_INSTITUTIONS_2025.xlsx", "Official_ID", "2025-26"),
        ("CISCE", BASE / "CISCE_INSTITUTIONS_2025.xlsx", "Official_ID", "2025"),
    ]
    
    results = []
    
    for name, fpath, id_col, year in sources:
        if fpath and fpath.exists():
            wb = openpyxl.load_workbook(fpath, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            wb.close()
            
            if len(rows) > 1:
                headers = [str(h).strip() for h in rows[0]]
                h_map = {h: i for i, h in enumerate(headers)}
                
                records_cnt = len(rows) - 1
                
                # Check IDs
                id_idx = h_map.get(id_col)
                if id_idx is None:
                    # try alternative
                    for h, i in h_map.items():
                        if "id" in h.lower() or "code" in h.lower():
                            id_idx = i
                            break
                            
                ids = [str(r[id_idx]).strip() for r in rows[1:] if id_idx is not None and r[id_idx] is not None and str(r[id_idx]).strip() != ""]
                uniq_ids = len(set(ids))
                dupes = records_cnt - uniq_ids
                
                # Check states
                st_idx = h_map.get("State")
                if st_idx is not None:
                    states = set(str(r[st_idx]).strip() for r in rows[1:] if r[st_idx] is not None and str(r[st_idx]).strip() != "")
                    states_cnt = len(states)
                else:
                    states_cnt = 0
                    
                results.append({
                    "Source": name,
                    "Extracted": records_cnt,
                    "Unique": uniq_ids,
                    "Dupes": dupes,
                    "States": states_cnt,
                    "Official_ID": id_col,
                    "Year": year,
                    "File": fpath.name
                })
            else:
                results.append({
                    "Source": name,
                    "Extracted": 0,
                    "Unique": 0,
                    "Dupes": 0,
                    "States": 0,
                    "Official_ID": id_col,
                    "Year": year,
                    "File": fpath.name
                })
        else:
            results.append({
                "Source": name,
                "Extracted": 0,
                "Unique": 0,
                "Dupes": 0,
                "States": 0,
                "Official_ID": id_col,
                "Year": year,
                "File": "N/A"
            })
            
    df = pd.DataFrame(results)
    print(df.to_string(index=False))

def audit_udise_mapping():
    print("\n" + "=" * 80)
    print("UDISE+ PSEUDOCODE MAPPING STATUS AUDIT")
    print("=" * 80)
    csv_p = BASE / "UDISE_2025_26_PSEUDOCODE_MAPPING.csv"
    if csv_p.exists():
        df = pd.read_csv(csv_p)
        print(f"Total mapped rows in CSV: {len(df)}")
        print("\nMatch Status Counts:")
        status_counts = df['Match_Status'].value_counts()
        print(status_counts)
        
        exact_cnt = len(df[df['Match_Status'] == 'EXACT'])
        unmatched_cnt = len(df[df['Match_Status'] == 'UNMATCHED'])
        probable_cnt = len(df[df['Match_Status'] == 'PROBABLE']) if 'PROBABLE' in df['Match_Status'].values else 0
        ambiguous_cnt = len(df[df['Match_Status'] == 'AMBIGUOUS']) if 'AMBIGUOUS' in df['Match_Status'].values else 0
        
        print(f"\nBreakdown:")
        print(f"  EXACT      : {exact_cnt}")
        print(f"  PROBABLE   : {probable_cnt}")
        print(f"  AMBIGUOUS  : {ambiguous_cnt}")
        print(f"  UNMATCHED  : {unmatched_cnt}")
        print(f"  Total Probe: {len(df)}")
    else:
        print("CSV not found!")

if __name__ == "__main__":
    audit_sources()
    audit_udise_mapping()
