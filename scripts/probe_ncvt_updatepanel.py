"""
probe_ncvt_updatepanel.py — Test ASP.NET UpdatePanel / ScriptManager approach

The NCVT MIS portal uses ASP.NET UpdatePanel. The search form POST
with X-MicrosoftAjax: Delta=true returns pipe-delimited response with
updated HTML fragments for just the results panel.
"""
import sys, os, re, urllib.request, urllib.parse, ssl, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

NCVT_SEARCH_URL = "https://ncvtmis.gov.in/Pages/ITI/Search.aspx"

HEADERS_GET = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

HEADERS_AJAX = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": NCVT_SEARCH_URL,
    "X-MicrosoftAjax": "Delta=true",
    "X-Requested-With": "XMLHttpRequest",
}


def get(url, data=None, ajax=False):
    hdrs = HEADERS_AJAX if ajax else HEADERS_GET
    if data is not None and not ajax:
        hdrs = dict(hdrs)
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


print("Step 1: Load initial page and get ViewState...")
html0 = get(NCVT_SEARCH_URL)

vs = extract_field(html0, "__VIEWSTATE")
vsg = extract_field(html0, "__VIEWSTATEGENERATOR")
ev = extract_field(html0, "__EVENTVALIDATION")
vsenc = extract_field(html0, "__VIEWSTATEENCRYPTED")

# Look for ScriptManager and UpdatePanel IDs
sm_m = re.search(r'Sys\.WebForms\.PageRequestManager\._initialize\([\'"]([^\'"]+)[\'"].*?,\s*[\'"]([^\'"]+)[\'"]', html0)
if sm_m:
    print(f"  ScriptManager: {sm_m.group(1)}, Form: {sm_m.group(2)}")

# Find UpdatePanel triggers
panels = re.findall(r'UpdatePanel.*?(?=[,)])', html0)
print(f"  UpdatePanel refs: {panels[:10]}")

states = extract_select(html0, "cphBody_lbState")
print(f"  States: {len(states)}")
print(f"  ViewState length: {len(vs)}")

# Target: GOA or ANDAMAN (small states)
target_state = None
for val, lbl in states:
    if "GOA" in lbl.upper():
        target_state = (val, lbl.strip())
        break
if not target_state:
    for val, lbl in states:
        if val not in ("-1", ""):
            target_state = (val, lbl.strip())
            break

print(f"\nUsing state: {target_state}")

print("\nStep 2: Select state via AJAX UpdatePanel postback...")
ajax_state_data = urllib.parse.urlencode({
    "ctl00$ctl12": "ctl00$cphBody$UpdatePanel1|ctl00$cphBody$lbState",
    "__EVENTTARGET": "ctl00$cphBody$lbState",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": vs,
    "__VIEWSTATEGENERATOR": vsg,
    "__VIEWSTATEENCRYPTED": vsenc,
    "__EVENTVALIDATION": ev,
    "ctl00$cphBody$lbState": target_state[0],
    "ctl00$cphBody$lbDistrict": "",
    "ctl00$cphBody$lbTrade": "",
    "ctl00$cphBody$ddlScheme": "-1",
    "ctl00$cphBody$ddlITIScheme": "-1",
    "ctl00$cphBody$ddlOtherCategory": "-1",
    "__ASYNCPOST": "true",
}).encode("utf-8")

resp1 = get(NCVT_SEARCH_URL, data=ajax_state_data, ajax=True)
print(f"  AJAX state response length: {len(resp1)}")
# Save it
Path("data/raw/ncvt/ajax_state_response.txt").write_text(resp1, encoding="utf-8")
print("  AJAX state response saved.")

# Parse districts from AJAX response
districts = extract_select(resp1, "ctl00_cphBody_lbDistrict")
if not districts:
    districts = extract_select(resp1, "cphBody_lbDistrict")
print(f"  Districts in AJAX response: {len(districts)}")
if districts:
    print(f"  First 5: {districts[:5]}")

# Extract updated ViewState from AJAX response
vs2 = ""
for field in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
    m = re.search(rf'\|hiddenField\|{re.escape(field)}\|([^|]+)', resp1)
    if m:
        if field == "__VIEWSTATE":
            vs2 = m.group(1)
        print(f"  Updated {field}: {m.group(1)[:80]}...")

# Now try direct search with no district (just state)
print("\nStep 3: AJAX search for state (no district)...")
ajax_search_data = urllib.parse.urlencode({
    "ctl00$ctl12": "ctl00$cphBody$UpdatePanel1|ctl00$cphBody$btnSubmit",
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": vs2 or vs,
    "__VIEWSTATEGENERATOR": vsg,
    "__VIEWSTATEENCRYPTED": vsenc,
    "__EVENTVALIDATION": "",  # AJAX responses may omit EventValidation
    "ctl00$cphBody$lbState": target_state[0],
    "ctl00$cphBody$lbDistrict": "",
    "ctl00$cphBody$lbTrade": "",
    "ctl00$cphBody$ddlScheme": "-1",
    "ctl00$cphBody$ddlITIScheme": "-1",
    "ctl00$cphBody$ddlOtherCategory": "-1",
    "ctl00$cphBody$btnSubmit": "Search",
    "__ASYNCPOST": "true",
}).encode("utf-8")

resp2 = get(NCVT_SEARCH_URL, data=ajax_search_data, ajax=True)
print(f"  AJAX search response length: {len(resp2)}")
Path("data/raw/ncvt/ajax_search_response.txt").write_text(resp2, encoding="utf-8")

# Look for table data in AJAX response
tables = re.findall(r'<table[^>]*>.*?</table>', resp2, re.DOTALL | re.IGNORECASE)
print(f"  Tables in AJAX response: {len(tables)}")
for i, t in enumerate(tables):
    rows = re.findall(r'<tr[^>]*>.*?</tr>', t, re.DOTALL)
    if len(rows) > 1:
        cells0 = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)
        hdr = [re.sub(r'<[^>]+>', '', c).strip() for c in cells0]
        print(f"  Table {i}: {len(rows)} rows — Header: {hdr}")

# Check error or no-records message
error_m = re.search(r'(No\s+records?\s+found|No\s+data|0\s+records)', resp2, re.IGNORECASE)
if error_m:
    print(f"  [NOTE] Found: '{error_m.group(0)}'")

print("\nDone. Check data/raw/ncvt/ajax_*.txt for raw responses.")
