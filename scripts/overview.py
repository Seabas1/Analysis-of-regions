# -*- coding: utf-8 -*-
"""ОБЩАЯ СВОДКА: регион в цифрах и структура экономики.

Числа берутся из выборки сборника (data/rosstat/saratov_tables.json) через
rosstat_values — в коде нет ни одной вписанной вручную цифры.
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "steps"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rosstat_values as rv

OUT = os.path.join(PROJECT, "analiz")
os.makedirs(OUT, exist_ok=True)
t = rv.load(PROJECT)

# ---------------------------------------------------------------- показатели
area = rv.require(t, "1.1", label="Площадь территории", part=0)
pop = rv.require(t, "1.1", label="Численность   населения", part=0)
employed = rv.require(t, "1.1", label="численность занятых", part=0)
income = rv.require(t, "1.1", label="денежные доходы", part=0)
wage = rv.require(t, "1.1", label="заработная плата", part=0)
grp = rv.require(t, "1.1", label="Валовой  региональ", part=0)
grp_pc = rv.require(t, "9.2", year=2023)        # опубликованное значение, не расчёт
invest = rv.require(t, "1.1", label="Инвестиции  в основной", part=0)
pop_2010 = rv.require(t, "2.1", year=2010)
urban = rv.require(t, "2.3", year=2023, label="Городское")
mo = rv.require(t, "1.7", label="Муници- пальные  образо- вания")
districts = rv.require(t, "1.7", label="муници- пальные районы")
okrugs = rv.require(t, "1.7", label="городские округа")
pop_delta = 100.0 * (pop / pop_2010 - 1)

print("=" * 84)
print("ОБЩАЯ СВОДКА: САРАТОВСКАЯ ОБЛАСТЬ")
print("=" * 84)
print("площадь                       %8.1f тыс. км²" % area)
print("население (01.01.2024)        %8.1f тыс. чел." % pop)
print("население (2010)              %8.1f тыс. чел.  (%+.1f%%)" % (pop_2010, pop_delta))
print("городское население (2023)    %8.1f%%" % urban)
print("занятые                       %8.1f тыс. чел." % employed)
print("среднедушевые доходы          %8.0f ₽/мес" % income)
print("средняя зарплата              %8.0f ₽" % wage)
print("ВРП 2023                      %8.0f млрд ₽" % grp)
print("ВРП на душу                   %8.0f ₽" % grp_pc)
print("инвестиции в основной капитал %8.1f млрд ₽  (%.1f%% ВРП)" % (invest, 100 * invest / grp))
print("муниципальные образования     %8.0f  (районов %.0f, городских округов %.0f)"
      % (mo, districts, okrugs))

# ---------------------------------------------------------------- секторы
# Подписи столбцов в сборнике разорваны переносами, а местами содержат опечатки
# («Обеспечение электрическое энергией»), поэтому ищем по устойчивым фрагментам.
PRIMARY = {"сельское хозяйство": "Сельское, лесное хозяйство",
           "добыча": "Добыча полезных ископаемых"}
SECONDARY = {"обработка": "Обрабатывающие",
             "энергетика": "электрическ",
             "водоснабжение": "водоснабжение",
             "строительство": "строительств"}


def sectors(table_no):
    """Суммы по секторам с проверкой, что найдены все компоненты."""
    found, missing = {}, []
    for label in list(PRIMARY.values()) + list(SECONDARY.values()):
        v = rv.find(t, table_no, label=label)
        if v is None:
            missing.append(label)
        else:
            found[label] = v
    if missing:
        raise LookupError("табл. %s: не найдены столбцы %s" % (table_no, missing))
    return found


grp_s = sectors("9.4")
emp_s = sectors("3.6")
p_grp = sum(v for k, v in grp_s.items() if k in PRIMARY.values())
s_grp = sum(v for k, v in grp_s.items() if k in SECONDARY.values())
p_emp = sum(v for k, v in emp_s.items() if k in PRIMARY.values())
s_emp = sum(v for k, v in emp_s.items() if k in SECONDARY.values())

print("\nструктура ВРП по секторам (%%):")
print("   первичный  (сельское хозяйство + добыча)          %5.1f" % p_grp)
print("   вторичный  (обработка, энергетика, вода, стройка) %5.1f" % s_grp)
print("   третичный  (все остальные услуги)                 %5.1f" % (100 - p_grp - s_grp))
print("структура занятости по секторам (%%):")
print("   первичный  (сельское хозяйство + добыча)          %5.1f" % p_emp)
print("   вторичный  (обработка, энергетика, вода, стройка) %5.1f" % s_emp)
print("   третичный  (все остальные услуги)                 %5.1f" % (100 - p_emp - s_emp))

# ---------------------------------------------------------------- собственность
org_total = rv.require(t, "12.4", label="Всего организаций")
org_state = rv.require(t, "12.4", label="государственная")
org_mun = rv.require(t, "12.4", label="муниципальная")
org_priv = rv.require(t, "12.4", label="частная")
turn_total = rv.require(t, "12.7", label="Оборот –  всего")
turn_state = rv.require(t, "12.7", label="государственная")
turn_mun = rv.require(t, "12.7", label="муниципальная")
turn_priv = rv.require(t, "12.7", label="частная")

print("\nформы собственности:")
print("   организации: частных %.1f%%, государственных и муниципальных %.1f%% (всего %.0f)"
      % (100 * org_priv / org_total, 100 * (org_state + org_mun) / org_total, org_total))
print("   оборот:      частных %.1f%%, государственных и муниципальных %.1f%% (всего %.1f млрд ₽)"
      % (100 * turn_priv / turn_total, 100 * (turn_state + turn_mun) / turn_total, turn_total))

# ---------------------------------------------------------------- файлы
with open(os.path.join(OUT, "обзор_показатели.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["показатель", "значение", "единица", "источник"])
    for name, val, unit, src in [
        ("площадь", area, "тыс. км²", "табл. 1.1"),
        ("население на 01.01.2024", pop, "тыс. чел.", "табл. 1.1"),
        ("население 2010", pop_2010, "тыс. чел.", "табл. 2.1"),
        ("городское население 2023", urban, "%", "табл. 2.3"),
        ("занятые", employed, "тыс. чел.", "табл. 1.1"),
        ("среднедушевые доходы", income, "₽/мес", "табл. 1.1"),
        ("средняя зарплата", wage, "₽", "табл. 1.1"),
        ("ВРП 2023", grp, "млрд ₽", "табл. 1.1"),
        ("ВРП на душу", grp_pc, "₽", "расчёт"),
        ("инвестиции", invest, "млрд ₽", "табл. 1.1"),
        ("муниципальные образования", mo, "шт.", "табл. 1.7"),
    ]:
        w.writerow([name, ("%.2f" % val).rstrip("0").rstrip("."), unit, src])

with open(os.path.join(OUT, "обзор_секторы.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["разрез", "первичный", "вторичный", "третичный"])
    w.writerow(["ВРП, %", "%.1f" % p_grp, "%.1f" % s_grp, "%.1f" % (100 - p_grp - s_grp)])
    w.writerow(["занятость, %", "%.1f" % p_emp, "%.1f" % s_emp, "%.1f" % (100 - p_emp - s_emp)])

print("\nфайлы записаны в %s" % OUT)
