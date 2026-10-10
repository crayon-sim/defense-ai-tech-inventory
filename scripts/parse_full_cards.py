# -*- coding: utf-8 -*-
"""
Parse the 부록 국방기술 과제카드 (개요·연구항목·사업기간·예산·주관형태·무기체계 분야·기술 분야) from the
full-text extractions of the 2023-2026 editions.  Output: data/intermediate/full_cards_<year>.json

Card layout (all editions):
    [무기체계 분야]                       <- sometimes on its own line above the number
    N 과제명                [무기체계 분야]  <- or: 과제명 part 1 / N / 과제명 part 2 (long names)
    (기술 분야)
    개요 line / 개 요  개요 line / 개요 line   <- the label sits vertically centred in its paragraph
    연구항목 items / items line
    사업기간 YYYY-YYYY(NN개월) 예산(억원) X 주관형태 Y [사업구분 Z]
"""
import re, sys
from collections import Counter
from fulltext import pages, norm, is_junk_line, save

FOOT = re.compile(r'^사업기간\s*(20\d\d)\s*[-~]\s*(20\d\d)\s*\((\d+)개월\)\s*예산\(억원\)\s*([\d,.]+)\s*(?:주관형태|과제제안기관|수행기관)\s*(\S.*?)(?:\s*사업구분\s*(\S+))?\s*$')
# 응용/시험 cards: '2011-2014 /' , '사업기간 예산(억원) 133.03 주관형태 산학연' , '2026-2030(90개월)'
FOOT_SPLIT = re.compile(r'^사업기간\s*예산\(억원\)\s*([\d,.]+)\s*(?:주관형태|과제제안기관|수행기관)\s*(\S.*?)(?:\s*사업구분\s*(\S+))?\s*$')
PHASE_LINE = re.compile(r'^(20\d\d)\s*[-~]\s*(20\d\d)\s*(?:\((\d+)개월\))?\s*(?:/\s*(?:(20\d\d)\s*[-~]\s*(20\d\d)\s*(?:\((\d+)개월\))?)?)?\s*$')
MONTHS_LINE = re.compile(r'^\((\d+)개월(?:\s*/\s*(\d+)개월)?\)$')
NUM_ONLY = re.compile(r'^(\d{1,3})\.?$')
INLINE = re.compile(r'^(\d{1,3})\.?\s+(\S.*)$')
WS_FIELDS = {'지휘통제·통신', '지휘통제통신', '지휘통제', '감시·정찰', '감시정찰', '기동', '함정', '항공', '화력', '방호', '사이버', '우주', '기타', '국방M&S', '국방 M&S', '전력지원', '통신', '감시 정찰', '지휘 통제'}
TECH_TAIL = re.compile(r'^(.*?)\s*\((.{1,30})\)\s*$')
SUBTYPE_LINE = re.compile(r'^(?:\d\s+|(?:가|나|다|라|마|바|사)\.\s*)(개별기초|특화연구실|특화연구센터|응용연구|응용/시험|시험개발|국방\s?협업|국방\s?선행|선도형 핵심기술|핵심\s?SW|선행핵심기술|PM\s?기획|개별과제|가교적 연구|기술경진대회|개별|PM)\s*$')


def split_tail(s):
    """'과제명   화력' -> ('과제명', '화력'); '과제명  (기계)' -> ('과제명', None, '기계')"""
    ws = tech = None
    m = TECH_TAIL.match(s)
    if m and (m.group(1).endswith(' ') or len(m.group(1)) == 0 or re.search(r'\s{2,}\S*$', s[:m.start(2) - 1] if m.start(2) > 0 else '')):
        body, tech = m.group(1).rstrip(), m.group(2)
        if '(' in tech:
            body, tech = s, None
        s = body
    parts = re.split(r'\s{3,}', s.strip())
    if len(parts) >= 2 and (parts[-1] in WS_FIELDS or (len(parts[-1]) <= 7 and re.match(r'^[가-힣·&\s]+$', parts[-1]))):
        ws = parts[-1]; s = ' '.join(parts[:-1])
    return norm(s), ws, tech


def finish(card, buf):
    """Assign name/desc/research_items from the buffered lines of one card."""
    lines = [l for l in buf if l.strip()]
    i_items = next((i for i, l in enumerate(lines) if l.strip().startswith('연구항목')), None)
    desc_lines, item_lines = [], []
    if i_items is None:
        desc_lines = lines
    else:
        lab = lines[i_items].strip()
        inline = re.sub(r'^연구항목\s*', '', lab).strip()
        after = lines[i_items + 1:]
        before = lines[:i_items]
        if inline:
            item_lines = [inline] + after
        else:
            # label alone: the item text is vertically centred around it -> one line above belongs to it
            if before:
                item_lines = [before[-1]] + after; before = before[:-1]
            else:
                item_lines = after
        desc_lines = before
    desc = ' '.join(re.sub(r'^개\s?요\s*', '', l.strip()) for l in desc_lines)
    card['desc'] = norm(desc)
    card['research_items'] = norm(' '.join(l.strip() for l in item_lines))
    card['name'] = norm(card['name'])
    return card


def parse(year):
    P = pages(year)
    if not P:
        return []
    start = None
    for i, p in enumerate(P):
        h = norm(' '.join(p.split('\n')[:5]))
        if re.search(r'부록\s*1\s*\|?\s*기초연구', h) and i > 80:
            start = i; break
    if start is None:
        return []
    cards = []
    cur = None; buf = []; subtype = None
    pre = []            # orphan lines just before a card header (무기체계 분야, or name part 1)
    expect = 1
    for pi in range(start, len(P)):
        lines = [l.rstrip() for l in P[pi].split('\n')]
        nonempty = [l.strip() for l in lines if l.strip()]
        page_no = nonempty[-1] if nonempty and re.match(r'^\d{1,3}$', nonempty[-1]) else None
        head = norm(' '.join(lines[:4]))
        if cur is None and ('국방기술과제 분류' in head or re.match(r'^(약어|약 어)', head)):
            break
        seen_page_no = False
        for raw in lines:
            s = raw.strip()
            if not s or is_junk_line(s, numbers_are_junk=False):
                continue
            if page_no is not None and s == page_no and raw is lines[-1 - (len(lines) - 1 - max(i for i, x in enumerate(lines) if x.strip()))]:
                continue
            if cur is None:
                sm = SUBTYPE_LINE.match(s)
                if sm:
                    subtype = {'개별': '개별과제', 'PM': 'PM기획', '국방 협업': '국방협업', '국방 선행': '국방선행', '핵심 SW': '핵심SW', 'PM 기획': 'PM기획'}.get(sm.group(1), sm.group(1)); pre = []; continue
                if re.match(r'^부록\s*\d', s) or re.match(r'^부\s*록', s):
                    subtype = None; pre = []; continue
                m1 = NUM_ONLY.match(s); m2 = INLINE.match(s)
                num = int(m1.group(1)) if m1 else (int(m2.group(1)) if m2 else None)
                if num is not None and (expect <= num <= expect + 5 or num == 1):
                    cur = {'edition': year, 'id': num, 'name': '', 'desc': '', 'research_items': '', 'ws_field': None, 'tech_field': None, 'subtype': subtype, 'page': pi + 1}
                    expect = num + 1; buf = []
                    if cur['ws_field'] in ('연구항목', '세부과제', '개 요', '개요'):
                        cur['ws_field'] = None
                    # 무기체계 분야 / name part 1 from the lines above
                    p1 = None
                    for x in pre:
                        if x in WS_FIELDS or (len(x) <= 7 and re.match(r'^[가-힣·&\s]+$', x)):
                            cur['ws_field'] = x
                        else:
                            p1 = x
                    pre = []
                    if m1:
                        if p1:
                            n, ws, tech = split_tail(p1); cur['name'] = n; cur['ws_field'] = cur['ws_field'] or ws; cur['tech_field'] = cur['tech_field'] or tech
                        cur['_need_part2'] = True
                    else:
                        n, ws, tech = split_tail(m2.group(2)); cur['name'] = n; cur['ws_field'] = cur['ws_field'] or ws; cur['tech_field'] = cur['tech_field'] or tech
                        cur['_need_part2'] = bool(ws) and not tech   # 2023 style: "N. part1   화력" / "part2   (추진)"
                        if p1:   # a name fragment above an inline header (rare) -> prefix
                            n1, ws1, _ = split_tail(p1); cur['name'] = norm(n1 + ' ' + cur['name']); cur['ws_field'] = cur['ws_field'] or ws1
                    continue
                pre.append(s)
                if len(pre) > 3:
                    pre = pre[-3:]
                continue
            # inside a card
            if cur.get('_await_phase'):
                pm = PHASE_LINE.match(s); mm = MONTHS_LINE.match(s)
                done = False
                if pm:
                    ph = ['%s-%s' % (pm.group(1), pm.group(2))] + (['%s-%s' % (pm.group(4), pm.group(5))] if pm.group(4) else [])
                    cur['phase_periods'] = [p for p in [cur.pop('_phase1', None)] if p] + ph
                    last = cur['phase_periods'][-1].split('-')
                    cur['start'], cur['end'] = int(last[0]), int(last[1])
                    cur['months'] = int(pm.group(6) or pm.group(3)) if (pm.group(6) or pm.group(3)) else cur.get('months')
                    done = True
                elif mm:
                    cur['months'] = int(mm.group(2) or mm.group(1)); done = True
                if done or True:
                    if cur.get('_phase1') and 'phase_periods' not in cur:
                        cur['phase_periods'] = cur['_phase1'].split(' / ')
                        last = cur['phase_periods'][-1].split('-'); cur['start'], cur['end'] = int(last[0]), int(last[1])
                    cur.pop('_phase1', None); cur.pop('_await_phase', None); cur.pop('_need_part2', None)
                    if cur['ws_field'] in ('연구항목', '세부과제', '개 요', '개요', '연구실', '연구소'):
                        cur['ws_field'] = None
                    cards.append(finish(cur, buf)); cur = None; buf = []
                    if done:
                        continue
                    # the line belongs to the next card: fall through with cur = None
                    sm = SUBTYPE_LINE.match(s)
                    if sm:
                        subtype = {'개별': '개별과제', 'PM': 'PM기획', '국방 협업': '국방협업', '국방 선행': '국방선행', '핵심 SW': '핵심SW', 'PM 기획': 'PM기획'}.get(sm.group(1), sm.group(1)); pre = []; continue
                    m1 = NUM_ONLY.match(s); m2 = INLINE.match(s)
                    num = int(m1.group(1)) if m1 else (int(m2.group(1)) if m2 else None)
                    if num is not None and (expect <= num <= expect + 5 or num == 1):
                        cur = {'edition': year, 'id': num, 'name': '', 'desc': '', 'research_items': '', 'ws_field': None, 'tech_field': None, 'subtype': subtype, 'page': pi + 1}
                        expect = num + 1; buf = []
                        if m1:
                            cur['_need_part2'] = True
                        else:
                            n, ws, tech = split_tail(m2.group(2)); cur['name'] = n; cur['ws_field'] = ws; cur['tech_field'] = tech
                            cur['_need_part2'] = bool(ws) and not tech
                    else:
                        pre = [s]
                    continue
            fs = FOOT_SPLIT.match(s)
            if fs:
                cur['budget'] = float(fs.group(1).replace(',', '')); cur['lead'] = fs.group(2).strip()
                if fs.group(3):
                    cur['subtype_card'] = fs.group(3)
                if buf and PHASE_LINE.match(buf[-1]):
                    pm = PHASE_LINE.match(buf[-1])
                    cur['_phase1'] = '%s-%s' % (pm.group(1), pm.group(2)) + (' / %s-%s' % (pm.group(4), pm.group(5)) if pm.group(4) else '')
                    cur['start'], cur['end'] = int(pm.group(4) or pm.group(1)), int(pm.group(5) or pm.group(2))
                    buf = buf[:-1]
                cur['_await_phase'] = True
                continue
            fm = FOOT.match(s)
            if fm:
                cur['start'], cur['end'], cur['months'] = int(fm.group(1)), int(fm.group(2)), int(fm.group(3))
                cur['budget'] = float(fm.group(4).replace(',', '')); cur['lead'] = fm.group(5)
                if fm.group(6):
                    cur['subtype_card'] = fm.group(6)
                cur.pop('_need_part2', None)
                if cur['ws_field'] in ('연구항목', '세부과제', '개 요', '개요', '연구실', '연구소'):
                    cur['ws_field'] = None
                cards.append(finish(cur, buf)); cur = None; buf = []
                continue
            if cur.get('_need_part2'):
                cur['_need_part2'] = False
                if re.match(r'^\(.{1,30}\)$', s):
                    cur['tech_field'] = cur['tech_field'] or s[1:-1]; continue
                if not s.startswith('개') and not s.startswith('연구항목'):
                    n, ws, tech = split_tail(s)
                    cur['name'] = norm(cur['name'] + ' ' + n); cur['ws_field'] = cur['ws_field'] or ws; cur['tech_field'] = cur['tech_field'] or tech
                    continue
            if not buf and re.match(r'^\(.{1,40}\)$', s) and not cur['tech_field']:
                cur['tech_field'] = s[1:-1]; continue
            if not buf and re.match(r'^\(구\.', s):
                buf.append(s); continue
            buf.append(s)
    return cards


if __name__ == '__main__':
    years = sys.argv[1:] or ['2023', '2024', '2025', '2026']
    for y in years:
        cards = parse(y)
        print(y, 'cards', len(cards), 'with desc', sum(1 for c in cards if c['desc']), 'with items', sum(1 for c in cards if c['research_items']),
              Counter(c['subtype'] for c in cards).most_common(14))
        ids = [c['id'] for c in cards]
        print('  id range', min(ids) if ids else None, max(ids) if ids else None, 'dupes', len(ids) - len(set(ids)), 'missing', sorted(set(range(1, max(ids) + 1)) - set(ids))[:30] if ids else None)
        print('  ws', Counter(c['ws_field'] for c in cards).most_common(14))
        print('  tech', Counter(c['tech_field'] for c in cards).most_common(14))
        for c in cards[:3]:
            print('  ', {k: (v[:70] if isinstance(v, str) else v) for k, v in c.items()})
        save('full_cards_%s.json' % y, cards)
