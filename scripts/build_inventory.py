# -*- coding: utf-8 -*-
"""
Build the unified 국방기술과제 inventory from the per-edition intermediate JSON files.

Inputs (data/intermediate/):
  full_lists_<year>.json   제3장 국방기술과제 목록 (2023-2026, full text)
  full_cards_<year>.json   부록 국방기술 과제카드 (2023-2026, full text)
  full_2026_ch2.json       '26-'40 국방전략기술 기술트리 Lv.1-3 + Lv.4 집계 (full text)
  full_2023_ch2.json       '23-'37 국방전략기술별 국방기술·과제 (full text)
  parse_2025_ch2.json      '25-'39 국방전략기술별 세부기술·과제 (Drive text)
  parse_2024.json          '24-'38 국방전략기술별 과제 (Drive text)
  parse_2022.json          '22-'36 국방전략기술·핵심기술·반영과제 (Drive text)

Outputs: data/inventory.json, data/taxonomy.json, data/inventory.csv, data/stats.json

Merge rule (최신자료 우선): a project that appears in several editions keeps the values of the most
recent edition that lists it; older editions are kept as history so that changes can be shown.
"""
import os, re, json, csv, difflib
from collections import OrderedDict, Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INT = os.path.join(ROOT, 'data', 'intermediate')
OUT = os.path.join(ROOT, 'data')

REFERENCE_YEAR = 2026
LATEST = '2026'
EDITIONS = OrderedDict([
    ('2022', {'title': "'22-'36 국방기술기획서(일반본)", 'published': '2022-04', 'pages_total': 394,
              'coverage': '제2장 국방전략기술 기반 핵심기술 확보전략(8대 분야 99개 국방전략기술·핵심기술 목록 및 반영과제 590건). 제3·4장(과제 목록·과제카드)은 원본 PDF의 글꼴 매핑 손상으로 텍스트 추출 불가'}),
    ('2023', {'title': "'23-'37 국방기술기획서(일반본)", 'published': '2023-06', 'pages_total': 335,
              'coverage': '제2장 10대 분야 30개 국방전략기술별 국방기술·진행/예정과제 전체, 제3장 과제 목록 전체(기초연구~민·군기술협력 853건), 부록 과제카드(개요·연구항목)'}),
    ('2024', {'title': "'24-'38 국방기술기획서(일반본)", 'published': '2024-07', 'pages_total': 247,
              'coverage': '제2장 10대 분야 30개 국방전략기술별 과제 목록 전체, 제3장 과제 목록 전체(778건 중 772건), 부록 과제카드'}),
    ('2025', {'title': "'25-'39 국방기술기획서(일반본)", 'published': '2025-05', 'pages_total': 257,
              'coverage': '제2장 30개 국방전략기술·92개 세부기술·연계 과제, 제3장 과제 목록 전체(644건 : 과제번호·기간·주관형태·예산), 부록 과제카드 전체'}),
    ('2026', {'title': "'26-'40 국방기술기획서(일반본)", 'published': '2026-07', 'pages_total': 455,
              'coverage': '제2장 10대 분야 30개 국방전략기술 기술트리(Lv.1~Lv.3)와 기술개발소요 집계, 제3장 과제 목록 전체(461건 : 과제번호·기간·주관형태·예산·국방전략기술 분야), 부록 과제카드 전체'}),
])

FIELDS = ['인공지능', '유·무인 복합', '양자', '우주', '에너지', '첨단소재', '사이버·네트워크', '센서·전자기전', '추진', 'WMD 대응']
FIELD_ALIASES = {'유무인 복합': '유·무인 복합', '유·무인복합': '유·무인 복합', '유무인복합': '유·무인 복합', '사이버네트워크': '사이버·네트워크', '센서전자기전': '센서·전자기전',
                 'WMD대응': 'WMD 대응', '사이버·네트워크': '사이버·네트워크'}
STECH_ALIASES = {'유무인 협업': '유·무인 협업', '유무인 협업(지상/해양/공중)': '유·무인 협업', '유·무인 협업(지상/해양/공중)': '유·무인 협업',
                 '자율 임무수행(지상/해양/공중)': '자율 임무수행'}

STAGE_MAP = {
    '기초': '기초연구', '기초연구': '기초연구', '개별기초': '기초연구', '특화실': '기초연구', '특화연구실': '기초연구', '특화센터': '기초연구', '특화연구센터': '기초연구',
    '응용': '응용연구', '응용연구': '응용연구',
    '시험': '시험개발', '시험개발': '시험개발',
    '응용/시험': '응용/시험',
    '패키지형': '무기체계 패키지형', '국방협업': '무기체계 패키지형', '국방선행': '무기체계 패키지형', '무기체계 패키지형': '무기체계 패키지형', '국방 협업': '무기체계 패키지형', '국방 선행': '무기체계 패키지형',
    '선도형': '선도형 핵심기술', '선도형 핵심기술': '선도형 핵심기술',
    '핵심SW': '핵심SW', '핵심 SW': '핵심SW',
    '선행핵심': '선행핵심기술', '선행핵심기술': '선행핵심기술',
    '국제공동': '국제공동기술개발', '국제공동기술개발': '국제공동기술개발',
    '미래도전': '미래도전국방기술', '미래도전국방기술': '미래도전국방기술', '개별과제': '미래도전국방기술', 'PM기획': '미래도전국방기술', '가교적 연구': '미래도전국방기술', '기술경진대회': '미래도전국방기술',
    '민군': '민·군기술협력', '민군협력': '민·군기술협력', '민·군기술협력': '민·군기술협력',
}
SUBTYPE_MAP = {'특화실': '특화연구실', '특화연구실': '특화연구실', '특화센터': '특화연구센터', '특화연구센터': '특화연구센터',
               '국방협업': '국방협업', '국방 협업': '국방협업', '국방선행': '국방선행', '국방 선행': '국방선행', '개별기초': '개별기초', 'PM기획': 'PM기획', '개별과제': '개별과제',
               '가교적 연구': '가교적 연구', '기술경진대회': '기술경진대회'}

# Projects whose name changed (or was garbled by PDF column extraction) between editions: old name -> '25-'39 과제번호
RENAMED_PROJECTS = {
    '사이버 기술 시범 전장관리체계 핵심기술을 활용한 미래 지능형 함정 통합 사이버방호체계': 625,
    '유·무인 감지 시스템 무기체계용 개발 2차전지의 안전성 확보를 위한 초고감도 배터리 열폭주 조기': 641,
    '무기체계 핵심기술 전자부품/단말 개발 연구 탑재형 온센서 AI 지원 초경량 인공지능 컴퓨팅 SW 플랫폼': 595,
    '미래 위성 전장용 자유공간 광통신(FSO, 간 초고속 통신시스템 개발 Free-space optical Communication) 기반': 562,
    '120mm 유·무인복합 자주박격포 무인포탑 설계 및 사거리 연장기술': 423,
    'IMINT(영상)와 HUMINT(텍스트) 융합기법 연구(Image Captioning)': 507,
    '초정밀 이용한 지자기 실내측위 기반 해군 함정의 대테러 작전 수행 시스템 연구 실시간 디지털 트윈 서비스 및 AR 글래스를': 616,
    '전장상황 변화에 따른 지능형 방책 추천 기술': 211,
    '비정형 대응 합동지휘통제 멀티모달 데이터 초지능화 융합 기술개발 다중가설 뉴로-심볼릭 AI기반 미래 하이브리드전': 577,
    '517 이중대역 넷기반 탄도탄 적외선 작전 센서 능력 기반 기술 미사일 개발 탐지 기술': 333,
    '초저궤도 광학위성 발사모델 개발': 542,
}
GARBLED = {k for k in RENAMED_PROJECTS if k.startswith(('사이버 기술 시범', '유·무인 감지', '무기체계 핵심기술 전자부품', '미래 위성 전장용', '초정밀 이용한', '비정형 대응', '517 '))}
STAGE_PERIOD_RE = re.compile(r"(기초연구|응용연구|시험개발|응용/시험|패키지형|국방협업|국방선행|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터)\s+'\d\d-'\d\d\s*")


def load(name):
    p = os.path.join(INT, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def norm_name(s):
    s = s or ''
    s = s.replace('\\', '')
    s = re.sub(r'\(구\.[^)]*\)', '', s)
    s = re.sub(r'[\s·ㆍ‧∙・‧･·ㆍ\-–—/,.()\[\]:;’\'"`~!?]', '', s)
    return s.lower()


def period_years(p):
    if not p:
        return None, None
    m = re.match(r"'(\d\d)-'(\d\d)", p)
    if not m:
        return None, None
    return 2000 + int(m.group(1)), 2000 + int(m.group(2))


def field_norm(f):
    if not f:
        return None
    f = re.sub('[ㆍ‧･∙⸱]', '·', f.strip())
    f = FIELD_ALIASES.get(f, f)
    return f if f in FIELDS else None


def stech_norm(s):
    if not s:
        return None
    s = re.sub('[ㆍ‧･∙⸱]', '·', s.strip())
    return STECH_ALIASES.get(s, s)


def clean_sub(s):
    if not s:
        return None
    s = STAGE_PERIOD_RE.sub('', s)
    s = re.sub(r'\s+', ' ', s).strip(' -')
    return s or None


class Inventory:
    def __init__(self):
        self.records = []
        self.by_norm = {}
        self.norm_keys = []
        self.by_no_2025 = {}

    def find(self, name):
        n = norm_name(name)
        if n in self.by_norm:
            return self.by_norm[n]
        if name in RENAMED_PROJECTS and self.by_no_2025:
            return self.by_no_2025.get(RENAMED_PROJECTS[name])
        best, score = None, 0
        for k in self.norm_keys:
            if abs(len(k) - len(n)) > max(6, len(n) * 0.25):
                continue
            r = difflib.SequenceMatcher(None, n, k).ratio()
            if r > score:
                best, score = k, r
        if best and score >= 0.9:
            return self.by_norm[best]
        return None

    def add(self, rec):
        self.records.append(rec)
        for v in rec['name_variants']:
            self._index(rec, v)

    def _index(self, rec, name):
        n = norm_name(name)
        if n and n not in self.by_norm:
            self.by_norm[n] = rec
            self.norm_keys.append(n)

    def register_variant(self, rec, name):
        if name in GARBLED or not name:
            return
        if name not in rec['name_variants']:
            rec['name_variants'].append(name)
        self._index(rec, name)


def new_record(name):
    return {
        'name': name, 'name_variants': [name],
        'program_type': None, 'program_subtype': None, 'lead_type': None,
        'start_year': None, 'end_year': None, 'duration_months': None, 'budget_100m_krw': None,
        'field': None, 'strategic_tech': None, 'sub_tech': None,
        'weapon_system_field': None, 'tech_field': None,
        'legacy_2022_field': None, 'legacy_2022_tech': None,
        'linked_core_techs': [],
        'description': None, 'research_items': None,
        'editions': OrderedDict(),
        'first_edition': None, 'latest_edition': None,
    }


def set_edition(rec, year, data):
    ed = rec['editions'].setdefault(year, {})
    for k, v in data.items():
        if v is None:
            continue
        if k == 'core_techs':
            ed.setdefault(k, [])
            for x in v:
                if x and x not in ed[k] and not re.match(r'^\d{3}\s', x) and len(x) <= 80:
                    ed[k].append(x)
        else:
            ed[k] = v
    rec['first_edition'] = min([rec['first_edition'], year]) if rec['first_edition'] else year
    rec['latest_edition'] = max([rec['latest_edition'], year]) if rec['latest_edition'] else year


def apply_card(rec, year, card):
    if not card:
        return
    ed = rec['editions'].setdefault(year, {})
    ed['card'] = {'desc': card.get('desc'), 'research_items': card.get('research_items') or None, 'weapon_system_field': card.get('ws_field'),
                  'tech_field': card.get('tech_field'), 'phase_periods': card.get('phase_periods')}


def main():
    inv = Inventory()
    lists = {y: load('full_lists_%s.json' % y) or [] for y in ('2023', '2024', '2025', '2026')}
    cards = {y: load('full_cards_%s.json' % y) or [] for y in ('2023', '2024', '2025', '2026')}
    cards_by_id = {y: {c['id']: c for c in cards[y]} for y in cards}
    cards_by_norm = {y: {norm_name(c['name']): c for c in cards[y]} for y in cards}
    p25_2 = load('parse_2025_ch2.json')
    p24 = load('parse_2024.json')
    p23 = load('full_2023_ch2.json')
    p22 = load('parse_2022.json')
    p26 = load('full_2026_ch2.json')

    # 2023 list rows: numbering restarts per section -> recover the global 과제번호 through the cards (same order, same names)
    for r in lists['2023']:
        c = cards_by_norm['2023'].get(norm_name(r['name']))
        r['id'] = c['id'] if c else None

    # ------------------------------------------------------------------ 제3장 과제 목록, latest edition first
    def absorb_list(year):
        new = 0
        for p in lists[year]:
            rec = inv.find(p['name']) if year != LATEST else None
            if rec is None:
                rec = new_record(p['name']); inv.add(rec); new += 1
            inv.register_variant(rec, p['name'])
            ptype = STAGE_MAP.get(p['subtype'] or p['type'], p['type'])
            psub = SUBTYPE_MAP.get(p['subtype']) if p.get('subtype') else None
            ed = {'project_no': p['id'], 'stage': p['subtype'] or p['type'], 'period': "'%02d-'%02d" % (p['start'] % 100, p['end'] % 100),
                  'start_year': p['start'], 'end_year': p['end'], 'duration_months': p.get('months'), 'lead_type': p['lead'], 'budget_100m_krw': p['budget'],
                  'tbd_years': True if p.get('tbd_years') else None, 'source': '제3장 국방기술과제 목록'}
            if p.get('field'):
                ed['field'] = field_norm(p['field'])
            set_edition(rec, year, ed)
            card = cards_by_id[year].get(p['id']) if p['id'] else None
            apply_card(rec, year, card)
            # latest-edition values win: fill only if not yet set by a newer edition
            if rec['latest_edition'] == year:
                rec['program_type'] = ptype; rec['program_subtype'] = psub; rec['lead_type'] = p['lead']
                rec['start_year'], rec['end_year'] = p['start'], p['end']
                rec['duration_months'] = p.get('months'); rec['budget_100m_krw'] = p['budget']
                if ed.get('field'):
                    rec['field'] = ed['field']
        print(year, 'list absorbed, new records:', new)

    for y in ('2026', '2025', '2024', '2023'):
        absorb_list(y)
        if y == '2025':
            inv.by_no_2025 = {r['editions']['2025']['project_no']: r for r in inv.records if '2025' in r['editions'] and r['editions']['2025'].get('project_no')}

    # ------------------------------------------------------------------ 제2장 국방전략기술 연계 (분야/국방전략기술/세부기술)
    def absorb_ch2(year, items, source, with_sub=True):
        new = 0
        for p in items:
            rec = inv.find(p['name'])
            if rec is None:
                rec = new_record(p['name']); inv.add(rec); new += 1
                rec['program_type'] = STAGE_MAP.get(p['stage'], p['stage']); rec['program_subtype'] = SUBTYPE_MAP.get(p['stage'])
                rec['start_year'], rec['end_year'] = period_years(p['period'])
            inv.register_variant(rec, p['name'])
            ed = {'project_no': p.get('id'), 'stage': p['stage'], 'period': p['period'], 'source2': source}
            f = field_norm(p.get('field'))
            if f:
                ed['field'] = f
            if p.get('stech'):
                ed['strategic_tech'] = stech_norm(p['stech'])
            if with_sub and p.get('sub'):
                ed['sub_tech'] = clean_sub(p['sub'])
            if p.get('ktech'):
                ed['core_techs'] = [p['ktech']]
            if p.get('status'):
                ed['status_tag'] = p['status']
            set_edition(rec, year, ed)
            if rec['program_type'] is None:
                rec['program_type'] = STAGE_MAP.get(p['stage'], p['stage'])
            if rec['start_year'] is None:
                rec['start_year'], rec['end_year'] = period_years(p['period'])
        print(year, source, 'new records:', new)

    absorb_ch2('2025', p25_2['projs'], '제2장 국방전략기술별 국방기술과제 목록')
    absorb_ch2('2024', p24['projs'], '제2장 국방전략기술별 국방기술과제 목록')
    absorb_ch2('2023', p23['projs'], '제2장 국방전략기술별 국방기술 목록', with_sub=False)
    for p in p22['projs']:
        rec = inv.find(p['name'])
        if rec is None:
            rec = new_record(p['name']); inv.add(rec)
            rec['program_type'] = STAGE_MAP.get(p['stage'], p['stage']); rec['program_subtype'] = SUBTYPE_MAP.get(p['stage'])
            rec['start_year'], rec['end_year'] = period_years(p['period'])
        inv.register_variant(rec, p['name'])
        set_edition(rec, '2022', {'project_no': p['id'], 'stage': p['stage'], 'period': p['period'], 'legacy_field': p['field'], 'legacy_tech': p['stech'],
                                  'core_techs': [p['ktech']] if p.get('ktech') else None, 'source': '제2장 국방전략기술별 핵심기술 목록(반영과제)'})
        rec['legacy_2022_field'] = p['field']
        rec['legacy_2022_tech'] = rec['legacy_2022_tech'] or p['stech']

    # ------------------------------------------------------------------ derived fields
    for rec in inv.records:
        eds = rec['editions']
        years = sorted(eds.keys())
        latest = years[-1]
        led = eds[latest]
        if led.get('period') and rec['start_year'] is None:
            rec['start_year'], rec['end_year'] = period_years(led['period'])
        if rec['program_type'] is None and led.get('stage'):
            rec['program_type'] = STAGE_MAP.get(led['stage'], led['stage'])
        if rec['program_subtype'] is None and led.get('stage') in SUBTYPE_MAP:
            rec['program_subtype'] = SUBTYPE_MAP[led['stage']]
        # 국방전략기술 classification: newest edition that gives it; the 2026 list gives the 분야 only
        for y in reversed(years):
            e = eds[y]
            if e.get('strategic_tech'):
                rec['strategic_tech'] = e['strategic_tech']; rec['sub_tech'] = e.get('sub_tech'); rec['field'] = rec['field'] or e.get('field')
                if e.get('field') and rec['field'] and e['field'] != rec['field']:
                    rec['strategic_tech_note'] = '%s년판 분류(%s › %s)와 최신 분야(%s)가 다름' % (y, e['field'], e['strategic_tech'], rec['field'])
                break
        if rec['field'] is None:
            for y in reversed(years):
                if eds[y].get('field'):
                    rec['field'] = eds[y]['field']; break
        # card data (개요·연구항목·무기체계 분야·기술 분야): newest card wins
        for y in reversed(years):
            c = eds[y].get('card')
            if c:
                rec['description'] = c.get('desc') or None
                rec['research_items'] = c.get('research_items') or None
                rec['weapon_system_field'] = c.get('weapon_system_field')
                rec['tech_field'] = c.get('tech_field')
                if c.get('phase_periods'):
                    rec['phase_periods'] = c['phase_periods']
                break
        lct = []
        for y, ed in eds.items():
            for k in ed.get('core_techs', []):
                if k not in lct:
                    lct.append(k)
        rec['linked_core_techs'] = lct
        s, e = rec['start_year'], rec['end_year']
        if s and s > REFERENCE_YEAR:
            st = '착수 예정'
        elif e and e < REFERENCE_YEAR:
            st = '종료'
        else:
            st = '진행 중'
        rec['status'] = st
        rec['in_latest_master_list'] = (LATEST in eds and 'source' in eds[LATEST])
        rec['status_note'] = None if rec['in_latest_master_list'] else '최신 과제 목록(’26-’40 기획서)에 미수록 — 종료·통합·명칭 변경 가능성'
        # change log between consecutive editions
        changes = []
        for a, b in zip(years, years[1:]):
            ea, eb = eds[a], eds[b]
            for key, label in (('period', '사업기간'), ('stage', '사업구분'), ('project_no', '과제번호'), ('strategic_tech', '국방전략기술'), ('sub_tech', '세부기술'), ('field', '국방전략기술 분야'), ('budget_100m_krw', '예산(억원)'), ('lead_type', '주관형태')):
                va, vb = ea.get(key), eb.get(key)
                if va is None or vb is None:
                    continue
                if key == 'stage':
                    ta, tb = STAGE_MAP.get(va, va), STAGE_MAP.get(vb, vb)
                    sa, sb = SUBTYPE_MAP.get(va), SUBTYPE_MAP.get(vb)
                    if ta == tb and (sa is None or sb is None or sa == sb):
                        continue
                if key == 'sub_tech' and norm_name(va) == norm_name(vb):
                    continue
                if key == 'budget_100m_krw' and abs(float(va) - float(vb)) < 0.005:
                    continue
                if str(va) != str(vb):
                    changes.append({'from_edition': a, 'to_edition': b, 'item': label, 'before': va, 'after': vb})
        if len(rec['name_variants']) > 1 and len({norm_name(v) for v in rec['name_variants']}) > 1:
            changes.append({'from_edition': rec['first_edition'], 'to_edition': latest, 'item': '과제명', 'before': rec['name_variants'][-1], 'after': rec['name_variants'][0]})
        rec['changes'] = changes
        rec['editions_listed'] = years

    # ------------------------------------------------------------------ ids & ordering
    def sort_key(r):
        no = r['editions'].get(LATEST, {}).get('project_no')
        if no:
            return (0, no, '')
        no25 = r['editions'].get('2025', {}).get('project_no')
        if no25:
            return (1, no25, '')
        return (2, 0, r['latest_edition'] + r['name'])
    inv.records.sort(key=sort_key)
    for i, rec in enumerate(inv.records, 1):
        rec['inventory_id'] = 'KDTI-%04d' % i
    keys = ['inventory_id', 'name', 'name_variants', 'program_type', 'program_subtype', 'lead_type', 'start_year', 'end_year', 'duration_months',
            'budget_100m_krw', 'field', 'strategic_tech', 'sub_tech', 'strategic_tech_note', 'weapon_system_field', 'tech_field', 'legacy_2022_field', 'legacy_2022_tech',
            'linked_core_techs', 'status', 'status_note', 'in_latest_master_list', 'first_edition', 'latest_edition', 'editions_listed', 'editions', 'changes',
            'description', 'research_items', 'phase_periods']
    ordered = []
    for rec in inv.records:
        o = OrderedDict()
        for k in keys:
            o[k] = rec.get(k)
        ordered.append(o)

    # ------------------------------------------------------------------ taxonomy
    tax = {'fields': [], 'legacy_2022': {'fields': []}, 'lv4_summary_2026': p26.get('lv4_summary') if p26 else None}
    nodes = p26['nodes'] if p26 else []
    lv1_26 = {(n['field'], stech_norm(n['name'])): n for n in nodes if n['level'] == 1}
    lv2_26 = defaultdict(list); lv3_26 = defaultdict(list)
    for n in nodes:
        if n['level'] == 2:
            lv2_26[(n['field'], stech_norm(n['lv1']))].append(n)
        elif n['level'] == 3:
            lv3_26[(n['field'], n['lv2'])].append(n)
    t25 = {(t['field'], stech_norm(t['name'])): t for t in p25_2['techs']}
    t24 = {(t['field'], stech_norm(t['name'])): t for t in p24['techs']}
    t23 = {(t['field'], stech_norm(t['name'])): t for t in p23['techs']}
    subdefs = defaultdict(list)
    for sd in p25_2['subdefs']:
        subdefs[(sd['field'], stech_norm(sd['stech']))].append(sd)
    proj_by_sub = defaultdict(list); proj_by_tech = defaultdict(list); proj_by_field = defaultdict(list)
    for rec in ordered:
        if rec['field']:
            proj_by_field[rec['field']].append(rec['inventory_id'])
        if rec['field'] and rec['strategic_tech']:
            proj_by_tech[(rec['field'], rec['strategic_tech'])].append(rec['inventory_id'])
            proj_by_sub[(rec['field'], rec['strategic_tech'], rec['sub_tech'])].append(rec['inventory_id'])
    order25 = [(t['field'], stech_norm(t['name'])) for t in p25_2['techs']]
    for f in FIELDS:
        fo = {'name': f, 'techs': [], 'projects': sorted(set(proj_by_field.get(f, []))), 'lv4_summary_2026': (tax['lv4_summary_2026'] or {}).get(f)}
        for (ff, tn) in order25:
            if ff != f:
                continue
            t = {'name': tn, 'desc': None, 'desc_source': None, 'subs': []}
            for src, d in (('2026', lv1_26.get((f, tn))), ('2025', t25.get((ff, tn))), ('2024', t24.get((ff, tn))), ('2023', t23.get((ff, tn)))):
                if d and d.get('desc'):
                    t['desc'] = d['desc']; t['desc_source'] = src; break
            subs = []
            for n in lv2_26.get((f, tn), []):
                subs.append({'code': n['code'], 'name': n['name'], 'desc': n['desc'], 'desc_source': '2026',
                             'lv3': [{'code': m['code'], 'name': m['name'], 'desc': m['desc']} for m in lv3_26.get((f, n['name']), [])]})
            for sd in subdefs.get((ff, tn), []):
                hit = None
                for s_ in subs:
                    a, b = norm_name(s_['name']), norm_name(sd['name'])
                    if a == b or (len(b) > 3 and b in a) or (len(a) > 3 and a in b):
                        hit = s_; break
                if hit:
                    hit['desc_2025'] = sd['desc']
                else:
                    subs.append({'code': str(sd['order']), 'name': sd['name'], 'desc': sd['desc'], 'desc_source': '2025', 'lv3': []})
            for s_ in subs:
                ids = []
                for (pf, pt, ps), lst in proj_by_sub.items():
                    if pf == f and pt == tn and ps:
                        a, b = norm_name(ps), norm_name(s_['name'])
                        if a == b or (len(b) > 3 and b in a) or (len(a) > 3 and a in b):
                            ids += lst
                s_['projects'] = sorted(set(ids))
            t['subs'] = subs
            t['projects'] = sorted(set(proj_by_tech.get((f, tn), [])))
            fo['techs'].append(t)
        tax['fields'].append(fo)
    kt_by = defaultdict(list)
    for k in p22['ktechs']:
        kt_by[(k['field'], k['stech'])].append(k)
    proj22 = defaultdict(list)
    for rec in ordered:
        ed = rec['editions'].get('2022')
        if ed:
            for k in ed.get('core_techs', []):
                proj22[k].append(rec['inventory_id'])
    for f in ['자율·인공지능 기반 감시정찰 분야', '초연결 지능형 지휘통제 분야', '초고속·고위력 정밀타격 분야', '미래형 추진 및 스텔스 기반 플랫폼 분야',
              '유·무인 복합 전투수행 분야', '첨단기술 기반 개인전투체계 분야', '사이버 능동대응 및 미래형 방호 분야', '미래형 첨단 신기술 분야']:
        fo = {'name': f, 'techs': []}
        for t in p22['techs']:
            if t['field'] != f:
                continue
            fo['techs'].append({'name': t['name'], 'desc': t['desc'],
                                'core_techs': [{'name': k['name'], 'desc': k['desc'], 'projects': sorted(set(proj22.get(k['name'], [])))} for k in kt_by[(f, t['name'])]]})
        tax['legacy_2022']['fields'].append(fo)
    # 2023 국방기술 (name + 명세) grouped by 국방전략기술, with linked projects
    kt23 = defaultdict(list)
    for k in p23['ktechs']:
        kt23[(k['field'], stech_norm(k['stech']))].append(k)
    proj23 = defaultdict(list)
    for rec in ordered:
        ed = rec['editions'].get('2023')
        if ed:
            for k in ed.get('core_techs', []):
                proj23[k].append(rec['inventory_id'])
    for fo in tax['fields']:
        for t in fo['techs']:
            t['defense_techs_2023'] = [{'name': k['name'], 'desc': k['desc'], 'projects': sorted(set(proj23.get(k['name'], [])))} for k in kt23.get((fo['name'], t['name']), [])]

    # ------------------------------------------------------------------ stats
    latest_recs = [r for r in ordered if r['in_latest_master_list']]
    stats = {
        'total_projects': len(ordered),
        'by_edition': {y: sum(1 for r in ordered if y in r['editions']) for y in EDITIONS},
        'by_status': dict(Counter(r['status'] for r in ordered)),
        'by_field': dict(Counter(r['field'] or '미분류(국방전략기술 미연계)' for r in ordered)),
        'by_field_latest': dict(Counter(r['field'] or '미분류' for r in latest_recs)),
        'by_program_type': dict(Counter(r['program_type'] for r in ordered)),
        'by_program_type_latest': dict(Counter(r['program_type'] for r in latest_recs)),
        'by_lead_type': dict(Counter(r['lead_type'] or '미상' for r in ordered)),
        'latest_master_count': len(latest_recs),
        'budget_total_latest_master': round(sum(r['budget_100m_krw'] or 0 for r in latest_recs), 2),
        'budget_by_field_latest_master': {},
        'with_description': sum(1 for r in ordered if r['description']),
        'with_changes': sum(1 for r in ordered if [c for c in r['changes'] if c['item'] != '과제번호']),
        'ai_projects': sum(1 for r in ordered if r['field'] == '인공지능'),
        'ai_projects_latest': sum(1 for r in latest_recs if r['field'] == '인공지능'),
        'reference_year': REFERENCE_YEAR, 'latest_edition': LATEST,
    }
    bf = defaultdict(float)
    for r in latest_recs:
        if r['budget_100m_krw']:
            bf[r['field'] or '미분류'] += r['budget_100m_krw']
    stats['budget_by_field_latest_master'] = {k: round(v, 2) for k, v in bf.items()}

    meta = {'generated_from': 'scripts/build_inventory.py', 'reference_year': REFERENCE_YEAR, 'latest_edition': LATEST, 'editions': EDITIONS,
            'record_count': len(ordered), 'notes': [
                '각 과제의 현재 값(과제명·사업구분·기간·주관형태·예산·국방전략기술 분류·개요)은 해당 과제가 수록된 가장 최신 기획서를 기준으로 한다.',
                '과제번호는 기획서 발간 연도마다 다시 매겨지므로 연도별 과제번호는 editions 아래에 보관하고, 사이트용 식별자는 KDTI-#### 를 별도 부여한다.',
                '상태(status)는 2026년을 기준으로 사업기간으로부터 산출한 값이며, 기획서에 명시된 진행/예정 표기(’23-’37)는 editions.status_tag 에 보관한다.',
                '국방전략기술 분야는 ’26-’40 과제 목록 기준, 국방전략기술·세부기술은 ’25-’39 제2장(없으면 ’24-’38, ’23-’37) 기준이다.',
                '’22-’36 기획서는 Google Drive 텍스트 변환(앞부분 약 150쪽)으로 제2장만 반영되었다. 나머지 네 권은 PDF 전문을 변환해 제2장·제3장·부록을 모두 반영했다.',
            ]}
    with open(os.path.join(OUT, 'inventory.json'), 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'stats': stats, 'projects': ordered}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'taxonomy.json'), 'w', encoding='utf-8') as f:
        json.dump(tax, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    cols = ['inventory_id', 'name', 'program_type', 'program_subtype', 'lead_type', 'start_year', 'end_year', 'duration_months', 'budget_100m_krw',
            'field', 'strategic_tech', 'sub_tech', 'weapon_system_field', 'tech_field', 'status', 'status_note', 'in_latest_master_list', 'first_edition', 'latest_edition', 'editions_listed',
            'project_no_2022', 'project_no_2023', 'project_no_2024', 'project_no_2025', 'project_no_2026', 'legacy_2022_field', 'legacy_2022_tech', 'linked_core_techs',
            'name_variants', 'description', 'research_items', 'changes']
    with open(os.path.join(OUT, 'inventory.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in ordered:
            row = []
            for c in cols:
                if c.startswith('project_no_'):
                    row.append(r['editions'].get(c[-4:], {}).get('project_no', ''))
                elif c in ('editions_listed', 'linked_core_techs', 'name_variants'):
                    row.append('; '.join(map(str, r[c] or [])))
                elif c == 'changes':
                    row.append('; '.join('%s→%s %s: %s → %s' % (ch['from_edition'], ch['to_edition'], ch['item'], ch['before'], ch['after']) for ch in r['changes']))
                else:
                    v = r.get(c)
                    row.append('' if v is None else v)
            w.writerow(row)
    print('records', len(ordered))
    print('stats', json.dumps({k: v for k, v in stats.items() if k not in ('budget_by_field_latest_master',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
