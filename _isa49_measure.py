# -*- coding: utf-8 -*-
import re, io, sys, os

path = sys.argv[1]
h = io.open(path, encoding="utf-8").read()
SECTIONS = ["before", "bg", "overview", "map", "reading", "key", "theology", "prayer", "apply", "tasks", "review", "refs"]


def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def strip(t):
    t = re.sub(r"<script\b.*?</script>", "", t, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", "", t)


out = ["file=%s bytes=%d" % (path, os.path.getsize(path))]
for s in SECTIONS:
    m = re.search(r'<section id="' + s + r'"[^>]*>(.*?)</section>', h, re.S)
    out.append("%-10s %d" % (s, cjk(strip(m.group(1)))))
segs = re.findall(r'<article class="seg">(.*?)</article>', h, re.S)
out.append("segs=%d" % len(segs))
for i, sg in enumerate(segs, 1):
    b = re.search(r'<div class="body">(.*?)</div>', sg, re.S).group(1)
    sc = re.search(r'<div class="scripture">(.*?)</div>', sg, re.S).group(1)
    out.append("  SEG%02d body %d scripture %d" % (i, cjk(strip(b)), cjk(strip(sc))))
out.append("kv=%d cb=%d tg=%d details=%d notes=%d" % (
    len(re.findall(r'<div class="kv">', h)),
    len(re.findall(r'type="checkbox"', h)),
    len(re.findall(r'class="taskgroup"', h)),
    len(re.findall(r"<details", h)),
    len(re.findall(r'<div class="note', h))))
out.append("TOTAL %d" % cjk(strip(h)))
io.open("_isa49_counts.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out).encode("ascii", "replace").decode("ascii"))
