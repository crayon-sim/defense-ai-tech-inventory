# -*- coding: utf-8 -*-
"""
Parse 제2장 of the '23-'37 edition from the full text: 10 fields x 30 국방전략기술 -> 국방기술 (name + 명세)
-> 진행/예정/종료과제 references (과제번호, 과제명, 단계, 기간).  Output: data/intermediate/full_2023_ch2.json
"""
import re
from collections import Counter
from fulltext import pages, norm, is_junk_line, save

FIELDS = ['인공지능', '유·무인 복합', '양자', '우주', '에너지', '첨단소재', '사이버·네트워크', '센서·전자기전', '추진', 'WMD 대응']
SEC = re.compile(r'^제\s*(\d+)\s*절\s+(.+)$')
ST = '기초|응용|시험|응용/시험|패키지형|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터|민군'
REF = re.compile(r'(\d{3})\s+(.+?)\((' + ST + r')[^,()]*,\s*(\d{2})\s*[-~∼]\s*(\d{2})\)')
STATUS = re.compile(r'^\((진행과제|예정과제|종료과제|반영과제)\)\s*')
STECH = re.compile(r'^(\d{1,2})\.\s+(\S.*)$')


def parse():
    P = pages('2023')
    techs = []; ktechs = []; projs = []
    field = None; stech = None; mode = None; cur = None; status = None; prev = ''; skip_desc = False
    for pi, page in enumerate(P):
        for raw in page.split('\n'):
            s = raw.strip()
            if not s:
                continue
            m = SEC.match(s)
            if m and pi > 20:
                title = norm(m.group(2))
                if title in FIELDS:
                    field = title; mode = None; cur = None; stech = None; prev = ''; continue
                if title.startswith('추진 현황') or title.startswith('기초연구'):
                    field = None; mode = None; continue
            if field is None or is_junk_line(s):
                continue
            if s.startswith('라 국방전략기술별 국방기술 목록'):
                mode = 'list'; cur = None; prev = ''; continue
            if s.startswith('나 국방전략기술'):
                mode = 'spec'; continue
            if s.startswith('다 ') or s.startswith('02/') or s.startswith('01/'):
                if mode != 'list':
                    mode = None
                continue
            ms = STECH.match(s)
            if ms and len(ms.group(2)) < 50:
                name = norm(ms.group(2))
                if mode == 'spec':
                    stech = name; techs.append({'field': field, 'order': int(ms.group(1)), 'name': name, 'desc': ''}); cur = None; prev = s; continue
                if mode == 'list':
                    hit = [t for t in techs if t['field'] == field and t['name'] == name]
                    stech = name
                    if not hit:
                        techs.append({'field': field, 'order': int(ms.group(1)), 'name': name, 'desc': ''})
                    cur = None; prev = s; skip_desc = True; continue
            if mode == 'spec':
                if techs and techs[-1]['field'] == field and not s.startswith('∙'):
                    techs[-1]['desc'] = norm(techs[-1]['desc'] + ' ' + s)
                prev = s; continue
            if mode != 'list':
                prev = s; continue
            if s.startswith('국방기술/국방기술과제'):
                cur = None; prev = s; skip_desc = False; continue
            if skip_desc:
                if len(s) > 50 and not STATUS.match(s) and not re.match(r'^\d{3}\s', s):
                    prev = s; continue
                skip_desc = False
            sm = STATUS.match(s)
            if sm:
                status = sm.group(1); rest = s[sm.end():]
                for mm in REF.finditer(rest):
                    projs.append({'field': field, 'stech': stech, 'ktech': cur['name'] if cur else None, 'status': status, 'id': int(mm.group(1)),
                                  'name': norm(mm.group(2)), 'stage': mm.group(3), 'period': "'%s-'%s" % (mm.group(4), mm.group(5))})
                if cur is not None:
                    cur['has_refs'] = True
                prev = s; continue
            if re.match(r'^\d{3}\s', s) and REF.search(s) and cur is not None and cur.get('has_refs'):
                for mm in REF.finditer(s):
                    projs.append({'field': field, 'stech': stech, 'ktech': cur['name'], 'status': status, 'id': int(mm.group(1)),
                                  'name': norm(mm.group(2)), 'stage': mm.group(3), 'period': "'%s-'%s" % (mm.group(4), mm.group(5))})
                prev = s; continue
            # 국방기술 name vs 명세 lines
            if STECH.match(prev) and len(s) > 50:
                prev = s; continue          # description of the 국방전략기술 itself (before 국방기술/국방기술과제)
            prev_is_ref = bool(STATUS.match(prev)) or (re.match(r'^\d{3}\s', prev) and REF.search(prev)) or prev.startswith('국방기술/국방기술과제') or STECH.match(prev) is not None
            if cur is None or prev_is_ref or (len(s) <= 45 and cur.get('desc') and len(prev) < 70 and not cur.get('has_refs') is None and not s.endswith(('.', ','))):
                cur = {'field': field, 'stech': stech, 'name': s, 'desc': '', 'has_refs': False}; ktechs.append(cur)
            else:
                cur['desc'] = norm(cur['desc'] + ' ' + s)
            prev = s
    bad = {k['name'] for k in ktechs if len(k['name']) > 55 or re.match(r'^\d{3}\s', k['name'])}
    ktechs = [k for k in ktechs if k['name'] not in bad]
    for k in ktechs:
        k.pop('has_refs', None)
    for p in projs:
        if p['ktech'] in bad:
            p['ktech'] = None
    return techs, ktechs, projs


if __name__ == '__main__':
    techs, ktechs, projs = parse()
    print('techs', len(techs), 'ktechs', len(ktechs), 'projs', len(projs), 'unique ids', len({p['id'] for p in projs}))
    print(Counter(t['field'] for t in techs)); print(Counter(p['field'] for p in projs)); print(Counter(p['status'] for p in projs))
    print([k['name'] for k in ktechs[:8]])
    save('full_2023_ch2.json', {'techs': techs, 'ktechs': ktechs, 'projs': projs})
