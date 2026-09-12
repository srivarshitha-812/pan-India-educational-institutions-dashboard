import urllib.request, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("Fetching main-RCIDFHPD.js...")
url = 'https://kys.udiseplus.gov.in/main-RCIDFHPD.js'
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8', errors='replace')
        print(f"Downloaded main.js: {len(content)} chars")
        
        # 1. Search for API URLs
        urls = set(re.findall(r'https?://[a-zA-Z0-9_\-\./:]+', content))
        print("\n=== Government / API URLs found ===")
        for u in sorted(urls):
            if any(k in u.lower() for k in ['gov.in', 'api', 'kys', 'backend', 'service']):
                print("  ", u)

        # 2. Search for path patterns
        endpoints = set(re.findall(r'["\'`](/(?:api|kys|school|v[0-9]|public|search|master)[^"\'`\s<>]*)["\'`]', content))
        print(f"\n=== Endpoints found ({len(endpoints)}) ===")
        for ep in sorted(endpoints)[:40]:
            print("  ", ep)

        # 3. Search for environment config / baseUrl / apiUrl
        env_matches = re.findall(r'(?:apiUrl|baseUrl|BASE_URL|api_url|apiEndpoint|serviceUrl|domainUrl)\s*:\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        print("\n=== Configured API base URLs ===")
        for m in set(env_matches):
            print("  ", m)

        # 4. Search for pseudocode
        pseudo = re.findall(r'.{0,30}pseudo.{0,30}', content, re.IGNORECASE)
        print(f"\n=== Pseudocode mentions ({len(pseudo)}) ===")
        for p in pseudo[:10]:
            print("  ", repr(p))
            
        # 5. Search for UDISE / school lookup functions
        school_lookups = set(re.findall(r'["\'`]([^"\'`]*(?:school|udise|search|lookup)[^"\'`]*)["\'`]', content, re.IGNORECASE))
        filtered_lookups = [x for x in school_lookups if len(x) < 50 and ('api' in x.lower() or 'get' in x.lower() or 'search' in x.lower())]
        print(f"\n=== School / Search API paths ({len(filtered_lookups)}) ===")
        for l in sorted(filtered_lookups)[:30]:
            print("  ", l)

except Exception as e:
    print("Error:", e)
