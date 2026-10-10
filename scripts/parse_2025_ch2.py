# -*- coding: utf-8 -*-
"""Parser for the 2025 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2025_25-39_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2025_ch2.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json
from collections import Counter
c=open(SRC, encoding='utf-8').read()
s=c.find('<<P29>>'); e=c.find('<<P95>>')
L=[l for l in c[s:e].split('\n')]
FIELDS=['인공지능','유·무인 복합','양자','우주','에너지','첨단소재','사이버·네트워크','센서·전자기전','추진','WMD 대응']
STAGES={'기초연구','응용연구','시험개발','응용/시험','패키지형','국방협업','국방선행','선도형','핵심SW','선행핵심','국제공동','미래도전','특화실','특화센터','특화연구실','특화연구센터','민군협력','기초','응용','시험'}
field=None; stech=None; stech_desc=[]; sub=None; mode=None
techs=[]   # strategic techs with desc
subdefs=[] # (field, stech, subname, desc)
projs=[]
cur=None; sublines=[]
i=0
def norm(x): return re.sub(r'\s+',' ',x).strip()
while i<len(L):
    l=L[i].strip()
    if l.startswith('<<P') or re.match(r'^257-\d+$',l) or l in ('','세부기술','과제명','단계','기간','\\-','-'): i+=1; continue
    if re.match(r'^제 \d+절$',l):
        nxt=L[i+1].strip()
        if nxt in FIELDS: field=nxt; mode=None; i+=2; continue
    m=re.match(r'^(\d{1,2})\\\. (.+)$',l)
    if m and field:
        stech=norm(m.group(2)); 
        # description = following lines until ◯ or 세부기술 header
        j=i+1; d=[]
        while j<len(L) and not re.match(r'^(◯\d+|세부기술|<<P|\d{1,2}\\\. )',L[j].strip()) and L[j].strip()!='':
            d.append(L[j].strip()); j+=1
        desc=norm(' '.join(d))
        if mode!='list':
            techs.append({'field':field,'name':stech,'desc':desc,'order':int(m.group(1))})
        if cur: projs.append(cur); cur=None
        sublines=[]
        i=j; continue
    if l.startswith('라 국방전략기술별 국방기술'):
        mode='list'; i+=1; continue
    if mode!='list':
        m=re.match(r'^◯(\d+)\s*(.+)$',l)
        if m:
            j=i+1; d=[]
            while j<len(L) and not re.match(r'^(◯\d+|<<P|\d{1,2}\\\. |다 |02|01)',L[j].strip()) and L[j].strip()!='' and not re.match(r'^257-\d+$',L[j].strip()):
                d.append(L[j].strip()); j+=1
            subdefs.append({'field':field,'stech':stech,'name':norm(m.group(2)),'desc':norm(' '.join(d)),'order':int(m.group(1))})
            i=j; continue
        i+=1; continue
    # list mode
    m=re.match(r'^(\d{3})(?:\s+(.+))?$',l)
    if not m and (cur is None or cur['period'] is not None):
        m2=re.match(r'^(.+?)\s+(\d{3})\s+(.+)$',l)
        if m2 and not re.search(r'\d',m2.group(1)):
            sublines.append(m2.group(1)); m=re.match(r'^(\d{3})(?:\s+(.+))?$',m2.group(2)+' '+m2.group(3))
    if m:
        if cur: projs.append(cur)
        if sublines: sub=norm(' '.join(sublines)); sublines=[]
        cur={'field':field,'stech':stech,'sub':sub,'id':int(m.group(1)),'name':[],'stage':None,'period':None}
        if m.group(2):
            mm=re.match(r'^(.*\S)\s+(기초연구|응용연구|시험개발|응용/시험|패키지형|국방협업|국방선행|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터)$',m.group(2))
            if mm: cur['name'].append(mm.group(1)); cur['stage']=mm.group(2)
            else: cur['name'].append(m.group(2))
        i+=1; continue
    if cur and cur['period'] is None:
        if re.match(r"^'\d\d-'\d\d$",l) or re.match(r"^’\d\d-’\d\d$",l):
            cur['period']=l.replace('’',"'"); i+=1; continue
        if l in STAGES and cur['stage'] is None:
            cur['stage']=l; i+=1; continue
        if cur['stage'] is None:
            mm=re.match(r'^(.*\S)\s+(기초연구|응용연구|시험개발|응용/시험|패키지형|국방협업|국방선행|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터)$',l)
            if mm: cur['name'].append(mm.group(1)); cur['stage']=mm.group(2)
            else: cur['name'].append(l)
            i+=1; continue
    # otherwise it's 세부기술 name lines
    if l.startswith('02') or l.startswith('01') or l.startswith('/ ') or l.startswith('가 ') or l.startswith('나 ') or l.startswith('다 ') or l.startswith('라 '):
        i+=1; continue
    sublines.append(l); i+=1
if cur: projs.append(cur)
for p in projs: p['name']=norm(' '.join(p['name']))
print('techs',len(techs),'subdefs',len(subdefs),'projs',len(projs))
print(Counter(p['field'] for p in projs))
bad=[p for p in projs if not p['stage'] or not p['period'] or not p['sub']]
print('bad',len(bad)); 
for b in bad[:10]: print(b)
print(Counter(p['stage'] for p in projs))
json.dump({'techs':techs,'subdefs':subdefs,'projs':projs},open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
for p in projs[:3]: print(p)
subs=Counter((p['field'],p['stech'],p['sub']) for p in projs); print(len(subs))
