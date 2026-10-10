# -*- coding: utf-8 -*-
"""
Parse 제2장 of the '26-'40 edition from the full text: 10 fields x 30 국방전략기술 (Lv.1) -> 100 세부기술 (Lv.2)
-> 300 구성기술 (Lv.3) with descriptions, plus a per-field count of the Lv.4 기술개발소요 roadmap rows
(확보시기 / 사업추진방안 / 확보여부).  Output: data/intermediate/full_2026_ch2.json
"""
import re
from collections import Counter, defaultdict
from fulltext import pages, norm, is_junk_line, save

FIELDS = ['인공지능', '유·무인 복합', '양자', '우주', '에너지', '첨단소재', '사이버·네트워크', '센서·전자기전', '추진', 'WMD 대응']
SEC = re.compile(r'^제(\d+)절\s*\|\s*(.+)$')
LV1 = re.compile(r'^(\d{1,2})\.\s+(\S.*)$')
LV2 = re.compile(r'^(\d{1,3})\s+([^\d\s].*)$')
LV3 = re.compile(r'^(\d{1,3})-(\d{1,2})\s+(\S.*)$')
LV4 = re.compile(r'(단기|중기|장기|단/중기|중/장기|단/장기)\s+(핵심기술|미래도전|민간기술|핵심/미래)\s+(●|○)')


def parse():
    P = pages('2026')
    nodes = []; lv4 = defaultdict(list)
    field = None; mode = None; lv1 = None; lv2 = None
    cur = None
    for pi, page in enumerate(P):
        lines = [l.rstrip() for l in page.split('\n')]
        for raw in lines:
            s = raw.strip()
            if not s:
                continue
            m = SEC.match(s)
            if m and not re.search(r'\s제\d+절', s):
                title = norm(m.group(2))
                if title in FIELDS and pi > 20:
                    field = title; mode = None; cur = None
                    continue
                if title in ('추진 현황', '기초연구') and pi > 250:
                    field = None; mode = None
                continue
            if field is None:
                continue
            if s.startswith('나 국방전략기술 명세'):
                mode = 'spec'; cur = None; continue
            if s.startswith('다 ') or s.startswith('나 국방전략기술별 기술개발소요') or s.startswith('02'):
                if mode == 'spec':
                    cur = None
                mode = 'other' if not s.startswith('나 국방전략기술별 기술개발소요') else 'lv4'
                continue
            for mm in LV4.finditer(s):
                lv4[field].append(mm.groups())
            if mode == 'lv4' or mode != 'spec':
                continue
            if is_junk_line(s):
                continue
            m3 = LV3.match(s); m1 = LV1.match(s); m2 = LV2.match(s)
            if m3:
                cur = {'level': 3, 'field': field, 'lv1': lv1, 'lv2': lv2, 'code': m3.group(1) + '-' + m3.group(2), 'name': norm(m3.group(3)), 'desc': ''}
                nodes.append(cur); continue
            if m1 and len(m1.group(2)) < 60:
                lv1 = norm(m1.group(2)); lv2 = None
                cur = {'level': 1, 'field': field, 'code': m1.group(1), 'name': lv1, 'desc': ''}
                nodes.append(cur); continue
            if m2 and len(m2.group(2)) < 60 and not re.match(r'^\d{1,3}\s+\d', s):
                lv2 = norm(m2.group(2))
                cur = {'level': 2, 'field': field, 'lv1': lv1, 'code': m2.group(1), 'name': lv2, 'desc': ''}
                nodes.append(cur); continue
            if cur is not None:
                if s.startswith('개 요') or s.startswith('∙') or s.startswith('·'):
                    continue
                cur['desc'] = norm(cur['desc'] + ' ' + s)
    # de-duplicate (a Lv.1 title reappears as a running heading on later pages)
    seen = set(); out = []
    for n in nodes:
        k = (n['field'], n['level'], n['code'], n['name'])
        if k in seen:
            continue
        seen.add(k); out.append(n)
    summary = {}
    for f, rows in lv4.items():
        summary[f] = {'total': len(rows), 'by_timing': dict(Counter(r[0] for r in rows)), 'by_approach': dict(Counter(r[1] for r in rows)),
                      'by_need': dict(Counter({'●': '확보 가능(추가 과제화 필요성 낮음)', '○': '추가 과제화 필요'}[r[2]] for r in rows))}
    return out, summary


if __name__ == '__main__':
    nodes, summary = parse()
    print(Counter((n['field'], n['level']) for n in nodes))
    print('lv4', {k: v['total'] for k, v in summary.items()})
    for n in nodes[:6]:
        print(n['level'], n['code'], n['name'], '|', n['desc'][:50])
    save('full_2026_ch2.json', {'nodes': nodes, 'lv4_summary': summary})
