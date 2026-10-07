# -*- coding: utf-8 -*-
"""Извлечение экономических объектов Саратовской области из PBF Geofabrik.

Фильтр — не bbox, а реальная граница области (Nominatim), поэтому объекты
соседних регионов в выборку не попадают.
"""
import csv, json, os, sys, time
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
sys.path.insert(0, TOOLS)
import numpy as np
import osmium

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OSMDIR = os.path.join(PROJECT, "data", "osm")
PBF = os.path.join(OSMDIR, "volga-fed-district-latest.osm.pbf")

geo = json.load(open(os.path.join(OSMDIR, "region_boundary.geojson"), encoding="utf-8"))
coords = geo["coordinates"]
outer = np.asarray(coords[0], dtype=np.float64)
holes = [np.asarray(h, dtype=np.float64) for h in coords[1:]]
BB = (outer[:, 0].min(), outer[:, 1].min(), outer[:, 0].max(), outer[:, 1].max())
print("граница: %d точек внешнего контура, bbox %.2f..%.2f / %.2f..%.2f" % (len(outer), *BB))


def ray_inside(poly, pts):
    x = pts[:, 0:1]
    y = pts[:, 1:2]
    x1 = poly[None, :, 0]
    y1 = poly[None, :, 1]
    x2 = np.roll(poly[:, 0], -1)[None, :]
    y2 = np.roll(poly[:, 1], -1)[None, :]
    cond = (y1 > y) != (y2 > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xint = (x2 - x1) * (y - y1) / (y2 - y1) + x1
    return (cond & (x < xint)).sum(axis=1) % 2 == 1


def inside(pts, batch=800):
    out = np.zeros(len(pts), dtype=bool)
    for i in range(0, len(pts), batch):
        chunk = pts[i:i + batch]
        m = ray_inside(outer, chunk)
        for h in holes:
            m &= ~ray_inside(h, chunk)
        out[i:i + batch] = m
    return out


def classify(t):
    out = []
    amen = t.get("amenity")
    if amen == "bank":
        out.append("bank")
    if amen == "atm":
        out.append("atm")
    if t.get("industrial"):
        out.append("industry")
    shop = t.get("shop")
    if shop in ("supermarket", "convenience", "general"):
        out.append("shop")
    if shop in ("beauty", "hairdresser", "massage") or t.get("leisure") == "tanning_salon":
        out.append("service")
    return out


def row_for(kind, oid, lon, lat, t, cat):
    return {"osm_type": kind, "osm_id": oid, "category": cat,
            "name": t.get("name", ""), "lon": lon, "lat": lat,
            "city": t.get("addr:city", ""), "street": t.get("addr:street", ""),
            "housenumber": t.get("addr:housenumber", ""),
            "operator": t.get("operator", ""), "brand": t.get("brand", ""),
            "shop": t.get("shop", ""), "industrial": t.get("industrial", ""),
            "amenity": t.get("amenity", "")}


class Collector(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.raw = []
        self.n_nodes = self.n_ways = 0
        self.t0 = time.time()

    def node(self, n):
        self.n_nodes += 1
        if self.n_nodes % 5000000 == 0:
            print("   обработано узлов: %d (%.0f с)" % (self.n_nodes, time.time() - self.t0), flush=True)
        t = dict(n.tags)
        cats = classify(t)
        if not cats:
            return
        loc = n.location
        if not loc.valid():
            return
        for c in cats:
            self.raw.append(row_for("node", n.id, loc.lon, loc.lat, t, c))

    def way(self, w):
        self.n_ways += 1
        t = dict(w.tags)
        cats = classify(t)
        if not cats:
            return
        try:
            pts = [(nr.location.lon, nr.location.lat) for nr in w.nodes if nr.location.valid()]
        except Exception:
            return
        if not pts:
            return
        lon = sum(p[0] for p in pts) / len(pts)
        lat = sum(p[1] for p in pts) / len(pts)
        for c in cats:
            self.raw.append(row_for("way", w.id, lon, lat, t, c))


print("разбор PBF (это несколько минут)...", flush=True)
h = Collector()
h.apply_file(PBF, locations=True)
print("кандидатов до фильтра по границе: %d (узлов просмотрено %d, линий %d)"
      % (len(h.raw), h.n_nodes, h.n_ways))

pts = np.array([[r["lon"], r["lat"]] for r in h.raw], dtype=np.float64)
mask = inside(pts)
rows = [r for r, keep in zip(h.raw, mask) if keep]
print("после фильтра по границе области: %d" % len(rows))

cols = ["osm_type", "osm_id", "category", "name", "lon", "lat", "city", "street",
        "housenumber", "operator", "brand", "shop", "industrial", "amenity"]
with open(os.path.join(OSMDIR, "objects.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
json.dump(rows, open(os.path.join(OSMDIR, "objects.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

from collections import Counter
print("\nИТОГО объектов: %d" % len(rows))
for k, v in Counter(r["category"] for r in rows).most_common():
    print("   %-9s %d" % (k, v))
