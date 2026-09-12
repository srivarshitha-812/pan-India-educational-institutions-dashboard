import urllib.request
from bs4 import BeautifulSoup

url = 'https://coa.gov.in/institutionStatus.php'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read().decode('utf-8', errors='replace')
        print(f'Status: {resp.status}, length: {len(content):,} chars')
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        print(f'Tables found: {len(tables)}')
        for i, t in enumerate(tables):
            rows = t.find_all('tr')
            print(f' Table {i}: {len(rows)} rows')
            if rows:
                first = [c.get_text(strip=True) for c in rows[0].find_all(['th', 'td'])]
                print(f'   Header: {first[:6]}')
                if len(rows) > 1:
                    sample = [c.get_text(strip=True) for c in rows[1].find_all(['th', 'td'])]
                    print(f'   Sample row: {sample[:6]}')
except Exception as e:
    print('Error:', e)
