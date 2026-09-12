"""
inspect_inc_row_html.py
Dumps the outerHTML of the report table rows to see if hidden IDs or links exist.
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", "2025-2026")
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label="Delhi")
            
        await page.click("#ctl00_cphContent_btnSubmit")
        await page.wait_for_timeout(6000)
        
        # Look for the data table
        rows = await page.query_selector_all("table tr")
        for r in rows:
            text = (await r.inner_text()).strip()
            parts = [p.strip() for p in text.split("\t") if p.strip()]
            if len(parts) >= 6 and parts[0] == "1":
                html = await r.inner_html()
                print("--- ROW 1 HTML ---")
                print(html[:1000])
                break
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_html())
