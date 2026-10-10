# -*- coding: utf-8 -*-
"""Parser for the 2023 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2023_23-37_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2023.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json
from collections import Counter
c=open(SRC, encoding='utf-8').read()
c=re.sub(r'\n\s*\n','\n',c); c=re.sub('[ㆍ‧･∙]','·',c)
L=[l.strip() for l in c.split('\n')]
FIELDS=['인공지능','유·무인 복합','양자','우주','에너지','첨단소재','사이버·네트워크','센서·전자기전','추진','WMD 대응']
ST='기초|응용|시험|응용/시험|패키지형|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터|민군'
REF=re.compile(r'(\d{3})\s+(.+?)\((?:'+ST+r')[^,()]*,\s*(\d{2})\s*[-~∼]\s*(\d{2})\)')
REF2=re.compile(r'(\d{3})\s+(.+?)\(('+ST+r')[^,()]*,\s*(\d{2})\s*[-~∼]\s*(\d{2})\)')
STATUS=re.compile(r'\((진행과제|예정과제|종료과제|반영과제)\)')
s=next(i for i,l in enumerate(L) if l=='제2 절 인공지능')
field=None; stech=None; mode=None; techs=[]; projs=[]; ktechs=[]
def norm(x): return re.sub(r'\s+',' ',x).strip()
status=None; ktech=None
i=s
while i<len(L):
    l=L[i]
    m=re.match(r'^제(\d+) 절 (.+)$',l)
    if m and m.group(2) in FIELDS: field=m.group(2); mode=None; i+=1; continue
    if l.startswith('제1 절 추진 현황'): break
    m=re.match(r'^(\d{1,2})\\\. (.+)$',l)
    if m and field:
        rest=m.group(2)
        prev=[t for t in techs if t['field']==field and rest.replace(' ','').startswith(t['name'].replace(' ',''))]
        if prev: stech=prev[0]['name']; 
        else:
            stech=norm(rest); d=[]; j=i+1
            while j<len(L) and L[j] and not re.match(r'^(\d{1,2}\\\. |∙|다 |02|라 |국방기술/)',L[j]) and not re.match(r'^335-\d+$',L[j]): d.append(L[j]); j+=1
            techs.append({'field':field,'name':stech,'desc':norm(' '.join(d)),'order':int(m.group(1))}); i=j
            continue
        # list-mode header line may contain first ktech after tech desc; handle rest of line
        l=rest
        if not mode=='list': i+=1; continue
    if l.startswith('라 국방전략기술별'): mode='list'; ktech=None; i+=1; continue
    if mode=='list' and not re.match(r'^335-\d+$',l):
        # split line by status markers and refs
        text=l
        # merge continuation lines: a ref may wrap to the next line
        pos=0
        parts=STATUS.split(text)
        # parts: [pre, status, after, status, after...]
        pre=parts[0]
        def handle_refs(seg, st):
            global ktech
            last=0
            for mm in REF2.finditer(seg):
                projs.append({'field':field,'stech':stech,'ktech':ktech,'status':st,'id':int(mm.group(1)),'name':norm(mm.group(2)),'stage':mm.group(3),'period':"'%s-'%s"%(mm.group(4),mm.group(5))})
                last=mm.end()
            return seg[last:].strip()
        if pre.strip():
            tail=handle_refs(pre.strip(), status) if status else pre.strip()
            if tail and not status:
                ktechs.append({'field':field,'stech':stech,'line':tail})
            elif tail:
                ktechs.append({'field':field,'stech':stech,'line':tail}); status=None; ktech=tail
        for k in range(1,len(parts),2):
            status=parts[k]; seg=parts[k+1].strip()
            tail=handle_refs(seg,status)
            if tail:
                ktechs.append({'field':field,'stech':stech,'line':tail}); status=None; ktech=tail
    i+=1
print('techs',len(techs),'projs',len(projs),'ktech lines',len(ktechs))
print(Counter(p['field'] for p in projs)); print(Counter(p['status'] for p in projs)); print(Counter(p['stage'] for p in projs))
# unique projects by id
uniq={}
for p in projs: uniq.setdefault(p['id'],p)
print('unique ids',len(uniq))
json.dump({'techs':techs,'projs':projs,'ktechs':ktechs},open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
print([ (t['field'],t['name']) for t in techs])
print(projs[:2])
