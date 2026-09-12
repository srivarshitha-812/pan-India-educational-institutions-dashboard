"""
Quick test: Get full response from KYS school/track and school/profile
to confirm what fields are returned (especially school name, UDISE code).
"""
import urllib.request, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://kys.udiseplus.gov.in/",
}

BASE = "https://kys.udiseplus.gov.in/web-app/api/"

def get(ep):
    url = BASE + ep
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return 0, str(e)

# Test pseudocodes that returned True status
test_pcs = ["4545250", "4552494", "1024396", "5002144"]

print("=" * 60)
for pc in test_pcs:
    print(f"\n--- pseudocode: {pc} ---")

    # Test school/track
    s, d = get(f"school/track?schoolId={pc}")
    print(f"[track] status={s}")
    if isinstance(d, dict) and d.get("data"):
        print(f"  data keys: {list(d['data'].keys()) if isinstance(d['data'], dict) else type(d['data'])}")
        print(f"  FULL DATA: {json.dumps(d['data'], indent=2)[:1000]}")

    # Test school/profile with yearId=12
    s2, d2 = get(f"school/profile?schoolId={pc}&yearId=12")
    print(f"[profile yearId=12] status={s2}")
    if isinstance(d2, dict) and d2.get("data"):
        print(f"  data type: {type(d2['data'])}")
        print(f"  FULL DATA: {json.dumps(d2['data'], indent=2)[:1000]}")

    # Test without yearId
    s3, d3 = get(f"school/profile?schoolId={pc}")
    print(f"[profile no year] status={s3}")
    if isinstance(d3, dict) and d3.get("data"):
        print(f"  FULL DATA: {json.dumps(d3['data'], indent=2)[:500]}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("If 'data' above contains 'schoolName' or 'udiseCode' → pseudocode = KYS schoolId")
print("If 'data' is empty or missing those fields → no direct mapping")
