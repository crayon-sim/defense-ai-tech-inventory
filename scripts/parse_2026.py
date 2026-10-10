# -*- coding: utf-8 -*-
"""Parser for the 2026 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2026_26-40_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2026.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json
from collections import Counter
c=open(SRC, encoding='utf-8').read()
c=re.sub(r'\n\s*\n','\n',c); c=re.sub('[ㆍ‧･∙]','·',c)
L=[l.strip() for l in c.split('\n')]
FIELDS=['인공지능','유·무인 복합','양자','우주','에너지','첨단소재','사이버·네트워크','센서·전자기전','추진','WMD 대응']
def norm(x): return re.sub(r'\s+',' ',x).strip()
s=next(i for i,l in enumerate(L) if l=='제2절 | 인공지능' and i>100)
field=None; lv1=None; lv2=None; nodes=[]; mode=None
i=s
HDR=re.compile(r'^(제\d+절 \| |제2장|’26-’40|제 2 장|\d{1,3}$)')
while i<len(L):
    l=L[i]
    m=re.match(r'^제(\d+)절 \| (.+)$',l)
    if m and m.group(2).replace('･','·') in FIELDS and not l.startswith('제1절'):
        if '제3절' in l and '제4절' in l: i+=1; continue  # running header
        field=m.group(2).replace('･','·'); mode='spec'; i+=1; continue
    if l.startswith('나 국방전략기술 명세'): mode='spec'; i+=1; continue
    if l.startswith('다 ') or l.startswith('02') : mode=None
    if mode!='spec' or field is None: i+=1; continue
    m1=re.match(r'^(\d{1,2})\\\. (.+)$',l); m2=re.match(r'^(\d{1,3}) ([^\d].+)$',l); m3=re.match(r'^(\d{1,3})-(\d{1,2}) (.+)$',l)
    def grab(j):
        d=[]
        while j<len(L) and L[j] and not re.match(r'^(\d{1,2}\\\. |\d{1,3} [^\d]|\d{1,3}-\d{1,2} |개 요|∙|다 |02|제\d+절|제2장|’26)',L[j]) and not re.match(r'^\d{1,3}$',L[j]) and not L[j].startswith('나 '):
            d.append(L[j]); j+=1
        return d,j
    if m3:
        name=m3.group(3); d,j=grab(i+1)
        # name may wrap: if the next line is short and no desc follows... keep simple
        nodes.append({'level':3,'field':field,'lv1':lv1,'lv2':lv2,'code':m3.group(1)+'-'+m3.group(2),'name':norm(name),'desc':norm(' '.join(d))}); i=j; continue
    if m1:
        lv1=norm(m1.group(2)); d,j=grab(i+1)
        nodes.append({'level':1,'field':field,'code':m1.group(1),'name':lv1,'desc':norm(' '.join(d))}); i=j; continue
    if m2:
        lv2=norm(m2.group(2)); d,j=grab(i+1)
        nodes.append({'level':2,'field':field,'lv1':lv1,'code':m2.group(1),'name':lv2,'desc':norm(' '.join(d))}); i=j; continue
    i+=1
print(Counter((n['field'],n['level']) for n in nodes))
seen=set(); nn=[]
for n in nodes:
    if n['field']!='인공지능': continue
    k=(n['level'],n['name'])
    if k in seen: continue
    seen.add(k); nn.append(n)
nodes=nn
seg='\n'.join(L[s:])
ai_end=seg.find('제3절 | 유·무인 복합', 2000)
ai=seg[:ai_end] if ai_end>0 else seg
lv4=re.findall(r'(단기|중기|장기)\s+(핵심기술|미래도전|민간기술|핵심/미래)\s+(●|○)',ai)
lv4s={'total':len(lv4),'by_timing':dict(Counter(x[0] for x in lv4)),'by_approach':dict(Counter(x[1] for x in lv4)),'by_need':dict(Counter({'●':'확보 가능(추가 과제화 필요성 낮음)','○':'추가 과제화 필요'}[x[2]] for x in lv4))}
print('lv4',lv4s)
json.dump({'nodes':nodes,'lv4_summary':lv4s},open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
for n in nodes:
    if n['level']<=2: print(n['level'],n['code'],n['name'],'|',n['desc'][:40])
# Lv4 기술개발소요 (AI) best effort
seg='\n'.join(L[s:])
k=seg.find('기술개발소요')
print('Lv4 mentions', seg.count('기술개발소요'), seg.count('단기 핵심기술'), seg.count('중기'), seg.count('●'), seg.count('○'))
