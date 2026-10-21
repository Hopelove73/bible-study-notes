# -*- coding: utf-8 -*-
"""给指定章节的某个背景格补写内容（把 <p> 里的文字追加到句末）。

用法：py extend_bg.py <cid> <格名> <要追加的句子>
"""
import io, os, re, sys

ROOT = r"D:\圣经笔记\skill"
cid, cell, extra = sys.argv[1], sys.argv[2], sys.argv[3]
path = os.path.join(ROOT, cid + ".html")
h = io.open(path, encoding="utf-8").read()

m = re.search(r'<div class="bg-cell"><h4>%s</h4><div class="body"><p>(.*?)</p></div></div>' % re.escape(cell), h, re.S)
if not m:
    raise SystemExit("找不到背景格：%s" % cell)
old = m.group(1)
new = old + extra
h = h[:m.start(1)] + new + h[m.end(1):]
io.open(path, "w", encoding="utf-8", newline="\n").write(h)

n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", new)))
print("%s [%s] 现有 %d 字" % (cid, cell, n))
