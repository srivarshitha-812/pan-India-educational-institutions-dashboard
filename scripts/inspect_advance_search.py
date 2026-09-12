import urllib.request, re

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://kys.udiseplus.gov.in/chunk-LYTETKPR.js', headers=headers)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8', errors='replace')

print('chunk-LYTETKPR.js length:', len(js))

# Look for by-region
for m in re.finditer(r'by-region', js):
    pos = m.start()
    print('=== by-region at', pos, '===')
    print(js[max(0, pos-200):min(len(js), pos+400)])

# Look for search parameters / query strings built
for m in re.finditer(r'search-school', js):
    pos = m.start()
    print('=== search-school at', pos, '===')
    print(js[max(0, pos-150):min(len(js), pos+300)])
