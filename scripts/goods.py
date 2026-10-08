# -*- coding: utf-8 -*-
"""РЫНОК ТОВАРОВ И УСЛУГ: размещение объектов и стоимостной масштаб.

Источники: objects_by_city.csv (OpenStreetMap) + табл. 1.1 сборника.
"""
import csv, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "steps"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rosstat_values as rv

OUT = os.path.join(PROJECT, "analiz")
os.makedirs(OUT, exist_ok=True)
t = rv.load(PROJECT)

path = os.path.join(PROJECT, "data", "osm", "objects_by_city.csv")
if not os.path.exists(path):
    raise SystemExit("нет data/osm/objects_by_city.csv — запустите шаги сбора и парсинга")
rows = list(csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";"))

shops = [r for r in rows if r["category"] == "shop"]
serv = [r for r in rows if r["category"] == "service"]
ind = [r for r in rows if r["category"] == "industry"]

# ---------------------------------------------------------------- деньги
mining = rv.require(t, "1.1", label="добыча  полезных  ископаемых", part=1)
manuf = rv.require(t, "1.1", label="обрабаты- вающие производства", part=1)
energy = rv.require(t, "1.1", label="обеспечение электрической энергией", part=1)
water = rv.require(t, "1.1", label="водоснабжение; водоотведение", part=1)
agro = rv.require(t, "1.1", label="Продукция  сельского  хозяйства", part=1)
retail = rv.require(t, "1.1", label="Оборот  розничной  торговли", part=1)
finres = rv.require(t, "1.1", label="Сальдированный  финансовый  результат", part=1)
industry = mining + manuf + energy + water

print("=" * 84)
print("РЫНОК ТОВАРОВ И УСЛУГ")
print("=" * 84)
print("объекты OSM в границах области:")
print("   магазины %d | услуги %d | производства %d | всего %d"
      % (len(shops), len(serv), len(ind), len(rows)))

print("\nформаты магазинов:")
for k, v in Counter(r["shop"] for r in shops).most_common():
    print("   %-14s %4d  (%.1f%%)" % (k, v, 100 * v / len(shops)))

brands = Counter((r["brand"] or r["operator"]).strip() for r in shops
                 if (r["brand"] or r["operator"]).strip())
print("\nторговые сети (brand или operator):")
for k, v in brands.most_common(10):
    print("   %-26s %4d" % (k[:26], v))
print("   с указанием сети: %d из %d (%.1f%%), сетей всего %d"
      % (sum(brands.values()), len(shops), 100 * sum(brands.values()) / len(shops), len(brands)))

print("\nпроизводства по видам:")
ci = Counter(r["industrial"] for r in ind)
for k, v in ci.most_common(8):
    print("   %-14s %4d" % (k, v))
oil_gas = sum(v for k, v in ci.items() if k in ("oil", "gas"))
print("   нефть и газ: %d из %d (%.0f%%)" % (oil_gas, len(ind), 100 * oil_gas / len(ind)))

by = defaultdict(Counter)
for r in rows:
    by[r["settlement"]][r["category"]] += 1
print("\nтерритории (топ-6 по магазинам): магазины / услуги / производства")
for city, cnt in sorted(by.items(), key=lambda kv: -kv[1]["shop"])[:6]:
    print("   %-24s %4d / %3d / %2d" % (city[:24], cnt["shop"], cnt["service"], cnt["industry"]))
top3 = sum(cnt["shop"] for city, cnt in by.items() if city in ("Саратов", "Балаково", "Энгельс"))
total_shop = sum(cnt["shop"] for cnt in by.values())
print("   доля трёх крупнейших городов: %.1f%%  |  доля Саратова: %.1f%%"
      % (100 * top3 / total_shop, 100 * by["Саратов"]["shop"] / total_shop))
street = sum(1 for r in rows if r["street"].strip())
print("   адрес улицы указан у %d из %d (%.1f%%)" % (street, len(rows), 100 * street / len(rows)))

print("\nденежный масштаб (Росстат, 2024), млрд ₽:")
print("   промышленность всего %8.1f  (добыча %.1f + обработка %.1f + энергетика %.1f + вода %.1f)"
      % (industry, mining, manuf, energy, water))
print("   доля обрабатывающих производств в промышленности: %.1f%%" % (100 * manuf / industry))
print("   продукция сельского хозяйства %8.1f" % agro)
print("   оборот розничной торговли     %8.1f" % retail)
print("   сальдированный финансовый результат %.1f" % finres)
print("\nсоотношение: магазинов к производствам %.0f : 1 по объектам, "
      "но промышленность больше розницы в %.1f раза по деньгам"
      % (len(shops) / len(ind), industry / retail))

with open(os.path.join(OUT, "объекты_по_городам.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["населённый пункт", "банки", "банкоматы", "производства", "магазины", "услуги", "всего"])
    for city, cnt in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        w.writerow([city, cnt["bank"], cnt["atm"], cnt["industry"], cnt["shop"],
                    cnt["service"], sum(cnt.values())])

with open(os.path.join(OUT, "товары_сводка.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["показатель", "значение", "единица", "источник"])
    for name, val, unit, src in [("магазины", len(shops), "объектов", "OSM"),
                                 ("услуги", len(serv), "объектов", "OSM"),
                                 ("производства", len(ind), "объектов", "OSM"),
                                 ("промышленность всего", industry, "млрд ₽", "табл. 1.1"),
                                 ("обрабатывающие производства", manuf, "млрд ₽", "табл. 1.1"),
                                 ("продукция сельского хозяйства", agro, "млрд ₽", "табл. 1.1"),
                                 ("оборот розничной торговли", retail, "млрд ₽", "табл. 1.1")]:
        w.writerow([name, "%.2f" % val, unit, src])

print("\nфайлы записаны в %s" % OUT)
