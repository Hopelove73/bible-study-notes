# -*- coding: utf-8 -*-
import json, io, re

html = io.open('isa-54.html', encoding='utf-8').read()
verses = json.load(io.open('verses/isa-54.json', encoding='utf-8'))
V = {v['n']: v['text'] for v in verses['verses']}

def fix(m):
    n = int(m.group(1))
    return '<p><sup>%d</sup>%s</p>' % (n, V[n])

html, cnt = re.subn(r'<p><sup>\s*(\d+)\s*</sup>.*?</p>', fix, html, flags=re.S)
io.open('isa-54.html','w',encoding='utf-8',newline='\n').write(html)
print('verses fixed:', cnt)
