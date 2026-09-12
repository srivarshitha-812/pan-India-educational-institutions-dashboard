"""
probe_inc_playwright.py
Inspects the Indian Nursing Council portal structure, dropdowns, and form fields.
"""

import asyncio
from playwright.async_api import async_playwright

async def probe():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx"
        print(f"Navigating to {url}...")
        try:
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            print(f"Status: {resp.status}")
            title = await page.title()
            print(f"Title: {title}")
            
            # Select elements
            selects = await page.query_selector_all("select")
            print(f"\nFound {len(selects)} dropdowns:")
            for s in selects:
                name = await s.get_attribute("name")
                elem_id = await s.get_attribute("id")
                options = await s.query_selector_all("option")
                print(f"\n  [Dropdown] id={elem_id}, name={name}, total_options={len(options)}")
                for opt in options[:10]:
                    val = await opt.get_attribute("value")
                    txt = await opt.inner_text()
                    print(f"    val='{val}' | text='{txt.strip()}'")
                    
            # Buttons / Inputs
            inputs = await page.query_selector_all("input[type='submit'], input[type='button'], button")
            print(f"\nFound {len(inputs)} submit/action buttons:")
            for b in inputs:
                bid = await b.get_attribute("id")
                bval = await b.get_attribute("value")
                btype = await b.get_attribute("type")
                print(f"  Button id={bid}, type={btype}, value='{bval}'")
                
        except Exception as e:
            print(f"Error during probe: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(probe())
