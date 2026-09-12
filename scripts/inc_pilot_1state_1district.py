"""
inc_pilot_1state_1district.py
INC (Indian Nursing Council) Yearly Report - Pilot Extraction
Phase 1: 1-State (Delhi) + 1-District (Central Delhi) pilot
"""
import asyncio, csv, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_INC_DIR = BASE_DIR / "data" / "raw" / "inc"
LOG_DIR = BASE_DIR / "data" / "logs"
CHECKPOINT_DIR = BASE_DIR / "data" / "checkpoints" / "inc"

for d in [RAW_INC_DIR, LOG_DIR, CHECKPOINT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PORTAL_URL    = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
ACADEMIC_YEAR = "2025-2026"
PILOT_STATE   = "Delhi"
PILOT_DISTRICT = "Central Delhi"
PAGE_WAIT_MS  = 6000
MAX_PAGES     = 200

PILOT_ALL_CSV   = RAW_INC_DIR / "INC_Delhi_AllDistricts_2025-26_pilot.csv"
PILOT_DIST_CSV  = RAW_INC_DIR / "INC_Delhi_CentralDelhi_2025-26_pilot.csv"
PILOT_INST_CSV  = RAW_INC_DIR / "INC_Delhi_institutions_deduplicated.csv"
PILOT_JSON      = RAW_INC_DIR / "INC_Delhi_AllDistricts_2025-26_pilot.json"
PILOT_LOG       = LOG_DIR / "inc_pilot_run.log"
SS_DIR          = RAW_INC_DIR / "screenshots"
SS_DIR.mkdir(exist_ok=True)

PROG_COLS = ["sl_no","institution_name_raw","institution_address_raw","trust_name",
             "district_name","sector","programme","annual_intake","state","academic_year",
             "page_number","extraction_timestamp","source_url"]
INST_COLS = ["inc_institution_key","institution_name","institution_address","trust_name",
             "district_name","state","sector","programmes","annual_intakes","total_intake",
             "pin_code","academic_year","source","source_url","extraction_timestamp"]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(PILOT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_pin(addr):
    m = re.search(r"\b(\d{6})\b", addr)
    return m.group(1) if m else ""

def normalize(name):
    return re.sub(r"\s+", " ", name.strip().upper())

async def extract_rows(page):
    """
    SSRS flat-row parser.

    The INC portal's SSRS ReportViewer renders the entire page of results as a
    single <tr> containing hundreds of sequential <td> cells.  The flat sequence
    looks like:
        ...toolbar cells..., 'Delhi', '', '', '',
        '1', 'Institution Name, Address', 'Trust', 'District', 'Sector', 'Prog', 'Intake', '',
        '', 'Prog2', 'Intake2', '',
        '2', ...
    We find the largest <tr> (the data row), collect all cell texts, then parse
    them with a lightweight state machine.
    """
    rows = await page.query_selector_all("table tr")

    # ── Step 1: Find the data-bearing row (most cells, containing numeric SL) ──
    best_row = None
    best_count = 0
    for r in rows:
        cells = await r.query_selector_all("td")
        if len(cells) > best_count:
            best_count = len(cells)
            best_row = r

    if best_row is None or best_count < 10:
        return []

    # ── Step 2: Extract all cell texts ────────────────────────────────────────
    all_cells = await best_row.query_selector_all("td")
    cell_texts = []
    for c in all_cells:
        t = (await c.inner_text()).strip().replace("\n", " ").replace("\r", " ")
        t = re.sub(r"\s+", " ", t)
        cell_texts.append(t)

    # ── Step 3: Locate the data start (first numeric SL after header cells) ──
    DATA_START_KEYWORDS = {"sl.no.", "institution name", "sl no"}
    NURSING_PROGS = {"anm","gnm","b.sc","m. sc","m.sc","p b b","nurse practitioner",
                     "npcc","diploma","b sc","post basic","rn rm"}
    GOVT_SECTORS = {"government","private","government aided"}

    # Find position of first valid SL number (after header area)
    data_start_idx = 0
    for i, t in enumerate(cell_texts):
        if t == "1":
            # Confirm by checking next few cells look like institution data
            next_cells = cell_texts[i+1:i+5] if i+5 <= len(cell_texts) else []
            if next_cells and len(next_cells[0]) > 10:  # Name should be long
                data_start_idx = i
                break

    tokens = cell_texts[data_start_idx:]

    # ── Step 4: State machine parse ───────────────────────────────────────────
    data_rows = []
    cur_sl = cur_name = cur_addr = cur_trust = cur_dist = cur_sector = None
    i = 0
    n = len(tokens)

    while i < n:
        t = tokens[i]

        # Is this a new serial number?
        if t.strip().isdigit() and int(t.strip()) >= 1:
            sl_candidate = t.strip()
            # Peek ahead: expect Name, Trust, District, Sector, Programme, Intake pattern
            if i + 5 < n:
                name_cand  = tokens[i+1].strip()
                trust_cand = tokens[i+2].strip()
                dist_cand  = tokens[i+3].strip()
                sect_cand  = tokens[i+4].strip()
                prog_cand  = tokens[i+5].strip()

                # Validate: name must be reasonably long, sector must look valid
                name_valid = len(name_cand) >= 5
                sect_valid = sect_cand.lower() in GOVT_SECTORS or len(sect_cand) < 20
                dist_valid = len(dist_cand) >= 3

                if name_valid and dist_valid:
                    cur_sl     = sl_candidate
                    cur_addr   = name_cand  # full address in this cell
                    cur_trust  = trust_cand
                    cur_dist   = dist_cand
                    cur_sector = sect_cand
                    cur_prog   = prog_cand
                    cur_intake = tokens[i+6].strip() if i+6 < n else ""
                    # Institution name = first line/clause of address
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
                    i += 7  # advance past: SL, Name, Trust, Dist, Sector, Prog, Intake
                    continue

        # Is this an additional programme for the current institution?
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
                i += 2  # advance past Prog, Intake
                continue

        i += 1

    return data_rows

async def test_export(page, context, save_dir):
    log("Testing SSRS export functionality...")
    result = {"export_tested":True,"export_success":False,"export_format":None,"export_file":None,"export_error":None}
    try:
        sels = ["input[id*='ctl05_ctl04_ctl00']","a[id*='ctl05_ctl04_ctl00']",
                "[id*='ExportButton']","[title='Export']","a[title*='export' i]"]
        el = None
        for sel in sels:
            el = await page.query_selector(sel)
            if el:
                log(f"  Found export trigger: {sel}")
                break
        if not el:
            result["export_error"] = "No export button found"
            log("  No SSRS export button found")
            return result
        await el.click()
        await page.wait_for_timeout(1500)
        xsels = ["a:has-text('Excel')","a[title='Excel']","a[onclick*='Excel']","[id*='Excel']"]
        xel = None
        for sel in xsels:
            xel = await page.query_selector(sel)
            if xel:
                log(f"  Found Excel option: {sel}")
                break
        if not xel:
            result["export_error"] = "Excel option not found"
            return result
        sp = save_dir / "INC_Delhi_SSRS_export_test.xlsx"
        async with context.expect_event("download", timeout=30000) as dl_info:
            await xel.click()
        dl = await dl_info.value
        await dl.save_as(str(sp))
        sz = sp.stat().st_size
        log(f"  SUCCESS: {sp} ({sz:,} bytes)")
        result.update({"export_success":True,"export_format":"Excel","export_file":str(sp)})
    except Exception as e:
        log(f"  Export error: {e}")
        result["export_error"] = str(e)
    return result

async def scrape(page, context, state, district="--Select--", screenshots=True):
    log(f"\n{'='*60}\nScraping: State={state!r} District={district!r}\n{'='*60}")
    await page.goto(PORTAL_URL, timeout=60000, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    log(f"Title: {await page.title()}")
    try:
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", ACADEMIC_YEAR)
    except:
        pass
    try:
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label=state)
        log("State postback complete")
    except PlaywrightTimeout:
        await page.wait_for_timeout(3000)
        log("State selected (no nav, waited 3s)")
    except Exception as e:
        log(f"ERROR selecting state: {e}")
        return {"programme_rows":[],"pages_scraped":0,"export_result":{},"all_districts":[]}

    # Wait for SSRS async response to fully stabilise before querying DOM
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    await page.wait_for_timeout(2000)

    dist_opts = await page.query_selector_all("#ctl00_cphContent_ddlDistrict option")
    all_dists = []
    for o in dist_opts:
        v = (await o.get_attribute("value") or "").strip()
        t = (await o.inner_text()).strip()
        all_dists.append({"value":v,"label":t})
    log(f"Districts available: {len(dist_opts)}")

    if district not in ("--Select--","All",""):
        try:
            await page.select_option("#ctl00_cphContent_ddlDistrict", label=district)
            await page.wait_for_timeout(1500)
            log(f"Selected district: {district}")
        except Exception as e:
            log(f"WARNING selecting district: {e}")

    log("Clicking Search...")
    await page.click("#ctl00_cphContent_btnSubmit")
    await page.wait_for_timeout(PAGE_WAIT_MS)

    if screenshots:
        sp = SS_DIR / f"INC_{state.replace(' ','_')}_{district.replace(' ','_')}_page1.png"
        await page.screenshot(path=str(sp), full_page=False)
        log(f"Screenshot: {sp}")

    all_rows = []
    page_num = 1

    while True:
        log(f"  Extracting page {page_num}...")
        rows = await extract_rows(page)
        log(f"  Page {page_num}: {len(rows)} programme rows")
        ts = datetime.now().isoformat()
        for row in rows:
            row.update({"state":state,"academic_year":ACADEMIC_YEAR,
                        "page_number":page_num,"extraction_timestamp":ts,"source_url":PORTAL_URL})
        all_rows.extend(rows)

        if screenshots and page_num <= 5:
            sp = SS_DIR / f"INC_{state.replace(' ','_')}_p{page_num:02d}.png"
            await page.screenshot(path=str(sp), full_page=False)

        # Check total pages indicator if available
        tp_el = await page.query_selector("[id*='TotalPages']")
        if tp_el:
            tp_text = (await tp_el.inner_text()).strip()
            if tp_text.isdigit() and page_num >= int(tp_text):
                log(f"  Reached total pages: {page_num} of {tp_text}")
                break

        next_btn = await page.query_selector(
            "input[title='Next Page'],input[id*='_Next_ctl00_ctl00'],"
            "input[id*='ctl05_ctl28'],a[title='Next Page']")
        if not next_btn:
            log("  No Next Page button found — last page.")
            break
        if await next_btn.get_attribute("disabled") is not None:
            log("  Next Page button disabled — last page.")
            break
        if not await next_btn.is_visible():
            log("  Next Page button not visible — last page.")
            break

        log("  Clicking Next Page...")
        try:
            await next_btn.click(timeout=5000)
            await page.wait_for_timeout(PAGE_WAIT_MS)
        except Exception as e:
            log(f"  Next button click failed or timed out ({e}) — treating as last page.")
            break

        page_num += 1
        if page_num > MAX_PAGES:
            log(f"  WARNING: Safety limit {MAX_PAGES} reached.")
            break

    log(f"  Pages: {page_num} | Total programme rows: {len(all_rows)}")
    exp = {}
    try:
        exp = await test_export(page, context, SS_DIR)
    except Exception as e:
        exp = {"export_tested":True,"export_success":False,"export_error":str(e)}
    return {"programme_rows":all_rows,"pages_scraped":page_num,"export_result":exp,"all_districts":all_dists}

def dedup(programme_rows):
    inst_map = defaultdict(lambda:{"programmes":[],"annual_intakes":[],"rows":[],"initialized":False})
    for row in programme_rows:
        name_norm = normalize(row["institution_name_raw"])
        dist  = (row.get("district_name") or "").strip()
        state = row.get("state","")
        key   = f"{state}|{dist}|{name_norm}"
        e = inst_map[key]
        if not e["initialized"]:
            e["initialized"] = True
            e.update({"inc_institution_key":key,"institution_name":row["institution_name_raw"],
                "institution_address":row["institution_address_raw"],"trust_name":row["trust_name"],
                "district_name":dist,"state":state,"sector":row["sector"],
                "pin_code":parse_pin(row["institution_address_raw"]),"academic_year":row["academic_year"],
                "source":"INC Yearly Report","source_url":row["source_url"],
                "extraction_timestamp":row["extraction_timestamp"]})
        prog = row.get("programme","").strip()
        intake = row.get("annual_intake","").strip()
        if prog and prog not in e["programmes"]:
            e["programmes"].append(prog)
            e["annual_intakes"].append(intake)
        e["rows"].append(row)

    result = []
    for key, e in inst_map.items():
        total = sum(int(m.group()) for s in e["annual_intakes"] if (m := re.search(r"\d+", s)))
        result.append({"inc_institution_key":e["inc_institution_key"],"institution_name":e["institution_name"],
            "institution_address":e["institution_address"],"trust_name":e["trust_name"],
            "district_name":e["district_name"],"state":e["state"],"sector":e["sector"],
            "programmes":" | ".join(e["programmes"]),"annual_intakes":" | ".join(e["annual_intakes"]),
            "total_intake":total,"pin_code":e["pin_code"],"academic_year":e["academic_year"],
            "source":e["source"],"source_url":e["source_url"],"extraction_timestamp":e["extraction_timestamp"]})
    return result

def write_prog_csv(rows, path):
    if not rows:
        log(f"  No rows for {path}")
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=PROG_COLS, extrasaction="ignore").writeheader()
        csv.DictWriter(f, fieldnames=PROG_COLS, extrasaction="ignore").writerows(rows)
    log(f"  Wrote {len(rows)} programme rows -> {path}")

def write_inst_csv(rows, path):
    if not rows:
        log(f"  No rows for {path}")
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=INST_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    log(f"  Wrote {len(rows)} institution rows -> {path}")

async def main():
    log("="*70)
    log("INC PILOT EXTRACTION - Phase 1: 1 State + 1 District")
    log(f"Portal: {PORTAL_URL}")
    log(f"Year: {ACADEMIC_YEAR} | State: {PILOT_STATE} | District: {PILOT_DISTRICT}")
    log("="*70)

    results = {"pilot_state":PILOT_STATE,"pilot_district":PILOT_DISTRICT,
               "academic_year":ACADEMIC_YEAR,"portal_url":PORTAL_URL,
               "run_timestamp":datetime.now().isoformat()}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(accept_downloads=True, viewport={"width":1400,"height":900})
        page = await context.new_page()

        # QUERY A: All Districts
        log("\n[QUERY A] Delhi - All Districts")
        ra = await scrape(page, context, PILOT_STATE, "--Select--")
        rows_a = ra["programme_rows"]
        pages_a = ra["pages_scraped"]
        export_info = ra["export_result"]
        dists = ra["all_districts"]
        log(f"\n[QUERY A] {len(rows_a)} programme rows | {pages_a} pages")
        write_prog_csv(rows_a, PILOT_ALL_CSV)
        insts_a = dedup(rows_a)
        log(f"[QUERY A] Unique institutions: {len(insts_a)}")
        write_inst_csv(insts_a, PILOT_INST_CSV)

        # QUERY B: Central Delhi
        log(f"\n[QUERY B] Delhi - {PILOT_DISTRICT}")
        rb = await scrape(page, context, PILOT_STATE, PILOT_DISTRICT)
        rows_b = rb["programme_rows"]
        pages_b = rb["pages_scraped"]
        log(f"\n[QUERY B] {len(rows_b)} programme rows | {pages_b} pages")
        write_prog_csv(rows_b, PILOT_DIST_CSV)
        insts_b = dedup(rows_b)
        log(f"[QUERY B] Unique institutions ({PILOT_DISTRICT}): {len(insts_b)}")

        # VALIDATIONS
        log("\n" + "="*60 + "\nVALIDATION CHECKS\n" + "="*60)
        vc1 = len(insts_a) >= len(insts_b)
        log(f"  [{'PASS' if vc1 else 'FAIL'}] All-districts ({len(insts_a)}) >= Single-district ({len(insts_b)})")
        keys_a = {i["inc_institution_key"] for i in insts_a}
        keys_b = {i["inc_institution_key"] for i in insts_b}
        missing = keys_b - keys_a
        vc2 = len(missing) == 0
        log(f"  [{'PASS' if vc2 else 'WARN'}] District-B subset of all-districts (missing: {len(missing)})")
        for k in list(missing)[:3]:
            log(f"    Missing: {k}")
        dups = len(insts_a) - len(keys_a)
        vc3 = dups == 0
        log(f"  [{'PASS' if vc3 else 'FAIL'}] No duplicate institution keys (dups: {dups})")
        sl_vals = [int(r["sl_no"]) for r in rows_a if str(r.get("sl_no","")).isdigit()]
        mono = all(sl_vals[i] <= sl_vals[i+1] for i in range(len(sl_vals)-1)) if sl_vals else True
        vc4 = mono
        log(f"  [{'PASS' if vc4 else 'WARN'}] SL monotonic: {vc4} | Range: {min(sl_vals) if sl_vals else 'N/A'} -> {max(sl_vals) if sl_vals else 'N/A'}")

        log("\n  [SAMPLE] First 5 deduplicated institutions:")
        for i, inst in enumerate(insts_a[:5], 1):
            log(f"    [{i}] {inst['institution_name'][:55]} | {inst['district_name']} | {inst['sector']} | {inst['programmes'][:60]}")

        sc = Counter(i["sector"] for i in insts_a)
        log("\n  Sector breakdown:")
        for s, c in sc.most_common():
            log(f"    {s}: {c}")
        dc = Counter(i["district_name"] for i in insts_a)
        log("\n  District breakdown:")
        for d, c in dc.most_common():
            log(f"    {d}: {c}")

        results.update({
            "all_districts_query":{"programme_rows":len(rows_a),"unique_institutions":len(insts_a),
                "pages_scraped":pages_a,"sector_breakdown":dict(sc),"district_breakdown":dict(dc),
                "export_result":export_info},
            "single_district_query":{"district":PILOT_DISTRICT,"programme_rows":len(rows_b),
                "unique_institutions":len(insts_b),"pages_scraped":pages_b},
            "all_available_districts":dists,
            "validation":{"all_districts_superset":vc1,"subset_confirmed":vc2,
                "no_duplicates":vc3,"sl_monotonic":vc4,"passed":sum([vc1,vc2,vc3,vc4]),"total":4}
        })

        with open(PILOT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        log(f"\nSaved JSON: {PILOT_JSON}")
        await browser.close()

    log("\n" + "="*70 + "\nPILOT COMPLETE")
    log(f"  State: {PILOT_STATE} | District: {PILOT_DISTRICT} | Year: {ACADEMIC_YEAR}")
    log(f"  Programme Rows (Delhi): {len(rows_a)} | Unique Institutions: {len(insts_a)}")
    log(f"  Pages Scraped: {pages_a}")
    log(f"  Export: {'SUCCESS' if export_info.get('export_success') else 'NOT AVAILABLE - ' + str(export_info.get('export_error',''))}")
    log(f"  Validations: {results['validation']['passed']}/4")
    log(f"  Outputs: {PILOT_ALL_CSV}")
    log(f"           {PILOT_DIST_CSV}")
    log(f"           {PILOT_INST_CSV}")
    log(f"           {PILOT_JSON}")
    log("="*70)
    return results

if __name__ == "__main__":
    asyncio.run(main())
