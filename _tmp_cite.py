# -*- coding: utf-8 -*-
"""复刻 qa_check 的 CITE 检测，列出「无法核对」的引文。"""
import re, io, os, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import qa_check as q

ROOT = os.path.dirname(os.path.abspath(__file__))
html = io.open(os.path.join(ROOT, "isa-59.html"), encoding="utf-8").read()
body = re.sub(r'<section id="refs".*?</section>', "", html, flags=re.S)
for quote, ref in q.CITE.findall(body):
    r = q.check_cite(quote, ref, q.verse_text)
    if r is None:
        print("SKIP:", quote, "|", ref)
    elif r is False:
        print("BAD :", quote, "|", ref)
    else:
        print("OK  :", quote[:24], "|", ref)
