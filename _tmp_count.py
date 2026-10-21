# -*- coding: utf-8 -*-
import re, io, sys
sys.stdout.reconfigure(encoding="utf-8")
html = io.open("isa-59.html", encoding="utf-8").read()

def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))

def st(t):
    t = re.sub(r"<script\b.*?</script>", "", t, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", "", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&nbsp;", " ").replace("&amp;", "&")

print("TOTAL CJK:", cjk(st(html)))
secs = re.findall(r'<section id="([^"]+)"[^>]*>(.*?)</section>', html, re.S)
for sid, body in secs:
    print("  ", sid, cjk(st(body)))
segs = re.findall(r'<article class="seg">(.*?)</article>', html, re.S)
print("SEGS:", len(segs))
for i, s in enumerate(segs, 1):
    b = re.search(r'<div class="body">(.*?)</div>', s, re.S)
    print("  seg", i, "body", cjk(st(b.group(1))) if b else 0,
          "notes", len(re.findall(r'<div class="note', s)),
          "kw", len(re.findall(r'<span>', re.search(r'<div class="kw">(.*?)</div>', s, re.S).group(1))))
print("KV:", len(re.findall(r'<div class="kv">', html)))
print("TASKS:", len(re.findall(r'type="checkbox"', html)), "GROUPS:", len(re.findall(r'class="taskgroup"', html)))
print("NOTES:", len(re.findall(r'<div class="note', html)))
print("DETAILS:", len(re.findall(r"<details", html)))
print("BGCELL:", len(re.findall(r'<div class="bg-cell">', html)))
print("EXCLAM:", html.count("!") + html.count("！"))
# forbidden
for w in ["神今天对你说", "主要你", "神绝不会让你", "只要相信就一定会", "家人们", "宝子们", "绝绝子", "不得不说", "说实话", "TODO", "待补充", "Lorem", "XXX", "{{", "}}", "??"]:
    if w in html:
        print("FORBIDDEN HIT:", w)
