import urllib.request, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

url = 'https://www.nmc.org.in/information-desk/college-and-course-search/'
print("Fetching NMC College and Course Search page...")
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
        print(f"Page length: {len(html)}")
        
        # Search for ajax, datatable, or api endpoints
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"Found {len(scripts)} script tags")
        for i, s in enumerate(scripts):
            if any(k in s for k in ['DataTable', 'ajax', 'url', 'college', 'course', '11585', 'json']):
                print(f"\n--- Script {i} ---")
                print(s[:1000])
                
        # Search for URLs in HTML
        urls = set(re.findall(r'https?://[^\s"\'<>]+', html))
        print("\n=== Government / NMC URLs ===")
        for u in sorted(urls):
            if 'nmc.org.in' in u and any(k in u for k in ['ajax', 'api', 'search', 'get', 'json', 'data', 'college']):
                print("  ", u)

except Exception as e:
    print("Error:", e)
