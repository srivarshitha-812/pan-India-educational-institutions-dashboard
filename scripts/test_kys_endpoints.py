import urllib.request, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'X-APP-SIGNATURE': '9f2c7a4b8e1d6c3f5a9b0e2d4f6a7c8b',
    'Referer': 'https://kys.udiseplus.gov.in/',
    'Origin': 'https://kys.udiseplus.gov.in'
}

base_url = 'https://kys.udiseplus.gov.in/web-app/api/'

def test_api(path):
    url = base_url + path
    print(f"\n[CALL] {url}")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}, Len: {len(data)}")
            try:
                js = json.loads(data)
                print("JSON preview:", json.dumps(js, indent=2)[:500])
                return js
            except:
                print("Raw preview:", data[:300])
                return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read()[:200]}")
    except Exception as e:
        print("Error:", e)
    return None

# Test 1: Year list
years = test_api('master/year?year=1')

# Test 2: Category list
test_api('fetchCategoryList')

# Test 3: Management list
test_api('fetchManagementList')
