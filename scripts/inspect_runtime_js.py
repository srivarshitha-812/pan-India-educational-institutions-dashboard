import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://dashboard.aishe.gov.in/hedirectory/runtime.e9922a690e161171.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    runtime_js = resp.read().decode('utf-8', errors='ignore')

print('Runtime JS length:', len(runtime_js))
# Look for chunk mapping, e.g. {337: "hash"}
chunk_map = re.findall(r'(\{[0-9]+:[^\}]+\})', runtime_js)
for m in chunk_map:
    print('Chunk map:', m[:200])

# Look for .js in runtime
print('All matches of .js in runtime:', re.findall(r'(\w+\.[a-f0-9]+\.js)', runtime_js))
