# -*- coding: utf-8 -*-
import json, io, os
ROOT = r"D:\圣经笔记\skill"
want = {
    "mat-15": [8, 9],
    "jer-18": [4],
    "rom-09": [20, 21],
    "ezk-13": [22],
    "ezk-36": [26],
    "isa-45": [11],
    "gal-02": [11, 12, 13, 14],
    "act-28": [27],
    "isa-41": [14],
    "isa-01": [17],
    "1pe-02": [6],
    "isa-28": [16, 17],
    "isa-30": [14, 15, 18],
    "luk-04": [17, 18, 19, 20, 21],
    "mat-12": [22, 23],
    "heb-12": [2],
    "2cor-05": [21],
}
for k, ns in want.items():
    p = os.path.join(ROOT, "verses", k + ".json")
    if not os.path.exists(p):
        print(k, "MISSING FILE")
        continue
    d = json.load(io.open(p, encoding="utf-8"))
    for v in d["verses"]:
        if v["n"] in ns:
            print(k, v["n"], v["text"])
