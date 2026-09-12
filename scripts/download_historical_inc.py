import requests
import os

os.makedirs('data/raw/inc/historical', exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0'}

urls = [
    'https://www.indiannursingcouncil.org/uploads/pdf/ANM_19122023.pdf',
    'https://www.indiannursingcouncil.org/uploads/pdf/GNM_19122023_Final.pdf',
    'https://www.indiannursingcouncil.org/uploads/pdf/BSC_19122023_Final.pdf',
    'https://www.indiannursingcouncil.org/uploads/pdf/ANM_31032023.pdf',
    'https://www.indiannursingcouncil.org/uploads/pdf/GNM_31032023.pdf',
    'https://www.indiannursingcouncil.org/uploads/pdf/BSC_31032023.pdf',
]

for u in urls:
    fname = os.path.join('data/raw/inc/historical', u.split('/')[-1])
    if os.path.exists(fname) and os.path.getsize(fname) > 1000:
        print(f"Already downloaded: {fname} ({os.path.getsize(fname)} bytes)")
        continue
    print(f"Downloading {u} -> {fname}...")
    try:
        r = requests.get(u, headers=headers, stream=True, timeout=30)
        with open(fname, 'wb') as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        print(f"Saved {fname} ({os.path.getsize(fname)} bytes)")
    except Exception as e:
        print(f"Error downloading {u}: {e}")
