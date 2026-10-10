# -*- coding: utf-8 -*-
"""Parser for the 2022 edition of 국방기술기획서(일반본). Reads the extracted text in data/source and writes an intermediate JSON to data/intermediate."""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,'data','source','2022_22-36_국방기술기획서_일반본.txt')
OUT=os.path.join(ROOT,'data','intermediate','parse_2022.json')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
import re, json
from collections import Counter
c=open(SRC, encoding='utf-8').read()
c=re.sub('[ㆍ‧･∙]','·',c)
L=[l.strip() for l in c.split('\n')]
FIELDS=['자율·인공지능 기반 감시정찰 분야','초연결 지능형 지휘통제 분야','초고속·고위력 정밀타격 분야','미래형 추진 및 스텔스 기반 플랫폼 분야','유·무인 복합 전투수행 분야','첨단기술 기반 개인전투체계 분야','사이버 능동대응 및 미래형 방호 분야','미래형 첨단 신기술 분야']
ST='기초|응용|시험|응용/시험|패키지형|선도형|핵심SW|선행핵심|국제공동|미래도전|특화실|특화센터|민군'
REF=re.compile(r'^(\d{3})\s+(.+?)\(('+ST+r')[^,()]*,\s*(\d{2})\s*[-~∼]\s*(\d{2})\)\s*$')
def norm(x): return re.sub(r'\s+',' ',x).strip()
s=next(i for i,l in enumerate(L) if l.startswith('<<P29>>'))
field=None; stech=None; mode=None; techs=[]; ktechs=[]; projs=[]
i=s; cur=None
while i<len(L):
    l=L[i]
    if l.startswith('<<P') or re.match(r'^394-\d+$',l) or l=='공 란': i+=1; continue
    if re.match(r'^제 \d+절$',l) and i+1<len(L) and L[i+1] in FIELDS: field=L[i+1]; mode=None; stech=None; cur=None; i+=2; continue
    if l.startswith('제3장') or l.startswith('제 3장'): break
    if l.startswith('라 국방전략기술별 핵심기술 목록'): mode='list'; i+=1; continue
    if mode!='list': i+=1; continue
    m=re.match(r'^(\d{1,2})\\\. (.+)$',l)
    if m:
        rest=norm(m.group(2))
        prev=[t for t in techs if t['field']==field and rest.replace(' ','')==t['name'].replace(' ','')]
        if prev: stech=prev[0]['name']; i+=1; continue
        # new tech: desc until '핵심기술/핵심기술과제'
        d=[]; j=i+1
        while j<len(L) and not L[j].startswith('핵심기술/핵심기술과제') and not L[j].startswith('<<P'): d.append(L[j]); j+=1
        stech=rest; techs.append({'field':field,'name':stech,'desc':norm(' '.join(d)),'order':int(m.group(1))}); cur=None; i=j; continue
    if l.startswith('핵심기술/핵심기술과제'): i+=1; continue
    # project ref lines
    rl=l
    if rl.startswith('(반영과제)'): rl=rl[len('(반영과제)'):].strip()
    mm=REF.match(rl)
    if not mm and re.match(r'^\d{3}\s',rl):
        # wrapped ref: join next line
        if i+1<len(L): mm=REF.match(rl+' '+L[i+1])
        if mm: i+=1
    if mm:
        projs.append({'field':field,'stech':stech,'ktech':cur['name'] if cur else None,'id':int(mm.group(1)),'name':norm(mm.group(2)),'stage':mm.group(3),'period':"'%s-'%s"%(mm.group(4),mm.group(5))})
        i+=1; continue
    if l.startswith('(반영과제)'): i+=1; continue
    # otherwise: a ktech name line (short, no trailing period) followed by desc lines.
    # Heuristic: ktech name lines are <= 45 chars and don't end with '기술로써' etc; desc lines are longer.
    prevl=L[i-1] if i>0 else ''
    prev_full=len(prevl)>=55
    if cur is None or (not cur.get('desc')) and False:
        pass
    nextl=L[i+1] if i+1<len(L) else ''
    if cur is None or (cur.get('desc') and len(l)<=45 and not l.endswith(('.', ',')) and (not prev_full or len(nextl)>=55)):
        cur={'field':field,'stech':stech,'name':l,'desc':''}; ktechs.append(cur)
    else:
        cur['desc']=norm(cur['desc']+' '+l)
    i+=1
print('techs',len(techs),'ktechs',len(ktechs),'projs',len(projs))
print(Counter(t['field'] for t in techs)); print(Counter(k['field'] for k in ktechs)); print(Counter(p['stage'] for p in projs))
uniq={}
for p in projs: uniq.setdefault(p['id'],p)
print('unique ids',len(uniq))
json.dump({'techs':techs,'ktechs':ktechs,'projs':projs},open(OUT,'w', encoding='utf-8'),ensure_ascii=False,indent=1)
print([k['name'] for k in ktechs[:12]])
print([(t['field'],t['name']) for t in techs][:12])
