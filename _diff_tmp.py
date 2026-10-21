# -*- coding: utf-8 -*-
import re, io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
h = io.open('gen-18.html', encoding='utf-8').read()
reading = re.search(r'<section id="reading".*?</section>', h, re.S).group(0)
segs = re.findall(r'<article class="seg">(.*?)</article>', reading, re.S)
vm = {}
for i, s in enumerate(segs, 1):
    for block in re.findall(r'<div class="scripture">(.*?)</div>', s, re.S):
        for m in re.finditer(r'<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)', block, re.S):
            vm[int(m.group(1))] = re.sub(r'<[^>]+>', '', m.group(2)).strip()
d = json.load(io.open('verses/gen-18.json', encoding='utf-8'))
bad = 0
for v in d['verses']:
    a = vm.get(v['n'])
    b = v['text']
    if a != b:
        bad += 1
        print('DIFF verse', v['n'])
        print('  HTML:', repr(a))
        print('  JSON:', repr(b))
print('total diffs:', bad, ' covered:', len(vm))
