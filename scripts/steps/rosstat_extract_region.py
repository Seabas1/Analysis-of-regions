# -*- coding: utf-8 -*-
"""Отбор таблиц сборника со строкой «Саратовская область».

Для каждой найденной таблицы сохраняются:
  table_no — номер таблицы сборника (например «20.10»); наследуется от подписи,
             потому что части одной таблицы идут отдельными блоками без подписи;
  head     — первые строки шапки (годы и подписи столбцов);
  saratov  — строки, в которых встречается название региона (в любой ячейке).

Из этих данных дальше читаются конкретные значения (см. rosstat_values.py).
"""
import glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(PROJECT, "data", "rosstat", "Region_Pokaz_2025", "txt")
OUTD = os.path.join(PROJECT, "data", "rosstat")
SAR = "Саратовская область"
HEAD_ROWS = 4          # сколько первых строк шапки сохраняем

RE_CAPTION = re.compile(r"^\s*(\d+\.\d+)\.\s*\S")
RE_CONT = re.compile(r"Продолжение\s+табл\.\s*(\d+\.\d+)")


def parse_tables(path):
    """Возвращает список (caption_block, rows) по текстовому дампу."""
    lines = open(path, encoding="utf-8").read().split("\n")
    tables, cur, pending = [], None, []
    for ln in lines:
        if ln.startswith("--- ТАБЛИЦА"):
            cur = []
            continue
        if ln.startswith("--- КОНЕЦ ТАБЛИЦЫ"):
            tables.append((list(pending), cur))
            cur, pending = None, []
            continue
        if cur is None:
            pending.append(ln)
        else:
            cur.append(ln)
    return tables


def table_number(caption_block, previous):
    """Номер таблицы: из подписи «Продолжение табл. X» или «X. НАЗВАНИЕ», иначе предыдущий."""
    for ln in reversed(caption_block):
        m = RE_CONT.search(ln)
        if m:
            return m.group(1)
        m = RE_CAPTION.match(ln)
        if m:
            return m.group(1)
    return previous


results = []
for f in sorted(glob.glob(os.path.join(D, "R_*.txt"))):
    chapter = ""
    for ln in open(f, encoding="utf-8"):
        if ln.strip() and not ln.startswith("---"):
            chapter = ln.strip()[:200]
            break
    cur_no = None
    for caption_block, rows in parse_tables(f):
        cur_no = table_number(caption_block, cur_no)
        title = ""
        for prev in reversed(caption_block):
            if prev.strip():
                title = prev.strip()
                break
        hit = [r for r in rows if SAR in r]        # регион ищем в любой ячейке строки
        if not hit:
            continue
        results.append({
            "file": os.path.basename(f),
            "chapter": chapter,
            "table_no": cur_no or "",
            "title": title[:250],
            "head": [r for r in rows[:HEAD_ROWS]],
            "saratov": hit,
        })

with open(os.path.join(OUTD, "saratov_tables.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

with open(os.path.join(OUTD, "saratov_tables.txt"), "w", encoding="utf-8") as f:
    for r in results:
        f.write("=" * 100 + "\n")
        f.write("%s | %s | табл. %s\n" % (r["file"], r["chapter"], r["table_no"]))
        f.write("ПОДПИСЬ: %s\n" % r["title"])
        for i, h in enumerate(r["head"]):
            f.write("ШАПКА%d: %s\n" % (i + 1, h[:400]))
        for s in r["saratov"]:
            f.write("РЕГИОН: %s\n" % s[:600])
        f.write("\n")

print("таблиц со строкой «Саратовская область»: %d" % len(results))
print("с определённым номером таблицы: %d" % sum(1 for r in results if r["table_no"]))
by = {}
for r in results:
    by[r["file"]] = by.get(r["file"], 0) + 1
for k in sorted(by):
    print("   %-10s %d" % (k, by[k]))
