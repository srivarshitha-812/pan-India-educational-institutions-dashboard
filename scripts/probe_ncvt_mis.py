import urllib.request
import ssl
import re

def probe():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    url = 'https://ncvtmis.gov.in/Pages/ITI/Search.aspx'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            print('Status:', resp.status)
            html = resp.read().decode('utf-8', errors='ignore')
            print('Total HTML Length:', len(html))
            
            # ViewState and event targets
            viewstate = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html)
            print('ViewState found:', bool(viewstate), f"len={len(viewstate.group(1)) if viewstate else 0}")
            
            # Select dropdowns
            selects = re.findall(r'<select[^>]+id="([^"]+)"[^>]*>', html)
            print('Select elements:', selects)
            
            # Options in State dropdown
            state_match = re.search(r'<select[^>]+id="[^"]*ddlState[^"]*"[^>]*>(.*?)</select>', html, re.DOTALL | re.IGNORECASE)
            if not state_match:
                # Find any select containing state
                state_match = re.search(r'<select[^>]+name="[^"]*state[^"]*"[^>]*>(.*?)</select>', html, re.DOTALL | re.IGNORECASE)
            
            if state_match:
                opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', state_match.group(1))
                print(f'State Options found: {len(opts)}')
                for v, label in opts[:10]:
                    print(f'   val: {v} -> {label.strip()}')
            else:
                print('No State select dropdown found directly. Examining all selects:')
                for s_id in selects:
                    m = re.search(rf'<select[^>]+id="{re.escape(s_id)}"[^>]*>(.*?)</select>', html, re.DOTALL)
                    if m:
                        sub_opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m.group(1))
                        labels = [lbl.strip() for _, lbl in sub_opts[:5]]
                        print(f'   {s_id}: {len(sub_opts)} options -> {labels}')

    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    probe()
