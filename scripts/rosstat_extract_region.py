import glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
D = os.path.join(PROJECT, "data", "rosstat", "Region_Pokaz_2025", "txt")
OUTD = os.path.join(PROJECT, "data", "rosstat")
SAR = "Саратовская область"


def parse_tables(path):
    """Возвращает список (title, rows) по текстовому дампу."""
    lines = open(path, encoding="utf-8").read().split("\n")
    tables, cur, title, pending = [], None, "", []
    for ln in lines:
        if ln.startswith("--- ТАБЛИЦА"):
            cur = []
            # заголовок = последняя непустая строка перед таблицей
            for prev in reversed(pending):
                if prev.strip():
                    title = prev.strip()
                    break
            continue
        if ln.startswith("--- КОНЕЦ ТАБЛИЦЫ"):
            tables.append((title, cur))
            cur = None
            continue
        if cur is None:
            pending.append(ln)
        else:
            cur.append(ln)
    return tables


results = []
for f in sorted(glob.glob(os.path.join(D, "R_*.txt"))):
    chapter = ""
    for t, rows in parse_tables(f):
        if not chapter:
            for ln in open(f, encoding="utf-8"):
                if ln.strip() and not ln.startswith("---"):
                    chapter = ln.strip()
                    break
        hit = [r for r in rows if r.split("|")[0].strip().startswith(SAR)]
        if hit:
            results.append({
                "file": os.path.basename(f), "chapter": chapter[:200],
                "title": t[:250],
                "header1": rows[0] if rows else "",
                "header2": rows[1] if len(rows) > 1 else "",
                "saratov": hit,
            })

with open(os.path.join(OUTD, "saratov_tables.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

with open(os.path.join(OUTD, "saratov_tables.txt"), "w", encoding="utf-8") as f:
    for r in results:
        f.write("=" * 100 + "\n")
        f.write("%s | %s\n" % (r["file"], r["chapter"]))
        f.write("ТАБЛИЦА: %s\n" % r["title"])
        f.write("ШАПКА1: %s\n" % r["header1"][:400])
        f.write("ШАПКА2: %s\n" % r["header2"][:400])
        for s in r["saratov"]:
            f.write("САРАТОВ: %s\n" % s[:600])
        f.write("\n")

print("таблиц со строкой «Саратовская область»: %d" % len(results))
by = {}
for r in results:
    by[r["file"]] = by.get(r["file"], 0) + 1
for k in sorted(by):
    print("   %-8s %d" % (k, by[k]))
