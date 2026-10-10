# -*- coding: utf-8 -*-
"""
Parse the 제3장 국방기술과제 목록 tables (과제번호·과제명·착수/종료년도·주관형태·예산 …) from the
full-text extractions of the 2023-2026 editions.  Output: data/intermediate/full_lists_<year>.json
"""
import re, sys
from collections import Counter
from fulltext import pages, norm, is_junk_line, save

LEAD = r'(산학연|국과연|정출연|미정|국/산|산/국|국과연/산학연|산학연/국과연)'
YEAR = r'(20\d\d)(?:년)?'
# data line: id [name] start end [months] lead budget [field]
DATA = re.compile(r'^(\d{1,3})\s+(.*?)\s*' + YEAR + r'\s+' + YEAR + r'\s+(?:(\d{1,3})\s+)?' + LEAD + r'\s*([\d][\d ,.]*?)\s*(?:\s+(\S.*?))?\s*$')
# rows without years on the data line (years printed as '2027년 2030년' on the line above): id [name] months lead budget [field]
NOYEAR = re.compile(r'^(\d{1,3})\s+(.*?)\s*(\d{1,3})\s+' + LEAD + r'\s*([\d][\d ,.]*?)\s*(?:\s+(\S.*?))?\s*$')
YEARPAIR = re.compile(r'(20\d\d)년\s+(20\d\d)년')
# 2023 glitch: "2018 2024 201산학연 5.40"
DATA23 = re.compile(r'^(\d{1,3})\s+(.*?)\s*' + YEAR + r'\s+' + YEAR + r'\s*\d*\s*' + LEAD + r'\s*([\d][\d ,.]*)\s*$')

SECTION_HDR = re.compile(r'^제\s*(\d+)\s*절\s*\|?\s*(.+)$')
LIST_HDR = re.compile(r'과제 목록\s*\(')
SUBTYPES = {'개별기초': ('기초연구', '개별기초'), '특화연구실': ('기초연구', '특화연구실'), '특화연구센터': ('기초연구', '특화연구센터'),
            '응용연구': ('응용연구', None), '응용/시험': ('응용/시험', None), '시험개발': ('시험개발', None),
            '국방 협업': ('무기체계 패키지형', '국방협업'), '국방협업': ('무기체계 패키지형', '국방협업'),
            '국방 선행': ('무기체계 패키지형', '국방선행'), '국방선행': ('무기체계 패키지형', '국방선행'),
            '선도형 핵심기술': ('선도형 핵심기술', None), '핵심SW': ('핵심SW', None), '선행핵심기술': ('선행핵심기술', None),
            'PM기획': ('미래도전국방기술', 'PM기획'), '개별과제': ('미래도전국방기술', '개별과제'),
            '가교적 연구': ('미래도전국방기술', '가교적 연구'), '기술경진대회': ('미래도전국방기술', '기술경진대회'),
            '과제형': ('민·군기술협력', '과제형'), '신규': ('민·군기술협력', None)}
SECTION_TYPE = {'기초연구': ('기초연구', None), '응용연구/시험개발': ('응용연구', None), '무기체계 패키지형 핵심기술': ('무기체계 패키지형', None),
                '선도형 핵심기술/핵심SW/선행핵심기술': ('선도형 핵심기술', None), '국제공동기술개발': ('국제공동기술개발', None), '국제공동 연구개발': ('국제공동기술개발', None),
                '국제공동연구개발': ('국제공동기술개발', None), '미래도전국방기술': ('미래도전국방기술', None), '민·군기술협력사업': ('민·군기술협력', None)}


def parse(year):
    P = pages(year)
    if not P:
        return []
    # chapter 3 spans from the first page whose text starts a '제N절 … 과제 목록' until the appendix
    rows = []
    in_ch3 = False
    sec_type = None; sub = None; seq_offset = 0; seen_in_section = 0
    counts_hdr = None
    pending_before = []
    cur = None     # row whose name may continue on following lines
    for pi, page in enumerate(P):
        lines = page.split('\n')
        head = norm(' '.join(lines[:6]))
        if ('부록' in head or '부 록' in head) and ('기초연구' in head) and in_ch3 and pi > 60:
            break   # appendix reached
        if '국방기술 과제카드' in head and in_ch3:
            break
        for raw in lines:
            l = raw.rstrip()
            s = l.strip()
            if not s:
                continue
            m = SECTION_HDR.match(s)
            if m and not re.search(r'\d{4}', s):
                title = norm(m.group(2))
                if title in SECTION_TYPE:
                    sec_type = SECTION_TYPE[title]; sub = None; in_ch3 = True
                    if year == '2023':
                        seq_offset += seen_in_section; seen_in_section = 0
                    cur = None; pending_before = []
                continue
            if not in_ch3:
                continue
            if LIST_HDR.search(s):
                counts_hdr = s; cur = None; pending_before = []
                continue
            if s in SUBTYPES:
                if cur and not cur['name'] and pending_before:
                    pass
                sub = SUBTYPES[s]; cur = None; pending_before = []
                continue
            if is_junk_line(s):
                continue
            m = DATA.match(s) or (DATA23.match(s) if year == '2023' else None)
            ny = None
            if not m:
                yp = None; src_k = None
                s_wo = YEARPAIR.sub('', s).strip()
                if YEARPAIR.search(s) and NOYEAR.match(s_wo):
                    yp = YEARPAIR.search(s); s = s_wo
                else:
                    for k in range(len(pending_before) - 1, -1, -1):
                        yy = YEARPAIR.search(pending_before[k])
                        if yy:
                            yp = yy; src_k = k; break
                if yp is not None:
                    ny = NOYEAR.match(s)
                    if ny:
                        if src_k is not None:
                            pending_before[src_k] = YEARPAIR.sub('', pending_before[src_k]).strip()
                            pending_before = [x for x in pending_before if x]
                        gg = ny.groups()
                        m = True
                        g = (gg[0], gg[1], yp.group(1), yp.group(2), gg[2], gg[3], gg[4], gg[5])
            if m:
                if ny is None:
                    g = m.groups()
                pid = int(g[0]); name = norm(g[1]); start = int(g[2]); end = int(g[3])
                if len(g) == 8:
                    months = int(g[4]) if g[4] else None; lead = g[5]; budget = g[6]; field = norm(g[7]) if g[7] else None
                else:
                    months = None; lead = g[4]; budget = g[5]; field = None
                budget = budget.replace(' ', '').replace(',', '')
                try:
                    budget = float(budget)
                except ValueError:
                    budget = None
                if field in ('-', '–', ''):
                    field = None
                tbd = '년' in s and re.search(r'20\d\d년', s) is not None
                row = {'edition': year, 'seq': pid, 'name': name, 'start': start, 'end': end, 'months': months, 'lead': lead, 'budget': budget,
                       'field': field, 'type': (sub or sec_type or (None, None))[0], 'subtype': (sub or (None, None))[1] or (sec_type[1] if sec_type else None),
                       'tbd_years': tbd, 'page': pi + 1}
                if not name and pending_before:
                    row['name'] = norm(' '.join(pending_before))
                    pending_before = []
                elif pending_before and cur is not None and cur.get('_open'):
                    cur['name'] = norm(cur['name'] + ' ' + ' '.join(pending_before)); pending_before = []
                elif pending_before:
                    # stray lines before a complete row: belong to the previous wrapped row (suffix)
                    if cur is not None and cur.get('_wrapped'):
                        cur['name'] = norm(cur['name'] + ' ' + ' '.join(pending_before))
                    pending_before = []
                row['_wrapped'] = not name
                row['_open'] = not name
                rows.append(row); cur = row; seen_in_section += 1
                continue
            # orphan line (name fragment)
            if re.match(r'^[\d.,\s]+$', s):
                continue
            if cur is not None and cur.get('_open'):
                # suffix of a wrapped name directly after the data line
                cur['name'] = norm(cur['name'] + ' ' + s); cur['_open'] = False
                continue
            pending_before.append(s)
    for r in rows:
        r.pop('_open', None); r.pop('_wrapped', None)
        r['name'] = norm(re.sub(r'(\s+이후)+\s*$', '', re.sub(r'\s+이후\s+이후\s+', ' ', r['name'])))
        if year == '2023':
            r['id'] = None   # 2023 lists restart numbering per section; global ids are reconstructed in the build step
        else:
            r['id'] = r['seq']
    return rows


if __name__ == '__main__':
    years = sys.argv[1:] or ['2023', '2024', '2025', '2026']
    for y in years:
        rows = parse(y)
        print(y, 'rows', len(rows), Counter((r['type'], r['subtype']) for r in rows))
        bad = [r for r in rows if not r['name'] or r['budget'] is None]
        print('  bad', len(bad), [(r['seq'], r['name'][:30], r['budget']) for r in bad[:8]])
        save('full_lists_%s.json' % y, rows)
