# -*- coding: utf-8 -*-
"""Презентация «Экономическое описание Саратовской области» на данных Росстата."""
import os
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "Саратовская_область_экономическое_описание.pptx")

DARK = RGBColor(0x1F, 0x35, 0x64)
ACCENT = RGBColor(0x2E, 0x74, 0xB5)
ACCENT2 = RGBColor(0xC0, 0x50, 0x4D)
GREEN = RGBColor(0x54, 0x82, 0x35)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xEE, 0xF2, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def new_slide():
    return prs.slides.add_slide(BLANK)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def box(slide, text, left, top, width, height, size=14, bold=False, color=GRAY,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, chunk in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = chunk
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = FONT
    return tb


def rect(slide, left, top, width, height, fill=LIGHT, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                Inches(width), Inches(height))
    sh.adjustments[0] = 0.06
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def header(slide, title, subtitle=None):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.16))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    bar.shadow.inherit = False
    box(slide, title, 0.6, 0.35, 12.2, 0.75, size=28, bold=True, color=DARK)
    if subtitle:
        box(slide, subtitle, 0.6, 1.05, 12.2, 0.45, size=13, color=GRAY)


def source(slide, text):
    box(slide, text, 0.6, 7.0, 12.2, 0.35, size=10, color=GRAY)


def kpi_row(slide, items, top=1.7, height=1.35, size_val=24, size_lab=10.5):
    n = len(items)
    gap = 0.22
    width = (12.13 - gap * (n - 1)) / n
    for i, (value, label) in enumerate(items):
        left = 0.6 + i * (width + gap)
        rect(slide, left, top, width, height, fill=LIGHT)
        box(slide, value, left + 0.12, top + 0.16, width - 0.24, 0.6, size=size_val,
            bold=True, color=DARK, align=PP_ALIGN.CENTER)
        box(slide, label, left + 0.12, top + 0.78, width - 0.24, 0.5, size=size_lab,
            color=GRAY, align=PP_ALIGN.CENTER, line_spacing=0.95)


def stacked_kpi(slide, items, left, top, width, row_h=1.0, size_val=22, size_lab=12):
    for i, (value, label) in enumerate(items):
        y = top + i * row_h
        box(slide, value, left, y, width, 0.45, size=size_val, bold=True, color=DARK)
        box(slide, label, left, y + 0.5, width, 0.45, size=size_lab, color=GRAY, line_spacing=1.0)


def bullets(slide, items, left=0.6, top=1.7, width=6.0, height=4.8, size=14, color=GRAY):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(9)
        r = p.add_run()
        r.text = "•  " + item
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = FONT
    return tb


def chart(slide, kind, categories, series, left, top, width, height,
          number_format="0.0", legend=False, labels=True, colors=None, label_size=10):
    data = CategoryChartData()
    data.categories = categories
    for name, values in series:
        data.add_series(name, values)
    gf = slide.shapes.add_chart(kind, Inches(left), Inches(top), Inches(width), Inches(height), data)
    ch = gf.chart
    ch.font.size = Pt(11)
    ch.font.name = FONT
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
    if kind in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT):
        ch.has_title = False
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(11)
        plot = ch.plots[0]
        plot.has_data_labels = labels
        dl = plot.data_labels
        dl.show_value = True
        dl.show_percentage = False
        dl.show_category_name = False
        dl.number_format = '0.0"%"'
        dl.number_format_is_linked = False
        dl.font.size = Pt(label_size)
        dl.font.bold = True
        dl.font.color.rgb = WHITE
        if colors:
            for i, point in enumerate(plot.series[0].points):
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = colors[i % len(colors)]
    else:
        plot = ch.plots[0]
        plot.gap_width = 60
        plot.has_data_labels = labels
        if labels:
            dl = plot.data_labels
            dl.number_format = number_format
            dl.number_format_is_linked = False
            dl.font.size = Pt(label_size)
            dl.font.bold = True
            dl.font.color.rgb = DARK
        if colors:
            for i, s in enumerate(ch.series):
                s.format.fill.solid()
                s.format.fill.fore_color.rgb = colors[i % len(colors)]
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
        va.tick_labels.font.size = Pt(10)
        ch.category_axis.tick_labels.font.size = Pt(10)
    return ch


def pair_chart(slide, kind, categories, series, left, top, width, height, **kw):
    return chart(slide, kind, categories, series, left, top, width, height, **kw)


# ---------------------------------------------------------------- 1. Титул
s = new_slide()
band = s.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(2.5))
band.fill.solid()
band.fill.fore_color.rgb = DARK
band.line.fill.background()
band.shadow.inherit = False
box(s, "Экономическое описание региона", 0.8, 0.7, 11.7, 0.8, size=34, bold=True, color=WHITE)
box(s, "Саратовская область", 0.8, 1.5, 11.7, 0.8, size=28, color=RGBColor(0x9D, 0xC3, 0xE6))
box(s, "Три разреза анализа: рынок денег — рынок труда — рынок товара;\n"
       "первичный — вторичный — третичный сектор; государственный — частный — смешанный сектор",
    0.8, 2.9, 11.7, 1.2, size=15, color=GRAY, line_spacing=1.3)
for i, (val, lab) in enumerate([("2 385,2", "тыс. человек — население"),
                                ("101,2", "тыс. км² — площадь"),
                                ("1 345", "млрд ₽ — ВРП в 2023 г.")]):
    left = 0.8 + i * 3.95
    rect(s, left, 4.35, 3.7, 1.15, fill=LIGHT)
    box(s, val, left + 0.15, 4.5, 3.4, 0.5, size=22, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    box(s, lab, left + 0.15, 5.02, 3.4, 0.4, size=11.5, color=GRAY, align=PP_ALIGN.CENTER)
box(s, "Источник: Росстат, «Регионы России. Социально-экономические показатели — 2025»\n"
       "Данные за 2023–2024 гг. • выгрузка 06.10.2026", 0.8, 6.05, 11.7, 1.0, size=13, color=GRAY)
notes(s, "Доклад: экономическое описание Саратовской области по данным официальной статистики. "
         "Три разреза заданы преподавателем: рынки (деньги, труд, товар), секторы экономики и формы собственности.")

# ---------------------------------------------------------------- 2. Методика
s = new_slide()
header(s, "Источник данных и методика", "Сплошная выборка показателей по одному региону из официального сборника")
bullets(s, [
    "Источник — сборник «Регионы России. Социально-экономические показатели — 2025», 22 раздела, 823 таблицы.",
    "Из сборника отобраны все 397 таблиц, содержащих строку «Саратовская область».",
    "Глубина данных: 2010–2024 гг.; основные показатели — за 2024 г., ВРП — за 2023 г. (последний опубликованный).",
    "Дата отсечения данных — 6 октября 2026 г.",
    "Сравнение ведётся с Приволжским федеральным округом и Российской Федерацией.",
    "Микроданные и опросы не используются: работа построена только на официальной статистике.",
], width=12.1, size=15)
source(s, "Росстат, «Регионы России — 2025»; раздел I, главы 2, 3, 9, 10, 12.")
notes(s, "Подчёркиваем: данные официальные и воспроизводимые. ВРП публикуется с лагом, поэтому 2023 год — "
         "последний доступный, это нормальная ситуация для региональной статистики.")

# ---------------------------------------------------------------- 3. Общая характеристика
s = new_slide()
header(s, "Саратовская область в цифрах", "2024 г., если не указано иное")
kpi_row(s, [("101,2", "тыс. км²\nплощадь территории"),
            ("2 385,2", "тыс. человек\nнаселение на 01.01.2024"),
            ("1 147,9", "тыс. человек\nсреднегодовая численность занятых"),
            ("1 345", "млрд ₽\nВРП в 2023 г.")], top=1.75, size_val=26)
kpi_row(s, [("561 623,7", "₽ ВРП на душу населения (2023)"),
            ("58 626", "₽ среднемесячная зарплата"),
            ("316,7", "млрд ₽ инвестиции в основной капитал"),
            ("328", "муниципальных образований")], top=3.4, size_val=26)
bullets(s, [
    "Регион занимает 101,2 тыс. км², население — 2,39 млн человек, 77% живёт в городах.",
    "В составе области 37 муниципальных районов, 4 городских округа, 37 городских и 250 сельских поселений.",
    "Экономика опирается на обрабатывающую промышленность, сельское хозяйство и энергетику.",
], top=5.15, width=12.1, size=13)
source(s, "Росстат, «Регионы России — 2025», табл. 1.1, 1.7, 2.1, 2.3.")
notes(s, "Ключевой слайд для знакомства с регионом. Обращаем внимание: население области медленно сокращается, "
         "при этом ВРП растёт быстрее — значит, экономика растёт не за счёт людей.")

# ---------------------------------------------------------------- 4. Динамика
s = new_slide()
header(s, "Динамика: население сокращается, ВРП растёт",
       "Население — на 1 января, тыс. человек; ВРП — млрд рублей в текущих ценах")
chart(s, XL_CHART_TYPE.LINE_MARKERS, ["2010", "2015", "2020", "2022", "2023"],
      [("Население, тыс. человек", (2519.3, 2518.6, 2457.6, 2404.9, 2385.2))],
      0.6, 1.75, 6.0, 4.3, number_format="# ##0", colors=[ACCENT2])
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, ["2010", "2015", "2020", "2022", "2023"],
      [("ВРП, млрд ₽", (376.2, 625.2, 856.5, 1176.2, 1345.1))],
      6.9, 1.75, 5.8, 4.3, number_format="# ##0", colors=[ACCENT])
box(s, "За 13 лет население сократилось на 134,1 тыс. человек (–5,3%), ВРП вырос в 3,6 раза.\n"
       "Индекс физического объёма ВРП в 2023 г. — 104,6% к уровню 2022 г.",
    0.6, 6.15, 12.1, 0.7, size=14, bold=True, color=DARK, line_spacing=1.15)
source(s, "Росстат, «Регионы России — 2025», табл. 2.1, 9.1, 9.3.")
notes(s, "Рост ВРП частично объясняется инфляцией: в текущих ценах он всегда выглядит внушительно. "
         "Поэтому отдельно приводим индекс физического объёма — 104,6%, то есть реальный рост есть, но он умеренный.")

# ---------------------------------------------------------------- 5. Разрез 1: три рынка
s = new_slide()
header(s, "Разрез 1. Три рынка: деньги, труд, товар", "Как распределены ресурсы региональной экономики")
cards = [
    ("РЫНОК ДЕНЕГ", ["Инвестиции в основной капитал — 316,7 млрд ₽",
                     "Основные фонды — 4 161 млрд ₽",
                     "Сальдированный финансовый результат — 155,5 млрд ₽",
                     "Инвестиции = 23,5% ВРП региона"], ACCENT),
    ("РЫНОК ТРУДА", ["Занято 1 147,9 тыс. человек",
                     "Средняя зарплата — 58 626 ₽ в месяц",
                     "7 939 активных вакансий на портале «Работа в России»",
                     "Каждый пятый занятый работает в торговле"], GREEN),
    ("РЫНОК ТОВАРА", ["Промышленность — 1 039,3 млрд ₽",
                      "Сельское хозяйство — 282,1 млрд ₽",
                      "Розничная торговля — 648,5 млрд ₽",
                      "77% отгрузки — обрабатывающие производства"], ACCENT2),
]
for i, (title, items, color) in enumerate(cards):
    left = 0.6 + i * 4.13
    rect(s, left, 1.75, 3.9, 3.5, fill=LIGHT)
    head = s.shapes.add_shape(1, Inches(left), Inches(1.75), Inches(3.9), Inches(0.55))
    head.fill.solid()
    head.fill.fore_color.rgb = color
    head.line.fill.background()
    head.shadow.inherit = False
    box(s, title, left + 0.18, 1.86, 3.6, 0.4, size=14, bold=True, color=WHITE)
    tb = s.shapes.add_textbox(Inches(left + 0.18), Inches(2.5), Inches(3.55), Inches(3.3))
    tf = tb.text_frame
    tf.word_wrap = True
    for j, it in enumerate(items):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.space_after = Pt(12)
        r = p.add_run()
        r.text = "•  " + it
        r.font.size = Pt(13)
        r.font.color.rgb = GRAY
        r.font.name = FONT
source(s, "Росстат, «Регионы России — 2025», табл. 1.1, 3.3, 4.6, 12.1; портал «Работа в России», выгрузка 06.10.2026.")
notes(s, "Первый заданный разрез. Логика такая: деньги превращаются в инвестиции, труд обеспечивает занятость, "
         "товарный рынок показывает результат — сколько регион реально производит и продаёт.")

# ---------------------------------------------------------------- 6. Рынок товара
s = new_slide()
header(s, "Рынок товара: что производит регион", "Отгружено товаров и услуг, 2024 г., млрд рублей")
chart(s, XL_CHART_TYPE.BAR_CLUSTERED,
      ["Обрабатывающие\nпроизводства", "Обеспечение\nэлектроэнергией", "Добыча полезных\nископаемых",
       "Водоснабжение,\nводоотведение"],
      [("млрд ₽", (799.0, 148.0, 70.4, 21.9))],
      0.6, 1.7, 7.3, 4.6, number_format="# ##0.0", colors=[ACCENT], label_size=11)
stacked_kpi(s, [("1 039,3", "млрд ₽ — промышленность всего"),
                ("282,1", "млрд ₽ — сельское хозяйство"),
                ("648,5", "млрд ₽ — розничная торговля")], left=8.15, top=1.85, width=4.6)
box(s, "Структура АПК: растениеводство — 199,2 млрд ₽, животноводство — 82,9 млрд ₽.\n"
       "Обрабатывающая промышленность даёт 77% всей отгрузки промышленности региона.",
    8.15, 4.95, 4.6, 1.3, size=13, color=GRAY, line_spacing=1.2)
box(s, "Ввод жилья — 1 056,4 тыс. м²", 8.15, 6.25, 4.6, 0.4, size=13, bold=True, color=DARK)
source(s, "Росстат, «Регионы России — 2025», табл. 1.1 (продолжение).")
notes(s, "Обратите внимание: добыча даёт всего 70,4 млрд из 1 039,3 — регион не сырьевой. "
         "Основа — обрабатывающие производства, то есть переработка.")

# ---------------------------------------------------------------- 7. Рынок труда
s = new_slide()
header(s, "Рынок труда: где заняты люди", "Среднегодовая численность занятых по видам деятельности, 2024 г., тыс. человек")
chart(s, XL_CHART_TYPE.BAR_CLUSTERED,
      ["Торговля оптовая и розничная", "Обрабатывающие производства", "Транспортировка и хранение",
       "Образование", "Сельское хозяйство", "Строительство", "Здравоохранение и соцуслуги"],
      [("тыс. человек", (234.6, 154.4, 92.4, 90.7, 90.2, 88.7, 81.7))],
      0.6, 1.7, 7.4, 4.6, number_format="# ##0.0", colors=[GREEN], label_size=11)
stacked_kpi(s, [("1 147,9", "тыс. человек занято в экономике"),
                ("58 626", "₽ среднемесячная зарплата"),
                ("7 939", "активных вакансий на портале\n«Работа в России»")], left=8.3, top=1.85, width=4.45)
box(s, "Крупнейший работодатель по числу рабочих мест — торговля: каждый пятый занятый (20,4%).",
    8.3, 5.4, 4.45, 1.1, size=13, color=GRAY, line_spacing=1.2)
source(s, "Росстат, «Регионы России — 2025», табл. 3.3, 3.5, 4.6; портал «Работа в России», выгрузка 06.10.2026.")
notes(s, "Торговля — крупнейшая сфера занятости. Это типично для регионов с крупным областным центром. "
         "Обрабатывающая промышленность на втором месте — 154,4 тыс. человек.")

# ---------------------------------------------------------------- 8. Рынок денег
s = new_slide()
header(s, "Рынок денег: банки, вклады, инвестиции", "Данные Банка России (на начало года) и Росстата, 2024–2025 гг.")
kpi_row(s, [("4", "кредитные организации,\nзарегистрированные в области"),
            ("3", "филиала в регионе\n(в 2011 г. было 66)"),
            ("316,7", "млрд ₽\nинвестиции в основной капитал"),
            ("155,5", "млрд ₽\nфинансовый результат")], top=1.72, height=1.5, size_val=26)
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED,
      ["2011", "2016", "2021", "2023", "2024", "2025"],
      [("Вклады, млрд ₽", (97.3, 209.8, 293.9, 404.1, 453.7, 585.1))],
      0.6, 3.45, 7.3, 3.1, number_format="# ##0.0", colors=[ACCENT], label_size=10)
box(s, "Вклады населения — 514,7 млрд ₽\nиз 585,1 млрд ₽ всех вкладов (2025)",
    8.15, 3.5, 4.6, 1.0, size=14, color=DARK, line_spacing=1.15)
box(s, "Кредиты юридическим лицам — 219,1 млрд ₽, жилищные кредиты — 84,7 млрд ₽ (2024).\n"
       "Сеть сократилась в 20 раз, но объём привлечённых средств вырос в 6 раз.",
    8.15, 4.6, 4.6, 1.7, size=13, color=GRAY, line_spacing=1.2)
source(s, "Росстат, «Регионы России — 2025», табл. 1.1, 20.9–20.17 (по данным Банка России).")
notes(s, "Рынок денег: банковская сеть области резко сократилась — с 66 филиалов в 2011 году "
         "до 3 в 2025-м, при этом вклады выросли с 97 до 585 млрд рублей. Это общероссийский тренд "
         "консолидации банковского сектора: отделения заменяются дистанционным обслуживанием.")

# ---------------------------------------------------------------- 9. Разрез 2: секторы
s = new_slide()
header(s, "Разрез 2. Первичный — вторичный — третичный сектор",
       "Сравнение структуры ВРП (2023) и структуры занятости (2024), %")
chart(s, XL_CHART_TYPE.PIE, ["Первичный", "Вторичный", "Третичный"],
      [("ВРП", (17.6, 28.3, 54.1))], 0.5, 1.75, 4.1, 4.2,
      colors=[GREEN, ACCENT, ACCENT2], label_size=11)
chart(s, XL_CHART_TYPE.PIE, ["Первичный", "Вторичный", "Третичный"],
      [("Занятость", (8.6, 24.8, 66.6))], 4.6, 1.75, 4.1, 4.2,
      colors=[GREEN, ACCENT, ACCENT2], label_size=11)
box(s, "Структура ВРП, 2023 г.", 0.5, 5.95, 4.1, 0.4, size=14, bold=True, color=DARK, align=PP_ALIGN.CENTER)
box(s, "Структура занятости, 2024 г.", 4.6, 5.95, 4.1, 0.4, size=14, bold=True, color=DARK, align=PP_ALIGN.CENTER)
box(s, "Вывод\nДоля вторичного сектора в ВРП выше, чем в занятости, а сельское хозяйство даёт 13,8% ВРП "
       "при 7,9% занятых: производительность в первичном секторе выше средней по региону.",
    8.95, 2.0, 3.85, 4.0, size=14, color=GRAY, line_spacing=1.25)
source(s, "Росстат, «Регионы России — 2025», табл. 9.4 (структура ВРП), 3.5 и 3.6 (занятость).")
notes(s, "Ключевой аналитический слайд. Агрегация сделана нами: первичный = сельское хозяйство + добыча, "
         "вторичный = обработка + энергетика + водоснабжение + строительство, третичный = все услуги.")

# ---------------------------------------------------------------- 10. Отраслевая структура ВРП
s = new_slide()
header(s, "Отраслевая структура ВРП", "2023 г., % к итогу; основные отрасли и прочие")
chart(s, XL_CHART_TYPE.BAR_CLUSTERED,
      ["Обрабатывающие производства", "Сельское хозяйство", "Операции с недвижимостью",
       "Торговля оптовая и розничная", "Транспортировка и хранение", "Государственное управление",
       "Строительство", "Прочие отрасли"],
      [("% ВРП", (17.6, 13.8, 12.5, 10.8, 7.0, 6.7, 5.8, 26.2))],
      0.6, 1.7, 8.0, 4.6, number_format="0.0", colors=[ACCENT], label_size=11)
box(s, "Что важно\nОбрабатывающая промышленность и сельское хозяйство вместе дают 31,4% ВРП — "
       "почти треть экономики региона создаётся в реальном секторе.\n\n"
       "Финансовый сектор занимает лишь 0,3% — регион не является финансовым центром.",
    8.9, 1.9, 3.9, 4.4, size=14, color=GRAY, line_spacing=1.25)
source(s, "Росстат, «Регионы России — 2025», табл. 9.4. Прочие отрасли — сумма отраслей с долей менее 6%.")
notes(s, "Прочие отрасли просуммированы, чтобы диаграмма читалась: там добыча, энергетика, образование, "
         "здравоохранение, связь, культура и остальное.")

# ---------------------------------------------------------------- 11. Территориальная структура
s = new_slide()
header(s, "Территориальная структура", "Муниципальное устройство области на 1 января 2025 г.")
kpi_row(s, [("328", "муниципальных\nобразований"),
            ("37", "муниципальных\nрайонов"),
            ("4", "городских\nокруга"),
            ("250", "сельских\nпоселений")], top=1.8, height=1.7, size_val=28)
bullets(s, [
    "Городское население — 77,0%, сельское — 23,0%: область высокоурбанизирована.",
    "Экономический каркас формируют областной центр Саратов, Энгельс, Балаково и Вольск.",
    "4 городских округа концентрируют промышленность, энергетику и транспортные узлы.",
    "Сельские поселения (250) — основа агропромышленного комплекса: 282,1 млрд ₽ продукции сельского хозяйства.",
], top=4.0, width=12.1, size=15)
source(s, "Росстат, «Регионы России — 2025», табл. 1.6, 1.7, 2.3.")
notes(s, "Здесь показано, как экономика распределена по территории. Далее можно добавить карту объектов "
         "из OpenStreetMap, когда данные будут собраны.")

# ---------------------------------------------------------------- 12. Разрез 3: собственность
s = new_slide()
header(s, "Разрез 3. Государственный — частный — смешанный сектор", "2024 г.")
chart(s, XL_CHART_TYPE.PIE,
      ["Частная", "Муниципальная", "Государственная", "Прочие"],
      [("Организации, %", (81.6, 9.4, 3.5, 5.5))], 0.5, 1.75, 4.2, 4.2,
      colors=[ACCENT, GREEN, ACCENT2, RGBColor(0x9E, 0x9E, 0x9E)], label_size=11)
chart(s, XL_CHART_TYPE.PIE,
      ["Частная", "Иностранная и совместная", "Смешанная российская", "Государственная и муниципальная"],
      [("Оборот, %", (79.9, 12.0, 4.0, 3.6))], 4.9, 1.75, 4.2, 4.2,
      colors=[ACCENT, ACCENT2, RGBColor(0x9E, 0x9E, 0x9E), GREEN], label_size=10)
box(s, "Число организаций: всего 38 314", 0.5, 5.95, 4.2, 0.4, size=14, bold=True,
    color=DARK, align=PP_ALIGN.CENTER)
box(s, "Оборот: всего 1 425,9 млрд ₽", 4.9, 5.95, 4.2, 0.4, size=14, bold=True,
    color=DARK, align=PP_ALIGN.CENTER)
box(s, "Вывод\nЧастный сектор — основа экономики: 81,6% организаций и 79,9% оборота.\n"
       "Государство и муниципалитеты дают лишь 12,9% организаций и 3,6% оборота.\n"
       "Иностранный и совместный бизнес — 12% оборота при 0,7% организаций.",
    9.35, 2.0, 3.45, 4.0, size=13.5, color=GRAY, line_spacing=1.25)
source(s, "Росстат, «Регионы России — 2025», табл. 12.4 (организации), 12.7 (оборот).")
notes(s, "Второй заданный разрез — по формам собственности. Здесь видно, что частный сектор доминирует "
         "и по числу организаций, и по обороту.")

# ---------------------------------------------------------------- 13. Динамика собственности
s = new_slide()
header(s, "Формы собственности в динамике", "Работники организаций по формам собственности, % от общей численности")
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED,
      ["Государственная", "Муниципальная", "Частная", "Смешанная российская", "Иностранная, совместная"],
      [("2010", (29.6, 21.3, 40.9, 3.8, 4.1)), ("2020", (29.6, 14.9, 46.0, 2.9, 5.1))],
      0.6, 1.75, 7.9, 4.5, number_format="0.0", colors=[RGBColor(0x9E, 0x9E, 0x9E), ACCENT],
      legend=True, label_size=10)
box(s, "Тренд\nМуниципальный сектор сократился с 21,3% до 14,9% работников — функции переданы "
       "в частный сектор и на уровень области.\n\n"
       "Частный сектор вырос с 40,9% до 46,0%.\n\n"
       "Государственный сектор стабилен — 29,6%.",
    8.75, 1.95, 4.05, 4.2, size=14, color=GRAY, line_spacing=1.25)
source(s, "Росстат, «Регионы России — 2025», табл. 3.7 (данные за 2010 и 2020 гг.).")
notes(s, "Показатель «работники организаций по формам собственности» публикуется не каждый год — "
         "в сборнике доступны 2010 и 2020 годы. В абсолютном выражении: 716,9 тыс. работников в 2010 г. "
         "и 623,0 тыс. в 2020 г.")

# ---------------------------------------------------------------- 14. Выводы
s = new_slide()
header(s, "Выводы", "Что показывает экономическое описание Саратовской области")
bullets(s, [
    "Экономика региона — индустриально-аграрная с доминирующим третичным сектором (54,1% ВРП, 66,6% занятости).",
    "Реальный сектор даёт 31,4% ВРП: обрабатывающие производства (17,6%) и сельское хозяйство (13,8%).",
    "Промышленность не сырьевая: 77% отгрузки — обрабатывающие производства, добыча — лишь 6,8%.",
    "Население сокращается (–5,3% с 2010 г.) при росте ВРП; экономика растёт за счёт производительности, а не людей.",
    "Производительность в сельском хозяйстве выше средней по региону: 13,8% ВРП при 7,9% занятых.",
    "Основа экономики — частный сектор: 81,6% организаций и 79,9% оборота; доля государства и муниципалитетов в обороте — 3,6%.",
    "Банковская сеть сжалась с 66 филиалов (2011) до 3 (2025), но вклады выросли с 97 до 585 млрд ₽.",
    "Инвестиции составляют 23,5% ВРП, совокупный финансовый результат положителен — 155,5 млрд ₽.",
], width=12.1, top=1.8, size=13.5)
notes(s, "Семь выводов — по одному на каждый содержательный блок плюс обобщение. "
         "Если нужно уложиться в 10 минут, оставляем 4 главных: секторы, реальный сектор, население, собственность.")

# ---------------------------------------------------------------- 15. Источники
s = new_slide()
header(s, "Источники", "Все данные — официальная статистика")
bullets(s, [
    "Росстат. Регионы России. Социально-экономические показатели — 2025: статистический сборник. — М., 2025. URL: rosstat.gov.ru/folder/210/document/13204",
    "Таблицы, использованные в работе: 1.1, 1.6, 1.7, 2.1, 2.3, 3.3, 3.5, 3.6, 3.7, 4.6, 9.1, 9.3, 9.4, 10.1, 12.4, 12.7, 20.9–20.17.",
    "Портал «Работа в России» (Роструд): открытые данные о вакансиях, выгрузка 06.10.2026 — opendata.trudvsem.ru",
    "Дата отсечения данных — 6 октября 2026 г. Все показатели приведены в ценах соответствующих лет.",
    "Данные за 2023–2024 гг. — последние опубликованные на дату выгрузки; ВРП публикуется с лагом в один год.",
], width=12.1, top=1.8, size=14.5)
notes(s, "Список источников для вопросов преподавателя. Ключевое: ВРП за 2024 год ещё не опубликован, "
         "поэтому используется 2023 год.")

prs.save(OUT)
print("Слайдов: %d" % len(prs.slides.__iter__.__self__._sldIdLst))
print("Файл: %s (%d КБ)" % (OUT, os.path.getsize(OUT) // 1024))
