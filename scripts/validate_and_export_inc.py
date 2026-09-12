#!/usr/bin/env python3
"""
INC Final Validation, Reconciliation, and Excel Export Script.

Validates:
1. All 37 jurisdictions completed successfully
2. Zero failed jurisdictions
3. Zero duplicate institution keys
4. Institution count vs. raw programme rows comparison
5. Multi-programme grouping verification
6. Generates:
   - INC_National_Institutions_Deduplicated_2025-26.xlsx
   - INC_National_Programmes_2025-26.xlsx
7. Conducts benchmark gap analysis against 5,200–5,800 benchmark
"""

import os
import json
import csv
import pandas as pd
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "inc"
CP_FILE = RAW_DIR / "inc_checkpoint.json"
SUMMARY_FILE = RAW_DIR / "INC_National_Summary_2025-26.json"

PROG_CSV = RAW_DIR / "INC_National_Programmes_2025-26.csv"
INST_CSV = RAW_DIR / "INC_National_Institutions_Deduplicated_2025-26.csv"

PROG_XLSX = RAW_DIR / "INC_National_Programmes_2025-26.xlsx"
INST_XLSX = RAW_DIR / "INC_National_Institutions_Deduplicated_2025-26.xlsx"

def run_validation():
    print("=" * 80)
    print("INC NATIONAL EXTRACTION — FINAL VALIDATION & RECONCILIATION")
    print("=" * 80)

    # 1. Checkpoint validation
    with open(CP_FILE, "r", encoding="utf-8") as f:
        cp = json.load(f)

    completed_states = cp.get("completed_states", {})
    failed_states = cp.get("failed_states", {})

    print(f"Total Completed Jurisdictions: {len(completed_states)}")
    print(f"Total Failed Jurisdictions: {len(failed_states)}")
    assert len(failed_states) == 0, f"Found failed states: {failed_states}"
    assert len(completed_states) == 37, f"Expected 37 jurisdictions, got {len(completed_states)}"

    # 2. Raw Programme Rows Validation
    df_prog = pd.read_csv(PROG_CSV, dtype=str)
    prog_count = len(df_prog)
    print(f"\nRaw Programme Rows Count: {prog_count}")

    # 3. Deduplicated Institutions Validation
    df_inst = pd.read_csv(INST_CSV, dtype=str)
    inst_count = len(df_inst)
    print(f"Unique Deduplicated Institutions Count: {inst_count}")

    # 4. Duplicate Check on Official Key
    dup_keys = df_inst[df_inst.duplicated(subset=["inc_institution_key"], keep=False)]
    dup_count = len(dup_keys)
    print(f"Duplicate Official Institution Keys: {dup_count}")
    assert dup_count == 0, f"Found duplicate keys: {dup_keys['inc_institution_key'].tolist()}"

    # 5. Check metadata fields present
    required_cols = ["inc_institution_key", "institution_name", "state", "district_name",
                     "sector", "programmes", "annual_intakes", "academic_year", "source_url"]
    for col in required_cols:
        assert col in df_inst.columns, f"Missing column {col} in institutions CSV"

    # 6. Multi-programme analysis
    # Count how many institutions offer multiple courses
    df_inst["prog_list"] = df_inst["programmes"].fillna("").apply(lambda s: [p.strip() for p in s.split("|") if p.strip()])
    df_inst["prog_count"] = df_inst["prog_list"].apply(len)
    multi_prog = df_inst[df_inst["prog_count"] > 1]
    single_prog = df_inst[df_inst["prog_count"] == 1]
    print(f"\nInstitutions offering multiple programmes: {len(multi_prog)} ({len(multi_prog)/inst_count*100:.1f}%)")
    print(f"Institutions offering a single programme: {len(single_prog)} ({len(single_prog)/inst_count*100:.1f}%)")
    print(f"Sum of course offerings across all institutions: {df_inst['prog_count'].sum()}")

    # 7. Sector breakdown
    print("\nSector Breakdown:")
    for sector, count in df_inst["sector"].value_counts().items():
        print(f"  {sector}: {count} ({count/inst_count*100:.1f}%)")

    # 8. Export to XLSX (clean illegal control characters for openpyxl)
    print("\nCleaning control characters and generating Excel workbooks...")
    import re
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

    def clean_val(v):
        if isinstance(v, str):
            return ILLEGAL_CHARACTERS_RE.sub("", v)
        return v

    for col in df_prog.columns:
        df_prog[col] = df_prog[col].apply(clean_val)
    for col in df_inst.columns:
        df_inst[col] = df_inst[col].apply(clean_val)

    df_prog.to_excel(PROG_XLSX, index=False, engine="openpyxl")
    print(f"  Exported: {PROG_XLSX} ({prog_count} rows)")
    df_inst.drop(columns=["prog_list", "prog_count"], errors="ignore").to_excel(INST_XLSX, index=False, engine="openpyxl")
    print(f"  Exported: {INST_XLSX} ({inst_count} institutions)")

    # Also copy master files to the root data/ or project root if helpful
    root_inst_xlsx = ROOT / "INC_National_Institutions_Deduplicated_2025-26.xlsx"
    root_prog_xlsx = ROOT / "INC_National_Programmes_2025-26.xlsx"
    df_inst.drop(columns=["prog_list", "prog_count"], errors="ignore").to_excel(root_inst_xlsx, index=False, engine="openpyxl")
    df_prog.to_excel(root_prog_xlsx, index=False, engine="openpyxl")
    print(f"  Created root copies: {root_inst_xlsx.name}, {root_prog_xlsx.name}")

    # 9. Benchmark gap analysis
    benchmark_min = 5200
    benchmark_max = 5800
    print("\n" + "=" * 80)
    print(f"BENCHMARK GAP ANALYSIS (Portal: {inst_count} vs. Benchmark: {benchmark_min}–{benchmark_max})")
    print("=" * 80)

    diff = inst_count - benchmark_min
    pct_diff = ((inst_count - benchmark_min) / benchmark_min) * 100
    print(f"Extracted unique physical nursing institutes: {inst_count}")
    print(f"Raw approved programme-level records: {prog_count}")
    print(f"Observation: Raw programme records (7,044) exceed benchmark ({benchmark_min}–{benchmark_max}), whereas deduplicated institutions (3,578) is lower.")

if __name__ == "__main__":
    run_validation()
