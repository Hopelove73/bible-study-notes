# -*- coding: utf-8 -*-
"""修正人物表：改 id、调星级。直接改 assets/people.js。

用法：py scripts\\fix_people.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEOPLE = os.path.join(ROOT, "assets", "people.js")

try:
    sys_stdout = True
except Exception:
    pass

# 改 id
RENAME = {
    "jacob-to-egypt-isa65": "jacob-to-egypt-exo01",
    "joseph-egypt-isa65": "joseph-exo01",
    "moses-isa65": "moses-exo02",
    "levi-family-isa65": "levi-family-exo02",
    "pharaoh-isa65": "pharaoh-exo02",
}

# 降星：每章只留 3 位 ★★★
DEMOTE = {"moses-isa63", "zion-isa64", "blessed-offspring-isa65"}

# 删除：合并时误建的重复条目
DELETE = {"zion-purified-isa04", "zion-daughters-isa04"}


def main():
    raw = io.open(PEOPLE, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    people = json.loads(raw[i:j + 1])
    head, tail = raw[:i], raw[j + 1:]

    changed = []
    kept = []
    for p in people:
        if p["id"] in DELETE:
            changed.append("删除重复条目: %s (%s)" % (p["id"], p.get("name")))
            continue
        kept.append(p)
    people = kept
    for p in people:
        if p["id"] in RENAME:
            old = p["id"]
            p["id"] = RENAME[old]
            changed.append("改 id: %s -> %s" % (old, p["id"]))
        if p["id"] in DEMOTE and p.get("star") == 1:
            p["star"] = 2
            changed.append("降星: %s (%s) -> ★★" % (p["id"], p.get("name")))

    text = json.dumps(people, ensure_ascii=False, indent=2)
    io.open(PEOPLE, "w", encoding="utf-8", newline="\n").write(head + text + tail)
    for c in changed:
        print("  " + c)
    print("共 %d 处修改，总人数 %d" % (len(changed), len(people)))


if __name__ == "__main__":
    main()
