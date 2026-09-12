import csv, urllib.request, json

# 1. Read first 5 pseudocodes
samples = []
with open('data/processed/UDISE_PLUS_2025_26_SCHOOLS.csv', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for i, row in enumerate(r):
        samples.append(row)
        if len(samples) >= 5:
            break

print(f"Sampled {len(samples)} records:")
for s in samples:
    print(f"  pseudocode={s['pseudocode']} (len {len(s['pseudocode'])}), state={s['state']}, district={s['district']}, block={s['block']}")

# 2. Test each pseudocode against KYS API
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'X-APP-SIGNATURE': '9f2c7a4b8e1d6c3f5a9b0e2d4f6a7c8b',
    'Referer': 'https://kys.udiseplus.gov.in/'
}
base_url = 'https://kys.udiseplus.gov.in/web-app/api/'

print("\n--- Testing pseudocodes against KYS endpoints ---")
for s in samples:
    pc = s['pseudocode']
    
    # Test as udiseSchCode
    for ep in [
        f"school/by-year?udiseSchCode={pc}&action=1",
        f"school/track?schoolId={pc}",
        f"school/profile?udiseSchCode={pc}&yearId=12",
        f"school/profile?schoolId={pc}&yearId=12",
        f"school/report-card?udiseSchCode={pc}&yearId=12"
    ]:
        url = base_url + ep
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read().decode('utf-8')
                js = json.loads(data)
                print(f"[TEST] {ep} -> status: {js.get('status')}, msg: {js.get('message')}")
        except urllib.error.HTTPError as e:
            print(f"[HTTP {e.code}] {ep}")
        except Exception as e:
            print(f"[ERR] {ep}: {e}")
