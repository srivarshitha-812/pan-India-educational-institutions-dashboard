import requests
from bs4 import BeautifulSoup

urls = [
    ('Feb_2026', 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2225755&lang=1&reg=3'),
    ('Dec_2025', 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2197614&lang=2&reg=3')
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for label, u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(['script', 'style', 'input']):
            s.decompose()
        print(f"=== {label} : {u} ===")
        main_div = soup.find('div', {'id': 'PdfDiv'}) or soup.body
        text = main_div.get_text() if main_div else soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_text = '\n'.join(lines)
        print(full_text[:1500])
        with open(f'data/raw/inc/pib_{label}.txt', 'w', encoding='utf-8') as out:
            out.write(full_text)
    except Exception as e:
        print(f"Error fetching {label}: {e}")
