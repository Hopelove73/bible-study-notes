# -*- coding: utf-8 -*-
"""build.py — 把「内容 JSON」编译成章节 HTML。

设计原则：模型只写内容（约 6–8k 字），结构、经文、导航、标注、目录一律由脚本生成。
这样经文逐字取自 verses/<id>.json，A01–A11 / A20–A23 / A28 结构性错误不可能发生。

用法：
    py scripts\\build.py amo-02            # 校验 + 编译到 <书卷>/amo-02.html
    py scripts\\build.py amo-02 --dry      # 只校验，不落盘
    py scripts\\build.py --book amo         # 编译整卷（_src 下所有 json）
    py scripts\\build.py --book amo --dry

内容文件位置：<书卷中文目录>/_src/<id>.json
字段说明见 scripts\\content_schema.md。

退出码：0 = 全部通过；1 = 有错误或预算不符（会列出字段级原因）。
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _paths import book_dir, chapter_file  # noqa: E402

SECTIONS = ["before", "bg", "overview", "map", "reading", "key",
            "theology", "prayer", "apply", "tasks", "review", "refs"]

BUDGET = {
    "before": (120, 700),
    "bg": (600, 1800),
    "overview": (250, 900),
    "map": (80, 900),
    "reading": (2500, 9500),
    "key": (500, 2200),
    "theology": (250, 1200),
    "prayer": (150, 700),
    "apply": (300, 1300),
    "tasks": (250, 1200),
    "review": (200, 900),
    "refs": (150, 900),
}
TOTAL_BUDGET = (4500, 16000)

FORBIDDEN = ["神今天对你说", "主要你", "神绝不会让你", "只要相信就一定会",
             "家人们", "宝子们", "绝绝子", "不得不说", "说实话"]
PLACEHOLDERS = ["TODO", "待补充", "Lorem", "XXX", "{{", "}}", "??"]

TASK_TITLES = {
    "A": "A · 观察任务（读经时随手做）",
    "B": "B · 记忆任务（本章只背 3 位）",
    "C": "C · 关联任务（接人物总表）",
    "D": "D · 输出任务（写完才算过关）",
}
BG_LABELS = ["历史", "地理", "文化", "文学", "救赎史"]
NOTE_LEVEL = {"info": ("note--info", "🟦"), "warn": ("note--warn", "🟨"), "christ": ("note--christ", "🟧")}
CN_DIGITS = "零一二三四五六七八九"


def cn_num(n):
    if n < 10:
        return CN_DIGITS[n]
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    if n < 100:
        h, r = divmod(n, 10)
        return CN_DIGITS[h] + "十" + (CN_DIGITS[r] if r else "")
    h, r = divmod(n, 100)
    s = CN_DIGITS[h] + "百"
    if r == 0:
        return s
    if r < 10:
        return s + "零" + CN_DIGITS[r]
    return s + cn_num(r)


def cjk(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def strip_tags(text):
    text = re.sub(r"<script\b.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").replace("&amp;", "&")


def load_books():
    raw = io.open(os.path.join(ROOT, "assets", "books.js"), encoding="utf-8").read()
    return {b["id"]: b for b in json.loads(raw[raw.find("["):raw.rfind("]") + 1])}


class Ctx(object):
    def __init__(self, cid, books):
        self.cid = cid
        self.book_code, ch = cid.rsplit("-", 1)
        self.chapter = int(ch)
        self.book = books[self.book_code]
        self.name = self.book["name"]
        self.en = self.book["en"]
        self.nt = self.book["testament"] == "nt"
        self.dir = os.path.join(ROOT, book_dir(self.book_code))
        self.src = os.path.join(self.dir, "_src", "%s.json" % cid)
        vp = os.path.join(ROOT, "verses", "%s.json" % cid)
        self.vdata = json.load(io.open(vp, encoding="utf-8")) if os.path.exists(vp) else None
        self.verses = {v["n"]: v["text"] for v in (self.vdata or {}).get("verses", [])}
        self.nverses = len(self.verses)

    def vtext(self, nums):
        return "".join(self.verses.get(n, "") for n in nums)

    def parse_ref(self, ref, where):
        """把 '2:4-6' / '2:4–6' / '2:4' 解析成节号列表。"""
        s = (ref or "").strip().replace("–", "-").replace("—", "-")
        m = re.match(r"^(\d+):(\d+)(?:\s*-\s*(\d+))?$", s)
        if not m:
            raise ValueError("%s 经文引用格式不对：%r（应写成 2:4-6）" % (where, ref))
        ch, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3) or m.group(2))
        if ch != self.chapter:
            raise ValueError("%s 里的章号 %d 与本章 %d 不符" % (where, ch, self.chapter))
        if not (1 <= a <= b <= self.nverses):
            raise ValueError("%s 的节范围 %d-%d 超出 1-%d" % (where, a, b, self.nverses))
        return list(range(a, b + 1))


def p(text):
    return "<p>%s</p>" % text


def paras(items):
    if isinstance(items, str):
        items = [items]
    return "".join(p(x) for x in items if str(x).strip())


def note(level, title, body):
    cls, emo = NOTE_LEVEL[level]
    t = title.strip()
    if not t.startswith(emo):
        t = "%s %s" % (emo, t)
    return ('<div class="note %s">\n            <span class="tag">%s</span>\n'
            '            <p>%s</p>\n          </div>') % (cls, t, body)


def script_block(ctx, nums):
    return "".join('<p><sup>%d</sup>%s</p>' % (n, ctx.verses[n]) for n in nums)


# ---------------------------------------------------------------- sections

def sec_before(ctx, d):
    rows = d.get("rows") or []
    trs = "".join("<tr><td>%s</td><td>%s</td></tr>" % (r[0], r[1]) for r in rows)
    pos = "".join("<li>%s</li>" % x for x in (d.get("position") or []))
    return """
      <section id="before">
        <div class="sec-head">
          <span class="sec-num">00</span>
          <h2>读前准备</h2>
          <span class="sub">Before You Read</span>
        </div>
        <p class="lead">{lead}</p>
        <table class="tbl">
          <thead><tr><th>观察问题</th><th>读的时候留意</th></tr></thead>
          <tbody>
            {trs}
          </tbody>
        </table>
        <h3>本章在全书的位置</h3>
        <ul class="plain">
          {pos}
        </ul>
      </section>
""".format(lead=d.get("lead", ""), trs=trs, pos=pos)


def sec_bg(ctx, d):
    cells = []
    for lab in BG_LABELS:
        cells.append('<div class="bg-cell"><h4>%s</h4><div class="body">%s</div></div>'
                     % (lab, paras(d.get(lab) or [])))
    return """
      <section id="bg">
        <div class="sec-head">
          <span class="sec-num">01</span>
          <h2>章节背景</h2>
          <span class="sub">Background</span>
        </div>
        <div class="bg-grid">
          %s
        </div>
      </section>
""" % "\n          ".join(cells)


def sec_overview(ctx, d):
    trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in row)
                  for row in (d.get("outline") or []))
    return """
      <section id="overview">
        <div class="sec-head">
          <span class="sec-num">02</span>
          <h2>章节概述</h2>
          <span class="sub">Overview</span>
        </div>
        <p class="lead">{lead}</p>
        {paras}
        <h3>结构大纲</h3>
        <table class="tbl">
          <thead><tr><th>段落</th><th>经文</th><th>内容</th><th>功能</th></tr></thead>
          <tbody>
            {trs}
          </tbody>
        </table>
      </section>
""".format(lead=d.get("lead", ""), paras=paras(d.get("paras") or []), trs=trs)


def sec_map(ctx, d):
    lis = []
    for br in d.get("branches") or []:
        title, ref, items = br[0], br[1], br[2]
        sub = "".join("<li>%s<em>%s</em></li>" % (i[0], i[1]) if isinstance(i, (list, tuple))
                      else "<li>%s</li>" % i for i in items)
        lis.append('<li><b>%s</b><em>%s</em>\n                <ul>\n                  %s\n                </ul>\n              </li>'
                   % (title, ref, "\n                  ".join(sub)))
    pills = '<span class="arrow">→</span>'.join('<span class="pill">%s</span>' % x for x in (d.get("flow") or []))
    extra = note("info", "读图提示", d["note"]) if d.get("note") else ""
    return """
      <section id="map">
        <div class="sec-head">
          <span class="sec-num">03</span>
          <h2>思维导图</h2>
          <span class="sub">Structure Map</span>
        </div>
        <p class="prose">{intro}</p>
        <div class="mm-scroll">
          <div class="mindmap">
            <div class="mm-root">{root}</div>
            <ul class="mm">
              {lis}
            </ul>
          </div>
        </div>
        <div class="flow">
          {pills}
        </div>
        {extra}
      </section>
""".format(intro=d.get("intro", ""), root=d.get("root", ""),
           lis="\n              ".join(lis), pills=pills, extra=extra)


def seg_html(ctx, i, s):
    nums = ctx.parse_ref(s.get("r"), "segs[%d]" % i)
    kw = "".join('<span>「%s」<i>%s</i></span>' % (k[0], k[1]) for k in (s.get("kw") or []) if k)
    notes = []
    for nt in s.get("notes") or []:
        notes.append(note(nt[0], nt[1], nt[2]))
    if not any((nt[0] == "christ") for nt in (s.get("notes") or [])):
        notes.append(note("christ", "与基督的关联", s.get("christ") or "见本节经文在整本圣经中的走向。"))
    return """
        <article class="seg">
          <div class="seg-head"><span class="seg-idx">SEG {idx:02d}</span><h3>{title}</h3><span class="seg-ref">{ref}</span></div>
          <div class="scripture">
            {scripture}
          </div>
          <div class="kw">{kw}</div>
          <div class="body">
            {body}
          </div>
          {notes}
        </article>""".format(idx=i + 1, title=s.get("t", ""), ref=s.get("r", ""),
                               scripture=script_block(ctx, nums), kw=kw,
                               body=paras(s.get("p") or []),
                               notes="\n          ".join(notes))


def sec_reading(ctx, d, segs_html):
    intro = ""
    if d.get("intro"):
        intro = '<p class="prose">%s</p>\n' % d["intro"]
    return """
      <section id="reading">
        <div class="sec-head">
          <span class="sec-num">04</span>
          <h2>分段精读</h2>
          <span class="sub">Verse by Verse</span>
        </div>

        %s%s
      </section>
""" % (intro, "\n".join(segs_html))


def sec_key(ctx, keys):
    blocks = []
    for k in keys:
        nums = ctx.parse_ref(k.get("r"), "key")
        steps = k.get("s") or []
        lis = "".join("<li><b>%s</b><span>%s</span></li>" % (lab, steps[j] if j < len(steps) else "")
                      for j, lab in enumerate(["上下文", "字词", "神学", "应用"]))
        blocks.append("""
        <div class="kv">
          <div>
            <div class="kv-ref">%s %s:%s</div>
            <blockquote>%s</blockquote>
          </div>
          <ol class="steps">
            %s
          </ol>
        </div>""" % (ctx.en, ctx.chapter, k["r"].split(":")[1], ctx.vtext(nums), lis))
    return """
      <section id="key">
        <div class="sec-head">
          <span class="sec-num">05</span>
          <h2>重点经文</h2>
          <span class="sub">Key Verses</span>
        </div>
%s
      </section>
""" % "\n".join(blocks)


def sec_theology(ctx, d):
    return """
      <section id="theology">
        <div class="sec-head">
          <span class="sec-num">06</span>
          <h2>神学要点</h2>
          <span class="sub">Theology</span>
        </div>
        <h3>关于神</h3>
        <p class="prose">{god}</p>
        <h3>关于人</h3>
        <p class="prose">{man}</p>
        <h3>关于基督</h3>
        <p class="prose">{christ}</p>
      </section>
""".format(god=d.get("god", ""), man=d.get("man", ""), christ=d.get("christ", ""))


def sec_prayer(ctx, d):
    extra = note("info", "祷读提示", d["note"]) if d.get("note") else ""
    return """
      <section id="prayer">
        <div class="sec-head">
          <span class="sec-num">07</span>
          <h2>祷告</h2>
          <span class="sub">Prayer</span>
        </div>
        <div class="prayer">
          {paras}
          <p class="amen">阿们。</p>
        </div>
        {extra}
      </section>
""".format(paras=paras(d.get("p") or []), extra=extra)


def sec_apply(ctx, d):
    scenes = "".join('<div class="scene"><h4>%s</h4><p>%s</p></div>' % (s[0], s[1])
                     for s in (d.get("scenes") or []))
    extra = []
    for nt in d.get("notes") or []:
        extra.append(note("info", nt[0], nt[1]))
    return """
      <section id="apply">
        <div class="sec-head">
          <span class="sec-num">08</span>
          <h2>生活应用</h2>
          <span class="sub">Application</span>
        </div>
        <div class="apply-main">
          <h3>本周一个行动</h3>
          <p>{act}</p>
        </div>
        <div class="grid grid-3">
          {scenes}
        </div>
        {extra}
      </section>
""".format(act=d.get("act", ""), scenes=scenes, extra="\n        ".join(extra))


def sec_tasks(ctx, d):
    groups = []
    for letter in ("A", "B", "C", "D"):
        items = d.get(letter) or []
        lis = []
        for j, txt in enumerate(items, 1):
            lis.append('<label class="task"><input type="checkbox" data-id="%s%d"><span class="t-body">'
                       '<span class="txt">%s</span></span></label>' % (letter.lower(), j, txt))
        groups.append('<div class="taskgroup">\n            <div class="tg-title">%s</div>\n            %s\n          </div>'
                      % (TASK_TITLES[letter], "\n            ".join(lis)))
    return """
      <section id="tasks">
        <div class="sec-head">
          <span class="sec-num">09</span>
          <h2>本章任务</h2>
          <span class="sub">Tasks</span>
        </div>
        <div class="taskbar">
          <span id="taskText">0 / 0</span>
          <span class="pbar"><i id="taskBar"></i></span>
          <span>全部完成约 {minutes} 分钟</span>
        </div>
        <div id="taskList">
          {groups}
        </div>
        <textarea id="quickNote" placeholder="我的输出任务 / 读经随手记（自动保存在本机浏览器）"></textarea>
        <h3>本章人物卡</h3>
        <p class="prose">★★★ 必须记住；★★ 知道他在本章起什么作用；★ 看一眼即可。</p>
        <div class="people-grid" id="chapterPeople" data-chapter="{cid}"></div>
      </section>
""".format(minutes=d.get("_minutes", 30), groups="\n          ".join(groups), cid=ctx.cid)


def sec_review(ctx, d):
    dets = "".join("<details><summary>%s</summary><div class=\"ans\">%s</div></details>\n        " % (q[0], q[1])
                   for q in (d.get("q") or []))
    mem = ctx.parse_ref(d.get("mem"), "review.mem")
    return """
      <section id="review">
        <div class="sec-head">
          <span class="sec-num">10</span>
          <h2>复习与预告</h2>
          <span class="sub">Review</span>
        </div>
        <h3>三道自测</h3>
        {dets}<h3>本周背诵</h3>
        <div class="scripture">{memtext}</div>
        <p class="prose">背法：{how}</p>
        <h3>下一章预告：{next}</h3>
        <p class="prose">{nexttext}</p>
      </section>
""".format(dets=dets, memtext=script_block(ctx, mem), how=d.get("how", ""),
           next=d.get("next", ""), nexttext=d.get("nextText", ""))


def sec_refs(ctx, d):
    return """
      <section id="refs">
        <div class="sec-head">
          <span class="sec-num">附</span>
          <h2>资料来源与标注说明</h2>
          <span class="sub">Sources</span>
        </div>
        <h3>三级标注</h3>
        <table class="tbl">
          <thead><tr><th>标记</th><th>含义</th><th>可信度</th></tr></thead>
          <tbody>
            <tr><td>🟦 经文直述</td><td>和合本原文直接支持的内容</td><td>可直接引用</td></tr>
            <tr><td>🟨 注释书观点</td><td>来自历代注释传统，会注明分歧</td><td>参考，非绝对</td></tr>
            <tr><td>🟧 推论</td><td>由经文推导的应用与联想</td><td>需自行分辨</td></tr>
          </tbody>
        </table>
        <h3>版本与参考</h3>
        <ul class="plain">
          <li><b>经文</b>：中文和合本（1919），存于 verses/{cid}.json，本页 scripture 区块由脚本逐字注入。</li>
          <li><b>注释</b>：{commentary}</li>
          <li><b>背景</b>：{background}</li>
          <li><b>说明</b>：本页为个人学习笔记，非出版级注释。凡标 🟧 处，请当作推论而非教义。</li>
        </ul>
      </section>
""".format(cid=ctx.cid, commentary=d.get("commentary", "本页观点为一般注释传统的转述，不逐句引用单一注释书；涉及分歧处标 🟨 并列。"),
           background=d.get("background", "历史、地理、风俗均为一般性描述，不作年代换算。"))


TOC = [
    ("before", "00", "读前准备"), ("bg", "01", "章节背景"), ("overview", "02", "章节概述"),
    ("map", "03", "思维导图"), ("reading", "04", "分段精读"), ("key", "05", "重点经文"),
    ("theology", "06", "神学要点"), ("prayer", "07", "祷告"), ("apply", "08", "生活应用"),
    ("tasks", "09", "本章任务"), ("review", "10", "复习与预告"), ("refs", "附", "资料来源"),
]


def render(ctx, d):
    minute = d.get("minutes") or 30
    d["_minutes"] = minute
    segs_html = [seg_html(ctx, i, s) for i, s in enumerate(d.get("segs") or [])]
    golden = ctx.vtext(ctx.parse_ref(d.get("golden"), "golden"))

    toc = "".join('<li><a href="#%s"><span class="n">%s</span>%s</a></li>\n        ' % (sid, num, lab)
                  for sid, num, lab in TOC)
    meta_desc = d.get("desc") or ("%s第%d章精读：%s" % (ctx.name, ctx.chapter, d.get("thesis", "")))
    body = "".join([
        sec_before(ctx, d.get("before") or {}),
        sec_bg(ctx, d.get("bg") or {}),
        sec_overview(ctx, d.get("overview") or {}),
        sec_map(ctx, d.get("map") or {}),
        sec_reading(ctx, d.get("reading") or {}, segs_html),
        sec_key(ctx, d.get("key") or []),
        sec_theology(ctx, d.get("theology") or {}),
        sec_prayer(ctx, d.get("prayer") or {}),
        sec_apply(ctx, d.get("apply") or {}),
        sec_tasks(ctx, d.get("tasks") or {}),
        sec_review(ctx, d.get("review") or {}),
        sec_refs(ctx, d.get("refs") or {}),
    ])
    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} 第{ch}章 · 圣经精读笔记</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="../assets/style.css">
<script>try{{var t=localStorage.getItem('bible.theme');if(t)document.documentElement.dataset.theme=JSON.parse(t);}}catch(e){{}}</script>
</head>
<body data-chapter="{cid}" data-verses="{nv}">
<div id="readbar"></div>

<header class="topbar">
  <a class="brand" href="../index.html">圣经<span>·</span>精读</a>
  <span class="spacer"></span>
  <a href="../people.html">人物总表</a>
  <a href="../index.html">总目录</a>
  <button class="iconbtn no-print" id="themeBtn">深色</button>
  <button class="iconbtn no-print" id="doneBtn">标记本章完成</button>
</header>

<div class="wrap">

  <div class="hero">
    <div class="crumb">{testament} <span class="dot"></span> {name} <span class="dot"></span> 第 {ch} 章</div>
    <div class="hero-title">
      <h1><span class="book">{en}</span>{name} <span class="num">{ch_cn}</span></h1>
      <div class="hero-num">{ch}</div>
    </div>
    <p class="thesis">{thesis}</p>
    <div class="meta">
      <span>共 <b>{nv}</b> 节</span>
      <span>精读约 <b>{minute}</b> 分钟</span>
      <span><b>{nseg}</b> 个段落</span>
      <span>文体 <b>{genre}</b></span>
      <span>和合本</span>
    </div>
    <div class="golden">
      <span class="lab">金 句</span>
      <div>
        <p>{golden}</p>
        <cite>{name} {ch}:{golden_ref} · 和合本</cite>
      </div>
    </div>
  </div>

  <div class="layout">

    <nav class="toc-rail no-print">
      <div class="toc-title">目 录</div>
      <ol>
        {toc}
      </ol>
    </nav>

    <main>
{body}
      <footer>
        <div class="frow">
          <span><b>{name} {ch} 章</b> · 共 {nv} 节 · {nseg} 个段落</span>
          <span>笔记版本 v1.0</span>
          <span>和合本经文，仅供个人研读</span>
        </div>
        <div class="frow print-hide">
          <a href="../index.html">← 返回总目录</a>
          <a href="../people.html">人物总表 →</a>
        </div>
      </footer>

    </main>
  </div>
</div>

<script src="../assets/people.js"></script>
<script src="../assets/app.js"></script>
</body>
</html>
""".format(name=ctx.name, en=ctx.en, ch=ctx.chapter, ch_cn=cn_num(ctx.chapter), cid=ctx.cid,
           nv=ctx.nverses, minute=minute, nseg=len(d.get("segs") or []),
           genre=d.get("genre", "叙事"), thesis=d.get("thesis", ""),
           desc=meta_desc.replace('"', "“"), golden=golden,
           golden_ref=d.get("golden", "").split(":")[-1],
           testament="新约" if ctx.nt else "旧约", toc=toc, body=body)


# ---------------------------------------------------------------- validate

def validate(ctx, d):
    """字段级校验。返回 (errors, warnings)。"""
    err, warn = [], []

    def need(cond, msg):
        if not cond:
            err.append(msg)

    for k in ("thesis", "genre", "golden", "minutes"):
        need(d.get(k), "缺字段 %s" % k)

    before = d.get("before") or {}
    need(before.get("lead"), "before.lead 缺")
    rows = before.get("rows") or []
    need(3 <= len(rows) <= 4 and all(len(r) >= 2 and r[0] and r[1] for r in rows),
         "before.rows 需 3–4 行，每行 [观察问题, 留意]")
    pos = before.get("position") or []
    need(len(pos) >= 3, "before.position 至少 3 条（建议 <b>小标题</b>：说明）")

    bg = d.get("bg") or {}
    for lab in BG_LABELS:
        need(bg.get(lab), "bg.%s 缺（五格都要有内容）" % lab)

    ov = d.get("overview") or {}
    need(ov.get("lead"), "overview.lead 缺")
    need(len(ov.get("paras") or []) >= 2, "overview.paras 至少 2 段（最后一段写「一句话概括」）")
    outline = ov.get("outline") or []
    need(5 <= len(outline) <= 8, "overview.outline 需 5–8 行，现在 %d 行" % len(outline))
    for i, r in enumerate(outline):
        need(len(r) == 4 and all(str(c).strip() for c in r), "overview.outline[%d] 应为 4 列 [段落, 经文, 内容, 功能]" % i)

    mp = d.get("map") or {}
    need(mp.get("intro") and mp.get("root"), "map.intro / map.root 缺")
    br = mp.get("branches") or []
    need(3 <= len(br) <= 6, "map.branches 需 3–6 支，现在 %d" % len(br))
    for i, b in enumerate(br):
        need(len(b) == 3 and len(b[2]) >= 2, "map.branches[%d] 应为 [标题, 经节, [[要点, 批注], …]] 且要点≥2" % i)
    need(3 <= len(mp.get("flow") or []) <= 10, "map.flow 需 3–10 个节点")

    segs = d.get("segs") or []
    need(6 <= len(segs) <= 12, "segs 需 6–12 段，现在 %d" % len(segs))
    cover = []
    for i, s in enumerate(segs):
        try:
            cover += ctx.parse_ref(s.get("r"), "segs[%d]" % i)
        except ValueError as e:
            err.append(str(e))
        need(s.get("t"), "segs[%d].t 缺标题" % i)
        need(len(s.get("p") or []) >= 1 and all(str(x).strip() for x in s.get("p") or []),
             "segs[%d].p 缺正文段落" % i)
        need(s.get("kw"), "segs[%d].kw 缺（要 1–3 个原文词/关键词）" % i)
        levels = [nt[0] for nt in (s.get("notes") or []) if nt]
        need("christ" in levels, "segs[%d] 缺 note--christ（每段必须有与基督的关联）" % i)
        for nt in (s.get("notes") or []):
            need(len(nt) == 3 and nt[0] in NOTE_LEVEL, "segs[%d].notes 每项应为 [info|warn|christ, 标题, 正文]" % i)
    if cover:
        want = list(range(1, ctx.nverses + 1))
        if sorted(cover) != want:
            lack = sorted(set(want) - set(cover))
            dup = sorted({n for n in cover if cover.count(n) > 1})
            err.append("segs 的经文范围未严丝合缝覆盖 1–%d：缺 %s%s" % (
                ctx.nverses, lack[:12], ("，重复 %s" % dup[:12]) if dup else ""))

    keys = d.get("key") or []
    need(3 <= len(keys) <= 5, "key 重点经文需 3–5 处，现在 %d" % len(keys))
    for i, k in enumerate(keys):
        try:
            ctx.parse_ref(k.get("r"), "key[%d]" % i)
        except ValueError as e:
            err.append(str(e))
        need(len(k.get("s") or []) == 4 and all(str(x).strip() for x in k.get("s") or []),
             "key[%d].s 需 4 段（上下文/字词/神学/应用）" % i)

    th = d.get("theology") or {}
    for k, lab in (("god", "关于神"), ("man", "关于人"), ("christ", "关于基督")):
        need(th.get(k), "theology.%s 缺（%s）" % (k, lab))

    pr = d.get("prayer") or {}
    need(len(pr.get("p") or []) >= 2, "prayer.p 至少 2 段")

    ap = d.get("apply") or {}
    need(ap.get("act"), "apply.act（本周一个行动）缺")
    scenes = ap.get("scenes") or []
    need(len(scenes) == 3 and all(len(s) == 2 for s in scenes), "apply.scenes 需 3 组 [职场/家庭/教会, 内容]")

    tk = d.get("tasks") or {}
    boxes = sum(len(tk.get(k) or []) for k in "ABCD")
    need(8 <= boxes <= 12, "tasks 复选框需 8–12 项，现在 %d（A/B/C/D 四组都要有）" % boxes)
    for k in "ABCD":
        need(tk.get(k), "tasks.%s 缺" % k)

    rv = d.get("review") or {}
    need(len(rv.get("q") or []) == 3 and all(len(q) == 2 for q in rv.get("q") or []), "review.q 需 3 组 [问, 答]")
    try:
        ctx.parse_ref(rv.get("mem"), "review.mem")
    except ValueError as e:
        err.append(str(e))
    for k in ("how", "next", "nextText"):
        need(rv.get(k), "review.%s 缺" % k)

    return err, warn


def budget_report(sections):
    """按 check_note 的算法复核每节 CJK 字数。"""
    out = []
    total = 0
    for sid in SECTIONS:
        n = cjk(strip_tags(sections.get(sid, "")))
        total += n
        lo, hi = BUDGET[sid]
        if n < lo:
            out.append((sid, n, lo, hi, "还差 %d 字" % (lo - n)))
        elif n > hi:
            out.append((sid, n, lo, hi, "超 %d 字" % (n - hi)))
    if not (TOTAL_BUDGET[0] <= total <= TOTAL_BUDGET[1]):
        out.append(("总字数", total, TOTAL_BUDGET[0], TOTAL_BUDGET[1], "超出范围"))
    return total, out


def split_sections(html):
    secs = {}
    for m in re.finditer(r'<section\s+id="([^"]+)"[^>]*>', html):
        start = m.end()
        end = html.find("</section>", start)
        secs[m.group(1)] = html[start:end] if end != -1 else html[start:]
    return secs


def build_one(cid, books, dry=False):
    ctx = Ctx(cid, books)
    if not os.path.exists(ctx.src):
        print("✗ %s：缺少内容文件 %s" % (cid, os.path.relpath(ctx.src, ROOT)))
        return False
    try:
        d = json.load(io.open(ctx.src, encoding="utf-8"))
    except Exception as e:
        print("✗ %s：JSON 解析失败：%s" % (cid, e))
        return False
    if d.get("id") != cid:
        print("✗ %s：JSON 里 id=%r，与文件名不符" % (cid, d.get("id")))
        return False

    err, warn = validate(ctx, d)
    if err:
        print("✗ %s 结构错误 %d 处：" % (cid, len(err)))
        for e in err:
            print("    - %s" % e)
        return False

    try:
        html = render(ctx, d)
    except Exception as e:
        print("✗ %s 渲染失败：%s" % (cid, e))
        return False

    # 禁用句式只约束写手正文；经文由 verses 逐字注入，和合本原文可能含这些词
    # （如路 4:25「我对你们说实话」），故先剔除注入的 scripture 区块与 blockquote。
    writer_text = re.sub(r'<div class="scripture">.*?</div>', '', html, flags=re.S)
    writer_text = re.sub(r'<blockquote>.*?</blockquote>', '', writer_text, flags=re.S)
    hits = [w for w in FORBIDDEN if w in writer_text]
    if hits:
        print("✗ %s 出现禁用句式：%s" % (cid, "、".join(hits)))
        return False
    ph = [w for w in PLACEHOLDERS if w in html]
    if ph:
        print("✗ %s 出现占位符：%s" % (cid, ph))
        return False

    total, bad = budget_report(split_sections(html))
    out_path = os.path.join(ctx.dir, "%s.html" % cid)
    if not dry:
        os.makedirs(ctx.dir, exist_ok=True)
        io.open(out_path, "w", encoding="utf-8", newline="\n").write(html)

    if bad:
        print("△ %s 已生成（%d 字），但有 %d 处字数不合规：" % (cid, total, len(bad)))
        for sid, n, lo, hi, msg in bad:
            print("    %-8s %5d 字（预算 %d–%d）%s" % (sid, n, lo, hi, msg))
        return False
    print("✓ %s 通过（%d 字，%d 段）%s" % (cid, total, len(d.get("segs") or []),
                                       "" if dry else "→ %s" % os.path.relpath(out_path, ROOT)))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--book")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    books = load_books()
    ids = list(args.ids)
    if args.book:
        src_dir = os.path.join(ROOT, book_dir(args.book), "_src")
        if not os.path.isdir(src_dir):
            print("没有内容目录：%s" % src_dir)
            return 1
        ids += [os.path.splitext(n)[0] for n in sorted(os.listdir(src_dir)) if n.endswith(".json")]
    if not ids:
        print("用法：py scripts\\build.py <id>… 或 --book <书卷代码>")
        return 1

    ok = 0
    for cid in ids:
        if build_one(cid, books, args.dry):
            ok += 1
    print("\n合计：%d/%d 通过" % (ok, len(ids)))
    return 0 if ok == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())
