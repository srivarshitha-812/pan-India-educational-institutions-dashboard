"""
test_inc_export_button.py
Tests clicking the SSRS Export -> Excel button on INC ReportViewer.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_export():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        print("Navigating to INC...", flush=True)
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        
        await page.select_option("#ctl00_cphContent_ddlAcademicYear", "2025-2026")
        async with page.expect_navigation(timeout=30000):
            await page.select_option("#ctl00_cphContent_ddlState", label="Delhi")
            
        print("Searching Delhi...", flush=True)
        await page.click("#ctl00_cphContent_btnSubmit")
        await page.wait_for_timeout(6000)
        
        # Click the Export icon/link
        export_link = await page.query_selector("[id*='ctl05_ctl04_ctl00_ButtonLink']")
        if export_link:
            print("Clicking Export menu link...", flush=True)
            await export_link.click()
            await page.wait_for_timeout(1000)
            
            # Find the dropdown menu options
            menu_items = await page.query_selector_all("a[onclick*='Export'], div[id*='ctl04'] a, [title='Excel'], a:has-text('Excel')")
            print(f"Found {len(menu_items)} export format links:", flush=True)
            for m in menu_items:
                txt = (await m.inner_text()).strip()
                title = await m.get_attribute("title")
                onclick = await m.get_attribute("onclick")
                print(f"  Export option: text='{txt}', title='{title}', onclick='{onclick}'", flush=True)
                
            # Try to trigger Excel download
            excel_link = await page.query_selector("a:has-text('Excel'), a[title='Excel']")
            if excel_link:
                print("\nTriggering Excel download...", flush=True)
                async with page.expect_download(timeout=30000) as download_info:
                    await excel_link.click()
                download = await download_info.value
                save_path = Path("data/raw/INC/Delhi_test_export.xlsx")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                await download.save_as(str(save_path))
                print(f"SUCCESS! Downloaded Excel to {save_path} ({save_path.stat().st_size} bytes)", flush=True)
            else:
                print("Could not find Excel option link", flush=True)
        else:
            print("Export link not found", flush=True)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_export())
