import urllib.request, urllib.parse
from bs4 import BeautifulSoup

url = 'https://rciregistration.nic.in/rehabcouncil/instapproval_statewise.jsp'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://rciregistration.nic.in/rehabcouncil/filterapprovalinst.jsp'
}

body = urllib.parse.urlencode({
    'statewise': 'Andhra Pradesh',
    'Submit': 'Submit'
}).encode()

req = urllib.request.Request(url, data=body, headers=headers, method='POST')
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
                first_row = [c.get_text(strip=True) for c in rows[0].find_all(['th', 'td'])]
                print(f'   First row: {first_row[:6]}')
                if len(rows) > 1:
                    second_row = [c.get_text(strip=True) for c in rows[1].find_all(['th', 'td'])]
                    print(f'   Second row sample: {second_row[:4]}')
except Exception as e:
    print('Error:', e)
