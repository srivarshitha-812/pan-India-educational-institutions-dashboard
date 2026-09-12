"""
inspect_inc_reportviewer.py
Inspects the SSRS ReportViewer toolbar on INC portal (Export options, Page navigation, etc.)
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        print("Navigating to INC portal...")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        
        # Select Year and State
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", "2025-2026")
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label="Delhi")
            
        print("Clicking Search...")
        await page.click("#ctl00_cphContent_btnSubmit")
        await page.wait_for_timeout(6000)
        
        # Check ReportViewer toolbar controls
        print("\n--- Inspecting ReportViewer Toolbar Controls ---")
        export_dropdown = await page.query_selector_all("select[id*='Export'], [id*='ExportFormats'], [id*='Export']")
        print(f"Export controls found: {len(export_dropdown)}")
        for e in export_dropdown:
            eid = await e.get_attribute("id")
            print(f"  Export control: {eid}")
            options = await e.query_selector_all("option")
            for o in options:
                val = await o.get_attribute("value")
                txt = await o.inner_text()
                print(f"    Export option: val='{val}', text='{txt.strip()}'")
                
        # Check Export button or menu
        export_btn = await page.query_selector("[id*='ctl05_ctl04_ctl00_Button'], a[title='Export'], [title*='Export']")
        if export_btn:
            eid = await export_btn.get_attribute("id")
            title = await export_btn.get_attribute("title")
            print(f"Found Export Button/Link: id='{eid}', title='{title}'")
            
        # Check page navigation controls
        print("\n--- Inspecting Page Navigation Controls ---")
        nav_inputs = await page.query_selector_all("[id*='ReportViewer1_ctl05'] input, [id*='ReportViewer1_ctl05'] a")
        for n in nav_inputs:
            nid = await n.get_attribute("id")
            ntitle = await n.get_attribute("title")
            nval = await n.get_attribute("value")
            tag = await n.evaluate("el => el.tagName")
            print(f"  Nav control: <{tag}> id='{nid}', title='{ntitle}', value='{nval}'")
            
        # Also inspect the rendered data table and cells
        print("\n--- Inspecting Data Cells in Report ---")
        # Let's find rows with Sl.No.
        rows = await page.query_selector_all("table tr")
        data_rows = []
        for r in rows:
            text = (await r.inner_text()).strip()
            parts = [p.strip() for p in text.split("\t") if p.strip()]
            if len(parts) >= 5 and parts[0].isdigit():
                data_rows.append(parts)
                
        print(f"Extracted {len(data_rows)} data rows on Page 1:")
        for r in data_rows[:5]:
            print(f"  {r}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
