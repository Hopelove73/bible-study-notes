# -*- coding: utf-8 -*-
"""审查辅助：把一章的机械校验结果与结构明细导出，供写审查报告时定位。

用法：py scripts\\review_helper.py isa-57
输出：写到 logs\\review_helper_<id>.txt（UTF-8，便于人工审阅）
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")


def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def strip_tags(t):
    t = re.sub(r"<script\b.*?</script>", "", t, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", "", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&nbsp;", " ").replace("&amp;", "&")


def main():
    cid = sys.argv[1]
    path = os.path.join(ROOT, "%s.html" % cid)
    h = io.open(path, encoding="utf-8").read()

    out = []
    r = subprocess.run([sys.executable, CHECK, path, "--json"], capture_output=True, cwd=ROOT)
    raw = r.stdout.decode("utf-8", "ignore")
    i, j = raw.find("{"), raw.rfind("}")
    data = json.loads(raw[i:j + 1])
    out.append("=== check_note.py ===")
    out.append("P0 %d/%d 通过 · P1 %d · P2 %d" % (
        sum(1 for x in data["items"] if x["level"] == "P0" and x["ok"]),
        sum(1 for x in data["items"] if x["level"] == "P0"),
        sum(1 for x in data["items"] if x["level"] == "P1" and not x["ok"]),
        sum(1 for x in data["items"] if x["level"] == "P2" and not x["ok"])))
    for x in data["items"]:
        if not x["ok"]:
            out.append("  ✗ [%s] %s %s %s" % (x["level"], x["code"], x["msg"], ("@" + x["loc"]) if x["loc"] else ""))
    out.append("")

    secs = {}
    order = []
    for m in re.finditer(r'<section\s+id="([^"]+)"[^>]*>', h):
        sid = m.group(1)
        start = m.end()
        end = h.find("</section>", start)
        secs[sid] = h[start:end] if end != -1 else h[start:]
        order.append(sid)

    out.append("=== 各 section 字数（汉字）===")
    for sid in order:
        out.append("  %-9s %5d" % (sid, cjk(strip_tags(secs[sid]))))
    out.append("  %-9s %5d" % ("TOTAL", cjk(strip_tags(h))))
    out.append("")

    out.append("=== 段落 ===")
    segs = re.findall(r'<article class="seg">(.*?)</article>', secs.get("reading", ""), re.S)
    for i, s in enumerate(segs, 1):
        m = re.search(r'<span class="seg-idx">SEG \d+</span><h3>(.*?)</h3><span class="seg-ref">(.*?)</span>', s, re.S)
        title = m.group(1) if m else "?"
        ref = m.group(2) if m else "?"
        b = re.search(r'<div class="body">(.*?)</div>\s*<div class="note', s, re.S)
        blen = cjk(strip_tags(b.group(1))) if b else 0
        notes = re.findall(r'<div class="note (note--\w+)">', s)
        verses = re.findall(r"<sup>(\d+)</sup>", s)
        out.append("  SEG%02d [%s] %s  body=%d 字  note=%s  节=%s" % (
            i, ref, title, blen, ",".join(n[5:] for n in notes),
            verses[0] + "-" + verses[-1] if verses else "-"))
    out.append("")

    out.append("=== 重点经文 ===")
    for i, kv in enumerate(re.findall(r'<div class="kv">(.*?)</ol>', secs.get("key", ""), re.S), 1):
        ref = re.search(r'<div class="kv-ref">(.*?)</div>', kv)
        bq = re.search(r"<blockquote>(.*?)</blockquote>", kv, re.S)
        out.append("  KV%d %s | %s" % (i, ref.group(1) if ref else "?", strip_tags(bq.group(1))[:70] if bq else ""))
    out.append("")

    out.append("=== note 统计 ===")
    for cls in ("info", "warn", "christ"):
        found = re.findall(r'<div class="note note--%s">' % cls, h)
        out.append("  note--%-8s %d 条" % (cls, len(found)))
    out.append("")

    out.append("=== 人物卡（本章）===")
    praw = io.open(os.path.join(ROOT, "assets", "people.js"), encoding="utf-8").read()
    pi, pj = praw.find("["), praw.rfind("]")
    people = json.loads(praw[pi:pj + 1])
    for p in people:
        if cid in p.get("chapters", []):
            out.append("  [%s] %s (%s) id=%s" % ("★" * p.get("star", 0), p.get("name"), p.get("role"), p.get("id")))
    out.append("")

    out.append("=== 自测三问 ===")
    for d in re.findall(r"<details><summary>(.*?)</summary>", secs.get("review", ""), re.S):
        out.append("  " + strip_tags(d))
    out.append("")
    out.append("=== 下一章预告 ===")
    m = re.search(r"<h3>下一章预告[^<]*</h3>(.*?)</section>", secs.get("review", ""), re.S)
    if m:
        out.append("  " + strip_tags(m.group(1)).strip()[:400])

    dst = os.path.join(ROOT, "logs", "review_helper_%s.txt" % cid)
    io.open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("已写入 %s" % dst)


if __name__ == "__main__":
    main()
