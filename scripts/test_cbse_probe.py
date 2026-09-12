import sys
sys.path.insert(0, 'scripts')
from extract_cbse_saras import probe_json_endpoint, fetch_page_html, parse_html_table

print('Testing CBSE SARAS connection...')
try:
    has_json = probe_json_endpoint()
    print('has_json:', has_json)
    raw = fetch_page_html(draw=1, start=0, state_cd="AP", aff_status="")
    print('Raw fetched:', len(raw) if raw else 0, 'bytes')
    if raw:
        recs, total = parse_html_table(raw.decode('utf-8', errors='replace'))
        print(f'Parsed {len(recs)} records, total reported: {total}')
        if recs:
            print('Sample record:', recs[0])
except Exception as e:
    print('Error:', e)
