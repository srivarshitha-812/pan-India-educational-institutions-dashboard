"""
investigate_kys_school_search.py — Investigate KYS School Search API
======================================================================
The KYS API at https://kys.udiseplus.gov.in/web-app/api/ is confirmed working.

We need to:
1. Find the school search/lookup endpoint
2. Test if pseudocode (from UDISE+ research export) maps to KYS schoolId or udiseSchCode
3. Document the relationship definitively

Known working endpoints:
  GET /web-app/api/master/year?year=1  → returns year list (yearId 12 = 2025-26)
  GET /web-app/api/fetchCategoryList   → returns category list

Need to find:
  School search by name or code
  School lookup by UDISE code
  pseudocode → school name/UDISE code mapping
"""

import urllib.request, urllib.error
import json
import re

BASE = "https://kys.udiseplus.gov.in/web-app/api/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://kys.udiseplus.gov.in/",
    "Origin": "https://kys.udiseplus.gov.in",
}


def fetch(endpoint, extra_headers=None, method="GET", data=None):
    url = BASE + endpoint
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    req = urllib.request.Request(url, headers=hdrs, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw[:500]
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return e.code, body
    except Exception as ex:
        return 0, str(ex)


print("=" * 70)
print("KYS API COMPREHENSIVE ENDPOINT INVESTIGATION")
print("=" * 70)

# ── 1. Fetch and parse main.js to find API base URL ───────────────────────────
print("\n[1] Fetching main JS bundle for API URL discovery...")
js_url = "https://kys.udiseplus.gov.in/main-RCIDFHPD.js"
try:
    req = urllib.request.Request(js_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        js = resp.read().decode("utf-8", errors="replace")
        print(f"    JS bundle size: {len(js):,} chars")

        # Search for API URL patterns
        api_patterns = [
            r'https?://[a-zA-Z0-9\-\.]+udise[a-zA-Z0-9\-\.]*gov\.in[/a-zA-Z0-9\-_\.]*',
            r'"apiUrl"\s*:\s*"([^"]+)"',
            r'"baseUrl"\s*:\s*"([^"]+)"',
            r'"BASE_URL"\s*:\s*"([^"]+)"',
            r'environment\s*=\s*\{[^}]*\}',
            r'production:\s*!0.*?apiUrl:\s*"([^"]+)"',
        ]
        found_urls = set()
        for pat in api_patterns:
            matches = re.findall(pat, js, re.I)
            for m in matches:
                if "udise" in m.lower() or "kys" in m.lower() or "api" in m.lower():
                    found_urls.add(m)
        print(f"    API URLs found in JS: {list(found_urls)[:10]}")

        # Look for endpoint names
        ep_patterns = re.findall(r'"(/[a-zA-Z0-9\-_/]+)"', js)
        api_eps = [ep for ep in ep_patterns if any(k in ep for k in ("school", "api/", "search", "udise", "master", "fetch"))]
        print(f"    Possible API endpoints in JS: {api_eps[:20]}")
except Exception as e:
    print(f"    Error fetching JS: {e}")

# ── 2. Probe all known endpoint patterns ──────────────────────────────────────
print("\n[2] Probing known API endpoint patterns...")

SAMPLE_PSEUDOCODES = ["9664514", "4684147", "8904089", "1837010", "6327270"]
YEAR_ID = 12  # 2025-26

endpoints_to_test = [
    # School search by name
    f"school/search?name=Government&yearId={YEAR_ID}",
    f"school/search?q=Government&yearId={YEAR_ID}",
    f"school/searchSchool?name=Government&yearId={YEAR_ID}",

    # School lookup by UDISE code
    f"school/by-year?udiseSchCode={SAMPLE_PSEUDOCODES[0]}&yearId={YEAR_ID}&action=1",
    f"school/by-year?udiseSchCode={SAMPLE_PSEUDOCODES[0]}&action=1",
    f"school/track?schoolId={SAMPLE_PSEUDOCODES[0]}",
    f"school/profile?udiseSchCode={SAMPLE_PSEUDOCODES[0]}&yearId={YEAR_ID}",
    f"school/report-card?udiseSchCode={SAMPLE_PSEUDOCODES[0]}&yearId={YEAR_ID}",

    # Master endpoints
    "master/state",
    "master/state?yearId=12",
    "fetchManagementList",
    "fetchManagementList?yearId=12",

    # By state/district
    f"school/list?stateId=1&yearId={YEAR_ID}&page=1&size=5",
    f"school/getSchoolByDistrict?stateId=1&districtId=1&yearId={YEAR_ID}",

    # Alternative search paths
    f"searchSchool?name=GOVERNMENT&stateId=1&yearId={YEAR_ID}",
    f"school?udiseCode={SAMPLE_PSEUDOCODES[0]}&yearId={YEAR_ID}",
    f"schoolInfo?schoolId={SAMPLE_PSEUDOCODES[0]}&yearId={YEAR_ID}",
]

results = {}
for ep in endpoints_to_test:
    status, data = fetch(ep)
    preview = ""
    if isinstance(data, dict):
        preview = f"keys={list(data.keys())[:5]}"
        if data.get("status") == True or data.get("httpStatus") == 200:
            if data.get("data"):
                preview += f", data_type={type(data['data']).__name__}"
                if isinstance(data["data"], list):
                    preview += f", count={len(data['data'])}"
                    if data["data"]:
                        preview += f", first_keys={list(data['data'][0].keys())[:8] if isinstance(data['data'][0], dict) else '...'}"
                elif isinstance(data["data"], dict):
                    preview += f", data_keys={list(data['data'].keys())[:8]}"
    elif isinstance(data, str):
        preview = data[:150]

    print(f"  [{status}] {ep}")
    print(f"         {preview}")
    results[ep] = {"status": status, "preview": preview}
    if isinstance(data, dict) and data.get("status") == True and data.get("data"):
        print(f"  *** WORKING ENDPOINT FOUND: {ep} ***")
        if isinstance(data["data"], list) and len(data["data"]) > 0:
            first = data["data"][0]
            if isinstance(first, dict):
                print(f"  Sample record keys: {list(first.keys())}")
                print(f"  Sample record: {json.dumps(first, indent=2)[:500]}")

# ── 3. Test pseudocodes specifically ──────────────────────────────────────────
print("\n[3] Testing UDISE+ pseudocodes against KYS endpoints...")
print("    (If pseudocode == schoolId, we get school name + UDISE code)")

working_endpoints = []
for pc in SAMPLE_PSEUDOCODES[:3]:
    for ep_template in [
        f"school/by-year?udiseSchCode={pc}&yearId=12&action=1",
        f"school/by-year?udiseSchCode={pc}&action=1",
        f"school/track?schoolId={pc}",
        f"school/profile?schoolId={pc}&yearId=12",
        f"school/reportCard?udiseSchCode={pc}&yearId=12",
    ]:
        status, data = fetch(ep_template)
        if isinstance(data, dict) and data.get("status") == True and data.get("data"):
            d = data["data"]
            if (isinstance(d, list) and d) or (isinstance(d, dict) and d):
                print(f"\n  *** MATCH for pseudocode {pc}! ***")
                print(f"  Endpoint: {ep_template}")
                print(f"  Response: {json.dumps(data, indent=2)[:800]}")
                working_endpoints.append((pc, ep_template, data))
        elif status not in (404, 0):
            if isinstance(data, dict):
                print(f"  [{status}] pc={pc} ep={ep_template}: {data.get('message', str(data)[:80])}")

# ── 4. Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Working KYS API base: {BASE}")
print(f"Confirmed endpoints: /master/year, /fetchCategoryList")
print(f"Pseudocode→KYS matches found: {len(working_endpoints)}")
if working_endpoints:
    print("  CONCLUSION: UDISE+ pseudocode CAN be used to look up schools via KYS API")
else:
    print("  CONCLUSION: UDISE+ pseudocode does NOT directly map to KYS udiseSchCode")
    print("  The pseudocode in the DSP research export is an anonymized identifier")
    print("  NOT equivalent to the real UDISE school code used in KYS lookups")
