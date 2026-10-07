import os, ssl, sys, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CTX = ssl._create_unverified_context()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "data", "osm")
os.makedirs(OUT, exist_ok=True)
dest = os.path.join(OUT, "volga-fed-district-latest.osm.pbf")
url = "https://download.geofabrik.de/russia/volga-fed-district-latest.osm.pbf"

if os.path.exists(dest) and os.path.getsize(dest) > 7e8:
    print("[skip] уже скачан: %.2f ГБ" % (os.path.getsize(dest) / 1e9))
    raise SystemExit

req = urllib.request.Request(url, headers=H)
with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
    total = int(r.headers.get("Content-Length") or 0)
    print("[get ] %.2f ГБ" % (total / 1e9), flush=True)
    got = 0
    mark = 0
    with open(dest, "wb") as f:
        while True:
            chunk = r.read(4 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if got // (100 << 20) > mark:
                mark = got // (100 << 20)
                print("   %.0f%% (%.2f ГБ)" % (100.0 * got / max(total, 1), got / 1e9), flush=True)
print("[ok  ] %s: %.2f ГБ" % (dest, os.path.getsize(dest) / 1e9))
