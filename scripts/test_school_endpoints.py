import urllib.request, json

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'X-APP-SIGNATURE': '9f2c7a4b8e1d6c3f5a9b0e2d4f6a7c8b',
    'Referer': 'https://kys.udiseplus.gov.in/'
}

base_url = 'https://kys.udiseplus.gov.in/web-app/api/'

test_urls = [
    'school/report-card?udiseSchCode=36210200308',
    'school/report-card?udiseSchCode=36210200308&yearId=11',
    'school/report-card?udiseSchCode=36210200308&yearId=12',
    'school/by-year?udiseSchCode=36210200308&action=1',
    'school/facility?udiseSchCode=36210200308',
    'school-statistics/enrolment-teacher?udiseSchCode=36210200308&yearId=11',
    'school/track?schoolId=5454287',
]

for p in test_urls:
    url = base_url + p
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8')
            js = json.loads(data)
            print(f"\n[URL] {p}")
            print(f"Status: {js.get('status')}, Message: {js.get('message')}")
            if js.get('status'):
                print("Data preview:", str(js.get('data'))[:400])
            else:
                print("Error:", js.get('error'))
    except Exception as e:
        print(f"Exception for {p}: {e}")
