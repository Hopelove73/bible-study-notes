# -*- coding: utf-8 -*-
r"""核对并（可选）修正各章 scripture 区块里的经文，使它与 verses\<id>.json 逐字一致。

用法：
    py scripts\\fix_verses.py                 # 只报告
    py scripts\\fix_verses.py --write         # 报告并直接改回原文
    py scripts\\fix_verses.py isa-05 isa-10    # 只查指定章节

原理：把 scripture 区块里每一节的文字与 JSON 里的对应节逐一比对；
不一致时，用 JSON 的原文整节替换 HTML 里的那一节（连同上标一起替换）。
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def norm(t):
    # 与 check_note.py 的 normalize_verse 保持一致：整段去掉〔…〕校勘注
    t = re.sub(r"〔[^〕]*〕", "", t)
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", t)


def strip_tags(t):
    return re.sub(r"<[^>]+>", "", t)


def run(cid, write=False):
    path = os.path.join(ROOT, "%s.html" % cid)
    vp = os.path.join(ROOT, "verses", "%s.json" % cid)
    if not (os.path.exists(path) and os.path.exists(vp)):
        return []
    h = io.open(path, encoding="utf-8").read()
    d = json.load(io.open(vp, encoding="utf-8"))
    remote = {v["n"]: v["text"] for v in d["verses"]}
    issues = []

    def fix_block(block):
        out = block
        for m in list(re.finditer(r"<sup>(\d+)</sup>(.*?)</p>", block, re.S)):
            n = int(m.group(1))
            if n not in remote:
                continue
            txt = strip_tags(m.group(2))
            if norm(txt) == norm(remote[n]):
                continue
            issues.append((n, txt[:40], remote[n][:40]))
            if write:
                repl = "<sup>%d</sup>%s</p>" % (n, remote[n])
                out = out[:m.start()] + repl + out[m.end():]
        return out

    def repl_block(m):
        return '<div class="scripture">%s</div>' % fix_block(m.group(1))

    h2 = re.sub(r'<div class="scripture">(.*?)</div>', repl_block, h, flags=re.S)
    if write and h2 != h:
        io.open(path, "w", encoding="utf-8", newline="\n").write(h2)
    return issues


def main():
    args = sys.argv[1:]
    write = "--write" in args
    ids = [a for a in args if not a.startswith("--")]
    if not ids:
        ids = []
        for f in sorted(os.listdir(ROOT)):
            if re.match(r"^[a-z0-9]+-\d{2}\.html$", f):
                ids.append(f[:-5])
    total = 0
    for cid in ids:
        try:
            issues = run(cid, write)
        except Exception as e:
            print("%-9s 处理出错：%s" % (cid, e))
            continue
        if issues:
            total += len(issues)
            print("%-9s %d 节与原文不符%s" % (cid, len(issues), "（已改回原文）" if write else ""))
            for n, a, b in issues:
                print("   v%-3d 文件：%s" % (n, a))
                print("        原文：%s" % b)
    print("合计 %d 处经文不符%s" % (total, "，已全部改回" if write else ""))


if __name__ == "__main__":
    main()
