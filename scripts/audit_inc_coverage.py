#!/usr/bin/env python3
"""
Comprehensive Audit of INC National Extraction:
1. Verifies 7,044 programme rows -> 3,578 unique institutions.
2. Audits the deduplication key definition.
3. Checks state-by-state metrics, page counts, completion verification.
4. Checks district query coverage (did --Select-- query ALL districts?).
5. Flags unusually low/high states.
6. Investigates address vs name deduplication variations.
"""

import os
import re
import csv
import json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "inc"
PROG_CSV = RAW_DIR / "INC_National_Programmes_2025-26.csv"
INST_CSV = RAW_DIR / "INC_National_Institutions_Deduplicated_2025-26.csv"
CP_FILE = RAW_DIR / "inc_checkpoint.json"
TASK_LOG = Path(os.environ.get("TASK_LOG", ""))

def audit():
    print("=" * 90)
    print("INC INDEPENDENT COVERAGE & DEDUPLICATION AUDIT")
    print("=" * 90)

    # 1. Read Raw Programme Rows
    with open(PROG_CSV, "r", encoding="utf-8-sig") as f:
        progs = list(csv.DictReader(f))
    print(f"1. Total Raw Programme Rows Loaded: {len(progs)}")

    # 2. Read Institutions CSV
    with open(INST_CSV, "r", encoding="utf-8-sig") as f:
        insts = list(csv.DictReader(f))
    print(f"2. Total Deduplicated Institutions Loaded: {len(insts)}")

    # 3. Verify Pagination & Completion from Task Log
    print("\n3. Pagination & End-of-Report Verification from Log:")
    log_text = TASK_LOG.read_text(encoding="utf-8", errors="ignore") if TASK_LOG.exists() else ""
    
    with open(CP_FILE, "r", encoding="utf-8") as f:
        cp = json.load(f)

    all_done = True
    state_audit_rows = []
    
    for st, info in cp["completed_states"].items():
        pages = info["pages"]
        p_count = info["programme_rows"]
        u_count = info["unique_institutions"]
        
        # Look for the exact done line or total pages reached line in the log
        total_p_reached = f"[{st}] Reached total pages: {pages} of {pages}" in log_text
        done_pattern = f"[{st}] Done: {pages} pages, {p_count} programme rows" in log_text
        pilot_done = (st == "Delhi" and info.get("source") == "Validated Pilot")
        verified = (total_p_reached or done_pattern or pilot_done)
        
        if not verified:
            all_done = False
            
        state_audit_rows.append({
            "state": st,
            "pages": pages,
            "programmes": p_count,
            "institutions": u_count,
            "avg_prog_per_inst": round(p_count / u_count, 2) if u_count > 0 else 0,
            "log_verified": verified
        })

    print(f"   Total States Checked in Log: {len(state_audit_rows)}")
    print(f"   All States Pagination Fully Completed: {all_done}")

    # 4. Deduplication Key Deep Dive
    print("\n4. Deduplication Integrity & Granularity Check:")
    # Check key formula: f"{state}|{dist}|{name_norm}"
    # What if we deduplicate by State + District + Full Address?
    addr_map = defaultdict(list)
    name_map = defaultdict(list)
    key_map = defaultdict(list)

    for p in progs:
        st = p.get("state", "").strip()
        dist = p.get("district_name", "").strip()
        name_raw = p.get("institution_name_raw", "").strip()
        addr_raw = p.get("institution_address_raw", "").strip()
        
        name_norm = re.sub(r"\s+", " ", name_raw.upper())
        addr_norm = re.sub(r"\s+", " ", addr_raw.upper())
        
        key = f"{st}|{dist}|{name_norm}"
        addr_key = f"{st}|{dist}|{addr_norm}"
        
        key_map[key].append(p)
        addr_map[addr_key].append(p)
        name_map[f"{st}|{name_norm}"].append(p)

    print(f"   - Unique keys via State + District + Name: {len(key_map)}")
    print(f"   - Unique keys via State + District + Full Address: {len(addr_map)}")
    print(f"   - Unique keys via State + Name (ignoring District): {len(name_map)}")

    # Check if any address key splits what name merged or vice versa
    diff_addr_vs_name = len(addr_map) - len(key_map)
    print(f"   - Difference between Full Address vs Name: {diff_addr_vs_name} (Addr: {len(addr_map)} vs Key: {len(key_map)})")

    # 5. Check District Coverage in --Select-- Query
    print("\n5. District Coverage Verification:")
    dists_per_state = defaultdict(set)
    for p in progs:
        st = p.get("state", "").strip()
        d = p.get("district_name", "").strip()
        if d:
            dists_per_state[st].add(d)

    total_dists = sum(len(d) for d in dists_per_state.values())
    print(f"   Total Distinct Districts Extracted across India: {total_dists}")
    print(f"   Sample: Karnataka has {len(dists_per_state['Karnataka'])} districts, UP has {len(dists_per_state['Uttar Pradesh'])} districts, Maharashtra has {len(dists_per_state['Maharashtra'])} districts, Tamil Nadu has {len(dists_per_state['Tamilnadu'])} districts.")

    # 6. Flag Unusually Low / High States
    print("\n6. State Distribution Analysis (Sorted by Institution Count):")
    state_audit_rows.sort(key=lambda x: x["institutions"], reverse=True)
    for r in state_audit_rows:
        flag = ""
        if r["institutions"] == 0:
            flag = " [ZERO INSTITUTES]"
        elif r["institutions"] < 5:
            flag = " [VERY LOW UT/STATE]"
        elif r["institutions"] > 300:
            flag = " [HIGH VOLUME]"
        print(f"   {r['state']:<25} | Progs: {r['programmes']:>4} | Insts: {r['institutions']:>4} | Pages: {r['pages']:>2} | Avg Prog/Inst: {r['avg_prog_per_inst']:>4.2f}{flag}")

if __name__ == "__main__":
    audit()
