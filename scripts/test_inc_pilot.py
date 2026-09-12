"""
test_inc_pilot.py
Pilots the INC (Indian Nursing Council) portal for 1 State and 1 District.
"""

import sys
import asyncio
from playwright.async_api import async_playwright

async def run_pilot():
    print("Starting Playwright...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        print(f"Loading {url}...", flush=True)
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        print("Page loaded!", flush=True)
        
        # 1. State options
        state_opts = await page.query_selector_all("#ctl00_cphContent_ddlState option")
        state_map = {}
        for opt in state_opts:
            val = (await opt.get_attribute("value") or "").strip()
            txt = (await opt.inner_text()).strip()
            if val and val != "0":
                state_map[txt] = val
        print(f"Total States: {len(state_map)}", flush=True)
        
        # 2. Select Year
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", "2025-2026")
        print("Selected Year: 2025-2026", flush=True)
        
        # 3. Test State: Chandigarh or Delhi
        test_state = "Delhi" if "Delhi" in state_map else list(state_map.keys())[0]
        print(f"Selecting State: {test_state} by label...", flush=True)
        
        # Select by label and wait for ASP.NET navigation/response
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label=test_state)
        print("State postback navigation complete!", flush=True)
        
        # Check districts loaded
        dist_opts = await page.query_selector_all("#ctl00_cphContent_ddlDistrict option")
        print(f"Districts loaded for {test_state}: {len(dist_opts)}", flush=True)
        for opt in dist_opts[:5]:
            val = (await opt.get_attribute("value") or "").strip()
            txt = (await opt.inner_text()).strip()
            print(f"  District: val='{val}' | text='{txt}'", flush=True)
            
        # 4. Click Search with All Districts (value='0' or default)
        print("\nClicking Search button...", flush=True)
        await page.click("#ctl00_cphContent_btnSubmit")
        print("Clicked Submit, waiting 5s for results...", flush=True)
        await page.wait_for_timeout(5000)
        
        # 5. Inspect result tables
        tables = await page.query_selector_all("table")
        print(f"\nTables found: {len(tables)}", flush=True)
        for idx, t in enumerate(tables):
            tid = await t.get_attribute("id")
            tcls = await t.get_attribute("class")
            rows = await t.query_selector_all("tr")
            print(f"  Table #{idx} id='{tid}' class='{tcls}': {len(rows)} rows", flush=True)
            if len(rows) > 0:
                header_text = await rows[0].inner_text()
                print(f"    Row 0: {header_text.strip().replace(chr(10), ' | ')[:150]}", flush=True)
            if len(rows) > 1:
                row1_text = await rows[1].inner_text()
                print(f"    Row 1: {row1_text.strip().replace(chr(10), ' | ')[:150]}", flush=True)
                
        # Take screenshot for visual confirmation
        ss_path = "data/inc_pilot_screenshot.png"
        await page.screenshot(path=ss_path, full_page=True)
        print(f"\nSaved full page screenshot to {ss_path}", flush=True)

        await browser.close()
        print("Pilot completed successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(run_pilot())
