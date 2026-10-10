# -*- coding: utf-8 -*-
"""Parser for the 2024 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2024_24-38_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2024.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json
from collections import Counter
c=open(SRC, encoding='utf-8').read()
c=re.sub(r'\n\s*\n','\n',c)
c=re.sub('[ㆍ‧･∙]','·',c)
L=[l.strip() for l in c.split('\n')]
FIELDS=['인공지능','유·무인 복합','양자','우주','에너지','첨단소재','사이버·네트워크','센서·전자기전','추진','WMD 대응']
ST='기초연구|응용연구|시험개발|응용/시험|패키지형|국방협업|국방선행|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터'
PR=re.compile(r"(\d{3})\s+((?:(?!\s\d{3}\s).)+?)\s+("+ST+r")\s+'(\d\d)-'(\d\d)")
# chapter 2 region
s=next(i for i,l in enumerate(L) if l=='제2 절 인공지능'); e=next(i for i,l in enumerate(L) if l=='제1 절 추진 현황')
field=None; stech=None; mode=None; sub=None; projs=[]; techs=[]; subdefs=[]
def norm(x): return re.sub(r'\s+',' ',x).strip()
i=s
pending=[]  # lines possibly belonging to project name split across lines
while i<e:
    l=L[i]
    m=re.match(r'^제(\d+) 절 (.+)$',l)
    if m and m.group(2) in FIELDS: field=m.group(2); mode=None; i+=1; continue
    m=re.match(r'^(\d{1,2})\\\. (.+)$',l)
    if m and field:
        rest=m.group(2); n=int(m.group(1))
        prev=[t for t in techs if t['field']==field and (rest.startswith(t['name']) or rest.replace(' ','').startswith(t['name'].replace(' ','')))]
        if prev:
            stech=prev[0]['name']; sub=None; pending=[]; i+=1; continue
        stech=norm(rest); d=[]; j=i+1
        while j<e and L[j] and not re.match(r'^(\d{1,2}\\\. |∙|다 |02|라 |세부기술)',L[j]) and not re.match(r'^247-\d+$',L[j]): d.append(L[j]); j+=1
        techs.append({'field':field,'name':stech,'desc':norm(' '.join(d)),'order':n}); i=j; continue
    if l.startswith('라 국방전략기술별 국방기술'): mode='list'; i+=1; continue
    if mode=='list':
        if re.match(r'^247-\d+$',l) or l.startswith('세부기술 과제명'): i+=1; continue
        # a line may contain: [subname] ID name stage period [ID name stage period]...
        text=l
        # handle project name wrapped to next line: if line has ID but no stage/period, merge with next lines
        if re.match(r'^(.*?\s)?\d{3}\s',text) and not PR.search(text):
            j=i+1
            while j<e and not PR.search(text) and j<i+4: text=text+' '+L[j]; j+=1
            if PR.search(text): i=j-1
        ms=list(PR.finditer(text))
        if ms:
            pre=text[:ms[0].start()].strip()
            if pre or pending: sub=norm(' '.join(pending+([pre] if pre else []))); pending=[]
            for mm in ms:
                projs.append({'field':field,'stech':stech,'sub':sub,'id':int(mm.group(1)),'name':norm(mm.group(2)),'stage':mm.group(3),'period':"'%s-'%s"%(mm.group(4),mm.group(5))})
            tail=text[ms[-1].end():].strip()
            if tail and not re.match(r'^\d{1,2}\\\.',tail): pending=[tail]
            else: pending=[]
        else:
            if l in ('- - -','\\- - -'): pending=[]
            elif l.startswith('세부기술'): pass
            else: pending.append(l)
    i+=1
seen={}
for t in techs:
    k=(t['field'],t['name'])
    if k not in seen or len(t['desc'])>len(seen[k]['desc']): seen[k]=t
techs=list(seen.values())
print('techs',len(techs),'projs',len(projs))
print(Counter(p['field'] for p in projs))
print(Counter(p['stage'] for p in projs))
print([p for p in projs if p['field']=='인공지능'][:3])
print(sorted({str(p['sub']) for p in projs if p['field']=='인공지능'}))
# chapter 3 기초연구 list
s3=next(i for i,l in enumerate(L) if l.startswith('02/ 과제 목록 (개별기초'))
basic=[]; sub3=None
for l in L[s3:]:
    if l in ('개별기초','특화연구실','특화연구센터'): sub3=l; continue
    m=re.match(r'^(\d{1,2})\s+(.+?)\s+(20\d\d)\s+(20\d\d)\s+(산학연|국과연|정출연|미정)\s+([\d.]+)$',l)
    if m: basic.append({'id':int(m.group(1)),'name':norm(m.group(2)),'start':int(m.group(3)),'end':int(m.group(4)),'lead':m.group(5),'budget':float(m.group(6)),'type':'기초연구','subtype':sub3})
print('basic',len(basic), basic[0], basic[-1])
json.dump({'techs':techs,'projs':projs,'basic':basic},open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
