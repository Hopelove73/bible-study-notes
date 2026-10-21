# -*- coding: utf-8 -*-
import re, io, sys

path = sys.argv[1]
h = io.open(path, encoding="utf-8").read()


def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def strip(t):
    t = re.sub(r"<script\b.*?</script>", "", t, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", "", t)


reading = re.search(r'<section id="reading"[^>]*>(.*?)</section>', h, re.S).group(1)
segs = re.findall(r'<article class="seg">(.*?)</article>', reading, re.S)
tot_s = tot_k = tot_b = tot_n = 0
for i, sg in enumerate(segs, 1):
    s = cjk(strip(re.search(r'<div class="scripture">(.*?)</div>', sg, re.S).group(1)))
    k = cjk(strip(re.search(r'<div class="kw">(.*?)</div>', sg, re.S).group(1)))
    b = cjk(strip(re.search(r'<div class="body">(.*?)</div>', sg, re.S).group(1)))
    ns = re.findall(r'<div class="note[^"]*">(.*?)</div>', sg, re.S)
    n = sum(cjk(strip(x)) for x in ns)
    tot_s += s; tot_k += k; tot_b += b; tot_n += n
    print("SEG%02d script=%d kw=%d body=%d notes=%d (n=%d)" % (i, s, k, b, n, len(ns)))
print("reading totals: scripture=%d kw=%d body=%d notes=%d" % (tot_s, tot_k, tot_b, tot_n))
notes = re.findall(r'<div class="note([^"]*)">(.*?)</div>', h, re.S)
print("all notes=%d total chars=%d" % (len(notes), sum(cjk(strip(x[1])) for x in notes)))
for c, inner in notes:
    print("   %-18s %d" % (c.strip(), cjk(strip(inner))))
