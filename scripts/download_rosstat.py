import os, ssl, sys, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "data", "rosstat")
os.makedirs(OUT, exist_ok=True)

CTX = ssl._create_unverified_context()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
BASE = "https://rosstat.gov.ru"

FILES = [
    ("Region_Pokaz_2025.rar", "/storage/mediabank/Region_Pokaz_2025.rar"),
    ("Region_Pokaz_2025.pdf", "/storage/mediabank/Region_Pokaz_2025.pdf"),
]

for name, path in FILES:
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 100000:
        print("[skip] %s уже есть (%d байт)" % (name, os.path.getsize(dest)))
        continue
    url = BASE + urllib.parse.quote(path) if False else BASE + path
    try:
        req = urllib.request.Request(url, headers=H)
        with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
            total = int(r.headers.get("Content-Length") or 0)
            print("[get ] %s (%.1f МБ)" % (name, total / 1e6), flush=True)
            got = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    got += len(chunk)
                    if got % (10 << 20) < (1 << 20):
                        print("   %.1f МБ" % (got / 1e6), flush=True)
        print("[ok  ] %s -> %d байт" % (name, os.path.getsize(dest)), flush=True)
    except Exception as e:
        print("[err ] %s: %s" % (name, repr(e)[:150]), flush=True)
