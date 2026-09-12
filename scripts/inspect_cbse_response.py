import sys
sys.path.insert(0, 'scripts')
from extract_cbse_saras import fetch_page_html
from bs4 import BeautifulSoup

raw = fetch_page_html(draw=1, start=0, state_cd="AP", aff_status="")
if raw:
    content = raw.decode('utf-8', errors='replace')
    soup = BeautifulSoup(content, 'html.parser')
    print('Title:', soup.title.get_text(strip=True) if soup.title else 'No title')
    tables = soup.find_all('table')
    print('Tables:', len(tables))
    forms = soup.find_all('form')
    print('Forms:', [(f.get('action'), f.get('id'), f.get('method')) for f in forms])
    scripts = soup.find_all('script')
    print('Scripts:', len(scripts))
    for s in scripts:
        txt = s.get_text()
        if 'ajax' in txt.lower() or 'datatable' in txt.lower() or 'url' in txt.lower():
            print('Script match:', txt[:400])
