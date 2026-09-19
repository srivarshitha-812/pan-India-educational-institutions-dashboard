"""
probe_ncvt_search_results.py — Inspect NCVT MIS search results HTML structure
"""
import sys, os, re, urllib.request, urllib.parse, ssl, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": NCVT_SEARCH_URL,
}


def get(url, data=None, extra_hdrs=None):
    hdrs = dict(HEADERS)
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    if data is not None:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    time.sleep(1.5)
    req = urllib.request.Request(url, data=data, headers=hdrs)
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_field(html, field_id):
    m = re.search(rf'id="{re.escape(field_id)}"\s+value="([^"]*)"', html)
    return m.group(1) if m else ""


def extract_select(html, select_id):
    m = re.search(rf'<select[^>]+id="{re.escape(select_id)}"[^>]*>(.*?)</select>', html, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    return re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m.group(1), re.DOTALL)


print("Step 1: Load initial search page...")
html0 = get(NCVT_SEARCH_URL)

vs = extract_field(html0, "__VIEWSTATE")
vsg = extract_field(html0, "__VIEWSTATEGENERATOR")
ev = extract_field(html0, "__EVENTVALIDATION")
states = extract_select(html0, "cphBody_lbState")

print(f"  ViewState len: {len(vs)}")
print(f"  States found: {len(states)}")
if states:
    print(f"  First 5 states: {states[:5]}")

# Pick a small state: Goa (usually has ~50 ITIs)
target_state = None
for val, lbl in states:
    if "GOA" in lbl.upper() or "ANDAMAN" in lbl.upper():
        target_state = (val, lbl.strip())
        break

if not target_state:
    for val, lbl in states:
        if val not in ("-1", "") and not lbl.strip().startswith("-"):
            target_state = (val, lbl.strip())
            break

print(f"\nStep 2: Selecting state: {target_state}")

# Post state selection
form_data = urllib.parse.urlencode({
    "__EVENTTARGET": "cphBody_lbState",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": vs,
    "__VIEWSTATEGENERATOR": vsg,
    "__EVENTVALIDATION": ev,
    "cphBody_lbState": target_state[0],
    "cphBody_lbDistrict": "",
    "cphBody_lbTrade": "",
    "cphBody_ddlScheme": "-1",
    "cphBody_ddlITIScheme": "-1",
    "cphBody_ddlOtherCategory": "-1",
}).encode("utf-8")

html1 = get(NCVT_SEARCH_URL, data=form_data)
vs1 = extract_field(html1, "__VIEWSTATE") or vs
vsg1 = extract_field(html1, "__VIEWSTATEGENERATOR") or vsg
ev1 = extract_field(html1, "__EVENTVALIDATION") or ev
districts = extract_select(html1, "cphBody_lbDistrict")
print(f"  Districts for {target_state[1]}: {len(districts)}")
if districts:
    print(f"  Districts: {districts[:5]}")

# Try state-level search (no district filter)
print(f"\nStep 3: State-level search (no district)...")
form_search = urllib.parse.urlencode({
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": vs1,
    "__VIEWSTATEGENERATOR": vsg1,
    "__EVENTVALIDATION": ev1,
    "cphBody_lbState": target_state[0],
    "cphBody_lbDistrict": "",
    "cphBody_lbTrade": "",
    "cphBody_ddlScheme": "-1",
    "cphBody_ddlITIScheme": "-1",
    "cphBody_ddlOtherCategory": "-1",
    "cphBody_btnSubmit": "Search",
}).encode("utf-8")

html2 = get(NCVT_SEARCH_URL, data=form_search)

# Find all tables
tables = re.findall(r'(<table[^>]*>.*?</table>)', html2, re.DOTALL | re.IGNORECASE)
print(f"  Tables found: {len(tables)}")

for i, t in enumerate(tables):
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL | re.IGNORECASE)
    print(f"  Table {i}: {len(rows)} rows, length={len(t)}")
    if rows:
        cells0 = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL | re.IGNORECASE)
        hdr = [re.sub(r'<[^>]+>', '', c).strip() for c in cells0]
        print(f"    Header: {hdr}")
    if len(rows) > 1:
        cells1 = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[1], re.DOTALL | re.IGNORECASE)
        row1 = [re.sub(r'<[^>]+>', '', c).strip() for c in cells1]
        print(f"    Row 1:  {row1}")

# Save raw HTML for inspection
out = BASE / "data" / "raw" / "ncvt" / "probe_search_results.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html2, encoding="utf-8")
print(f"\nRaw search HTML saved: {out}")
print(f"HTML length: {len(html2)}")

# Check for 'no record' indicators
if "no record" in html2.lower() or "no data" in html2.lower():
    print("[NOTE] Page contains 'no record' or 'no data' — may need district selection")

# Check for ITI keyword
iti_count = html2.lower().count("iti")
print(f"'ITI' keyword occurrences in result HTML: {iti_count}")
