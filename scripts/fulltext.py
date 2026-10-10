# -*- coding: utf-8 -*-
"""Helpers for the full-text extractions (tools/pdf2text.html or pdftotext -layout output) in data/source/full/."""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FULL = os.path.join(ROOT, 'data', 'source', 'full')
FILES = {
    '2022': '2022_22-36_국방기술기획서_일반본.full.txt',
    '2023': '2023_23-37_국방기술기획서_일반본.full.txt',
    '2024': '2024_24-38_국방기술기획서_일반본.full.txt',
    '2025': '2025_25-39_국방기술기획서_일반본.full.txt',
    '2026': '2026_26-40_국방기술기획서_일반본.full.txt',
}
INT = os.path.join(ROOT, 'data', 'intermediate')


def pages(year):
    """Return the list of page texts (form-feed separated)."""
    path = os.path.join(FULL, FILES[year])
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        t = f.read()
    t = re.sub('[ㆍ‧･∙⸱‧]', '·', t)
    return t.split('\f')


def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def is_junk_line(l, numbers_are_junk=True):
    """Page furniture: running headers, vertical side labels, page numbers."""
    s = l.strip()
    if not s:
        return True
    if re.match(r"^(’\d\d-’\d\d 국방기술기획서|\d{3}-\d{1,3})$", s):
        return True
    if numbers_are_junk and re.match(r'^\d{1,3}$', s):
        return True
    if len(s) == 1 and not re.match(r'^\d$', s):      # vertical one-character side labels (제/장/국/방 ...)
        return True
    if re.match(r'^(과제|번호 년도.*|과 제 명|착수|종료|년도|기간|\(개월\)|주관|형태|예산|\(억원\)|국방전략기술|분야|순번 과 제 명.*)$', s):
        return True
    if re.match(r'^(착수|과제)\s+', s) and ('종료' in s or '년도' in s or '주관' in s):
        return True
    if re.match(r'^번호\s+년도', s) or re.match(r'^순번', s):
        return True
    if s in ('이후', '이후 이후') or re.match(r'^이후\s+이후$', s):
        return True
    return False


def save(name, obj):
    import json
    os.makedirs(INT, exist_ok=True)
    with open(os.path.join(INT, name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
