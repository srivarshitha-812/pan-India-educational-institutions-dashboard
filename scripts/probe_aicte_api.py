import urllib.request, urllib.error, urllib.parse, ssl, re, json, gzip as gz_mod

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.aicte-india.org/",
}

def fetch(method, url, params=None, body=None, timeout=12):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    if body and isinstance(body, str):
        body = body.encode()
    h = dict(HEADERS)
    if body:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gz_mod.decompress(raw)
            return r.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        bd = ""
        try:
            bd = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, bd[:300]
    except Exception as ex:
        return 0, str(ex)

candidates = [
    ("GET", "https://www.aicte-india.org/Approved_Institute_List", {"draw": 1, "start": 0, "length": 5}, None),
    ("POST", "https://www.aicte-india.org/Approved_Institute_List", None, "draw=1&start=0&length=5"),
    ("GET", "https://facilities.aicte-india.org/dashboard/pages/admin-approvedist.php", {"draw": 1, "start": 0, "length": 5}, None),
    ("POST", "https://facilities.aicte-india.org/dashboard/pages/admin-approvedist.php", None, "draw=1&start=0&length=5"),
    ("GET", "https://www.aicte-india.org/api/getInstituteList", {"State": "Maharashtra", "draw": 1, "start": 0, "length": 5}, None),
    ("GET", "https://www.aicte-india.org/api/institutions", {"state": "Maharashtra", "page": 1, "limit": 10}, None),
    ("GET", "https://www.aicte-india.org/searchInstitute", {"State": "Maharashtra", "draw": 1, "start": 0, "length": 5}, None),
    ("GET", "https://www.aicte-india.org/", None, None),
    ("GET", "https://www.aicte-india.org/institutions", None, None),
]

for method, url, params, body in candidates:
    s, resp = fetch(method, url, params=params, body=body)
    preview = resp[:200].replace("\n", " ").strip()
    print(f"[{s}] {method} {url[:70]}  =>  {preview[:120]}")
    if s == 200 and resp.strip().startswith("{"):
        try:
            d = json.loads(resp)
            if isinstance(d, dict):
                print("   keys:", list(d.keys()))
                if "recordsTotal" in d:
                    print("   *** DataTables! total=", d["recordsTotal"])
        except Exception:
            pass
    if s == 200 and resp.strip().startswith("["):
        try:
            d = json.loads(resp)
            print("   *** JSON array len=", len(d))
        except Exception:
            pass
