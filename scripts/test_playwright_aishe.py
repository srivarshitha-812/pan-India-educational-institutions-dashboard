from playwright.sync_api import sync_playwright
import json
import time

def test_aishe():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        captured_data = []

        def handle_response(response):
            if "getCollegeList" in response.url:
                print(f"[Captured API] {response.url[:120]}... Status: {response.status}")
                try:
                    data = response.json()
                    dtos = data.get("institutionDirectoryDto", [])
                    print(f"  Captured {len(dtos)} records! Status: {data.get('statusCode')}")
                    if dtos:
                        print("  Sample record:", dtos[0])
                        captured_data.append(dtos)
                except Exception as e:
                    print("  Error parsing JSON:", e)

        page.on("response", handle_response)

        print("Navigating to Affiliated Colleges page...")
        page.goto("https://dashboard.aishe.gov.in/hedirectory/#/hedirectory/collegeDetails/C/1", timeout=60000)
        
        # Wait for table to load
        page.wait_for_timeout(10000)
        
        print(f"Done waiting. Total captured batches: {len(captured_data)}")
        browser.close()

if __name__ == "__main__":
    test_aishe()
