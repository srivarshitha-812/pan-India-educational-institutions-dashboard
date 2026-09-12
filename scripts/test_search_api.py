import urllib.request, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'X-APP-SIGNATURE': '9f2c7a4b8e1d6c3f5a9b0e2d4f6a7c8b',
    'Referer': 'https://kys.udiseplus.gov.in/',
    'Origin': 'https://kys.udiseplus.gov.in'
}

base_url = 'https://kys.udiseplus.gov.in/web-app/api/'

def call(path):
    url = base_url + path
    print(f"\n[CALL] {url}")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}, Len: {len(data)}")
            try:
                js = json.loads(data)
                print("JSON preview:")
                print(json.dumps(js, indent=2)[:1000])
                return js
            except:
                print("Raw preview:", data[:300])
                return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read()[:200]}")
    except Exception as e:
        print("Error:", e)
    return None

# Test keyword search
res = call('search-school/by-keyword?schoolName=Kendriya%20Vidyalaya')

if res and isinstance(res, dict) and 'data' in res and res['data']:
    first = res['data'][0] if isinstance(res['data'], list) else res['data']
    print("\nFirst result item keys & values:")
    print(json.dumps(first, indent=2))
    
    # If there's a udise code or schoolId, test getSchoolProfile
    udise = first.get('udiseSchCode') or first.get('udiseCode') or first.get('schoolId')
    if udise:
        print(f"\nTesting profile for {udise}:")
        call(f'school/profile?udiseSchCode={udise}&yearId=12')
