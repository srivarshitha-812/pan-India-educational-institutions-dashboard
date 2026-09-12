import urllib.request, json, ssl, gzip

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://www.nmc.org.in',
    'Referer': 'https://www.nmc.org.in/information-desk/college-and-course-search/'
}

# 1. Test getCollegesForStateUniversity
url1 = 'https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getCollegesForStateUniversity'
req1 = urllib.request.Request(url1, data=b'{}', headers=headers, method='POST')
try:
    with urllib.request.urlopen(req1, context=ctx, timeout=30) as resp:
        raw = resp.read()
        if resp.headers.get('Content-Encoding') == 'gzip':
            raw = gzip.decompress(raw)
        text = raw.decode('utf-8', errors='replace')
        js = json.loads(text)
        print(f"Colleges count from getCollegesForStateUniversity: {len(js)}")
        if js:
            print("First college:", json.dumps(js[0], indent=2))
except Exception as e:
    print("url1 error:", e)

# 2. Test searchCourse with different payloads
# Look at collegesearch.js:
# input["courseIds"] = $('#list_courses').val();
# input["stateIds"] = $('#list_states').val();
# input["univIds"] = $('#list_universities').val();
# input["collegeIds"] = $('#list_college').val();
# input["status"] = $("input[name='status']:checked").val();
# input["management"] = $("input[name='management']:checked").val();
# What are the default values when radio buttons are checked?
# In HTML page 1 screenshot:
# Status: All (value?), Management: All (value?)
