# -*- coding: utf-8 -*-
import io, json, os, re, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import chapter_file
ROOT = r"D:\圣经笔记\skill"


def norm(t):
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", t)


cid = sys.argv[1]
h = io.open(chapter_file(cid), encoding="utf-8").read()
d = json.load(io.open(os.path.join(ROOT, "verses", "%s.json" % cid), encoding="utf-8"))
remote = {v["n"]: v["text"] for v in d["verses"]}
blocks = re.findall(r'<div class="scripture">(.*?)</div>', h, re.S)
seen = {}
for bi, b in enumerate(blocks):
    for m in re.finditer(r"<sup>(\d+)</sup>(.*?)(?=<sup>|$)", b, re.S):
        seen.setdefault(int(m.group(1)), []).append((bi, norm(re.sub(r"<[^>]+>", "", m.group(2)))))
for n in sorted(remote):
    if n not in seen:
        print("第 %d 节 缺" % n)
        continue
    for bi, txt in seen[n]:
        if txt != norm(remote[n]):
            print("第 %d 节（block %d）不一致" % (n, bi))
            print("   文件:", txt[:90])
            print("   经文:", norm(remote[n])[:90])
            for i, (a, b2) in enumerate(zip(txt, norm(remote[n]))):
                if a != b2:
                    print("   首个差异 @%d: 文件…%s… | 经文…%s…" % (i, txt[max(0, i-14):i+14], norm(remote[n])[max(0, i-14):i+14]))
                    break
            else:
                print("   长度不同 %d vs %d" % (len(txt), len(norm(remote[n]))))
