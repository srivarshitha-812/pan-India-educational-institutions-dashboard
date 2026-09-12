#!/usr/bin/env python3
"""
Parse official INC Statistics (as on 31st March 2025) PDF and compare
against our extracted live 2025-26 Yearly Report portal dataset (3,633 physical institutes / 7,044 courses).
"""

import re
import csv
import json
import PyPDF2
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data" / "raw" / "inc" / "Distribution_of_Nursing_Educational_institutions_31st_March_2025.pdf"
INST_CSV = ROOT / "data" / "raw" / "inc" / "INC_National_Institutions_Deduplicated_2025-26.csv"
PROG_CSV = ROOT / "data" / "raw" / "inc" / "INC_National_Programmes_2025-26.csv"

def parse_stats_pdf():
    reader = PyPDF2.PdfReader(str(PDF_PATH))
    txt = reader.pages[0].extract_text()
    
    lines = txt.split("\n")
    stats = {}
    
    # State lines pattern: State_Name followed by 20 integers (10 pairs of Instt, Seats)
    # Courses: ANM, GNM, B.Sc(N), M.Sc(N), PB B.Sc(N), PBDP, NPCC, NPM, NPM-Educator, NPETC
    for line in lines:
        line = line.strip()
        if not line or "States" in line:
            continue
        parts = line.split()
        if not parts:
            continue
        # Find where numbers start
        num_start = -1
        for idx, p in enumerate(parts):
            if p.isdigit():
                num_start = idx
                break
        if num_start != -1:
            state_name = " ".join(parts[:num_start])
            nums = [int(p) for p in parts[num_start:] if p.isdigit()]
            if len(nums) >= 6:
                stats[state_name] = {
                    "anm_inst": nums[0] if len(nums) > 0 else 0,
                    "anm_seats": nums[1] if len(nums) > 1 else 0,
                    "gnm_inst": nums[2] if len(nums) > 2 else 0,
                    "gnm_seats": nums[3] if len(nums) > 3 else 0,
                    "bsc_inst": nums[4] if len(nums) > 4 else 0,
                    "bsc_seats": nums[5] if len(nums) > 5 else 0,
                    "msc_inst": nums[6] if len(nums) > 6 else 0,
                    "msc_seats": nums[7] if len(nums) > 7 else 0,
                    "pb_bsc_inst": nums[8] if len(nums) > 8 else 0,
                    "pb_bsc_seats": nums[9] if len(nums) > 9 else 0,
                    "pbdp_inst": nums[10] if len(nums) > 10 else 0,
                    "npcc_inst": nums[12] if len(nums) > 12 else 0,
                    "total_course_units": sum(nums[i] for i in range(0, len(nums), 2)),
                    "total_seats": sum(nums[i] for i in range(1, len(nums), 2)),
                    "raw_nums": nums
                }
    return stats

def main():
    stats = parse_stats_pdf()
    print("=" * 80)
    print("OFFICIAL INC STATISTICS AS ON 31st MARCH 2025")
    print("=" * 80)
    
    gt = stats.get("Grand Total", {})
    print("NATIONAL GRAND TOTALS (from Official INC Statistics PDF):")
    print(f"  ANM:           {gt.get('anm_inst', 0):>5} institutions | {gt.get('anm_seats', 0):>7} seats")
    print(f"  GNM:           {gt.get('gnm_inst', 0):>5} institutions | {gt.get('gnm_seats', 0):>7} seats")
    print(f"  B.Sc(N):       {gt.get('bsc_inst', 0):>5} institutions | {gt.get('bsc_seats', 0):>7} seats")
    print(f"  M.Sc(N):       {gt.get('msc_inst', 0):>5} institutions | {gt.get('msc_seats', 0):>7} seats")
    print(f"  P B B.Sc(N):   {gt.get('pb_bsc_inst', 0):>5} institutions | {gt.get('pb_bsc_seats', 0):>7} seats")
    print(f"  PBDP:          {gt.get('pbdp_inst', 0):>5} institutions")
    print(f"  NPCC:          {gt.get('npcc_inst', 0):>5} institutions")
    print(f"  Total Course Units Reported by INC: {gt.get('total_course_units', 0):,}")
    print(f"  Total Approved Seats Reported by INC: {gt.get('total_seats', 0):,}")

    gnm_bsc = gt.get('gnm_inst', 0) + gt.get('bsc_inst', 0)
    anm_gnm_bsc = gt.get('anm_inst', 0) + gt.get('gnm_inst', 0) + gt.get('bsc_inst', 0)
    print(f"\nKey Combinations from INC Statistics:")
    print(f"  GNM + B.Sc(N): {gnm_bsc:,}")
    print(f"  ANM + GNM + B.Sc(N): {anm_gnm_bsc:,}")

    # Now load our live 2025-26 extracted data
    with open(PROG_CSV, "r", encoding="utf-8-sig") as f:
        live_progs = list(csv.DictReader(f))
    with open(INST_CSV, "r", encoding="utf-8-sig") as f:
        live_insts = list(csv.DictReader(f))

    print(f"\nLive 2025-26 Yearly Report Portal Extraction:")
    print(f"  Total Course Offerings on Portal: {len(live_progs):,}")
    print(f"  Total Unique Physical Institutions: {len(live_insts):,}")

    # Compare state by state
    print("\n" + "=" * 90)
    print("STATE-BY-STATE COMPARISON: INC STATS (31 MAR 2025) vs LIVE 2025-26 PORTAL")
    print("=" * 90)
    print(f"{'State':<22} | {'Stats GNM':>9} | {'Stats BSc':>9} | {'Stats Sum':>9} | {'Live Progs':>10} | {'Live PhysInst':>13}")
    print("-" * 90)
    
    # State name mapping
    name_map = {
        "Chattisgarh": "Chhattisgarh",
        "Orissa": "Orissa",
        "Uttarakhand": "Uttaranchal",
        "Pondicherry": "Pondicherry/Puducherry",
        "Tamilnadu": "Tamilnadu",
        "Jammu & Kashmir": "Jammu & kashmir"
    }

    live_progs_by_st = defaultdict(int)
    for p in live_progs:
        live_progs_by_st[p["state"]] += 1
    live_insts_by_st = defaultdict(int)
    for i in live_insts:
        live_insts_by_st[i["state"]] += 1

    comparison_data = []

    for st_name, s_data in stats.items():
        if st_name == "Grand Total":
            continue
        mapped_st = name_map.get(st_name, st_name)
        lp = live_progs_by_st.get(mapped_st, 0)
        li = live_insts_by_st.get(mapped_st, 0)
        
        gnm = s_data["gnm_inst"]
        bsc = s_data["bsc_inst"]
        tot_units = s_data["total_course_units"]
        
        print(f"{st_name:<22} | {gnm:>9} | {bsc:>9} | {tot_units:>9} | {lp:>10} | {li:>13}")
        
        comparison_data.append({
            "state_stats_name": st_name,
            "mapped_state": mapped_st,
            "stats_gnm": gnm,
            "stats_bsc": bsc,
            "stats_anm": s_data["anm_inst"],
            "stats_total_units": tot_units,
            "stats_seats": s_data["total_seats"],
            "live_programme_rows": lp,
            "live_physical_institutions": li
        })

    out_json = ROOT / "data" / "raw" / "inc" / "inc_stats_vs_live_comparison.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)
    print(f"\nSaved detailed comparison JSON -> {out_json}")

if __name__ == "__main__":
    main()
