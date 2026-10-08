# -*- coding: utf-8 -*-
"""РЫНОК ТРУДА: спрос по вакансиям и фактическая статистика.

Источники: vacancies.csv (портал «Работа в России») + раздел 3 сборника.
"""
import csv, os, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "steps"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rosstat_values as rv

OUT = os.path.join(PROJECT, "analiz")
os.makedirs(OUT, exist_ok=True)
t = rv.load(PROJECT)

path = os.path.join(PROJECT, "data", "labor", "vacancies.csv")
if not os.path.exists(path):
    raise SystemExit("нет data/labor/vacancies.csv — запустите шаг сбора вакансий")
rows = list(csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";"))

sal = [float(r["salary_min"]) for r in rows if r["salary_min"].strip()]
sal = [s for s in sal if s > 0]                 # 0 в поле означает «не указана»
geo = sum(1 for r in rows if r["lat"].strip() and r["lng"].strip())
prof = Counter(r["job_name"].strip().lower() for r in rows if r["job_name"].strip())
prof_raw = {(r["job_name"] or "").strip() for r in rows if (r["job_name"] or "").strip()}
cat = Counter(r["category"].strip() for r in rows if r["category"].strip())
comp = Counter(r["company"].strip() for r in rows if r["company"].strip())
exp = Counter(r["experience"].strip() or "не указан" for r in rows)

by_cat = defaultdict(list)
for r in rows:
    if r["salary_min"].strip() and r["category"].strip():
        by_cat[r["category"].strip()].append(float(r["salary_min"]))

# статистика Росстата по занятости и оплате
employed = rv.require(t, "1.1", label="численность занятых", part=0)
wage = rv.require(t, "4.6", year=2024)

print("=" * 84)
print("РЫНОК ТРУДА")
print("=" * 84)
print("вакансии в выборке: %d" % len(rows))
print("   с указанной зарплатой: %d (%.1f%%)  |  с координатами: %d (%.1f%%)"
      % (len(sal), 100 * len(sal) / len(rows), geo, 100 * geo / len(rows)))
print("   профессий: %d (с учётом регистра — %d)  |  работодателей: %d"
      % (len(prof), len(prof_raw), len(comp)))

q = st.quantiles(sal, n=4)
print("\nпредлагаемая зарплата, ₽ (n=%d):" % len(sal))
print("   минимум %8.0f | 1-й кв. %8.0f | медиана %8.0f | средняя %8.0f | 3-й кв. %8.0f | максимум %8.0f"
      % (min(sal), q[0], st.median(sal), st.mean(sal), q[2], max(sal)))
print("   выше 100 000 ₽: %d (%.1f%%)" % (sum(1 for s in sal if s > 100000),
                                         100 * sum(1 for s in sal if s > 100000) / len(sal)))

print("\nтоп-10 профессий:")
for k, v in prof.most_common(10):
    print("   %-38s %4d" % (k[:38], v))

print("\nсферы: число вакансий и медиана зарплаты (топ-10 по числу вакансий):")
for c, vals in sorted(by_cat.items(), key=lambda kv: -len(kv[1]))[:10]:
    print("   %-42s %4d вакансий  медиана %7.0f ₽" % (c[:42], len(vals), st.median(vals)))

EXP_LABEL = {"0": "без опыта", "1": "от 1 года", "2": "от 2 лет", "3": "от 3 лет",
             "4": "от 4 лет", "5": "от 5 лет", "6": "от 6 лет"}
print("\nтребуемый опыт (лет, как указано в вакансии):")
for k, v in exp.most_common(5):
    print("   %-16s %5d (%.1f%%)" % (EXP_LABEL.get(k, k + " лет"), v, 100 * v / len(rows)))
zero_one = sum(v for k, v in exp.items() if k in ("0", "1"))
print("   опыт 0–1 год: %d (%.1f%%)" % (zero_one, 100 * zero_one / len(rows)))

top10 = sum(v for _, v in comp.most_common(10))
print("\nконцентрация работодателей: топ-10 дают %d вакансий (%.1f%%), "
      "с одной вакансией — %d работодателей"
      % (top10, 100 * top10 / len(rows), sum(1 for _, v in comp.items() if v == 1)))

print("\nдля сравнения, статистика Росстата (2024):")
print("   занятых %8.1f тыс. чел.  |  средняя начисленная зарплата %8.0f ₽" % (employed, wage))

with open(os.path.join(OUT, "вакансии_топ_профессий.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["профессия", "вакансий"])
    w.writerows(prof.most_common())

with open(os.path.join(OUT, "вакансии_по_сферам.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["сфера деятельности", "вакансий", "медиана зарплаты, ₽"])
    for c, cnt in cat.most_common():
        vals = by_cat.get(c) or []
        w.writerow([c, cnt, "%.0f" % st.median(vals) if vals else ""])

print("\nфайлы записаны в %s" % OUT)
