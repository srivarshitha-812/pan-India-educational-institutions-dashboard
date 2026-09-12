import urllib.request, re, ssl, json, gzip

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.nmc.org.in/information-desk/college-and-course-search/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='replace')

print("=== Radio Inputs ===")
for m in re.finditer(r'<input[^>]*name=[\'"](?:status|management)[\'"][^>]*>', html, re.I):
    print(m.group(0))

print("\n=== Select Elements ===")
for m in re.finditer(r'<select[^>]*id=[\'"]list_[^\'"]+[\'"][^>]*>', html, re.I):
    print(m.group(0))
