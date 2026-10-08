import glob, os, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
D = os.path.join(PROJECT, "data", "rosstat", "Region_Pokaz_2025")
OUT = os.path.join(D, "txt")
os.makedirs(OUT, exist_ok=True)


def iter_block_items(parent):
    from docx.oxml.ns import qn
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def dump(path, dest):
    doc = Document(path)
    n_tab = 0
    with open(dest, "w", encoding="utf-8") as f:
        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                t = block.text.strip()
                if t:
                    f.write(t + "\n")
            else:
                n_tab += 1
                f.write("\n--- ТАБЛИЦА %d ---\n" % n_tab)
                for row in block.rows:
                    cells = [c.text.strip().replace("\n", " ").replace("\xa0", " ") for c in row.cells]
                    f.write(" | ".join(cells) + "\n")
                f.write("--- КОНЕЦ ТАБЛИЦЫ %d ---\n\n" % n_tab)
    return n_tab


for f in sorted(glob.glob(os.path.join(D, "R_*.docx"))):
    name = os.path.splitext(os.path.basename(f))[0]
    dest = os.path.join(OUT, name + ".txt")
    n = dump(f, dest)
    print("%-12s таблиц=%-3d  %d КБ -> %s" % (name, n, os.path.getsize(dest) // 1024, os.path.basename(dest)))
