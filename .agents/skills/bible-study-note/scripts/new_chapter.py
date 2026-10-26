#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_chapter.py — 从模板新建一章笔记骨架，登记到 index.html，并生成立项卡。

用法：
  python new_chapter.py --id mark-02 --book 马可福音 --book-en "THE GOSPEL OF MARK" \
      --chapter 2 --verses 28 --genre "叙事 · 古代传记" --segments 6 \
      --thesis "一句话主旨" --minutes 30

  python new_chapter.py ... --dir "D:\\某目录"     # 指定笔记根目录
  python new_chapter.py ... --force                # 覆盖已存在的 HTML
  python new_chapter.py ... --no-index             # 不写 index.html
"""

import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TPL = os.path.join(SKILL, "assets", "template.html")
ASSETS = ["style.css", "app.js", "people.js"]


def cn_num(n):
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 20:
        return "十" + (d[n % 10] if n % 10 else "")
    if n < 100:
        return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")
    if n < 1000:
        h, r = divmod(n, 100)
        s = d[h] + "百"
        if r == 0:
            return s
        if r < 10:
            return s + "零" + d[r]
        return s + cn_num(r)
    return str(n)


def find_project_root(root):
    """从 root 向上找含 assets/style.css 的项目根；找不到则返回 root。"""
    d = root
    while True:
        if os.path.exists(os.path.join(d, "assets", "style.css")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return root
        d = parent


def ensure_assets(root):
    """章节在 <书卷>/ 子目录时复用项目根 assets，不在子目录重复创建。"""
    proj = find_project_root(root)
    if os.path.abspath(proj) != os.path.abspath(root):
        return []
    os.makedirs(os.path.join(root, "assets"), exist_ok=True)
    copied = []
    for name in ASSETS:
        dst = os.path.join(root, "assets", name)
        if not os.path.exists(dst):
            src = os.path.join(SKILL, "assets", name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied.append(name)
    return copied


def find_div_end(html, start):
    depth = 0
    for m in re.finditer(r"<div\b[^>]*>|</div>", html[start:]):
        if m.group(0).startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return start + m.end()
    return -1


def register(html, cid, book, chapter, title, thesis):
    if 'href="%s.html"' % cid in html:
        return html, False
    marker = '<div class="booklist">'
    i = html.find(marker)
    if i == -1:
        return html, False
    end = find_div_end(html, i)
    if end == -1:
        return html, False
    close = html.rfind("</div>", i, end)
    idx = len(re.findall(r'class="bookrow"', html[:close])) + 1
    row = (
        '        <a class="bookrow" href="%s.html">\n'
        '          <span class="idx">%02d</span>\n'
        '          <span>\n'
        '            <h3>%s 第 %d 章</h3>\n'
        '            <span class="meta">%s</span>\n'
        '          </span>\n'
        '          <span class="status" data-chapter-progress="%s">未开始 · 0 / 1</span>\n'
        '        </a>\n'
    ) % (cid, idx, book, chapter, title or thesis, cid)
    html = html[:close] + row + html[close:]

    # 已上线章节数 +1
    m = re.search(r"<b>(\d+)</b>已上线章节", html)
    if m:
        html = html[:m.start(1)] + str(int(m.group(1)) + 1) + html[m.end(1):]
    return html, True


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="如 mark-02 / rom-08 / psa-119")
    ap.add_argument("--book", required=True)
    ap.add_argument("--book-en", default="")
    ap.add_argument("--chapter", required=True, type=int)
    ap.add_argument("--verses", required=True, type=int)
    ap.add_argument("--genre", required=True, help="叙事 / 书信 / 诗歌 / 律法 / 先知启示")
    ap.add_argument("--segments", type=int, default=8)
    ap.add_argument("--thesis", required=True)
    ap.add_argument("--minutes", type=int, default=30)
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-index", action="store_true")
    args = ap.parse_args()

    if not re.match(r"^[a-z0-9]+-\d{2}$", args.id):
        print("id 必须形如 mark-02（小写 + 两位章号）", file=sys.stderr)
        return 2
    if not re.match(r"^\d{2}$", args.id.rsplit("-", 1)[1]):
        print("章号必须是两位", file=sys.stderr)
        return 2

    root = os.path.abspath(args.dir)
    proj = find_project_root(root)
    os.makedirs(root, exist_ok=True)
    target = os.path.join(root, args.id + ".html")
    if os.path.exists(target) and not args.force:
        print("已存在 %s；要覆盖请加 --force" % target, file=sys.stderr)
        return 2
    if not os.path.exists(TPL):
        print("找不到模板：%s" % TPL, file=sys.stderr)
        return 2

    copied = ensure_assets(root)

    html = open(TPL, encoding="utf-8").read()
    repl = {
        "{{ID}}": args.id,
        "{{BOOK}}": args.book,
        "{{BOOK_EN}}": args.book_en or args.book,
        "{{CHAPTER}}": str(args.chapter),
        "{{CHAPTER_PAD}}": "%02d" % args.chapter,
        "{{CHAPTER_CN}}": "第" + cn_num(args.chapter) + "章",
        "{{VERSES}}": str(args.verses),
        "{{GENRE}}": args.genre,
        "{{THESIS}}": args.thesis,
        "{{MINUTES}}": str(args.minutes),
        "{{SEGMENTS}}": str(args.segments),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    # 立项卡
    brief_dir = os.path.join(proj, "_brief")
    os.makedirs(brief_dir, exist_ok=True)
    brief = os.path.join(brief_dir, args.id + ".md")
    if not os.path.exists(brief) or args.force:
        brief_text = (
            "# %s 第 %d 章 · 立项卡\n\n"
            "- id：`%s`\n- 文体：%s\n- 节数：%d\n- 预计段落：%d\n- 预计字数：待定\n"
            "- 主旨：%s\n\n"
            "## 结构（待填）\n\n1. TODO 段落 / 经文范围 / 功能\n\n"
            "## 人物（待填）\n\n- ★★★：TODO / TODO / TODO\n- ★★：TODO\n- ★：TODO\n\n"
            "## 重点经文（待填）\n\n- TODO\n\n"
            "## 最容易读错的一处（待填）\n\nTODO\n"
        ) % (args.book, args.chapter, args.id, args.genre, args.verses, args.segments, args.thesis)
        with open(brief, "w", encoding="utf-8", newline="\n") as f:
            f.write(brief_text)

    # 登记 index
    registered = False
    if not args.no_index:
        ipath = os.path.join(root, "index.html")
        if os.path.exists(ipath):
            idx = open(ipath, encoding="utf-8").read()
            new, ok = register(idx, args.id, args.book, args.chapter, args.thesis, args.thesis)
            if ok:
                with open(ipath, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                registered = True

    print("已创建 %s" % target)
    if copied:
        print("已补齐 assets：%s" % ", ".join(copied))
    print("立项卡：%s" % brief)
    print("index.html：%s" % ("已登记" if registered else "未改动（手动确认）"))
    print("")
    print("下一步：")
    print("  1. 填 _brief/%s.md，给用户看，等确认" % args.id)
    print("  2. python .agents/skills/bible-study-note/scripts/verify_verses.py --book <CODE> --chapter %d --out verses/%s.json" % (args.chapter, args.id))
    print("  3. 填内容 → check_note.py → 人工审查 → reviews/%s.txt" % args.id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
