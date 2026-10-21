# -*- coding: utf-8 -*-
"""章节内容体检：抓机器校验（check_note.py）查不出的问题。

硬错误（判失败）：
  1. 禁用句式（神今天对你说 / 主要你 / 神绝不会让你 / 只要相信就一定会 …）
  2. 长度 >= 40 字的整段重复
  3. 常用标签未闭合（div / section / article / details / p / span / li / table）
  4. note 条数与 emoji 个数不一一对应
  5. 本章 ★★★ 人物不是恰好 3 位
  6. 节号与 verses/<id>.json 不一致（独立于 check_note 再验一次）
  7. 缺 verses/<id>.json

提示（不判失败，供人工确认）：
  · 正文里出现的小写英文词（可能是手滑混入的英文，也可能是希伯来文转写）

用法：
  py scripts\\qa_scan.py                 # 扫全部章节
  py scripts\\qa_scan.py isa-11 isa-17   # 只扫指定章节
退出码：0 = 无硬错误；1 = 有硬错误。
"""
import glob
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

BANNED = [
    "神今天对你说", "主要你", "主提醒你", "神绝不会让你", "只要相信就一定会",
    "一定会蒙福", "保证平安", "家人们", "宝子们", "耶稣爱你",
    "多数解经家认为", "丁道尔说", "唐崇荣说", "灵修网站",
]

# 页面装饰与固定英文（章节页的栏目标题、书名、徽标等）
CHROME = set("""
Before You Read Background Overview Structure Map Verse Verses Key Bible
Notes Note People Prayer Application Tasks Review References Chapter Oracle
THE BOOK GOSPEL OF MARK ISAIAH Introduction Contents Section Part Page Title
Reading Guide Word Study Application Review Tasks People Prayer Notes
Applications Verses Keys Old Testament New Testament Chapter Notes
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
KJV Vulgate Septuagint Masoretic LXX
""".split())

TAGS = ["div", "section", "article", "details", "p", "span", "li", "table", "tbody", "tr", "td", "th"]


def strip_html(h):
    h = re.sub(r"<script\b.*?</script>", "", h, flags=re.S | re.I)
    h = re.sub(r"<style\b.*?</style>", "", h, flags=re.S | re.I)
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S)
    return h


def text_of(h):
    h = strip_html(h)
    h = re.sub(r"<[^>]+>", "\n", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&")
    return h


def english_hints(body, text):
    """列出可疑的小写英文词（可能是手滑混入，也可能是转写）。"""
    paren_text = " ".join(re.findall(r"[（(][^）)]*[）)]", body))
    hints = []
    seen = set()
    for m in re.finditer(r"[A-Za-z][A-Za-z'\-]{3,}", text):
        w = m.group(0)
        if w in CHROME or w in seen:
            continue
        seen.add(w)
        if w[0].isupper():          # 专名 / 地名 / 人名 / 转写
            continue
        if w in paren_text:          # 括号内的转写惯例
            continue
        if re.search(r"[^\x00-\x7F]", w):   # 带变音符的转写
            continue
        before = text[m.start() - 1] if m.start() > 0 else ""
        after = text[m.end()] if m.end() < len(text) else ""
        if before in "/." or after in "./":   # 文件名 / 网址的一部分
            continue
        ctx = text[max(0, m.start() - 20):m.end() + 20].replace("\n", " ")
        hints.append("%r（…%s…）" % (w, ctx))
    return hints


def scripture_blocks(body):
    """只取 reading 段里的经文块（重点经文区会重复引用经文，不计入节号统计）。"""
    m = re.search(r'<section id="reading"[^>]*>(.*?)</section>', body, re.S)
    region = m.group(1) if m else body
    return re.findall(r'<div class="scripture">(.*?)</div>', region, re.S)


def prose_text(body):
    """去掉经文块与重点经文区后的正文（那里会重复引用经文，不算重复段落）。"""
    t = re.sub(r'<div class="scripture">.*?</div>', "\n", body, flags=re.S)
    t = re.sub(r'<section id="key"[^>]*>.*?</section>', "\n", t, flags=re.S)
    return t


def scan(cid, h, people):
    errors = []
    hints = []
    body = strip_html(h)

    for b in BANNED:
        if b in body:
            errors.append("禁用句式：%s" % b)

    t = text_of(body)
    tp = text_of(prose_text(body))

    paras = [p.strip() for p in re.split(r"\n+", tp) if len(p.strip()) >= 40]
    seen = {}
    for p in paras:
        key = p[:40]
        if key in seen:
            errors.append("重复段落：%s…" % p[:40])
        seen[key] = 1

    for tag in TAGS:
        o = len(re.findall(r"<%s\b" % tag, body, re.I))
        c = len(re.findall(r"</%s>" % tag, body, re.I))
        if o != c:
            errors.append("标签未闭合：<%s> 开 %d 闭 %d" % (tag, o, c))

    notes = re.findall(r'<div class="note[^"]*">(.*?)</div>', body, re.S)
    for i, n in enumerate(notes, 1):
        em = re.findall(r"[\U0001F7E6\U0001F7E8\U0001F7E7]", n)
        if len(em) != 1:
            errors.append("第 %d 条 note 的 emoji 数为 %d（应为 1）" % (i, len(em)))

    stars = [p for p in people
             if p.get("star") == 1 and cid in (p.get("chapters") or [])]
    if len(stars) != 3:
        errors.append("本章 ★★★ 人物为 %d 位（应为 3）" % len(stars))

    vpath = os.path.join(ROOT, "verses", "%s.json" % cid)
    if os.path.exists(vpath):
        data = json.load(io.open(vpath, encoding="utf-8"))
        want = [v["n"] for v in data["verses"]]
        got = []
        for blk in scripture_blocks(body):
            got += [int(x) for x in re.findall(r"<sup>(\d+)</sup>", blk)]
        if sorted(got) != sorted(want):
            errors.append("节号与 verses/%s.json 不一致：页面 %d 节 / JSON %d 节"
                          % (cid, len(got), len(want)))
        if len(got) != len(set(got)):
            errors.append("节号有重复")
    else:
        errors.append("缺 verses/%s.json" % cid)

    hints = english_hints(body, t)
    return errors, hints


def main():
    ids = sys.argv[1:]
    if not ids:
        ids = sorted(os.path.splitext(os.path.basename(p))[0]
                     for p in glob.glob(os.path.join(ROOT, "*.html"))
                     if re.match(r"^[a-z0-9]+-\d{2}\.html$", os.path.basename(p)))
    praw = io.open(os.path.join(ROOT, "assets", "people.js"), encoding="utf-8").read()
    people = json.loads(praw[praw.find("["):praw.rfind("]") + 1])

    bad = 0
    n_hint = 0
    for cid in ids:
        path = os.path.join(ROOT, "%s.html" % cid)
        if not os.path.exists(path):
            print("%-8s 缺文件" % cid)
            bad += 1
            continue
        h = io.open(path, encoding="utf-8").read()
        errs, hints = scan(cid, h, people)
        if errs:
            bad += 1
            print("%-8s 硬错误 %d 项" % (cid, len(errs)))
            for e in errs[:12]:
                print("    ! %s" % e)
        else:
            print("%-8s 干净" % cid)
        if hints:
            n_hint += 1
            print("    · 待确认英文 %d：%s" % (len(hints), " / ".join(hints[:6])))
    print("—— 体检：%d 章有硬错误 / 共 %d 章；%d 章有待确认英文"
          % (bad, len(ids), n_hint))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
