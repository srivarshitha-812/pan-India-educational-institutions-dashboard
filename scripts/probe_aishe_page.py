import urllib.request
import ssl
import re
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://dashboard.aishe.gov.in/hedirectory/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print('HTML length:', len(html))
    scripts = re.findall(r'<script[^>]*src=[\'"]([^\'"]+)[\'"]', html)
    print('Script sources:', scripts)
    selects = re.findall(r'<select[^>]*id=[\'"]([^\'"]+)[\'"]', html)
    print('Select IDs:', selects)
    title = re.findall(r'<title>(.*?)</title>', html, re.I)
    print('Title:', title)
    
    # Save a snippet or search for api calls
    Path('scratch/aishe_hedirectory.html').parent.mkdir(parents=True, exist_ok=True)
    with open('scratch/aishe_hedirectory.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved to scratch/aishe_hedirectory.html')
except Exception as e:
    print('Error:', e)
