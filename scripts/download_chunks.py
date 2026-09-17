import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

chunks = {
    92: "b29fc2908f718ada",
    159: "2c5c446fdf8d94d9",
    337: "52e2d3e8e3776afe",
    735: "e99b1daaa3696639"
}

for chunk_id, hash_val in chunks.items():
    filename = f"{chunk_id}.{hash_val}.js"
    url = f"https://dashboard.aishe.gov.in/hedirectory/{filename}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
        print(f"Downloaded {filename}: {len(content)} bytes")
        with open(f"scratch/{filename}", "w", encoding="utf-8") as f:
            f.write(content)
        
        # Search for endpoints or collegeDetails
        if 'collegeDetails' in content:
            print(f"  *** collegeDetails FOUND in {filename} ***")
        
        # Find paths with /
        api_calls = set(re.findall(r'[\'"](/[^ \'",;()<>\[\]]+\b)[\'"]', content))
        relevant = [p for p in api_calls if any(k in p.lower() for k in ['college', 'inst', 'state', 'dist', 'univ', 'api', 'report', 'get'])]
        print(f"  Relevant paths in {filename} (sample 20):", relevant[:20])
    except Exception as e:
        print(f"Error fetching {filename}: {e}")
