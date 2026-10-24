# -*- coding: utf-8 -*-
"""重建「旧约 / 新约 → 书卷 → 章」目录，并生成每一卷的书卷页。

- 书卷元数据来自 assets/books.js（整个正典 66 卷）
- 章节文件命名 {bookId}-{NN}.html（如 isa-01.html）
- 每写完一章，重跑本脚本：
    * index.html 的目录自动归位
    * books/<bookId>.html 自动更新章节网格

用法：
  py reg_index.py            # 预览
  py reg_index.py --write    # 写回 index.html 与 books/*.html
"""
import glob
import html as htmllib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import chapter_file, scan_chapters as scan_all_ids

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_JS = os.path.join(ROOT, "assets", "books.js")
IDX = os.path.join(ROOT, "index.html")
BOOKS_DIR = os.path.join(ROOT, "books")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_books():
    s = io.open(BOOKS_JS, encoding="utf-8").read()
    i, j = s.find("["), s.rfind("]")
    return json.loads(s[i:j + 1])


def scan_chapters():
    """扫描全部章节，返回 {bid: {ch: (相对ROOT的href, 绝对路径)}}。

    兼容「根目录平铺」与「<书卷>/ 子目录」两种布局：
    - index.html 的 chips 直接用 href（index 在 ROOT）
    - books/<bid>.html 的 grid 用 "../" + href
    """
    avail = {}
    for cid in scan_all_ids():
        m = re.match(r"^([a-z0-9]+)-(\d{2})$", cid)
        if not m:
            continue
        bid, ch = m.group(1), int(m.group(2))
        p = chapter_file(cid)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        avail.setdefault(bid, {})[ch] = (rel, p)
    return avail


def brief(path):
    try:
        h = io.open(path, encoding="utf-8").read()
    except Exception:
        return ""
    m = re.search(r'<p class="thesis">(.*?)</p>', h, re.S)
    if m:
        t = re.sub(r"<[^>]+>", "", m.group(1))
        return re.sub(r"\s+", " ", t).strip()[:60]
    m = re.search(r'<div class="seg-head">.*?<h3>(.*?)</h3>', h, re.S)
    if m:
        return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", m.group(1)))[:40]
    return ""


def book_block(b, chapters):
    name = htmllib.escape(b["name"])
    en = htmllib.escape(b["en"])
    total = b["chapters"]
    have = sorted(chapters)
    page = "books/%s.html" % b["id"]
    if have:
        chips = []
        for ch in have:
            fname, path = chapters[ch]
            tip = htmllib.escape(brief(path), quote=True)
            attr = ' title="%s"' % tip if tip else ""
            chips.append('              <a class="chip" href="%s"%s>%d</a>' % (fname, attr, ch))
        pending = total - len(have)
        if pending > 0:
            chips.append('              <span class="chip-pending">另 %d 章待写</span>' % pending)
        chips.append('              <a class="chip bookpage" href="%s">全书 →</a>' % page)
        ov = os.path.join(BOOKS_DIR, "%s-overview.html" % b["id"])
        if os.path.exists(ov):
            chips.append('              <a class="chip overview" href="%s-overview.html">概论 →</a>' % b["id"])
        chip_html = "\n".join(chips)
        return (
            '          <details class="bookgroup">\n'
            '            <summary>\n'
            '              <span class="bg-title"><span class="bg-name">%s</span>'
            '<span class="bg-en">%s</span></span>\n'
            '              <span class="bg-meta"><b>%d</b> / %d 章 <span class="bg-caret">▾</span></span>\n'
            '            </summary>\n'
            '            <div class="chips">\n%s\n            </div>\n'
            '          </details>' % (name, en, len(have), total, chip_html)
        )
    return (
        '          <a class="bookgroup empty" href="%s">\n'
        '            <span class="bg-title"><span class="bg-name">%s</span>'
        '<span class="bg-en">%s</span></span>\n'
        '            <span class="bg-meta">待写 · %d 章</span>\n'
        '          </a>' % (page, name, en, total)
    )


# 体裁分组（按正典惯用分类；key 为组名，顺序按组内第一卷的 order 排列）
GENRES = {
    "gen": "五经", "exo": "五经", "lev": "五经", "num": "五经", "deu": "五经",
    "jos": "历史书", "jdg": "历史书", "rut": "历史书", "1sa": "历史书",
    "2sa": "历史书", "1ki": "历史书", "2ki": "历史书", "1ch": "历史书",
    "2ch": "历史书", "ezr": "历史书", "neh": "历史书", "est": "历史书",
    "job": "智慧书", "psa": "智慧书", "pro": "智慧书", "ecc": "智慧书", "sng": "智慧书",
    "isa": "先知书", "jer": "先知书", "lam": "先知书", "ezk": "先知书", "dan": "先知书",
    "hos": "先知书", "jol": "先知书", "amo": "先知书", "oba": "先知书",
    "jon": "先知书", "mic": "先知书", "nam": "先知书", "hab": "先知书",
    "zep": "先知书", "hag": "先知书", "zec": "先知书", "mal": "先知书",
    "mat": "福音书", "mark": "福音书", "luk": "福音书", "jhn": "福音书",
    "act": "历史书",
    "rom": "保罗书信", "1co": "保罗书信", "2co": "保罗书信", "gal": "保罗书信",
    "eph": "保罗书信", "php": "保罗书信", "col": "保罗书信", "1th": "保罗书信",
    "2th": "保罗书信", "1ti": "保罗书信", "2ti": "保罗书信", "tit": "保罗书信",
    "phm": "保罗书信",
    "heb": "一般书信", "jas": "一般书信", "1pe": "一般书信", "2pe": "一般书信",
    "1jn": "一般书信", "2jn": "一般书信", "3jn": "一般书信", "jud": "一般书信",
    "rev": "启示录",
}
GENRE_EN = {
    "五经": "TORAH · PENTATEUCH", "历史书": "HISTORY",
    "智慧书": "WISDOM & POETRY", "先知书": "PROPHETS",
    "福音书": "GOSPELS", "保罗书信": "PAULINE EPISTLES",
    "一般书信": "GENERAL EPISTLES", "启示录": "APOCALYPSE",
}


def testament_block(books, avail, key, title, en):
    subset = [b for b in books if b["testament"] == key]
    n_notes = sum(len(avail.get(b["id"], {})) for b in subset)
    groups = {}
    for b in subset:
        g = GENRES.get(b["id"], "其他")
        groups.setdefault(g, []).append(b)
    gorder = sorted(groups, key=lambda g: min(b["order"] for b in groups[g]))
    html = []
    for g in gorder:
        gb = groups[g]
        gnotes = sum(len(avail.get(b["id"], {})) for b in gb)
        gtotal = sum(b["chapters"] for b in gb)
        lis = "\n".join(book_block(b, avail.get(b["id"], {})) for b in gb)
        html.append(
            '      <div class="genregroup">\n'
            '        <div class="genre-head">\n'
            '          <span class="genre-name">%s</span><span class="genre-en">%s</span>\n'
            '          <span class="genre-meta">%d 卷 · <b>%d</b> / %d 章</span>\n'
            '        </div>\n'
            '        <div class="booklist" data-genre="%s">\n%s\n        </div>\n'
            '      </div>' % (g, GENRE_EN.get(g, ""), len(gb), gnotes, gtotal, g, lis)
        )
    return (
        '      <div class="testament" id="%s">\n'
        '        <div class="testament-head">\n'
        '          <h3>%s</h3>\n'
        '          <span class="sub">%s</span>\n'
        '          <span class="tally">%d 卷 · <b>%d</b> 章已上线</span>\n'
        '        </div>\n%s\n      </div>' % (key, title, en, len(subset), n_notes, "\n".join(html)),
        n_notes,
    )


BOOK_PAGE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} · 圣经精读笔记</title>
<meta name="description" content="{name}（{en}）共 {total} 章，已上线 {have} 章精读笔记。">
<link rel="stylesheet" href="../assets/style.css">
<script>try{{var t=localStorage.getItem('bible.theme');if(t)document.documentElement.dataset.theme=JSON.parse(t);}}catch(e){{}}</script>
</head>
<body>
<div id="readbar"></div>

<header class="topbar">
  <a class="brand" href="../index.html">圣经<span>·</span>精读</a>
  <span class="spacer"></span>
  <a href="../index.html#ot">旧约</a>
  <a href="../index.html#nt">新约</a>
  <a href="../people.html">人物总表</a>
  <button class="iconbtn no-print" id="themeBtn">深色</button>
</header>

<div class="wrap">

  <div class="hero-lg" style="padding:64px 0 34px">
    <div class="kicker">{testament_en} &nbsp;·&nbsp; {book_index} / {book_total}</div>
    <h1>{name}</h1>
    <p class="lead">{en} &nbsp;·&nbsp; 全卷 {total} 章 &nbsp;·&nbsp; 已上线 <b style="color:var(--accent);font-weight:400">{have}</b> 章</p>
  </div>

  <main style="padding-top:44px">
    <section>
      <div class="sec-head">
        <span class="sec-num">01</span>
        <h2>章节</h2>
        <span class="sub">Chapters</span>
      </div>
      <div class="chapter-grid">
{grid}
      </div>
      <p class="prose" style="margin-top:26px;color:var(--muted);font-size:13px">实线为已上线章节，虚线为待写。每完成一章，目录脚本会自动把它补进这一页。</p>
      <div class="booknav">
        <span>{prev}</span>
        <span><a href="../index.html#{anchor}">{testament_cn}目录</a></span>
        <span>{next}</span>
      </div>
    </section>
  </main>
</div>

<script src="../assets/app.js"></script>
</body>
</html>
"""


def book_page(b, chapters, books):
    tid = b["testament"]
    subset = [x for x in books if x["testament"] == tid]
    pos = subset.index(b) + 1
    prev_b = subset[pos - 2] if pos > 1 else None
    next_b = subset[pos] if pos < len(subset) else None
    have = sorted(chapters)
    grid = []
    for ch in range(1, b["chapters"] + 1):
        if ch in chapters:
            grid.append('        <a class="chap" href="../%s">%d</a>' % (chapters[ch][0], ch))
        else:
            grid.append('        <span class="chap pending">%d</span>' % ch)
    prev_html = ('上一卷：<a href="%s.html">%s</a>' % (prev_b["id"], htmllib.escape(prev_b["name"]))
                 if prev_b else "&nbsp;")
    next_html = ('下一卷：<a href="%s.html">%s</a>' % (next_b["id"], htmllib.escape(next_b["name"]))
                 if next_b else "&nbsp;")
    return BOOK_PAGE.format(
        name=htmllib.escape(b["name"]),
        en=htmllib.escape(b["en"]),
        total=b["chapters"],
        have=len(have),
        testament_en="OLD TESTAMENT" if tid == "ot" else "NEW TESTAMENT",
        testament_cn="旧约" if tid == "ot" else "新约",
        book_index=pos,
        book_total=len(subset),
        anchor=tid,
        grid="\n".join(grid),
        prev=prev_html,
        next=next_html,
    )


def main():
    write = "--write" in sys.argv
    books = load_books()
    avail = scan_chapters()

    known = {b["id"] for b in books}
    for bid in avail:
        if bid not in known:
            print("！未在 books.js 中登记的书卷 id：%s（相关章节不会显示）" % bid)

    ot_block, ot_notes = testament_block(books, avail, "ot", "旧约", "Old Testament")
    nt_block, nt_notes = testament_block(books, avail, "nt", "新约", "New Testament")
    total_notes = ot_notes + nt_notes
    total_chapters = sum(b["chapters"] for b in books)
    n_books_have = len([b for b in books if avail.get(b["id"])])

    catalog = (
        '      <div class="filters" style="border:none;padding:0;margin-bottom:6px">\n'
        '        <a class="fld" href="#ot">旧约 · 39 卷</a>\n'
        '        <a class="fld" href="#nt">新约 · 27 卷</a>\n'
        '        <span class="count-line" style="margin-left:auto">已上线 <b>%d</b> / %d 章'
        ' · 收录 <b>%d</b> / %d 卷</span>\n'
        '      </div>\n\n%s\n\n%s' % (
            total_notes, total_chapters, n_books_have, len(books), ot_block, nt_block
        )
    )

    h = io.open(IDX, encoding="utf-8").read()

    praw = io.open(os.path.join(ROOT, "assets", "people.js"), encoding="utf-8").read()
    pi, pj = praw.find("["), praw.rfind("]")
    n_people = len(json.loads(praw[pi:pj + 1]))
    h = re.sub(r'(<b>)\d+(</b>已上线章节)', lambda m: m.group(1) + str(total_notes) + m.group(2), h)
    h = re.sub(r'(<b>)\d+(</b>人物档案)', lambda m: m.group(1) + str(n_people) + m.group(2), h)

    pat = re.compile(r"(<!-- CATALOG:START -->)(.*?)(<!-- CATALOG:END -->)", re.S)
    if not pat.search(h):
        print("找不到 CATALOG 标记，未改动")
        return 1
    new_html = pat.sub(lambda m: m.group(1) + "\n" + catalog + "\n      " + m.group(3), h, count=1)

    print("已上线 %d / %d 章 · 收录 %d / %d 卷 · 人物 %d" % (
        total_notes, total_chapters, n_books_have, len(books), n_people))
    print("旧约 %d 章 / 新约 %d 章" % (ot_notes, nt_notes))

    if write:
        io.open(IDX, "w", encoding="utf-8", newline="\n").write(new_html)
        if not os.path.isdir(BOOKS_DIR):
            os.makedirs(BOOKS_DIR)
        written = 0
        for b in books:
            page = book_page(b, avail.get(b["id"], {}), books)
            io.open(os.path.join(BOOKS_DIR, "%s.html" % b["id"]), "w",
                    encoding="utf-8", newline="\n").write(page)
            written += 1
        print("已写入 index.html 与 books/ 下 %d 个书卷页" % written)
    else:
        print("（预览模式，加 --write 写回）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
