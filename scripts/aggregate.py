# -*- coding: utf-8 -*-
"""Сводные таблицы по собранным данным: вакансии и объекты OSM."""
import csv, json, os, statistics as st, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "analiz")
os.makedirs(OUT, exist_ok=True)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(x):
    try:
        v = float(str(x).replace(",", ".").replace(" ", ""))
        return v if v > 0 else None
    except Exception:
        return None


def money():
    print("\n" + "=" * 80)
    print("РЫНОК ДЕНЕГ: банки и банкоматы (OSM)")
    path = os.path.join(PROJECT, "data", "osm", "objects.csv")
    if not os.path.exists(path):
        print("нет файла objects.csv")
        return
    rows = read_csv(path)
    banks = [r for r in rows if r["category"] in ("bank", "atm")]
    c = Counter(r["category"] for r in banks)
    print("всего объектов: %d (банки: %d, банкоматы: %d)" % (len(banks), c["bank"], c["atm"]))
    by_city = Counter((r["city"] or "не указан") for r in banks)
    print("топ-15 населённых пунктов:")
    for k, v in by_city.most_common(15):
        print("   %-32s %d" % (k, v))
    brands = Counter(r["brand"] or r["operator"] for r in banks if (r["brand"] or r["operator"]))
    print("топ-15 банков (brand/operator):")
    for k, v in brands.most_common(15):
        print("   %-40s %d" % (k[:40], v))


def labor():
    print("\n" + "=" * 80)
    print("РЫНОК ТРУДА: вакансии (trudvsem)")
    path = os.path.join(PROJECT, "data", "labor", "vacancies.csv")
    if not os.path.exists(path):
        print("нет файла vacancies.csv")
        return
    rows = read_csv(path)
    print("вакансий: %d" % len(rows))

    prof = Counter(r["job_name"].strip().lower() for r in rows if r["job_name"].strip())
    print("\nтоп-25 профессий:")
    for k, v in prof.most_common(25):
        print("   %-42s %d" % (k[:42], v))

    cat = Counter(r["category"] for r in rows if r["category"])
    print("\nтоп-15 сфер деятельности:")
    for k, v in cat.most_common(15):
        print("   %-42s %d" % (k[:42], v))

    sal = [num(r["salary_min"]) or num(r["salary_max"]) for r in rows]
    sal = [s for s in sal if s]
    if sal:
        print("\nзарплаты (по %d вакансиям с указанной суммой), ₽:" % len(sal))
        print("   минимум %.0f | медиана %.0f | средняя %.0f | максимум %.0f"
              % (min(sal), st.median(sal), st.mean(sal), max(sal)))

    city = Counter((r["city"].split(",")[0].strip() if r["city"] else "не указан") for r in rows)
    print("\nтоп-15 локаций:")
    for k, v in city.most_common(15):
        print("   %-42s %d" % (k[:42], v))

    comp = Counter(r["company"] for r in rows if r["company"])
    print("\nтоп-15 работодателей по числу вакансий:")
    for k, v in comp.most_common(15):
        print("   %-42s %d" % (k[:42], v))

    with open(os.path.join(OUT, "вакансии_топ_профессий.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["профессия", "вакансий"])
        w.writerows(prof.most_common())
    with open(os.path.join(OUT, "вакансии_по_сферам.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["сфера деятельности", "вакансий"])
        w.writerows(cat.most_common())


def goods():
    print("\n" + "=" * 80)
    print("РЫНОК ТОВАРА: производства, услуги, магазины (OSM)")
    # приоритет — файл с территориальной привязкой (settlement), иначе objects.csv
    path = os.path.join(PROJECT, "data", "osm", "objects_by_city.csv")
    if not os.path.exists(path):
        path = os.path.join(PROJECT, "data", "osm", "objects.csv")
    if not os.path.exists(path):
        print("нет файла objects.csv")
        return
    rows = read_csv(path)
    key = "settlement" if "settlement" in (rows[0] if rows else {}) else "city"
    c = Counter(r["category"] for r in rows)
    names = {"industry": "производства", "shop": "магазины", "service": "услуги"}
    for k, v in c.most_common():
        print("   %-10s %-14s %d" % (k, names.get(k, ""), v))

    print("\nпроизводства по видам (industrial):")
    ind = Counter(r["industrial"] for r in rows if r["category"] == "industry" and r["industrial"])
    for k, v in ind.most_common(15):
        print("   %-30s %d" % (k, v))

    print("\nмагазины по типам (shop):")
    sh = Counter(r["shop"] for r in rows if r["category"] == "shop" and r["shop"])
    for k, v in sh.most_common(10):
        print("   %-30s %d" % (k, v))

    print("\nраспределение по населённым пунктам (топ-15, все категории):")
    city = Counter((r[key] or "не указан") for r in rows)
    for k, v in city.most_common(15):
        print("   %-32s %d" % (k, v))

    by = defaultdict(Counter)
    for r in rows:
        by[r[key] or "не указан"][r["category"]] += 1
    with open(os.path.join(OUT, "объекты_по_городам.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["населённый пункт", "банки", "банкоматы", "производства", "магазины", "услуги", "всего"])
        for city_name, cnt in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
            w.writerow([city_name, cnt["bank"], cnt["atm"], cnt["industry"], cnt["shop"],
                        cnt["service"], sum(cnt.values())])
    print("\nфайлы записаны в %s" % OUT)


if __name__ == "__main__":
    money()
    labor()
    goods()
