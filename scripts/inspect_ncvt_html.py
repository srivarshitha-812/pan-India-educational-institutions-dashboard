from pathlib import Path
import re

html = Path('data/raw/ncvt/probe_search_results.html').read_text(encoding='utf-8')

# Print all input fields that look like form controls
inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
print('INPUT FIELDS:')
for inp in inputs:
    if 'cphBody' in inp or 'btnSubmit' in inp or 'VIEWSTATE' in inp:
        print(' ', inp[:200])

# Print all selects
selects = re.findall(r'<select[^>]*>', html, re.IGNORECASE)
print('\nSELECT FIELDS:')
for s in selects:
    print(' ', s[:200])

# Look at context around the search button
btn_m = re.search(r'.{500}btnSubmit.{500}', html, re.DOTALL)
if btn_m:
    print('\nContext around Search button:')
    print(re.sub(r'<[^>]{200,}>', '<...>', btn_m.group(0)))

# Look for "cphBody" references
cph = re.findall(r'cphBody_\w+', html)
print('\ncphBody IDs referenced:', sorted(set(cph)))
