# -*- coding: utf-8 -*-
import json, io, os, re

def show(book, ch, ns=None):
    p = os.path.join("verses", "%s-%02d.json" % (book, ch))
    if not os.path.exists(p):
        print("MISSING", p); return
    d = json.load(io.open(p, encoding="utf-8"))
    for v in d["verses"]:
        if ns is None or v["n"] in ns:
            print("%s-%02d:%d %s" % (book, ch, v["n"], v["text"]))

show("psa", 46, [9, 10, 11])
print("---")
show("rev", 19, [11, 12, 13, 14, 15, 16, 19, 20])
print("---")
show("rev", 20, [10])
print("---")
show("exo", 2, [10])
print("---")
show("exo", 7, [15, 18, 19, 20, 21])
print("---")
show("jhn", 14, [6])
print("---")
show("mat", 11, [28, 29])
print("---")
show("heb", 4, [3, 10, 11])
print("---")
show("mat", 21, [42, 43, 44])
print("---")
show("1pe", 2, [4, 5, 6])
print("---")
show("rom", 9, [21])
print("---")
show("jhn", 15, [4, 5])
print("---")
show("psa", 121, [5])
print("---")
show("jhn", 1, [14, 17, 39])
print("---")
show("isa", 40, [21])
print("---")
show("jer", 31, [34])
print("---")
show("psa", 46, [10])
