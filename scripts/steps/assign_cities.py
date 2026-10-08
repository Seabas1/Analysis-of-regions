# -*- coding: utf-8 -*-
"""Привязка OSM-объектов к городам Саратовской области (по ближайшему населённому пункту).

В OSM поле addr:city заполнено редко, поэтому используем ближайший город
из списка (координаты берём в Nominatim и кэшируем).
"""
import csv, json, math, os, ssl, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CTX = ssl._create_unverified_context()
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OSMDIR = os.path.join(PROJECT, "data", "osm")

CITIES = ["Саратов", "Энгельс", "Балаково", "Балашов", "Вольск", "Ртищево", "Петровск",
          "Маркс", "Аткарск", "Пугачёв", "Ершов", "Красноармейск", "Новоузенск", "Хвалынск",
          "Красный Кут", "Аркадак", "Калининск", "Шиханы", "Александров Гай", "Степное",
          "Дергачи", "Озинки", "Татищево", "Советское", "Турки", "Ровное", "Воскресенское"]

cache = os.path.join(OSMDIR, "cities_geo.json")
if os.path.exists(cache):
    geo = json.load(open(cache, encoding="utf-8"))
else:
    geo = {}
    for name in CITIES:
        url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
               + urllib.parse.quote(name + ", Саратовская область, Россия"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "region-econ-research/1.0"})
            with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
                js = json.loads(r.read().decode("utf-8"))
            if js:
                geo[name] = (float(js[0]["lat"]), float(js[0]["lon"]))
                print("  %-20s %.4f, %.4f" % (name, geo[name][0], geo[name][1]))
            else:
                print("  %-20s не найден" % name)
        except Exception as e:
            print("  %-20s ошибка %s" % (name, repr(e)[:60]))
        time.sleep(1.1)
    json.dump(geo, open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("городов с координатами: %d" % len(geo))


def dist2(lat, lon, lat2, lon2):
    dlat = (lat - lat2) * 111.0
    dlon = (lon - lon2) * 111.0 * math.cos(math.radians((lat + lat2) / 2))
    return dlat * dlat + dlon * dlon


rows = list(csv.DictReader(open(os.path.join(OSMDIR, "objects.csv"), encoding="utf-8-sig"),
                           delimiter=";"))
print("объектов: %d" % len(rows))

by_city = defaultdict(Counter)
far = 0
for r in rows:
    lat, lon = float(r["lat"]), float(r["lon"])
    best, bd = None, 1e18
    for name, (clat, clon) in geo.items():
        d = dist2(lat, lon, clat, clon)
        if d < bd:
            best, bd = name, d
    km = math.sqrt(bd)
    if km > 30:
        best = "прочие населённые пункты"
        far += 1
    when = r["city"].strip() if r["city"].strip() else best
    r["settlement"] = when
    by_city[when][r["category"]] += 1

cols = list(rows[0].keys())
with open(os.path.join(OSMDIR, "objects_by_city.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

print("\nобъектов дальше 30 км от городов списка: %d (%.0f%%)" % (far, 100.0 * far / len(rows)))
print("\n%-32s %6s %6s %6s %6s %6s" % ("город", "банки", "банкоматы", "произв.", "магазины", "услуги"))
for city, cnt in sorted(by_city.items(), key=lambda kv: -sum(kv[1].values()))[:20]:
    print("%-32s %6d %6d %6d %6d %6d" % (city[:32], cnt["bank"], cnt["atm"], cnt["industry"],
                                         cnt["shop"], cnt["service"]))
