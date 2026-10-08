# -*- coding: utf-8 -*-
"""ФИНАНСОВЫЙ СЕКТОР: институты, деньги, размещение.

Источники: раздел 20 сборника (по данным Банка России) + объекты OSM.
Все числа читаются из данных, в коде нет вписанных вручную показателей.
"""
import csv, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "steps"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rosstat_values as rv

OUT = os.path.join(PROJECT, "analiz")
os.makedirs(OUT, exist_ok=True)
t = rv.load(PROJECT)
Y0, Y1 = 2011, 2025          # сопоставимые точки ряда

# ------------------------------------------------------------------ институты
org0, org1 = rv.require(t, "20.9", year=Y0, part=0), rv.require(t, "20.9", year=Y1, part=0)
fil0, fil1 = rv.require(t, "20.9", year=Y0, part=1), rv.require(t, "20.9", year=Y1, part=1)

# ------------------------------------------------------------------ деньги
dep_t0, dep_t1 = rv.require(t, "20.10", year=Y0, label="Всего", part=0), rv.require(t, "20.10", year=Y1, label="Всего", part=1)
dep_p0, dep_p1 = rv.require(t, "20.10", year=Y0, label="физических", part=0), rv.require(t, "20.10", year=Y1, label="физических", part=1)
dep_c0, dep_c1 = rv.require(t, "20.10", year=Y0, label="юридических", part=0), rv.require(t, "20.10", year=Y1, label="юридических", part=1)
loan0, loan1 = rv.require(t, "20.14", year=Y0), rv.require(t, "20.14", year=Y1)
sber0, sber1 = rv.require(t, "20.12", year=Y0), rv.require(t, "20.12", year=Y1)
fx0, fx1 = rv.require(t, "20.13", year=Y0), rv.require(t, "20.13", year=Y1)
# место региона в РФ — последний столбец таблицы 20.12
sber_rank = rv.to_num(rv.region_cells(rv.parts(t, "20.12")[0])[-1])

# население для подушевых показателей (ближайшие опубликованные годы)
pop0 = rv.require(t, "2.1", year=2010)
pop1 = rv.require(t, "1.1", label="Численность   населения", part=0)

print("=" * 84)
print("ФИНАНСОВЫЙ СЕКТОР")
print("=" * 84)
print("институты (на начало года):        %d г. -> %d г." % (Y0, Y1))
print("   кредитные организации           %6.0f -> %6.0f   (в %.0f раза меньше)"
      % (org0, org1, org0 / org1))
print("   филиалы                         %6.0f -> %6.0f   (в %.0f раза меньше)"
      % (fil0, fil1, fil0 / fil1))
print("деньги, млн ₽:")
for name, a, b in [("вклады всего", dep_t0, dep_t1),
                   ("   населения", dep_p0, dep_p1),
                   ("   юридических лиц", dep_c0, dep_c1),
                   ("кредиты юрлицам", loan0, loan1)]:
    print("   %-20s %10.0f -> %10.0f   (x%.1f)" % (name, a, b, b / a))
print("вклады на душу населения:          %8.0f ₽ -> %8.0f ₽"
      % (dep_t0 * 1e6 / (pop0 * 1e3), dep_t1 * 1e6 / (pop1 * 1e3)))
print("   (население в знаменателе: %.1f и %.1f тыс. чел. — ближайшие опубликованные годы)"
      % (pop0, pop1))
print("ПАО Сбербанк (табл. 20.12, 20.13):")
print("   вклады физлиц в рублях          %10.0f -> %10.0f" % (sber0, sber1))
print("   вклады физлиц в валюте          %10.0f -> %10.0f" % (fx0, fx1))
print("   доля в общем объёме вкладов     %9.1f%% -> %9.1f%%"
      % (100 * sber0 / dep_p0, 100 * sber1 / dep_p1))
if sber_rank:
    print("   место региона по рублёвым вкладам в РФ: %.0f" % sber_rank)

# ------------------------------------------------------------------ объекты OSM
path = os.path.join(PROJECT, "data", "osm", "objects_by_city.csv")
if os.path.exists(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";"))
    points = [r for r in rows if r["category"] in ("bank", "atm")]
    kinds = Counter(r["category"] for r in points)
    brands = Counter((r["brand"] or r["operator"]).strip() for r in points
                     if (r["brand"] or r["operator"]).strip())
    places = Counter(r["settlement"] for r in points)
    print("\nобъекты размещения (OpenStreetMap):")
    print("   всего %d, из них банков %.0f и банкоматов %.0f (1 : %.1f)"
          % (len(points), kinds["bank"], kinds["atm"], kinds["atm"] / kinds["bank"]))
    print("   топ брендов: " + " · ".join("%s %d" % (k[:22], v) for k, v in brands.most_common(7)))
    print("   топ территорий: " + " · ".join("%s %d" % (k[:18], v) for k, v in places.most_common(4)))

    with open(os.path.join(OUT, "финансы_бренды.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["бренд", "объектов"])
        w.writerows(brands.most_common())
else:
    print("\nнет data/osm/objects_by_city.csv — запустите шаги сбора и парсинга")

with open(os.path.join(OUT, "финансы_ряды.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["показатель", str(Y0), str(Y1), "кратность", "источник"])
    for name, a, b, src in [("кредитные организации", org0, org1, "табл. 20.9"),
                            ("филиалы", fil0, fil1, "табл. 20.9"),
                            ("вклады всего, млн ₽", dep_t0, dep_t1, "табл. 20.10"),
                            ("вклады населения, млн ₽", dep_p0, dep_p1, "табл. 20.10"),
                            ("вклады юрлиц, млн ₽", dep_c0, dep_c1, "табл. 20.10"),
                            ("кредиты юрлицам, млн ₽", loan0, loan1, "табл. 20.14"),
                            ("Сбербанк, рублёвые вклады, млн ₽", sber0, sber1, "табл. 20.12"),
                            ("Сбербанк, валютные вклады, млн ₽", fx0, fx1, "табл. 20.13")]:
        w.writerow([name, "%.0f" % a, "%.0f" % b, "%.2f" % (b / a), src])

print("\nфайлы записаны в %s" % OUT)
