import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://dashboard.aishe.gov.in/hedirectory/main.6a3f3221b4aecf63.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
    print('JS Length:', len(content))
    with open('scratch/aishe_main.js', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Search for http/https URLs or api paths
    urls = set(re.findall(r'https?://[a-zA-Z0-9\.\_\:\/\-]+', content))
    print('Found URLs:', [u for u in urls if 'aishe' in u or 'nic.in' in u or 'api' in u or 'dashboard' in u])
    
    # Search for api paths like /api/ or similar
    paths = set(re.findall(r'[\'"](/[\w\-\.\/]+)[\'"]', content))
    api_paths = [p for p in paths if any(k in p.lower() for k in ['college', 'inst', 'state', 'dist', 'univ', 'directory', 'list', 'search', 'heis', 'master'])]
    print('Found API paths (sample 30):', api_paths[:30])

except Exception as e:
    print('Error:', e)
