# -*- coding: utf-8 -*-
"""Parser for the 2025 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2025_25-39_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2025_ch3.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json, sys
c=open(SRC, encoding='utf-8').read()
# chapter 3 region: from 제 2절 기초연구 (page ~96) to 부록 (page 125)
s=c.find('<<P100>>'); e=c.find('<<P129>>')
seg=c[s:e]
lines=[l.strip() for l in seg.split('\n')]
SKIP={'과제','번호','과 제 명','착수','년도','종료','기간','(개월)','주관','형태','예산','(억원)','국방전략기술','분야','구분','개요','대상',''}
SUB={'개별기초':('기초연구','개별기초'),'특화연구실':('기초연구','특화연구실'),'특화연구센터':('기초연구','특화연구센터'),
     '응용연구':('응용연구','응용연구'),'응용/시험':('응용/시험','응용/시험'),'시험개발':('시험개발','시험개발'),
     '국방 협업':('무기체계 패키지형','국방협업'),'국방협업':('무기체계 패키지형','국방협업'),'국방 선행':('무기체계 패키지형','국방선행'),'국방선행':('무기체계 패키지형','국방선행'),
     '선도형 핵심기술':('선도형 핵심기술','선도형 핵심기술'),'핵심SW':('핵심SW','핵심SW'),'선행핵심기술':('선행핵심기술','선행핵심기술'),
     'PM기획':('미래도전국방기술','PM기획'),'개별과제':('미래도전국방기술','개별과제')}
rows=[]; cur=None; expect=1; sub=None
def flush():
    global cur
    if cur: rows.append(cur); cur=None
i=0
for l in lines:
    if l.startswith('<<P') or re.match(r'^257-\d+$',l) or l in SKIP: continue
    if l.startswith('제 ') or l.startswith('02') or l.startswith('01') or l.startswith('/ ') or l.startswith('과제 목록'): 
        if '국제공동' in l or l.startswith('과제 목록 (34건)'): pass
        continue
    if l in SUB:
        if cur and sub==SUB[l] and not re.search(r'20\d\d',' '.join(cur['lines'])):
            cur['lines'].append(l); continue
        flush(); sub=SUB[l]; continue
    if l=='국제공동' or l=='기술개발' or l.startswith('핵심기술 국제공동') or l.startswith('하여 전략적') or l.startswith('협력대상국과') or l.startswith('(대상)') or l.startswith('국과연/ 해외'): 
        if l=='국제공동': sub=('국제공동기술개발','국제공동기술개발')
        continue
    m=re.match(r'^(\d{1,3})(?:\s+(.*))?$',l)
    if m and int(m.group(1))==expect:
        flush(); cur={'id':expect,'lines':[],'sub':sub}; expect+=1
        if m.group(2): cur['lines'].append(m.group(2))
        continue
    if cur: cur['lines'].append(l)
flush()
print('rows',len(rows),'expect',expect)
out=[]
bad=[]
for r in rows:
    t=' '.join(r['lines'])
    m=re.search(r'\s(20\d\d)\s+(20\d\d)\s+(\d{1,3})\s+(산학연|국과연|정출연|미정|국/산|산/국|국과연/산학연|산학연/국과연)\s+([\d,]+(?:\.\d\d)?)(?:\s+(.*))?$',' '+t)
    if not m:
        bad.append((r['id'],t)); continue
    name=(' '+t)[:m.start()].strip()
    out.append({'id':r['id'],'name':name,'start':int(m.group(1)),'end':int(m.group(2)),'months':int(m.group(3)),'lead':m.group(4),'budget':float(m.group(5).replace(',','')),'field':((m.group(6) or '').replace('공 란','').strip() or None),'type':r['sub'][0] if r['sub'] else None,'subtype':r['sub'][1] if r['sub'] else None})
print('parsed',len(out),'bad',len(bad))
for b in bad[:20]: print(b)
from collections import Counter
print(Counter((o['type'],o['subtype']) for o in out))
print(Counter(o['field'] for o in out if o['type']=='미래도전국방기술'))
json.dump(out,open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
for o in out[:3]+out[300:303]+out[-3:]: print(o)
