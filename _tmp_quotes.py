# -*- coding: utf-8 -*-
"""人工复核：把全文所有「」引文逐条拿去和合本经文库里找，找不到就列出来人工判断。"""
import re, io, os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.abspath(__file__))
html = io.open(os.path.join(ROOT, "isa-59.html"), encoding="utf-8").read()
body = re.sub(r'<section id="refs".*?</section>', "", html, flags=re.S)

BOOKS = {}
for fn in os.listdir(os.path.join(ROOT, "verses")):
    if not fn.endswith(".json"):
        continue
    bid = fn[:-5]
    try:
        d = json.load(io.open(os.path.join(ROOT, "verses", fn), encoding="utf-8"))
    except Exception:
        continue
    BOOKS[bid] = "".join(v["text"] for v in d["verses"])

def norm(t):
    t = re.sub(r"[〔〕]", "", t)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", t)

NORM_ALL = {k: norm(v) for k, v in BOOKS.items()}

quotes = re.findall(r"「([^」]{2,120})」", body)
print("共 %d 处引文" % len(quotes))
seen = set()
for q in quotes:
    if q in seen:
        continue
    seen.add(q)
    nq = norm(q)
    frags = [f for f in re.split(r"…+", q) if len(norm(f)) >= 3]
    hits = []
    for bid, nall in NORM_ALL.items():
        if nq and nq in nall:
            hits.append(bid)
        elif frags and all(norm(f) in nall for f in frags):
            hits.append(bid)
    if not hits:
        print("  [未匹配] 「%s」" % q)
    else:
        print("  [OK %s] 「%s」" % (",".join(sorted(hits)[:4]), q))
