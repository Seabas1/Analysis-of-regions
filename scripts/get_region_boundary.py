import json, os, ssl, sys, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CTX = ssl._create_unverified_context()
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "data", "osm")

url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&polygon_geojson=1&q="
       + urllib.parse.quote("Саратовская область, Россия"))
req = urllib.request.Request(url, headers={"User-Agent": "region-econ-research/1.0 (student research)"})
with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
    js = json.loads(r.read().decode("utf-8"))

if not js:
    raise SystemExit("Nominatim не вернул результат")
item = js[0]
geo = item.get("geojson") or {}
print("тип геометрии:", geo.get("type"))
path = os.path.join(OUT, "region_boundary.geojson")
json.dump(geo, open(path, "w", encoding="utf-8"), ensure_ascii=False)
print("сохранено:", path)


def rings(geom):
    out = []
    if geom.get("type") == "Polygon":
        out.append(geom["coordinates"])
    elif geom.get("type") == "MultiPolygon":
        out.extend(geom["coordinates"])
    return out


poly = rings(geo)
print("полигонов:", len(poly), "| точек в первом:", len(poly[0][0]) if poly else 0)
