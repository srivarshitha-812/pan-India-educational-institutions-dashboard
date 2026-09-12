import urllib.request, re, json

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://kys.udiseplus.gov.in/chunk-6EKXFX4V.js', headers=headers)
with urllib.request.urlopen(req) as resp:
    js = resp.read().decode('utf-8', errors='replace')

# Look for this.path = ...
paths = re.findall(r'this\.path\s*=\s*["\']([^"\']+)["\']', js)
print("this.path assignments:", paths)

# Look for headers
hdrs = re.findall(r'this\.headers\s*=\s*([^\;]+)', js)
print("\nthis.headers assignments:")
for h in hdrs[:5]:
    print("  ", h[:150])

# Find all methods in the service
methods = re.findall(r'([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*\{[^}]*this\.http[^}]*\}', js)
print(f"\nAll API service methods ({len(methods)}):")
for name, args in methods:
    # find body snippet
    pos = js.find(name + '(' + args + ')')
    body = js[pos:pos+250] if pos != -1 else ''
    print(f"\n--- {name}({args}) ---")
    print(body)
