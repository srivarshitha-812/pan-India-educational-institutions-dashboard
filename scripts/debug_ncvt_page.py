"""
Quick debug: what is the page content after loading NCVT MIS?
"""
import sys, re, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    context = browser.new_context(
        ignore_https_errors=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.6613.84 Safari/537.36"
        ),
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    # Hide webdriver flag
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page.set_default_timeout(30000)

    print("Loading page...")
    try:
        page.goto(NCVT_SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"goto error: {e}")

    time.sleep(3)
    
    # Get page URL (check for redirect)
    print(f"Current URL: {page.url}")
    print(f"Page title: {page.title()}")
    
    # Get page content
    html = page.content()
    print(f"HTML length: {len(html)}")
    
    # Save
    out = BASE / "data" / "raw" / "ncvt" / "debug_page.html"
    out.write_text(html, encoding="utf-8")
    print(f"Saved: {out}")
    
    # Print first 2000 chars
    print("\nFirst 1500 chars of HTML:")
    print(html[:1500])
    
    # Screenshot
    page.screenshot(path=str(BASE / "data" / "raw" / "ncvt" / "debug_page.png"), full_page=False)
    print("Screenshot saved.")
    
    context.close()
    browser.close()
