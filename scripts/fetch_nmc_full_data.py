import urllib.request, json, ssl, gzip

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'https://www.nmc.org.in',
    'Referer': 'https://www.nmc.org.in/information-desk/college-and-course-search/'
}

# 1. Test getCollegesForStateUniversity with gzip decompression
print("--- 1. getCollegesForStateUniversity ---")
url1 = 'https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getCollegesForStateUniversity'
req1 = urllib.request.Request(url1, data=b'{}', headers=headers, method='POST')
try:
    with urllib.request.urlopen(req1, context=ctx, timeout=30) as resp:
        raw = resp.read()
        print(f"Raw len: {len(raw)}, encoding: {resp.headers.get('Content-Encoding')}")
        try:
            raw = gzip.decompress(raw)
            print(f"Decompressed len: {len(raw)}")
        except:
            pass
        text = raw.decode('utf-8', errors='replace')
        js = json.loads(text)
        print(f"Total Colleges returned: {len(js)}")
        if js:
            print("First college sample:", json.dumps(js[0], indent=2))
            with open('data/nmc_all_colleges_api.json', 'w', encoding='utf-8') as f:
                json.dump(js, f, indent=2)
            print("Saved to data/nmc_all_colleges_api.json")
except Exception as e:
    print("getCollegesForStateUniversity error:", e)

# 2. Test searchCourse with form defaults
print("\n--- 2. searchCourse ---")
url2 = 'https://www.nmc.org.in/MCIRest/open/searchCourse'
payloads = [
    {"courseIds": "", "stateIds": None, "univIds": None, "collegeIds": None, "status": "", "management": ""},
    {"courseIds": None, "stateIds": None, "univIds": None, "collegeIds": None, "status": "", "management": ""},
    {"status": "", "management": ""},
    {}
]

for i, p in enumerate(payloads):
    print(f"\nTrying payload {i+1}: {p}")
    req2 = urllib.request.Request(url2, data=json.dumps(p).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req2, context=ctx, timeout=60) as resp:
            raw = resp.read()
            print(f"Success! Status: {resp.status}, len: {len(raw)}, encoding: {resp.headers.get('Content-Encoding')}")
            try:
                raw = gzip.decompress(raw)
            except:
                pass
            text = raw.decode('utf-8', errors='replace')
            js = json.loads(text)
            print(f"Total courses returned: {len(js)}")
            if js:
                print("First course sample:", json.dumps(js[0], indent=2))
                with open('data/nmc_all_courses_api.json', 'w', encoding='utf-8') as f:
                    json.dump(js, f, indent=2)
                print("Saved to data/nmc_all_courses_api.json")
            break
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read()[:200]}")
    except Exception as e:
        print("Error:", e)
