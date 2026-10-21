# -*- coding: utf-8 -*-
"""gen-18 自检：字数预算、段落标题、关键词、步骤、引文逐字、感叹号、分歧覆盖。"""
import re, io, json, sys
sys.stdout.reconfigure(encoding='utf-8')

h = io.open('gen-18.html', encoding='utf-8').read()
d = json.load(io.open('verses/gen-18.json', encoding='utf-8'))
full = ''.join(v['text'] for v in d['verses'])


def cjk(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))


def strip_tags(t):
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S | re.I)
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', '', t)
    return t.replace('&nbsp;', ' ').replace('&amp;', '&')


def norm(t):
    return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', t)


def sec(sid):
    return re.search(r'<section id="%s".*?</section>' % sid, h, re.S).group(0)


print('=== 全章字数 ===', cjk(strip_tags(h)))
for sid in ['before', 'bg', 'overview', 'map', 'reading', 'key',
            'theology', 'prayer', 'apply', 'tasks', 'review', 'refs']:
    print('  %-9s %5d' % (sid, cjk(strip_tags(sec(sid)))))

print('\n=== bg 五格 ===')
for m in re.finditer(r'<div class="bg-cell"><h4>(.*?)</h4>.*?<div class="body">(.*?)</div></div>', sec('bg'), re.S):
    print('  %-6s %4d 字' % (m.group(1), cjk(strip_tags(m.group(2)))))

print('\n=== reading 分段 ===')
reading = sec('reading')
for i, s in enumerate(re.findall(r'<article class="seg">(.*?)</article>', reading, re.S), 1):
    title = re.search(r'<h3>(.*?)</h3>', s).group(1)
    body = re.search(r'<div class="body">(.*?)</div>\s*(?:<div class="note|<div class="note)', s, re.S)
    body = re.search(r'<div class="body">(.*?)</div>', s, re.S).group(1)
    kw = re.findall(r'<span>(.*?)<i>', s)
    refs = re.search(r'<span class="seg-ref">(.*?)</span>', s).group(1)
    nw = len(re.findall(r'<div class="note note--warn"', s))
    nc = len(re.findall(r'<div class="note note--christ"', s))
    print('  SEG%02d [%s] 标题%d字 正文%d字 kw%d warn%d christ%d %s'
          % (i, refs, len(title), cjk(strip_tags(body)), len(kw), nw, nc, title))

print('\n=== key 四步 ===')
for i, kv in enumerate(re.findall(r'<div class="kv">(.*?)</ol>', sec('key'), re.S), 1):
    ref = re.search(r'<div class="kv-ref">(.*?)</div>', kv).group(1)
    bq = re.search(r'<blockquote>(.*?)</blockquote>', kv, re.S).group(1)
    steps = re.findall(r'<li><b>(.*?)</b><span>(.*?)</span></li>', kv, re.S)
    ok = norm(bq) in norm(full)
    print('  KV%d %s 逐字=%s 步骤=%s' % (i, ref, ok, [cjk(s) for _, s in steps]))

print('\n=== 引文纪律：正文所有「…」片段是否出自本章经文 ===')
body_txt = re.sub(r'<section id="refs".*?</section>', '', h, flags=re.S)
body_txt = re.sub(r'<div class="scripture">.*?</div>', '', body_txt, flags=re.S)
body_txt = re.sub(r'<blockquote>.*?</blockquote>', '', body_txt, flags=re.S)
nf = norm(full)
bad = []
for q in re.findall(r'「([^」]{2,})」', body_txt):
    if norm(q) not in nf:
        bad.append(q)
print('  非本章经文的引号片段 %d 个：' % len(bad))
for b in bad:
    print('    -', b)

print('\n=== 感叹号 ===', h.count('！'), '个')

print('\n=== 释经分歧 note（🟨） ===')
warns = re.findall(r'<span class="tag">🟨 ([^<]*)</span>', h)
for w in warns:
    print('  ·', w)
print('  共', len(warns), '条')

print('\n=== 其他 ===')
print('  seg 数', len(re.findall(r'<article class="seg">', reading)))
print('  kv 数', len(re.findall(r'<div class="kv">', sec('key'))))
print('  taskgroup', len(re.findall(r'class="taskgroup"', sec('tasks'))),
      ' checkbox', len(re.findall(r'type="checkbox"', sec('tasks'))))
print('  details', len(re.findall(r'<details', sec('review'))))
print('  bg-cell', len(re.findall(r'<div class="bg-cell">', sec('bg'))))
print('  tbl rows in refs', len(re.findall(r'<tr>', re.search(r'<table class="tbl">(.*?)</table>', sec('refs'), re.S).group(1))) - 1)
print('  meta spans', len(re.findall(r'<span>', re.search(r'<div class="meta">(.*?)</div>', h, re.S).group(1))))
print('  pills', len(re.findall(r'class="pill"', sec('map'))), ' branches', len(re.findall(r'<li><b>', sec('map'))))
print('  下一章预告标题:', re.search(r'<h3>下一章预告[^<]*</h3>', h).group(0))
print('  people-grid:', re.search(r'<div[^>]*id="chapterPeople"[^>]*>', h).group(0))
