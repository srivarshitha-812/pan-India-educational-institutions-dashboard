import os
import requests
import urllib.parse
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

base = 'https://vci.dahd.gov.in'

# First fetch home and act_rule pages to see all documents
os.makedirs('data/vci_raw', exist_ok=True)

pages = ['/', '/act_rule', '/contact-us']
all_doc_links = set()

for p in pages:
    url = urllib.parse.urljoin(base, p)
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            txt = a.get_text(strip=True)
            if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']) or any(k in txt.lower() for k in ['college', 'recogni', 'provis']):
                full_href = urllib.parse.urljoin(base, href)
                all_doc_links.add((txt, full_href))
    except Exception as e:
        print(f"Error crawling {p}: {e}")

print(f"Found {len(all_doc_links)} relevant document links:")
for txt, href in sorted(all_doc_links):
    print(f"  {txt} -> {href}")

# Download each
for txt, href in sorted(all_doc_links):
    parsed = urllib.parse.urlparse(href)
    fname = os.path.basename(urllib.parse.unquote(parsed.path))
    if not fname:
        continue
    out_path = os.path.join('data/vci_raw', fname)
    print(f"\nDownloading: {href} to {out_path}")
    try:
        res = requests.get(href, headers=headers, verify=False, timeout=30)
        print(f"  Status: {res.status_code}, Bytes: {len(res.content)}")
        if res.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(res.content)
    except Exception as e:
        print(f"  Error downloading: {e}")
