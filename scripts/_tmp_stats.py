# -*- coding: utf-8 -*-
import re, io
h = io.open('isa-33.html', encoding='utf-8').read()
cjk = lambda t: len(re.findall(r'[\u4e00-\u9fff]', t))
strip = lambda t: re.sub(r'<[^>]+>', '', t)
secs = ['before','bg','overview','map','reading','key','theology','prayer','apply','tasks','review','refs']
chunks = re.split(r'<section id="', h)
tot = 0
for p in chunks[1:]:
    sid = p.split('"')[0]
    n = cjk(strip(p))
    tot += n
    print(sid, n)
print('sections total', tot)
hero = h.split('<div class="hero">')[1].split('<div class="layout">')[0]
print('hero', cjk(strip(hero)))
print('footer/toc rest', cjk(strip(h)) - tot - cjk(strip(hero)))
print('--- seg bodies ---')
for i, m in enumerate(re.findall(r'<div class="body">(.*?)</div>', h, re.S), 1):
    print('body', i, cjk(strip(m)))
print('--- bg cells ---')
for i, m in enumerate(re.findall(r'<div class="bg-cell">(.*?)</div></div>', h, re.S), 1):
    print('bg', i, cjk(strip(m)))
print('--- kv ---')
for i, m in enumerate(re.findall(r'<div class="kv">(.*?)</ol>', h, re.S), 1):
    print('kv', i, cjk(strip(m)))
print('--- notes ---')
for i, m in enumerate(re.findall(r'<div class="note[^"]*">(.*?)</div>', h, re.S), 1):
    print('note', i, cjk(strip(m)))
