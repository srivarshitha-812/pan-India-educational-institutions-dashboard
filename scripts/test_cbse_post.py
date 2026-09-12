import urllib.request, urllib.parse
from bs4 import BeautifulSoup
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

url = "https://saras.cbse.gov.in/SARAS/AffiliatedList/ListOfSchdirReport"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}

# 1. GET page to obtain session cookies and tokens
req1 = urllib.request.Request(url, headers=headers)
with opener.open(req1, timeout=20) as resp1:
    html1 = resp1.read().decode("utf-8", errors="replace")

soup = BeautifulSoup(html1, "html.parser")
form = soup.find("form")

token = form.find("input", {"name": "__RequestVerificationToken"})["value"]
ncinfo = form.find("input", {"name": "__ncforminfo"})["value"]

print("Token len:", len(token), "ncinfo len:", len(ncinfo))

# Get all State options
state_select = form.find("select", {"name": "State"})
state_options = [(o["value"], o.get_text(strip=True)) for o in state_select.find_all("option") if o.get("value")]
print(f"Total state options: {len(state_options)}")
print("Sample state options:", state_options[:5])

# 2. POST with State_wise = '1' (Andhra Pradesh)
post_headers = dict(headers)
post_headers["Content-Type"] = "application/x-www-form-urlencoded"
post_headers["Referer"] = url
post_headers["Origin"] = "https://saras.cbse.gov.in"

post_data = urllib.parse.urlencode({
    "MainRadioValue": "State_wise",
    "State": "1",  # Andhra Pradesh
    "District": "",
    "__Invariant": "RegiAffNo",
    "RegiAffNo": "0",
    "__RequestVerificationToken": token,
    "__ncforminfo": ncinfo,
}).encode()

req2 = urllib.request.Request(url, data=post_data, headers=post_headers, method="POST")
with opener.open(req2, timeout=30) as resp2:
    html2 = resp2.read().decode("utf-8", errors="replace")
    print(f"POST response: status={resp2.status}, len={len(html2):,} chars")
    soup2 = BeautifulSoup(html2, "html.parser")
    table = soup2.find("table", id="myTable")
    if table:
        rows = table.find_all("tr")
        print(f"Found table with {len(rows)} rows!")
        if len(rows) > 1:
            for r in rows[1:4]:
                cells = [c.get_text(" ", strip=True) for c in r.find_all(["td", "th"])]
                print("  Row:", cells[:6])
