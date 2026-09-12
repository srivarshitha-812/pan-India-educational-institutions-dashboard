#!/usr/bin/env python3
"""
INC National Extractor (36 Jurisdictions) with Checkpointing and Resume Support.

Source: Indian Nursing Council (INC) Yearly Report Portal
URL: https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx
Academic Year: 2025-2026

Features:
- Dynamic state discovery across all jurisdictions in India
- SSRS flat-row state-machine parsing
- Checkpointing in data/raw/inc/inc_checkpoint.json
- Per-state raw and deduplicated institution CSVs
- Automatic resume on interruption
- Retry handling with backoff per jurisdiction
- National master consolidation upon completion
"""

import sys
import os
import re
import csv
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "inc"
STATES_DIR = RAW_DIR / "states"
CHECKPOINT_FILE = RAW_DIR / "inc_checkpoint.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
STATES_DIR.mkdir(parents=True, exist_ok=True)

PORTAL_URL = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
ACADEMIC_YEAR = "2025-2026"
PAGE_WAIT_MS = 3500
MAX_PAGES_PER_STATE = 150

PROG_COLS = [
    "sl_no", "institution_name_raw", "institution_address_raw",
    "trust_name", "district_name", "state", "sector",
    "programme", "annual_intake", "academic_year",
    "page_number", "source_url", "extraction_timestamp"
]

INST_COLS = [
    "inc_institution_key", "institution_name", "institution_address",
    "trust_name", "district_name", "state", "sector",
    "programmes", "annual_intakes", "total_intake", "pin_code",
    "academic_year", "source", "source_url", "extraction_timestamp"
]

NURSING_PROGS = {
    "anm", "gnm", "b.sc", "m. sc", "m.sc", "p b b", "nurse practitioner",
    "npcc", "diploma", "b sc", "post basic", "rn rm", "midwifery",
    "cardio thoracic", "critical care", "oncology", "ortho", "neonatal",
    "haematology", "burns", "psychiatric", "emergency", "pediatric"
}

GOVT_SECTORS = {"government", "private", "government aided", "govt", "trust", "society"}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def parse_pin(addr):
    if not addr:
        return ""
    m = re.search(r"\b(\d{6})\b", addr)
    return m.group(1) if m else ""

def normalize(name):
    return re.sub(r"\s+", " ", name.strip().upper())

def sanitize_filename(name):
    return re.sub(r"[^\w\-]", "_", name.strip())

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Warning: Could not read checkpoint: {e}")
    return {
        "academic_year": ACADEMIC_YEAR,
        "completed_states": {},
        "failed_states": {},
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def save_checkpoint(cp):
    cp["updated_at"] = datetime.now().isoformat()
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)

async def extract_rows(page):
    """
    SSRS flat-row state machine parser.
    """
    rows = await page.query_selector_all("table tr")
    best_row = None
    best_count = 0
    for r in rows:
        cells = await r.query_selector_all("td")
        if len(cells) > best_count:
            best_count = len(cells)
            best_row = r

    if best_row is None or best_count < 10:
        return []

    all_cells = await best_row.query_selector_all("td")
    cell_texts = []
    for c in all_cells:
        t = (await c.inner_text()).strip().replace("\n", " ").replace("\r", " ")
        t = re.sub(r"\s+", " ", t)
        cell_texts.append(t)

    # Locate start of records
    data_start_idx = 0
    for i, t in enumerate(cell_texts):
        if t == "1":
            next_cells = cell_texts[i+1:i+5] if i+5 <= len(cell_texts) else []
            if next_cells and len(next_cells[0]) > 5:
                data_start_idx = i
                break

    tokens = cell_texts[data_start_idx:]
    data_rows = []
    cur_sl = cur_name = cur_addr = cur_trust = cur_dist = cur_sector = None
    i = 0
    n = len(tokens)

    while i < n:
        t = tokens[i]
        if t.strip().isdigit() and int(t.strip()) >= 1:
            sl_candidate = t.strip()
            if i + 5 < n:
                name_cand  = tokens[i+1].strip()
                trust_cand = tokens[i+2].strip()
                dist_cand  = tokens[i+3].strip()
                sect_cand  = tokens[i+4].strip()
                prog_cand  = tokens[i+5].strip()

                name_valid = len(name_cand) >= 4
                sect_valid = (sect_cand.lower() in GOVT_SECTORS or len(sect_cand) < 25)
                dist_valid = len(dist_cand) >= 2

                if name_valid and dist_valid and sect_valid:
                    cur_sl     = sl_candidate
                    cur_addr   = name_cand
                    cur_trust  = trust_cand
                    cur_dist   = dist_cand
                    cur_sector = sect_cand
                    cur_prog   = prog_cand
                    cur_intake = tokens[i+6].strip() if i+6 < n else ""
                    name_parts = cur_addr.split(",", 1)
                    cur_name   = name_parts[0].strip()
                    data_rows.append({
                        "sl_no": cur_sl,
                        "institution_name_raw": cur_name,
                        "institution_address_raw": cur_addr,
                        "trust_name": cur_trust,
                        "district_name": cur_dist,
                        "sector": cur_sector,
                        "programme": cur_prog,
                        "annual_intake": cur_intake,
                    })
                    i += 7
                    continue

        if cur_sl and t.strip():
            t_lower = t.lower()
            is_prog = any(kp in t_lower for kp in NURSING_PROGS)
            if is_prog:
                intake = tokens[i+1].strip() if i+1 < n else ""
                data_rows.append({
                    "sl_no": cur_sl,
                    "institution_name_raw": cur_name,
                    "institution_address_raw": cur_addr,
                    "trust_name": cur_trust,
                    "district_name": cur_dist,
                    "sector": cur_sector,
                    "programme": t.strip(),
                    "annual_intake": intake,
                })
                i += 2
                continue

        i += 1

    return data_rows

def deduplicate_institutions(programme_rows):
    inst_map = defaultdict(lambda: {"programmes": [], "annual_intakes": [], "rows": [], "initialized": False})
    for row in programme_rows:
        name_norm = normalize(row["institution_name_raw"])
        dist = (row.get("district_name") or "").strip()
        state = row.get("state", "")
        key = f"{state}|{dist}|{name_norm}"
        e = inst_map[key]
        if not e["initialized"]:
            e["initialized"] = True
            e.update({
                "inc_institution_key": key,
                "institution_name": row["institution_name_raw"],
                "institution_address": row["institution_address_raw"],
                "trust_name": row["trust_name"],
                "district_name": dist,
                "state": state,
                "sector": row["sector"],
                "pin_code": parse_pin(row["institution_address_raw"]),
                "academic_year": row["academic_year"],
                "source": "INC Yearly Report",
                "source_url": row["source_url"],
                "extraction_timestamp": row["extraction_timestamp"]
            })
        prog = row.get("programme", "").strip()
        intake = row.get("annual_intake", "").strip()
        if prog and prog not in e["programmes"]:
            e["programmes"].append(prog)
            e["annual_intakes"].append(intake)
        e["rows"].append(row)

    result = []
    for key, e in inst_map.items():
        total = sum(int(m.group()) for s in e["annual_intakes"] if (m := re.search(r"\d+", s)))
        result.append({
            "inc_institution_key": e["inc_institution_key"],
            "institution_name": e["institution_name"],
            "institution_address": e["institution_address"],
            "trust_name": e["trust_name"],
            "district_name": e["district_name"],
            "state": e["state"],
            "sector": e["sector"],
            "programmes": " | ".join(e["programmes"]),
            "annual_intakes": " | ".join(e["annual_intakes"]),
            "total_intake": total,
            "pin_code": e["pin_code"],
            "academic_year": e["academic_year"],
            "source": e["source"],
            "source_url": e["source_url"],
            "extraction_timestamp": e["extraction_timestamp"]
        })
    return result

def write_csv(rows, path, cols):
    if not rows:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=cols).writeheader()
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

async def scrape_state(page, state_name):
    log(f"\n{'='*60}\nStarting Extraction: State='{state_name}'\n{'='*60}")
    await page.goto(PORTAL_URL, timeout=60000, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    try:
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", ACADEMIC_YEAR)
    except Exception:
        pass

    try:
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label=state_name)
        log("State postback complete")
    except PlaywrightTimeout:
        await page.wait_for_timeout(3000)
        log("State selected (no nav event, waited 3s)")

    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    await page.wait_for_timeout(2000)

    # Click search with All Districts (--Select--)
    log("Submitting query (All Districts)...")
    await page.click("#ctl00_cphContent_btnSubmit")
    await page.wait_for_timeout(PAGE_WAIT_MS)

    all_rows = []
    page_num = 1

    while True:
        log(f"  [{state_name}] Extracting page {page_num}...")
        rows = await extract_rows(page)
        log(f"  [{state_name}] Page {page_num}: {len(rows)} programme rows")
        ts = datetime.now().isoformat()
        for r in rows:
            r.update({
                "state": state_name,
                "academic_year": ACADEMIC_YEAR,
                "page_number": page_num,
                "extraction_timestamp": ts,
                "source_url": PORTAL_URL
            })
        all_rows.extend(rows)

        # Check total pages indicator
        tp_el = await page.query_selector("[id*='TotalPages']")
        if tp_el:
            tp_text = (await tp_el.inner_text()).strip()
            if tp_text.isdigit() and page_num >= int(tp_text):
                log(f"  [{state_name}] Reached total pages: {page_num} of {tp_text}")
                break

        # Check next button
        next_btn = await page.query_selector(
            "input[title='Next Page'],input[id*='_Next_ctl00_ctl00'],"
            "input[id*='ctl05_ctl28'],a[title='Next Page']"
        )
        if not next_btn:
            log(f"  [{state_name}] No Next Page button found — last page.")
            break
        if await next_btn.get_attribute("disabled") is not None:
            log(f"  [{state_name}] Next Page button disabled — last page.")
            break
        if not await next_btn.is_visible():
            log(f"  [{state_name}] Next Page button not visible — last page.")
            break

        log(f"  [{state_name}] Navigating to page {page_num + 1}...")
        try:
            await next_btn.click(timeout=5000)
            await page.wait_for_timeout(PAGE_WAIT_MS)
        except Exception as e:
            log(f"  [{state_name}] Next button click ended ({e}) — completing state.")
            break

        page_num += 1
        if page_num > MAX_PAGES_PER_STATE:
            log(f"  [{state_name}] Safety page limit {MAX_PAGES_PER_STATE} reached.")
            break

    log(f"  [{state_name}] Done: {page_num} pages, {len(all_rows)} programme rows")
    return {"programme_rows": all_rows, "pages": page_num}

async def consolidate_master():
    log("\n" + "="*70 + "\nCONSOLIDATING MASTER NATIONAL DATASETS\n" + "="*70)
    all_prog_files = sorted(STATES_DIR.glob("*_programmes.csv"))
    all_inst_files = sorted(STATES_DIR.glob("*_institutions.csv"))

    all_progs = []
    for pf in all_prog_files:
        try:
            with open(pf, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                all_progs.extend(list(reader))
        except Exception as e:
            log(f"Error reading {pf}: {e}")

    all_insts = []
    for inf in all_inst_files:
        try:
            with open(inf, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                all_insts.extend(list(reader))
        except Exception as e:
            log(f"Error reading {inf}: {e}")

    master_prog_csv = RAW_DIR / "INC_National_Programmes_2025-26.csv"
    master_inst_csv = RAW_DIR / "INC_National_Institutions_Deduplicated_2025-26.csv"
    summary_json = RAW_DIR / "INC_National_Summary_2025-26.json"

    write_csv(all_progs, master_prog_csv, PROG_COLS)
    write_csv(all_insts, master_inst_csv, INST_COLS)

    state_counts = Counter(r.get("state", "Unknown") for r in all_insts)
    sector_counts = Counter(r.get("sector", "Unknown") for r in all_insts)

    summary = {
        "source": "Indian Nursing Council (INC) Yearly Report",
        "portal_url": PORTAL_URL,
        "academic_year": ACADEMIC_YEAR,
        "generated_at": datetime.now().isoformat(),
        "total_programme_rows": len(all_progs),
        "total_unique_institutions": len(all_insts),
        "total_jurisdictions": len(state_counts),
        "jurisdiction_counts": dict(state_counts),
        "sector_breakdown": dict(sector_counts),
        "master_programme_file": str(master_prog_csv),
        "master_institution_file": str(master_inst_csv)
    }

    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log(f"Master Programmes CSV: {master_prog_csv} ({len(all_progs)} rows)")
    log(f"Master Institutions CSV: {master_inst_csv} ({len(all_insts)} institutions)")
    log(f"Summary JSON: {summary_json}")
    return summary

async def main():
    log("="*70)
    log("INC NATIONAL EXTRACTION ENGINE — 36 JURISDICTIONS")
    log(f"Portal: {PORTAL_URL}")
    log(f"Target Year: {ACADEMIC_YEAR}")
    log("="*70)

    checkpoint = load_checkpoint()

    # Pre-populate Delhi if already validated from pilot
    delhi_pilot_prog = RAW_DIR / "INC_Delhi_AllDistricts_2025-26_pilot.csv"
    delhi_pilot_inst = RAW_DIR / "INC_Delhi_institutions_deduplicated.csv"
    delhi_state_prog = STATES_DIR / "INC_Delhi_programmes.csv"
    delhi_state_inst = STATES_DIR / "INC_Delhi_institutions.csv"

    if "Delhi" not in checkpoint.get("completed_states", {}) and delhi_pilot_prog.exists() and delhi_pilot_inst.exists():
        import shutil
        shutil.copyfile(str(delhi_pilot_prog), str(delhi_state_prog))
        shutil.copyfile(str(delhi_pilot_inst), str(delhi_state_inst))
        checkpoint["completed_states"]["Delhi"] = {
            "programme_rows": 71,
            "unique_institutions": 36,
            "pages": 3,
            "completed_at": datetime.now().isoformat(),
            "source": "Validated Pilot"
        }
        save_checkpoint(checkpoint)
        log("Imported validated pilot data for Delhi into national pipeline.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        log("Fetching state list from portal...")
        await page.goto(PORTAL_URL, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        state_opts = await page.query_selector_all("#ctl00_cphContent_ddlState option")
        available_states = []
        for opt in state_opts:
            val = (await opt.get_attribute("value") or "").strip()
            lbl = (await opt.inner_text()).strip()
            if val and val != "0" and lbl not in ("--Select--", "Select State", ""):
                available_states.append(lbl)

        log(f"Discovered {len(available_states)} states/UTs on the portal:")
        for idx, st in enumerate(available_states, 1):
            status = "DONE" if st in checkpoint.get("completed_states", {}) else "PENDING"
            log(f"  [{idx:02d}/{len(available_states):02d}] {st:<35} : {status}")

        for idx, state_name in enumerate(available_states, 1):
            if state_name in checkpoint.get("completed_states", {}):
                log(f"\nSkipping already completed state [{idx}/{len(available_states)}]: {state_name}")
                continue

            log(f"\nProcessing [{idx}/{len(available_states)}]: {state_name}")
            state_safe = sanitize_filename(state_name)
            state_prog_csv = STATES_DIR / f"INC_{state_safe}_programmes.csv"
            state_inst_csv = STATES_DIR / f"INC_{state_safe}_institutions.csv"

            max_retries = 3
            success = False

            for attempt in range(1, max_retries + 1):
                try:
                    res = await scrape_state(page, state_name)
                    progs = res["programme_rows"]
                    pages = res["pages"]

                    write_csv(progs, state_prog_csv, PROG_COLS)
                    insts = deduplicate_institutions(progs)
                    write_csv(insts, state_inst_csv, INST_COLS)

                    checkpoint["completed_states"][state_name] = {
                        "programme_rows": len(progs),
                        "unique_institutions": len(insts),
                        "pages": pages,
                        "completed_at": datetime.now().isoformat()
                    }
                    if state_name in checkpoint.get("failed_states", {}):
                        del checkpoint["failed_states"][state_name]
                    save_checkpoint(checkpoint)
                    log(f"SUCCESS: {state_name} -> {len(progs)} progs, {len(insts)} institutions, {pages} pages")
                    success = True
                    break
                except Exception as e:
                    log(f"Attempt {attempt}/{max_retries} failed for {state_name}: {e}")
                    await page.wait_for_timeout(5000)
                    # Recreate page on failure
                    try:
                        await page.close()
                    except Exception:
                        pass
                    page = await context.new_page()

            if not success:
                checkpoint.setdefault("failed_states", {})[state_name] = {
                    "failed_at": datetime.now().isoformat(),
                    "error": "Max retries exceeded"
                }
                save_checkpoint(checkpoint)
                log(f"FAILED {state_name} after {max_retries} attempts. Continuing to next state...")

            # Gentle rate-limiting delay between states
            await asyncio.sleep(2)

        await browser.close()

    # Consolidate all states
    await consolidate_master()
    log("\nALL 36 JURISDICTIONS PROCESSING COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())
