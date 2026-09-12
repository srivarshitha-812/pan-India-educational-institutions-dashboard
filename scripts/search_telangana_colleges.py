import requests, json

def search():
    queries = [
        'https://data.opencity.in/api/3/action/package_search?q=telangana+colleges',
        'https://data.opencity.in/api/3/action/package_search?q=telangana+education',
        'https://data.opencity.in/api/3/action/package_search?q=college',
        'https://data.opencity.in/api/3/action/package_search?q=intermediate'
    ]

    for q in queries:
        try:
            r = requests.get(q, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()
            results = r.get('result', {}).get('results', [])
            print(f"=== Query: {q} -> Found {len(results)} packages ===")
            for pkg in results:
                title = pkg.get('title')
                print(f"- Title: {title}")
                for res in pkg.get('resources', []):
                    name = res.get('name')
                    fmt = res.get('format')
                    url = res.get('url')
                    print(f"   * Res: {name} | Fmt: {fmt} | URL: {url}")
        except Exception as e:
            print("Error querying:", e)

if __name__ == '__main__':
    search()
