# -*- coding: utf-8 -*-
import io, re, os
os.chdir(r'D:\圣经笔记\skill')
def cjk(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))
def st(t):
    return re.sub(r'<[^>]+>', '', t)
h = io.open('isa-45.html', encoding='utf-8').read()
tot = 0
out = []
for i, m in enumerate(re.finditer(r'<div class="note([^"]*)">(.*?)</div>', h, re.S), 1):
    n = cjk(st(m.group(2)))
    tot += n
    tag = re.search(r'<span class="tag">(.*?)</span>', m.group(2), re.S).group(1)
    out.append('%2d %5d  %s' % (i, n, tag))
out.append('notes total %d' % tot)
# bodies
for i, m in enumerate(re.finditer(r'<div class="body">(.*?)</div>', h, re.S), 1):
    out.append('body %d: %d' % (i, cjk(st(m.group(1)))))
io.open('tmp_notes_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
