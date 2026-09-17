from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def test_download():
    out_dir = Path("scratch/aishe_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to C/1 (Affiliated Colleges)...")
        page.goto("https://dashboard.aishe.gov.in/hedirectory/#/hedirectory/collegeDetails/C/1", timeout=60000)

        # Wait for table to load
        page.wait_for_selector("table", timeout=45000)
        print("Table loaded! Looking for excel button...")

        # Find excel button
        # Let's inspect buttons/links on the page
        btns = page.query_selector_all("button, a, img")
        excel_elem = None
        for b in btns:
            title = b.get_attribute("title") or ""
            src = b.get_attribute("src") or ""
            cls = b.get_attribute("class") or ""
            text = b.inner_text() or ""
            if "excel" in title.lower() or "excel" in src.lower() or "xls" in title.lower() or "xls" in src.lower() or "export" in cls.lower():
                print(f"Found candidate: tag={b.evaluate('e => e.tagName')}, class={cls}, title={title}, src={src}, text={text}")
                excel_elem = b
                break

        if excel_elem:
            print("Clicking excel export element...")
            with page.expect_download(timeout=60000) as download_info:
                excel_elem.click()
            download = download_info.value
            saved_path = out_dir / download.suggested_filename
            download.save_as(saved_path)
            print(f"Downloaded successfully to: {saved_path} (size: {saved_path.stat().st_size} bytes)")
        else:
            print("Excel element not found! Inspecting all images and buttons:")
            for b in btns[:30]:
                print(b.evaluate("e => e.outerHTML")[:120])

        browser.close()

if __name__ == "__main__":
    test_download()
