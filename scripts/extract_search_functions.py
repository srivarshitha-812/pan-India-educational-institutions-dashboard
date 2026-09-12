import urllib.request, re

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://kys.udiseplus.gov.in/chunk-6EKXFX4V.js', headers=headers)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8', errors='replace')

funcs = [
    'getSearch', 'getSchoolListBySearch', 'captchaVerify', 'getSchoolByAdvance',
    'getSchoolDetails', 'getschoolYearWise', 'getSchoolProfile', 'getSchoolEnrollDetail',
    'getSchoolTracking', 'getAllDistrict', 'getAllBlocks', 'getAllVillages', 'getAllClusters',
    'captchaGenerate'
]

for fn in funcs:
    pos = js.find(fn + '(')
    if pos != -1:
        print(f"==================== {fn} ====================")
        print(js[pos:pos+500])
        print()
