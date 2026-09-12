"""
test_inc_next_page.py
Tests navigating through all pages of a State report via the Next Page button.
"""

import asyncio
from playwright.async_api import async_playwright

async def test_pagination():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        print("Navigating to INC...", flush=True)
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", "2025-2026")
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label="Delhi")
            
        print("Searching Delhi (All Districts)...", flush=True)
        await page.click("#ctl00_cphContent_btnSubmit")
        await page.wait_for_timeout(6000)
        
        page_num = 1
        all_records = []
        
        while True:
            # Extract data rows from current page
            rows = await page.query_selector_all("table tr")
            page_rows = []
            for r in rows:
                text = (await r.inner_text()).strip()
                parts = [p.strip() for p in text.split("\t") if p.strip()]
                # S.No., Inst Name, Trust, District, Sector, Programme, Intake
                if len(parts) >= 6 and parts[0].isdigit():
                    page_rows.append(parts)
                    
            print(f"Page {page_num}: Found {len(page_rows)} institution programme rows", flush=True)
            all_records.extend(page_rows)
            
            # Check Next button
            # SSRS next button input is usually named *_Next_ctl00_ctl00 or similar
            next_btn = await page.query_selector("input[title='Next Page'], input[id*='Next']")
            if not next_btn:
                print("No Next Page button found", flush=True)
                break
                
            disabled = await next_btn.get_attribute("disabled")
            if disabled is not None:
                print("Next Page button is disabled — reached final page!", flush=True)
                break
                
            print("Clicking Next Page...", flush=True)
            # In SSRS, Next Page causes an asynchronous update
            await next_btn.click()
            await page.wait_for_timeout(4000)
            page_num += 1
            if page_num > 100:  # safety break
                break
                
        print(f"\nTOTAL RECORDS EXTRACTED FOR DELHI: {len(all_records)}", flush=True)
        for idx, rec in enumerate(all_records[:5], 1):
            print(f"  [{idx}] {rec[1][:60]} | Dist: {rec[3]} | Prog: {rec[5]} | Intake: {rec[6]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_pagination())
