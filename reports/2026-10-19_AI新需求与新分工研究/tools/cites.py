#!/usr/bin/env python3
"""列出草稿中引用的来源编号及其台账内容；标出缺失编号。用法：python3 cites.py <草稿.md> [--brief]"""
import json,glob,re,sys,os
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src={}
for f in glob.glob(f'{base}/sources/*.jsonl'):
    for l in open(f,encoding='utf-8'):
        if l.strip():
            r=json.loads(l); src[r['id'].strip()]=r
txt=open(sys.argv[1],encoding='utf-8').read()
ids=sorted(set(re.findall(r'A\d\d-S\d{3}',txt)))
miss=[i for i in ids if i not in src]
print('引用编号数',len(ids),'缺失',miss)
if '--brief' not in sys.argv:
    for i in ids:
        if i in src: print(i,'|',src[i]['key_content'][:120])
