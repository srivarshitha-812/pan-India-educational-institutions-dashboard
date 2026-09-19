import json
import re
import ssl
import urllib.request
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def probe_url(url, label):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, context=ctx, timeout=20).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if any(k in (href+text).lower() for k in ['iti', 'institute', 'directory', 'cts', 'cits', 'affiliated', 'vocational', 'institutions', 'list', 'training', 'awarding']):
                links.append({"text": text, "href": href})
        return {"status": "ok", "title": soup.title.string if soup.title else "", "links": links}
    except Exception as e:
        return {"status": "error", "error": str(e)}

results = {
    "dgt": probe_url("https://dgt.gov.in/", "DGT"),
    "ncvet": probe_url("https://ncvet.gov.in/", "NCVET"),
    "ncvet_training": probe_url("https://ncvet.gov.in/en/training-centers/", "NCVET Training Centers"),
    "dgt_institutes": probe_url("https://dgt.gov.in/institutes", "DGT Institutes"),
    "dgt_iti": probe_url("https://dgt.gov.in/iti", "DGT ITI"),
}

with open("data/raw/ncvt/probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Saved probe results to data/raw/ncvt/probe_results.json")
