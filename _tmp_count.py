# -*- coding: utf-8 -*-
import re, io
html = io.open('isa-54.html', encoding='utf-8').read()
def strip_tags(t):
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S|re.I)
    t = re.sub(r'<[^>]+>', '', t)
    return t
def cjk(t): return len(re.findall(r'[\u4e00-\u9fff]', t))
for i, m in enumerate(re.finditer(r'<div class="note([^"]*)">(.*?)</div>', html, re.S), 1):
    cls = m.group(1).strip()
    tag = re.search(r'<span class="tag">(.*?)</span>', m.group(2), re.S)
    print('note %02d %-14s %4d  %s' % (i, cls, cjk(strip_tags(m.group(2))), strip_tags(tag.group(1)) if tag else ''))
