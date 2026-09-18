"""
ICAR Agricultural Institutions Dataset Extractor
Downloads all 4 official ICAR accreditation Excel files and extracts institutions.
"""
import os
import urllib.request
import time
from pathlib import Path

BASE_URL = "https://icar.org.in"
DOWNLOAD_DIR = Path("data/icar_raw")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

ICAR_FILES = [
    {
        "name": "List-1",
        "title": "List of ICAR Accredited Agricultural SAUs DUs CAUs Universities their Colleges and degree programmes",
        "url": "/sites/default/files/Circulars/List%20of%20ICAR%20Accredited%20Agricultural%20SAUs%20DUs%20CAUs%20Universities%20their%20Colleges%20and%20degree%20programmes-List%201.xlsx",
        "category": "Agricultural Universities (SAUs/DUs/CAUs) with Colleges and Programmes",
        "filename": "ICAR_List1_SAUs_DUs_CAUs_Universities_Colleges_Programmes.xlsx"
    },
    {
        "name": "List-1A",
        "title": "List of ICAR Accredited Constituent Colleges or Faculties of Agricultural Universities and their programmes",
        "url": "/sites/default/files/Circulars/List%20of%20ICAR%20Accredited%20Constituent%20Colleges%20or%20%20Faculties%20of%20Agricultural%20Universities%20and%20their%20programmes-List-1A.xlsx",
        "category": "Constituent Colleges or Faculties of Agricultural Universities",
        "filename": "ICAR_List1A_Constituent_Colleges_Faculties.xlsx"
    },
    {
        "name": "List-2",
        "title": "List of ICAR Accredited Private Colleges Affiliated to SAUs General Universities (Private and Public)",
        "url": "/sites/default/files/Circulars/List%20of%20%20ICAR%20Accredited%20Private%20Colleges%20Affliated%20to%20SAUs%20General%20Universities%20%28Private%20and%20Public%29-List-II.xlsx",
        "category": "Private/Public Colleges Affiliated to SAUs and General Universities",
        "filename": "ICAR_List2_Private_Public_Affiliated_Colleges.xlsx"
    },
    {
        "name": "List-3",
        "title": "List of ICAR Accredited Constituent affiliated Colleges Programmes of General Universities (Public)",
        "url": "/sites/default/files/Circulars/List%20of%20ICAR%20Accredited%20Constituent%20affiliated%20Colleges%20Programmes%20of%20General%20Universities%20%28Public%29-%20List-III.xlsx",
        "category": "Constituent/Affiliated Colleges of General Universities (Public)",
        "filename": "ICAR_List3_Constituent_Affiliated_General_Universities_Public.xlsx"
    }
]

print("=" * 70)
print("ICAR ACCREDITATION LIST DOWNLOADER")
print("Source: https://icar.org.in/en/list-accreditation-status-agricultural-universitiescollegesinstitutionprogrammes")
print("=" * 70)
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*',
    'Referer': 'https://icar.org.in/en/list-accreditation-status-agricultural-universitiescollegesinstitutionprogrammes'
}

for file_info in ICAR_FILES:
    full_url = BASE_URL + file_info["url"]
    dest_path = DOWNLOAD_DIR / file_info["filename"]
    
    print(f"Downloading: {file_info['name']} - {file_info['title']}")
    print(f"  URL: {full_url}")
    print(f"  Saving to: {dest_path}")
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            with open(dest_path, 'wb') as f:
                f.write(content)
            size_kb = len(content) / 1024
            print(f"  SUCCESS: {size_kb:.1f} KB downloaded")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    time.sleep(1)

print()
print("Download complete. Files saved to:", DOWNLOAD_DIR)
print("Files in directory:")
for f in sorted(DOWNLOAD_DIR.iterdir()):
    print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")
