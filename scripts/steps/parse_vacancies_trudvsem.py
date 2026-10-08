# -*- coding: utf-8 -*-
"""Вакансии Саратовской области (trudvsem): параллельный сбор по ключевым словам.

API: offset + limit <= 200, поэтому по каждому ключу берём до 2 страниц по 100.
"""
import json, os, ssl, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# локальные зависимости (numpy, python-docx, python-pptx, osmium)
TOOLS = os.environ.get("SARATOV_TOOLS") or os.path.join(os.path.dirname(PROJECT), ".tools")
OUT = os.path.join(PROJECT, "data", "labor")
os.makedirs(OUT, exist_ok=True)
CTX = ssl._create_unverified_context()
UA = {"User-Agent": "region-econ-research/1.0 (student research)", "Accept": "application/json"}
BASE = "https://opendata.trudvsem.ru/api/v1/vacancies/region/6400000000000"

KEYWORDS = """водитель продавец менеджер инженер учитель воспитатель врач медсестра фельдшер
бухгалтер экономист юрист кассир оператор слесарь электрик электромонтер сварщик токарь
фрезеровщик машинист стропальщик грузчик уборщик дворник повар кондитер пекарь официант
бармен администратор охранник сторож вахтер кладовщик комплектовщик укладчик фасовщик
мерчендайзер торговый агент логист экспедитор диспетчер секретарь делопроизводитель
специалист руководитель директор заведующий начальник мастер технолог конструктор
программист аналитик разработчик тестировщик дизайнер маркетолог кадровик психолог
социальный педагог преподаватель тренер библиотекарь лаборант химик биолог геолог эколог
агроном ветеринар зоотехник механизатор тракторист животновод рабочий подсобный
разнорабочий монтажник строитель каменщик бетонщик арматурщик плотник столяр маляр
штукатур плиточник кровельщик сантехник наладчик станочник аппаратчик энергетик связист
почтальон курьер фармацевт провизор санитарка сиделка няня соцработник инспектор методист
логопед товаровед калькулятор юрисконсульт электрогазосварщик газосварщик аккумуляторщик
кладовщик-комплектовщик комплектовщик-укладчик машинист-обходчик оператор-наладчик
электромеханик электромонтажник радиомонтажник сборщик литейщик шлифовщик фрезеровщик
намотчик контролер дозировщик шихтовщик""".split()
KEYWORDS = list(dict.fromkeys(KEYWORDS))


def fetch(kw, offset):
    url = "%s?%s" % (BASE, urllib.parse.urlencode({"text": kw, "limit": 100, "offset": offset}))
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45, context=CTX) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def collect_kw(kw):
    got = {}
    for offset in (0, 100):
        d = fetch(kw, offset)
        if not d:
            break
        vacs = d.get("results", {}).get("vacancies", []) or []
        for item in vacs:
            got[item["vacancy"]["id"]] = item
        if len(vacs) < 100:
            break
    return kw, got


def main():
    seen = {}
    print("ключевых слов: %d" % len(KEYWORDS), flush=True)
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(collect_kw, kw): kw for kw in KEYWORDS}
        done = 0
        for f in as_completed(futs):
            done += 1
            try:
                kw, got = f.result()
            except Exception as e:
                print("  ошибка: %s" % repr(e)[:80], flush=True)
                continue
            new = 0
            for k, v in got.items():
                if k not in seen:
                    seen[k] = v
                    new += 1
            if done % 10 == 0 or done == len(KEYWORDS):
                print("[%3d/%d] всего уникальных: %d" % (done, len(KEYWORDS), len(seen)), flush=True)

    items = list(seen.values())
    json.dump(items, open(os.path.join(OUT, "vacancies_raw.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    cols = ["id", "job_name", "salary_min", "salary_max", "company", "inn", "city", "lat", "lng",
            "creation_date", "category", "experience", "education", "employment", "schedule"]
    with open(os.path.join(OUT, "vacancies.csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(";".join(cols) + "\n")
        for item in items:
            v = item.get("vacancy", item)
            addr = ((v.get("addresses") or {}).get("address") or [{}])
            a0 = addr[0] if addr else {}
            cat = v.get("category")
            req = v.get("requirement") if isinstance(v.get("requirement"), dict) else {}
            row = {"id": v.get("id", ""), "job_name": (v.get("job-name") or "").strip(),
                   "salary_min": v.get("salary_min", ""), "salary_max": v.get("salary_max", ""),
                   "company": ((v.get("company") or {}).get("name") or "").strip(),
                   "inn": (v.get("company") or {}).get("inn", ""),
                   "city": a0.get("city", "") or (a0.get("location", "") or "")[:150],
                   "lat": a0.get("lat", ""), "lng": a0.get("lng", ""),
                   "creation_date": v.get("creation-date", ""),
                   "category": (cat.get("specialisation", "") if isinstance(cat, dict) else (cat or "")),
                   "experience": req.get("experience", ""), "education": req.get("education", ""),
                   "employment": v.get("employment", ""), "schedule": v.get("schedule", "")}
            f.write(";".join('"%s"' % str(row[c]).replace('"', "'") for c in cols) + "\n")

    print("\nИТОГО уникальных вакансий: %d из 7939" % len(items))
    print("профессий: %d | работодателей: %d" % (
        len({(i["vacancy"].get("job-name") or "") for i in items}),
        len({((i["vacancy"].get("company") or {}).get("name") or "") for i in items})))


if __name__ == "__main__":
    main()
