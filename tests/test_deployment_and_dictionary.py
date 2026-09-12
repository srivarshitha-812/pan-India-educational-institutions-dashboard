import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url):
    req = urllib.request.urlopen(url)
    assert req.status == 200, f"Failed status {req.status} for {url}"
    body = req.read()
    content_type = req.headers.get("Content-Type", "")
    if "json" in content_type:
        return json.loads(body.decode("utf-8"))
    return body

print("=== 1. Testing Summary Endpoint ===")
summary = test_endpoint(f"{BASE_URL}/api/summary")
kpis = summary["kpis"]
print(f"  States Covered: {kpis['states_covered']}/{kpis['total_states_target']}")
print(f"  Final Records: {kpis['total_records_final']}")
assert kpis['states_covered'] == 36, f"Expected 36 states, got {kpis['states_covered']}"
assert kpis['total_records_final'] == 7335, f"Expected 7,335 records, got {kpis['total_records_final']}"

print("\n=== 2. Testing Path Sanitization (Security Check) ===")
sources = test_endpoint(f"{BASE_URL}/api/datasets/sources")
for d in sources["datasets"]:
    fp = d.get("file_path", "")
    assert not ("C:\\" in fp or "c:\\" in fp or "Users" in fp), f"Security Leak: Path exposed: {fp}"
print(f"  Passed! All {len(sources['datasets'])} source dataset paths are properly sanitized relative paths.")

final_lists = test_endpoint(f"{BASE_URL}/api/datasets/final")
for l in final_lists["lists"]:
    fp = l.get("file_path", "")
    assert not ("C:\\" in fp or "c:\\" in fp or "Users" in fp), f"Security Leak: Path exposed: {fp}"
print(f"  Passed! All {len(final_lists['lists'])} final list paths are properly sanitized relative paths.")

print("\n=== 3. Testing Data Dictionary Endpoints ===")
dict_data = test_endpoint(f"{BASE_URL}/api/dictionary?page=1&page_size=200")
print(f"  Total fields documented: {dict_data['total_fields']}")
print(f"  Datasets available: {len(dict_data['available_datasets'])}")
assert dict_data['total_fields'] >= 90, f"Expected at least 90 fields, got {dict_data['total_fields']}"

# Test dataset filter
dict_udise = test_endpoint(f"{BASE_URL}/api/dictionary?dataset=UDISE%2B%20National%20Schools%20Register")
print(f"  UDISE+ fields: {dict_udise['total_fields']}")
assert dict_udise['total_fields'] == 32, f"Expected 32 UDISE+ fields, got {dict_udise['total_fields']}"

# Test field classification filter
dict_source = test_endpoint(f"{BASE_URL}/api/dictionary?field_classification=SOURCE%20FIELD")
print(f"  SOURCE FIELD count: {dict_source['total_fields']}")
assert dict_source['total_fields'] >= 50, f"Expected >= 50 source fields, got {dict_source['total_fields']}"

# Test search query
dict_search = test_endpoint(f"{BASE_URL}/api/dictionary?search=intake")
print(f"  Search for 'intake': {dict_search['total_fields']} matches")
assert dict_search['total_fields'] >= 2, "Expected matches for intake"

print("\n=== 4. Testing Global Search Requirements (Regression Prevention) ===")
# 1. Gachibowli -> IIIT Hyderabad
gachi = test_endpoint(f"{BASE_URL}/api/search?q=Gachibowli")
print(f"  'Gachibowli' matches: {gachi['total_matches']}")
assert any("International Institute" in r['institution'] or "IIIT" in r['institution'] for r in gachi['results'])

# 2. KPHB -> JNTUH
kphb = test_endpoint(f"{BASE_URL}/api/search?q=KPHB")
print(f"  'KPHB' matches: {kphb['total_matches']}")
assert any("JNTU" in r['institution'] or "Jawaharlal" in r['institution'] for r in kphb['results'])

# 3. Hyderabad
hyd = test_endpoint(f"{BASE_URL}/api/search?q=Hyderabad")
print(f"  'Hyderabad' matches: {hyd['total_matches']}")
assert hyd['total_matches'] >= 100

# 4. Exact District Name: Ranga Reddy
rr = test_endpoint(f"{BASE_URL}/api/search?q=Ranga%20Reddy")
print(f"  'Ranga Reddy' matches: {rr['total_matches']}")
assert rr['total_matches'] >= 15

print("\n=== 5. Testing Download Endpoint ===")
dl = test_endpoint(f"{BASE_URL}/api/dictionary/download")
print(f"  Download payload size: {len(dl):,} bytes")
assert len(dl) > 20000, "Downloaded Excel workbook is too small"

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! DEPLOYMENT & DICTIONARY READY <<<")
