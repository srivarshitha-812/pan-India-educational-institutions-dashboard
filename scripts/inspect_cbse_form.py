import sys
sys.path.insert(0, 'scripts')
from extract_cbse_saras import fetch_page_html
from bs4 import BeautifulSoup

raw = fetch_page_html(draw=1, start=0, state_cd="AP", aff_status="")
soup = BeautifulSoup(raw.decode('utf-8', errors='replace'), 'html.parser')

form = soup.find('form')
if form:
    inputs = form.find_all(['input', 'select', 'button'])
    print('Form inputs/selects:')
    for inp in inputs:
        print(f"  {inp.name} ({inp.get('type', inp.name)}): val='{inp.get('value', '')}'")

table = soup.find('table', id='myTable')
if not table:
    table = soup.find('table')
if table:
    rows = table.find_all('tr')
    print(f'Table rows: {len(rows)}')
    for r in rows[:5]:
        print('  Row:', [c.get_text(strip=True) for c in r.find_all(['th', 'td'])])
