import urllib.request, re

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://kys.udiseplus.gov.in/chunk-6EKXFX4V.js', headers=headers)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8', errors='replace')

print('chunk-6EKXFX4V.js length:', len(js))

# Look for URLs
urls = set(re.findall(r'https?://[a-zA-Z0-9_\-\./:]+', js))
print('\n=== URLs in chunk ===')
for u in sorted(urls):
    print('  ', u)

# Search for endpoint paths
endpoints = set(re.findall(r'["\'`](/[a-zA-Z0-9_\-\./\?=&]+)["\'`]', js))
filtered = [e for e in endpoints if any(k in e for k in ['school', 'kys', 'api', 'search', 'region', 'state', 'district', 'block', 'report', 'year'])]
print(f'\n=== API Endpoints ({len(filtered)}) ===')
for ep in sorted(filtered):
    print('  ', ep)

# Search for this.http calls
print('\n=== HTTP Calls ===')
for m in re.finditer(r'this\.http\.(?:get|post|put|delete)\([^;]+', js):
    print('  ', m.group(0)[:150])

# Search for pseudocode
pseudo = re.findall(r'.{0,30}pseudo.{0,30}', js, re.IGNORECASE)
print(f'\n=== Pseudocode matches: {len(pseudo)} ===')
for p in pseudo[:10]:
    print('  ', repr(p))
