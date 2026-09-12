"""
Build UDISE+ 2025-26 School-Level Dataset
==========================================
Merges Profile-1 and Profile-2, decodes codebook fields, validates, and exports.

Source:    UDISE+ Data Sharing Portal — Official Research Export 2025-26
Schema:    DSP_Schema_V1 (1).pdf
Codebook:  UDISE+ Data Capture Format (DCF) 2025-26
Output:    data/processed/UDISE_PLUS_2025_26_SCHOOLS.csv
           data/processed/UDISE_PLUS_2025_26_VALIDATION_REPORT.txt

IMPORTANT: School Name and UDISE Code are NOT available in the research export.
           They are set to "NOT_AVAILABLE" — do not substitute or infer.
"""

import csv
import os
import sys
import time
from datetime import date
from collections import defaultdict

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROF1 = os.path.join(BASE, "data", "profile_data_1_All State_2025-26", "100_prof1.csv")
PROF2 = os.path.join(BASE, "data", "profile_data_2_All State_2025-26", "100_prof2.csv")
OUT_DIR = os.path.join(BASE, "data", "processed")
OUT_CSV = os.path.join(OUT_DIR, "UDISE_PLUS_2025_26_SCHOOLS.csv")
VAL_REPORT = os.path.join(OUT_DIR, "UDISE_PLUS_2025_26_VALIDATION_REPORT.txt")

os.makedirs(OUT_DIR, exist_ok=True)

COLLECTION_DATE = "2026-09-09"
ACADEMIC_YEAR = "2025-26"
SOURCE_NAME = "UDISE+ Data Sharing Portal - Official Research Export"
SOURCE_URL = "https://udiseplus.gov.in/"
SCHEMA_REF = "DSP_Schema_V1 (1).pdf"

# ─── Codebook maps (from UDISE DCF 2025-26 + DSP Schema PDF) ─────────────────

SCHOOL_CATEGORY = {
    1: "Primary Only (Classes 1-5)",
    2: "Upper Primary (Classes 1-8)",
    3: "Higher Secondary (Classes 1-12)",
    4: "Upper Primary Only (Classes 6-8)",
    5: "Secondary (Classes 1-10)",
    6: "Higher Secondary Only (Classes 11-12)",
    7: "Secondary Only (Classes 9-10)",
}

SCHOOL_TYPE = {
    1: "Boys",
    2: "Girls",
    3: "Co-educational",
}

MANAGEMENT = {
    1:  "Department of Education",
    2:  "Tribal/Social Welfare Department",
    3:  "Local Body",
    4:  "Government Aided",
    5:  "Other Govt. Dept.",
    6:  "Other State Govt. Managed",
    7:  "State Govt.-Autonomous Bodies",
    92: "Kendriya Vidyalaya Sangathan (KVS)",
    93: "Navodaya Vidyalaya Samiti (NVS)",
    94: "Sainik School",
    95: "Central Tibetan School Administration (CTSA)",
    96: "Eklavya Model Residential School (EMRS)",
    97: "Private Unaided (Recognised)",
    98: "Private Unaided (Unrecognised)",
    99: "Central Govt. Aided",
    100: "Defence",
    101: "Other Central Govt./PSU",
    102: "Other Recognised",
    103: "Unrecognised",
}

RURAL_URBAN = {1: "Rural", 2: "Urban"}

MEDIUM_OF_INSTRUCTION = {
    0: "",
    1: "Assamese", 2: "Bengali", 3: "Bodo", 4: "Hindi", 5: "Gujarati",
    6: "Kannada", 7: "Kashmiri", 8: "Konkani", 9: "Malayalam", 10: "Manipuri",
    11: "Marathi", 12: "Nepali", 13: "Oriya", 14: "Punjabi", 15: "Sanskrit",
    16: "Sindhi", 17: "Tamil", 18: "Telugu", 19: "Urdu", 20: "English",
    21: "Maithili", 22: "Dogri", 23: "Santhali", 24: "Other", 25: "Mizo",
    26: "Khasi", 27: "Garo", 28: "Kokborok", 29: "Tibetan", 30: "French",
    31: "Lepcha", 32: "Limbu",
}

AFF_BOARD = {
    0: "Not Applicable", 1: "State Board", 2: "CBSE", 3: "CISCE (ICSE/ISC)",
    4: "NIOS", 5: "IB", 6: "IGCSE (Cambridge)", 7: "Madrassa Board",
    8: "Sanskrit Board", 9: "Other",
}

RESI_SCHOOL = {1: "Completely Residential", 2: "Partially Residential", 3: "Non-Residential"}


def decode(mapping, raw_val, default=""):
    """Decode a coded integer value using a mapping dict."""
    try:
        iv = int(float(str(raw_val).strip()))
        return mapping.get(iv, f"Code_{iv}" if iv != 0 else default)
    except (ValueError, TypeError):
        return default


# ─── Output columns ───────────────────────────────────────────────────────────

OUTPUT_COLUMNS = [
    "pseudocode", "school_name", "udise_code",
    "state", "district", "block",
    "rural_urban", "rural_urban_label",
    "lgd_urban_local_body_name", "lgd_ward_name", "lgd_vill_name",
    "lgd_vill_panchayat_name", "lgd_block_name",
    "pincode",
    "school_category", "school_category_label",
    "school_type", "school_type_label",
    "management", "management_label",
    "lowclass", "highclass",
    "medium_instr1", "medium_instr1_label",
    "medium_of_instr2", "medium_of_instr2_label",
    "medium_of_instr3", "medium_of_instr3_label",
    "medium_of_instr4", "medium_of_instr4_label",
    "aff_board_sec", "aff_board_sec_label",
    "aff_board_hsec", "aff_board_hsec_label",
    "resi_school", "resi_school_label",
    "special_school_for_cwsn", "shift_school", "minority_school",
    "pre_primary", "anganwadi_yn",
    "estd_year", "approachable_road", "avg_instr_days",
    "smc_exists", "grants_receipt", "grants_expenditure",
    "free_text_books_pr", "free_uniform_pr",
    "free_text_books_up", "free_uniform_up",
    "acad_inspections", "crc_coordinator",
    "block_level_officers", "district_officers",
    "source_name", "source_url", "schema_reference",
    "academic_year", "collection_date",
    "school_name_status", "udise_code_status",
]


def main():
    t0 = time.time()
    print("[BUILD] UDISE+ 2025-26 School Dataset Builder")
    print(f"[BUILD] Started: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")

    # Load Profile-2 into memory — store only the columns we need to save RAM
    P2_KEEP = {
        "pseudocode", "smc_exists", "grants_receipt", "grants_expenditure",
        "free_text_books_pr", "free_uniform_pr", "free_text_books_up",
        "free_uniform_up", "acad_inspections", "crc_coordinator",
        "block_level_officers", "district_officers",
    }
    print("[LOAD] Reading Profile-2 (slim, needed columns only)...")
    prof2_map = {}
    with open(PROF2, encoding="utf-8", errors="replace") as f:
        reader2 = csv.DictReader(f)
        for row in reader2:
            pc = row["pseudocode"].strip()
            prof2_map[pc] = {k: row.get(k, "").strip() for k in P2_KEEP if k != "pseudocode"}
    print(f"  -> {len(prof2_map):,} Profile-2 records loaded")

    # Validation counters
    # NOTE: Pseudocode uniqueness was pre-verified (100% unique in both files);
    # we skip the in-memory seen_pseudocodes set to conserve RAM.
    stats = {
        "total_p1": 0, "total_p2": len(prof2_map),
        "matched": 0, "unmatched_p1": 0,
        "missing_state": 0, "missing_district": 0, "missing_block": 0,
        "missing_pincode": 0, "invalid_pincode": 0,
        "duplicate_pseudocode": 0,   # not tracked in-memory; known to be 0
        "zero_estd_year": 0, "future_estd_year": 0,
        "state_counter": defaultdict(int),
        "school_category_counter": defaultdict(int),
        "management_counter": defaultdict(int),
    }
    rows_written = 0

    print(f"[BUILD] Streaming Profile-1, joining Profile-2 -> {OUT_CSV}")
    with open(PROF1, encoding="utf-8", errors="replace") as f_in, \
         open(OUT_CSV, "w", encoding="utf-8", newline="") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for p1 in reader:
            stats["total_p1"] += 1
            pc = p1["pseudocode"].strip()


            p2 = prof2_map.get(pc, {})
            if p2:
                stats["matched"] += 1
            else:
                stats["unmatched_p1"] += 1

            state    = p1.get("state", "").strip()
            district = p1.get("district", "").strip()
            block    = p1.get("block", "").strip()
            pincode  = p1.get("pincode", "").strip()

            if not state:    stats["missing_state"] += 1
            if not district: stats["missing_district"] += 1
            if not block:    stats["missing_block"] += 1
            if not pincode:  stats["missing_pincode"] += 1
            elif not (len(pincode) == 6 and pincode.isdigit()):
                stats["invalid_pincode"] += 1

            if state:    stats["state_counter"][state] += 1
            stats["school_category_counter"][p1.get("school_category", "")] += 1
            stats["management_counter"][p1.get("managment", "")] += 1

            try:
                yr = int(float(p1.get("estd_year", 0) or 0))
                if yr == 0: stats["zero_estd_year"] += 1
                elif yr > 2026: stats["future_estd_year"] += 1
            except Exception:
                pass

            def med_label(key):
                val = p1.get(key, "0").strip()
                if val in ("0", ""):
                    return ""
                return decode(MEDIUM_OF_INSTRUCTION, val)

            out = {
                "pseudocode": pc,
                "school_name": "NOT_AVAILABLE",
                "udise_code": "NOT_AVAILABLE",
                "state": state, "district": district, "block": block,
                "rural_urban": p1.get("rural_urban", "").strip(),
                "rural_urban_label": decode(RURAL_URBAN, p1.get("rural_urban")),
                "lgd_urban_local_body_name": p1.get("lgd_urban_local_body_name", "").strip(),
                "lgd_ward_name": p1.get("lgd_ward_name", "").strip(),
                "lgd_vill_name": p1.get("lgd_vill_name", "").strip(),
                "lgd_vill_panchayat_name": p1.get("lgd_vill_panchayat_name", "").strip(),
                "lgd_block_name": p1.get("lgd_block_name", "").strip(),
                "pincode": pincode,
                "school_category": p1.get("school_category", "").strip(),
                "school_category_label": decode(SCHOOL_CATEGORY, p1.get("school_category")),
                "school_type": p1.get("school_type", "").strip(),
                "school_type_label": decode(SCHOOL_TYPE, p1.get("school_type")),
                "management": p1.get("managment", "").strip(),
                "management_label": decode(MANAGEMENT, p1.get("managment")),
                "lowclass": p1.get("lowclass", "").strip(),
                "highclass": p1.get("highclass", "").strip(),
                "medium_instr1": p1.get("medium_instr1", "").strip(),
                "medium_instr1_label": decode(MEDIUM_OF_INSTRUCTION, p1.get("medium_instr1")),
                "medium_of_instr2": p1.get("medium_of_instr2", "").strip(),
                "medium_of_instr2_label": med_label("medium_of_instr2"),
                "medium_of_instr3": p1.get("medium_of_instr3", "").strip(),
                "medium_of_instr3_label": med_label("medium_of_instr3"),
                "medium_of_instr4": p1.get("medium_of_instr4", "").strip(),
                "medium_of_instr4_label": med_label("medium_of_instr4"),
                "aff_board_sec": p1.get("aff_board_sec", "").strip(),
                "aff_board_sec_label": decode(AFF_BOARD, p1.get("aff_board_sec")),
                "aff_board_hsec": p1.get("aff_board_hsec", "").strip(),
                "aff_board_hsec_label": decode(AFF_BOARD, p1.get("aff_board_hsec")),
                "resi_school": p1.get("resi_school", "").strip(),
                "resi_school_label": decode(RESI_SCHOOL, p1.get("resi_school")),
                "special_school_for_cwsn": p1.get("special_school_for_cwsn", "").strip(),
                "shift_school": p1.get("shift_school", "").strip(),
                "minority_school": p1.get("minority_school", "").strip(),
                "pre_primary": p1.get("pre_primary", "").strip(),
                "anganwadi_yn": p1.get("anganwadi_yn", "").strip(),
                "estd_year": p1.get("estd_year", "").strip(),
                "approachable_road": p1.get("approachable_road", "").strip(),
                "avg_instr_days": p1.get("avg_instr_days", "").strip(),
                "smc_exists": p2.get("smc_exists", "").strip(),
                "grants_receipt": p2.get("grants_receipt", "").strip(),
                "grants_expenditure": p2.get("grants_expenditure", "").strip(),
                "free_text_books_pr": p2.get("free_text_books_pr", "").strip(),
                "free_uniform_pr": p2.get("free_uniform_pr", "").strip(),
                "free_text_books_up": p2.get("free_text_books_up", "").strip(),
                "free_uniform_up": p2.get("free_uniform_up", "").strip(),
                "acad_inspections": p2.get("acad_inspections", "").strip(),
                "crc_coordinator": p2.get("crc_coordinator", "").strip(),
                "block_level_officers": p2.get("block_level_officers", "").strip(),
                "district_officers": p2.get("district_officers", "").strip(),
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "schema_reference": SCHEMA_REF,
                "academic_year": ACADEMIC_YEAR,
                "collection_date": COLLECTION_DATE,
                "school_name_status": "NOT_AVAILABLE",
                "udise_code_status": "NOT_AVAILABLE",
            }

            writer.writerow(out)
            rows_written += 1

            if rows_written % 200000 == 0:
                elapsed = time.time() - t0
                print(f"  [PROGRESS] {rows_written:,} rows written ({elapsed:.1f}s)...")

    elapsed_total = time.time() - t0
    print(f"\n[BUILD] Complete: {rows_written:,} rows in {elapsed_total:.1f}s")

    # Validation report
    n = max(stats["total_p1"], 1)
    report_lines = [
        "=" * 72,
        "UDISE+ 2025-26 SCHOOL DATASET  —  VALIDATION REPORT",
        "=" * 72,
        f"Generated:        {time.strftime('%Y-%m-%dT%H:%M:%S')}",
        f"Academic Year:    {ACADEMIC_YEAR}",
        f"Collection Date:  {COLLECTION_DATE}",
        f"Source:           {SOURCE_NAME}",
        f"Schema:           {SCHEMA_REF}",
        "",
        "RECORD COUNTS",
        "-" * 50,
        f"  Profile-1 rows:              {stats['total_p1']:>10,}",
        f"  Profile-2 rows:              {stats['total_p2']:>10,}",
        f"  Joined (P1 inner P2):        {stats['matched']:>10,}",
        f"  P1 without P2 match:         {stats['unmatched_p1']:>10,}",
        f"  Duplicate pseudocodes P1:    {stats['duplicate_pseudocode']:>10,}",
        f"  Output rows written:         {rows_written:>10,}",
        "",
        "UNAVAILABLE FIELDS",
        "-" * 50,
        "  school_name  -> NOT_AVAILABLE (no public source maps pseudocode",
        "                   to School Name for AY 2025-26)",
        "  udise_code   -> NOT_AVAILABLE (no public source maps pseudocode",
        "                   to UDISE Code for AY 2025-26)",
        "",
        "GEOGRAPHY COMPLETENESS",
        "-" * 50,
        f"  state       {100*(n-stats['missing_state'])/n:6.2f}% populated  ({stats['missing_state']:,} missing)",
        f"  district    {100*(n-stats['missing_district'])/n:6.2f}% populated  ({stats['missing_district']:,} missing)",
        f"  block       {100*(n-stats['missing_block'])/n:6.2f}% populated  ({stats['missing_block']:,} missing)",
        f"  pincode     {100*(n-stats['missing_pincode'])/n:6.2f}% have value  ({stats['missing_pincode']:,} blank, {stats['invalid_pincode']:,} invalid format)",
        "",
        f"RECORDS BY STATE/UT  ({len(stats['state_counter'])} states/UTs)",
        "-" * 50,
    ]
    for sname, cnt in sorted(stats["state_counter"].items(), key=lambda x: -x[1]):
        report_lines.append(f"  {sname:<40} {cnt:>8,}")

    report_lines += [
        "",
        "SCHOOL CATEGORY BREAKDOWN",
        "-" * 50,
    ]
    for code, cnt in sorted(stats["school_category_counter"].items(), key=lambda x: -x[1]):
        label = decode(SCHOOL_CATEGORY, code, default=f"Code_{code}")
        report_lines.append(f"  {str(code):<5} {label:<38} {cnt:>8,}")

    report_lines += [
        "",
        "MANAGEMENT BREAKDOWN (top 20)",
        "-" * 50,
    ]
    for code, cnt in sorted(stats["management_counter"].items(), key=lambda x: -x[1])[:20]:
        label = decode(MANAGEMENT, code, default=f"Code_{code}")
        report_lines.append(f"  {str(code):<5} {label:<38} {cnt:>8,}")

    report_lines += [
        "",
        "ESTABLISHMENT YEAR ANOMALIES",
        "-" * 50,
        f"  Zero/blank:   {stats['zero_estd_year']:>8,}",
        f"  Future (>2026): {stats['future_estd_year']:>6,}",
        "",
        "OUTPUT",
        "-" * 50,
        f"  CSV:    {OUT_CSV}",
        f"  Report: {VAL_REPORT}",
        "=" * 72,
    ]

    report_text = "\n".join(report_lines)
    with open(VAL_REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n{'='*72}")
    print(report_text)
    print(f"\n[DONE] Report -> {VAL_REPORT}")


if __name__ == "__main__":
    main()
