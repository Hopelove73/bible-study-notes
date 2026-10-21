import re, json, glob, os
html = open(r"isa-18.html", encoding="utf-8").read()
corpus = {}
for f in glob.glob("verses/*.json"):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        continue
    txt = json.dumps(d, ensure_ascii=False)
    corpus[f] = txt
alltxt = "\n".join(corpus.values())
quotes = re.findall(r"「([^「」]{4,})」", html)
seen=set()
for q in quotes:
    if q in seen: continue
    seen.add(q)
    if q in alltxt:
        hits = [f for f,t in corpus.items() if q in t]
        print("OK  ", q, "->", ",".join(sorted(hits)))
    else:
        print("MISS", q)
