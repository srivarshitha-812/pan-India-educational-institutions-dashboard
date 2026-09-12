import urllib.request, json, ssl

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

# 1. Test getCollegesForStateUniversity
print("=== Testing getCollegesForStateUniversity ===")
url1 = 'https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getCollegesForStateUniversity'
req1 = urllib.request.Request(url1, data=b'{}', headers=headers, method='POST')
try:
    with urllib.request.urlopen(req1, context=ctx, timeout=30) as resp:
        data = resp.read().decode('utf-8')
        js = json.loads(data)
        print(f"Colleges count: {len(js)}")
        if js:
            print("First college:", json.dumps(js[0], indent=2))
except Exception as e:
    print("Error 1:", e)

# 2. Test searchCourse
print("\n=== Testing searchCourse ===")
url2 = 'https://www.nmc.org.in/MCIRest/open/searchCourse'
payload = json.dumps({
    "courseIds": "",
    "stateIds": "",
    "univIds": "",
    "collegeIds": "",
    "status": "0",
    "management": "0"
}).encode('utf-8')

req2 = urllib.request.Request(url2, data=payload, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req2, context=ctx, timeout=60) as resp:
        data = resp.read().decode('utf-8')
        print(f"searchCourse response length: {len(data)} chars")
        js = json.loads(data)
        print(f"Total results: {len(js)}")
        if js:
            print("First course record:", json.dumps(js[0], indent=2))
            print("\nKeys in course record:", list(js[0].keys()))
except Exception as e:
    print("Error 2:", e)
