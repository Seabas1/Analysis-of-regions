# -*- coding: utf-8 -*-
"""Чтение чисел из выборки сборника (data/rosstat/saratov_tables.json).

Идея: analysis-скрипты не хранят числа у себя, а адресуют их в сборнике —
«таблица 20.10, 2025 год, вклады физических лиц» — и получают значение из данных.

Как определяется столбец:
  * строка годов шапки (первая строка, где не меньше двух ячеек похожи на год);
  * подписи столбцов — строки шапки ниже строки годов, склеенные по индексу;
  * значение берётся из строки региона по тому же индексу столбца.
"""
import json, os, re

NUM_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
YEAR_RE = re.compile(r"^(19|20)\d\d")


def load(project):
    path = os.path.join(project, "data", "rosstat", "saratov_tables.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_num(cell):
    """'585 130' -> 585130.0; '' -> None; 'Саратовская область' -> None."""
    s = (cell or "").replace("\u00a0", "").replace(" ", "").strip().rstrip(")")
    m = re.match(r"^(-?\d+(?:[.,]\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _norm(s):
    """Нормализация подписи: в сборнике слова разорваны переносами и двойными пробелами."""
    return re.sub(r"[\s\u00a0\u00ad\-–—]+", "", (s or "").lower())


def year_of(cell):
    m = YEAR_RE.match((cell or "").strip())
    return int(m.group(0)) if m else None


def parts(tables, table_no):
    """Все части одной таблицы сборника в порядке следования."""
    return [t for t in tables if t.get("table_no") == table_no]


def columns(entry):
    """[(индекс, год|None, подпись)] по шапке таблицы."""
    head = [h.split("|") for h in entry.get("head", [])]
    year_row = None
    year_idx = None
    for i, cells in enumerate(head):
        years = [c for c in cells if year_of(c)]
        if len(years) >= 2:
            year_row, year_idx = cells, i
            break
    width = max((len(c) for c in head), default=0)
    out = []
    for j in range(width):
        yr = year_of(year_row[j]) if year_row and j < len(year_row) else None
        labels = []
        for i, cells in enumerate(head):
            if i == year_idx:
                continue
            if j < len(cells) and cells[j].strip():
                labels.append(cells[j].strip())
        out.append((j, yr, " ".join(labels)))
    return out


def region_cells(entry):
    """Ячейки первой строки региона."""
    return [c.strip() for c in entry["saratov"][0].split("|")]


def value(tables, table_no, year=None, label=None, part=0):
    """Значение из строки региона. None, если столбец не найден."""
    ps = parts(tables, table_no)
    if part >= len(ps):
        return None
    entry = ps[part]
    cells = region_cells(entry)
    want = _norm(label) if label else None
    for j, yr, lab in columns(entry):
        if year is not None and yr != year:
            continue
        if want is not None and want not in _norm(lab):
            continue
        if j < len(cells):
            v = to_num(cells[j])
            if v is not None:
                return v
    return None


def find(tables, table_no, year=None, label=None):
    """Ищет значение по всем частям таблицы — удобно, когда часть заранее неизвестна."""
    for part in range(len(parts(tables, table_no))):
        v = value(tables, table_no, year=year, label=label, part=part)
        if v is not None:
            return v
    return None


def require(tables, table_no, year=None, label=None, part=0):
    """Как value(), но падает, если значение не найдено — молча терять числа нельзя."""
    v = value(tables, table_no, year=year, label=label, part=part)
    if v is None:
        raise LookupError("не найдено: табл. %s, год=%s, подпись=%r, часть=%d"
                          % (table_no, year, label, part))
    return v


def require_any(tables, table_no, year=None, label=None):
    """Как require(), но ищет по всем частям таблицы."""
    v = find(tables, table_no, year=year, label=label)
    if v is None:
        raise LookupError("не найдено ни в одной части: табл. %s, год=%s, подпись=%r"
                          % (table_no, year, label))
    return v


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    t = load(P)
    print("таблиц в выборке: %d, уникальных номеров: %d"
          % (len(t), len({x["table_no"] for x in t})))
    print("\nпроверка известных значений:")
    CHECKS = [
        ("20.10", 2011, "Всего", 0, 97314), ("20.10", 2011, "физических", 0, 90263),
        ("20.10", 2011, "юридических", 0, 7051),
        ("20.10", 2025, "Всего", 1, 585130), ("20.10", 2025, "физических", 1, 514711),
        ("20.10", 2025, "юридических", 1, 70419),
        ("20.9", 2011, None, 0, 10), ("20.9", 2025, None, 0, 4),
        ("20.9", 2011, None, 1, 66), ("20.9", 2025, None, 1, 3),
        ("20.12", 2011, None, 0, 50930), ("20.12", 2025, None, 0, 266542),
        ("20.14", 2011, None, 0, 74345), ("20.14", 2025, None, 0, 219109),
        ("10.1", 2024, None, 0, 316675),
    ]
    ok = 0
    for no, yr, lab, part, expect in CHECKS:
        got = value(t, no, year=yr, label=lab, part=part)
        good = got is not None and abs(got - expect) < 0.51
        ok += good
        print("  %-6s %s %-12s часть %d: %-10s ожидалось %-10s %s"
              % (no, yr, lab or "—", part, ("%g" % got) if got is not None else "нет",
                 expect, "ок" if good else "РАСХОЖДЕНИЕ"))
    print("\nсовпало %d из %d" % (ok, len(CHECKS)))
