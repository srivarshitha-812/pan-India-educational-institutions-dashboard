import urllib.request, urllib.error, re, time, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://kys.udiseplus.gov.in/',
}

def fetch(url, extra_headers=None, timeout=15):
    h = dict(headers)
    if extra_headers:
        h.update(extra_headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(200000).decode('utf-8', errors='replace')
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, str(e)

# ── Step 1: Fetch root page, find JS bundles ──────────────────────────────────
print('=== Step 1: KYS root page ===')
status, html = fetch('https://kys.udiseplus.gov.in/')
print(f'Status: {status}, length: {len(html)}')
print(html[:2000])
print()

# Extract script src
scripts = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
print('JS files found:', scripts)

# ── Step 2: Try fetching main.js / runtime.js ─────────────────────────────────
api_base = None
for script in scripts[:10]:
    url = script if script.startswith('http') else f'https://kys.udiseplus.gov.in{script}'
    print(f'\n=== Fetching: {url} ===')
    status, js_content = fetch(url)
    print(f'Status: {status}, size: {len(js_content)} chars')
    if status == 200 and len(js_content) > 100:
        # Look for API base URL patterns
        patterns = [
            r'https?://[a-z0-9\-\.]+udise[a-z\.]*gov\.in[/a-z0-9\-]*',
            r'apiUrl["\s:]+["\']([^"\']+)["\']',
            r'baseUrl["\s:]+["\']([^"\']+)["\']',
            r'BASE_URL["\s:]+["\']([^"\']+)["\']',
            r'environment[^{]*{[^}]*apiUrl[^"\']*["\']([^"\']+)["\']',
        ]
        for pat in patterns:
            matches = re.findall(pat, js_content, re.IGNORECASE)
            if matches:
                print(f'  Pattern "{pat[:40]}..." found: {matches[:5]}')
        # Print first 500 chars to see structure
        print(f'  First 500 chars: {js_content[:500]}')

# ── Step 3: Try the environment.js or assets/config.json ─────────────────────
config_urls = [
    'https://kys.udiseplus.gov.in/assets/config.json',
    'https://kys.udiseplus.gov.in/assets/environment.json',
    'https://kys.udiseplus.gov.in/environment.js',
    'https://kys.udiseplus.gov.in/config.json',
    'https://kys.udiseplus.gov.in/assets/app-config.json',
]
for url in config_urls:
    status, body = fetch(url)
    if status == 200:
        print(f'\n[FOUND] {url}\n{body[:1000]}')
    else:
        print(f'[{status}] {url}')
