import sys
sys.path.insert(0, 'scripts')
from extract_cbse_saras import fetch_page_html
from bs4 import BeautifulSoup

raw = fetch_page_html(draw=1, start=0, state_cd="AP", aff_status="")
soup = BeautifulSoup(raw.decode('utf-8', errors='replace'), 'html.parser')

form = soup.find('form')
for inp in form.find_all(['input', 'select']):
    name = inp.get('name')
    id_ = inp.get('id')
    typ = inp.get('type', inp.name)
    val = inp.get('value', '')
    if typ == 'select':
        opts = [(o.get('value'), o.get_text(strip=True)) for o in inp.find_all('option')]
        print(f"SELECT name='{name}' id='{id_}': {len(opts)} options, sample={opts[:4]}")
    elif typ == 'radio':
        print(f"RADIO name='{name}' id='{id_}' value='{val}'")
    elif typ == 'hidden':
        print(f"HIDDEN name='{name}' id='{id_}' len={len(val)}")
    else:
        print(f"INPUT ({typ}) name='{name}' id='{id_}' value='{val}'")
