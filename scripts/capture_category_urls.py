from playwright.sync_api import sync_playwright

def get_exact_urls():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        urls_called = []
        page.on("request", lambda r: urls_called.append(r.url) if "getCollegeList" in r.url else None)

        print("Navigating to home...")
        page.goto("https://dashboard.aishe.gov.in/hedirectory/", timeout=60000)
        page.wait_for_timeout(3000)

        # Categories: 1=Affiliated, 2=Constituent, 3=PG Centre, 4=Recognized, 5=Autonomous
        for cat_id in [1, 2, 3, 4, 5]:
            print(f"Navigating to category {cat_id}...")
            page.goto(f"https://dashboard.aishe.gov.in/hedirectory/#/hedirectory/collegeDetails/C/{cat_id}", timeout=60000)
            page.wait_for_timeout(4000)

        print("\nCaptured API URLs:")
        for u in urls_called:
            print(u)

        browser.close()

if __name__ == "__main__":
    get_exact_urls()
