#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_note.py — 圣经精读笔记的机械校验。

用法：
  python check_note.py mark-02.html
  python check_note.py mark-02.html --report
  python check_note.py mark-02.html --json

退出码：0 = 无 P0 失败；1 = 有 P0 失败；2 = 文件/参数错误。
P1 只提示，不阻断。
"""

import argparse
import json
import os
import re
import sys

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

FORBIDDEN = [
    "神今天对你说", "主要你", "神绝不会让你", "只要相信就一定会",
    "家人们", "宝子们", "绝绝子", "不得不说", "说实话",
]

PLACEHOLDERS = ["TODO", "待补充", "Lorem", "XXX", "{{", "}}", "??"]


def cjk(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def strip_tags(text):
    text = re.sub(r"<script\b.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, code, ok, msg, loc=""):
        self.items.append({"level": level, "code": code, "ok": ok, "msg": msg, "loc": loc})

    def count(self, level, ok=None):
        return sum(1 for i in self.items if i["level"] == level and (ok is None or i["ok"] == ok))

    def failed_p0(self):
        return [i for i in self.items if i["level"] == "P0" and not i["ok"]]

    def render(self, name):
        p0f = self.count("P0", False)
        lines = []
        lines.append("%s  %s" % ("PASS" if p0f == 0 else "FAIL", name))
        lines.append("P0 %d/%d 通过   P1 %d 提示   P2 %d 提示" % (
            self.count("P0", True), self.count("P0"),
            self.count("P1", False), self.count("P2", False)))
        lines.append("")
        for level in ("P0", "P1", "P2"):
            group = [i for i in self.items if i["level"] == level and not i["ok"]]
            if not group:
                continue
            lines.append("【%s】" % level)
            for i in group:
                loc = (" @ " + i["loc"]) if i["loc"] else ""
                lines.append("  ✗ %s  %s%s" % (i["code"], i["msg"], loc))
            lines.append("")
        passed = [i for i in self.items if i["ok"]]
        if passed:
            lines.append("通过项：%s" % " ".join(i["code"] for i in passed))
        return "\n".join(lines)


def split_sections(html):
    secs = {}
    order = []
    for m in re.finditer(r'<section\s+id="([^"]+)"[^>]*>', html):
        sid = m.group(1)
        start = m.end()
        end = html.find("</section>", start)
        secs[sid] = html[start:end] if end != -1 else html[start:]
        order.append(sid)
    return secs, order


def get_attr(tag, name):
    m = re.search(r'%s="([^"]*)"' % re.escape(name), tag)
    return m.group(1) if m else None


def load_people(note_path):
    path = os.path.join(os.path.dirname(note_path) or ".", "assets", "people.js")
    if not os.path.exists(path):
        return None, "找不到 assets/people.js"
    raw = open(path, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    if i == -1 or j == -1:
        return None, "people.js 里找不到数组"
    try:
        return json.loads(raw[i:j + 1]), None
    except Exception as e:
        return None, "people.js 不是合法 JSON 兼容格式：%s" % e


def normalize_verse(text):
    text = re.sub(r"〔[^〕]*〕", "", text)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("note")
    ap.add_argument("--report", action="store_true", help="把报告写入 reviews/<id>.txt")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    path = args.note
    if not os.path.exists(path):
        print("找不到文件：%s" % path, file=sys.stderr)
        return 2
    html = open(path, encoding="utf-8").read()
    stem = os.path.splitext(os.path.basename(path))[0]
    r = Report()

    # ---------- A01 结构与顺序 ----------
    secs, order = split_sections(html)
    if html.count("<section") != html.count("</section>"):
        r.add("P0", "A01", False, "section 开闭标签数量不一致（%d 开 / %d 闭）" % (html.count("<section"), html.count("</section>")))
    missing = [s for s in SECTIONS if s not in secs]
    extra = [s for s in order if s not in SECTIONS]
    if missing:
        r.add("P0", "A01", False, "缺少 section：%s" % ", ".join(missing))
    if extra:
        r.add("P0", "A01", False, "多出未定义 section：%s" % ", ".join(extra))
    if not missing and order != SECTIONS:
        r.add("P0", "A01", False, "section 顺序不对：%s" % " → ".join(order))
    if not missing and not extra and order == SECTIONS:
        r.add("P0", "A01", True, "11 个 section 齐全且顺序正确")

    # ---------- A02/A03 body 属性 ----------
    body_tag = re.search(r"<body[^>]*>", html)
    if not body_tag:
        r.add("P0", "A02", False, "没有 <body> 标签")
        cid, nverses = None, None
    else:
        tag = body_tag.group(0)
        cid = get_attr(tag, "data-chapter")
        nv = get_attr(tag, "data-verses")
        if cid != stem:
            r.add("P0", "A02", False, "data-chapter=%r，文件名是 %r" % (cid, stem))
        else:
            r.add("P0", "A02", True, "data-chapter 与文件名一致")
        try:
            nverses = int(nv) if nv else None
        except ValueError:
            nverses = None
        if not nverses:
            r.add("P0", "A03", False, "body 缺少 data-verses 或不是整数")
        else:
            r.add("P0", "A03", True, "本章 %d 节" % nverses)

    # ---------- A04 逐节覆盖 ----------
    reading = secs.get("reading", "")
    segs = re.findall(r'<article class="seg">(.*?)</article>', reading, re.S)
    if not segs:
        segs = re.findall(r'<article class="seg[^"]*">(.*?)</article>', reading, re.S)
    verse_map = {}
    for idx, seg in enumerate(segs, 1):
        blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
        for block in blocks:
            for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
                n = int(m.group(1))
                txt = strip_tags(m.group(2)).strip()
                verse_map.setdefault(n, []).append((idx, txt))

    if nverses:
        have = set(verse_map)
        want = set(range(1, nverses + 1))
        lack = sorted(want - have)
        over = sorted(have - want)
        if lack:
            r.add("P0", "A04", False, "缺 %d 节：%s" % (len(lack), lack[:15]))
        if over:
            r.add("P0", "A04", False, "出现超出范围的节号：%s" % over[:15])
        dup = sorted(n for n, v in verse_map.items() if len(v) > 1)
        if dup:
            r.add("P0", "A04", False, "重复的节号：%s" % dup[:15])
        if not lack and not over and not dup:
            r.add("P0", "A04", True, "1–%d 每节恰好出现一次" % nverses)

    # ---------- A05/A06 分段完整性 ----------
    if 6 <= len(segs) <= 12:
        r.add("P0", "A05", True, "%d 个分段（6–12）" % len(segs))
    else:
        r.add("P0", "A05", False, "分段数 %d，应在 6–12（少了是没分段，多了是按节切）" % len(segs))

    bad_seg = []
    for idx, seg in enumerate(segs, 1):
        need = {
            "scripture": '<div class="scripture">',
            "body": '<div class="body">',
        }
        miss = [k for k, v in need.items() if v not in seg]
        if not re.search(r'<div class="kw"', seg):
            miss.append("kw")
        if not re.search(r'<div class="note note--christ"', seg):
            miss.append("note--christ")
        if miss:
            bad_seg.append("SEG%02d 缺 %s" % (idx, "/".join(miss)))
    if bad_seg:
        r.add("P0", "A06", False, "；".join(bad_seg[:6]))
    else:
        r.add("P0", "A06", True, "每个 seg 组件完整")

    # ---------- A07 重点经文 ----------
    key = secs.get("key", "")
    kvs = re.findall(r'<div class="kv">(.*?)</ol>', key, re.S)
    if 3 <= len(kvs) <= 5:
        r.add("P0", "A07", True, "%d 处重点经文（3–5）" % len(kvs))
    else:
        r.add("P0", "A07", False, "重点经文 %d 处，应为 3–5" % len(kvs))
    ok_steps = True
    for i, kv in enumerate(kvs, 1):
        labels = re.findall(r"<li><b>(.*?)</b>", kv)
        want = ["上下文", "字词", "神学", "应用"]
        if labels[:4] != want:
            r.add("P0", "A07", False, "第 %d 处四步标签是 %s，应为 %s" % (i, labels[:4], want))
            ok_steps = False
            break
    if kvs and ok_steps:
        r.add("P0", "A07b", True, "每处四步标签正确")

    # ---------- A08 背景五格 ----------
    bg = secs.get("bg", "")
    cells = re.findall(r'<div class="bg-cell">(.*?)</div>\s*</div>', bg, re.S)
    if len(cells) != 5:
        cells = re.findall(r'<div class="bg-cell">', bg)
        labels = re.findall(r"<h4>(.*?)</h4>", bg)
    else:
        labels = [strip_tags(re.search(r"<h4>(.*?)</h4>", c, re.S).group(1)).strip() for c in cells if re.search(r"<h4>", c)]
    want = ["历史", "地理", "文化", "文学", "救赎史"]
    if len(re.findall(r'<div class="bg-cell">', bg)) == 5 and labels[:5] == want:
        r.add("P0", "A08", True, "背景五格齐全")
    else:
        r.add("P0", "A08", False, "背景格数 %d，标签 %s（应为 %s）" % (len(re.findall(r'<div class="bg-cell">', bg)), labels[:5], want))

    # ---------- A09 任务 ----------
    tasks = secs.get("tasks", "")
    boxes = len(re.findall(r'type="checkbox"', tasks))
    groups = len(re.findall(r'class="taskgroup"', tasks))
    if 8 <= boxes <= 12 and groups == 4:
        r.add("P0", "A09", True, "%d 项任务 / 4 组" % boxes)
    else:
        r.add("P0", "A09", False, "任务 %d 项、%d 组（应为 8–12 项 / 4 组）" % (boxes, groups))

    # ---------- A10 复习 ----------
    review = secs.get("review", "")
    details = len(re.findall(r"<details", review))
    if details == 3:
        r.add("P0", "A10", True, "3 道自测")
    else:
        r.add("P0", "A10", False, "自测 details 有 %d 个，应为 3" % details)

    # ---------- A11 资料来源 ----------
    refs = secs.get("refs", "")
    tbl = re.search(r'<table class="tbl">(.*?)</table>', refs, re.S)
    rows = len(re.findall(r"<tr>", tbl.group(1))) - 1 if tbl else 0
    lis = len(re.findall(r"<li>", refs))
    if rows == 3 and lis >= 4:
        r.add("P0", "A11", True, "三级标注 3 行 + 参考 %d 条" % lis)
    else:
        r.add("P0", "A11", False, "标注表 %d 行、参考 %d 条（应为 3 行 / ≥4 条）" % (rows, lis))

    # ---------- A12 占位符 ----------
    hit = [p for p in PLACEHOLDERS if p in html]
    if hit:
        r.add("P0", "A12", False, "存在占位符：%s" % hit)
    else:
        r.add("P0", "A12", True, "无占位符")

    # ---------- A13/A14 链接与外部依赖 ----------
    base = os.path.dirname(os.path.abspath(path))
    broken = []
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("#", "http://", "https://", "mailto:", "javascript:")):
            continue
        target = href.split("#")[0].split("?")[0]
        if target and not os.path.exists(os.path.join(base, target)):
            broken.append(href)
    if broken:
        r.add("P0", "A13", False, "本地链接不存在：%s" % broken[:8])
    else:
        r.add("P0", "A13", True, "本地链接有效")

    ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    ext += re.findall(r'url\(\s*["\']?(https?://[^)]+)', html)
    if ext:
        r.add("P0", "A14", False, "存在外部依赖：%s" % ext[:5])
    else:
        r.add("P0", "A14", True, "零外部依赖")

    # ---------- A15–A18 人物 ----------
    people, err = load_people(path)
    if people is None:
        r.add("P0", "A15", False, err)
    else:
        r.add("P0", "A15", True, "people.js 可解析（%d 人）" % len(people))
        ids = [p.get("id") for p in people]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            r.add("P0", "A16", False, "重复 id：%s" % dup)
        else:
            r.add("P0", "A16", True, "人物 id 唯一")
        stars = [p for p in people if p.get("star") == 1 and cid in p.get("chapters", [])]
        if len(stars) == 3:
            r.add("P0", "A17", True, "本章 ★★★ 恰好 3 位：%s" % "、".join(p["name"] for p in stars))
        else:
            r.add("P0", "A17", False, "本章 ★★★ 有 %d 位（应为 3）：%s" % (len(stars), "、".join(p["name"] for p in stars)))
        notag = [p.get("name") for p in people if cid in p.get("chapters", []) and not p.get("avoid")]
        if notag:
            r.add("P1", "A18", False, "本章人物缺 avoid 消歧说明：%s" % notag[:5])
        else:
            r.add("P0", "A18", True, "本章人物均标注了消歧信息")

    # ---------- A19/A27 字数 ----------
    total = cjk(strip_tags(html))
    if TOTAL_BUDGET[0] <= total <= TOTAL_BUDGET[1]:
        r.add("P0", "A19", True, "全章 %d 字（%d–%d）" % (total, TOTAL_BUDGET[0], TOTAL_BUDGET[1]))
    else:
        r.add("P1", "A19", False, "全章 %d 字，超出 %d–%d" % (total, TOTAL_BUDGET[0], TOTAL_BUDGET[1]))
    for sid in SECTIONS:
        if sid not in secs:
            continue
        n = cjk(strip_tags(secs[sid]))
        lo, hi = BUDGET[sid]
        if not (lo <= n <= hi):
            r.add("P1", "A27", False, "%s %d 字，预算 %d–%d" % (sid, n, lo, hi))

    # ---------- A20 经文逐字核对 ----------
    vfile = os.path.join(base, "verses", "%s.json" % stem)
    if nverses and os.path.exists(vfile):
        try:
            vdata = json.load(open(vfile, encoding="utf-8"))
            remote = {v["n"]: v["text"] for v in vdata["verses"]}
            bad = []
            for n, txt in remote.items():
                local = verse_map.get(n)
                if not local:
                    continue
                if normalize_verse(local[0][1]) != normalize_verse(txt):
                    bad.append(n)
            if bad:
                r.add("P0", "A20", False, "与 verses/%s.json 不一致的节：%s" % (stem, bad[:12]))
            else:
                r.add("P0", "A20", True, "经文与 verses/%s.json 逐字一致" % stem)
        except Exception as e:
            r.add("P1", "A20", False, "读取 verses 失败：%s" % e)
    elif nverses:
        r.add("P1", "A20", False, "缺少 verses/%s.json，无法逐字核对经文" % stem)

    # ---------- A21 封面 ----------
    hero = re.search(r'<div class="hero">(.*?)</div>\s*<div class="layout">', html, re.S)
    hero_html = hero.group(1) if hero else ""
    hero_ok = all([
        "<h1>" in hero_html,
        'class="thesis"' in hero_html,
        'class="golden"' in hero_html,
        len(re.findall(r'class="meta"', hero_html)) == 1,
        len(re.findall(r"<span>", re.search(r'<div class="meta">(.*?)</div>', hero_html, re.S).group(1) if re.search(r'<div class="meta">(.*?)</div>', hero_html, re.S) else "")) >= 5,
    ])
    if hero_ok:
        r.add("P0", "A21", True, "封面元素齐全")
    else:
        r.add("P0", "A21", False, "封面缺 h1 / thesis / meta(≥5) / golden 之一")

    # ---------- A22 目录 ----------
    toc = re.findall(r'<nav class="toc-rail.*?</nav>', html, re.S)
    anchors = re.findall(r'href="#([^"]+)"', toc[0]) if toc else []
    if anchors == SECTIONS:
        r.add("P1", "A22", True, "目录 12 条与 section 对应")
    else:
        r.add("P1", "A22", False, "目录条目与 section 不一致：%s" % anchors)

    # ---------- A23 三级标注 ----------
    notes = re.findall(r'<div class="note([^"]*)">(.*?)</div>', html, re.S)
    tag_bad = []
    for cls, inner in notes:
        emoji = re.findall(r"[🟦🟨🟧]", inner)
        if len(emoji) != 1:
            tag_bad.append("标签数 %d" % len(emoji))
            continue
        want = {"note--info": "🟦", "note--warn": "🟨", "note--christ": "🟧"}.get(cls.strip())
        if want and emoji[0] != want:
            tag_bad.append("%s 用了 %s" % (cls.strip(), emoji[0]))
    if tag_bad:
        r.add("P0", "A23", False, "note 标注不规范：%s" % tag_bad[:6])
    else:
        r.add("P0", "A23", True, "%d 条 note 均带且仅带一个正确标注" % len(notes))

    # ---------- A24 禁用句式 ----------
    fh = [w for w in FORBIDDEN if w in html]
    if fh:
        r.add("P0", "A24", False, "出现禁用句式：%s" % fh)
    else:
        r.add("P0", "A24", True, "无禁用句式")

    # ---------- A25/A26 概述表与导图 ----------
    overview = secs.get("overview", "")
    otbl = re.search(r'<table class="tbl">(.*?)</table>', overview, re.S)
    orows = len(re.findall(r"<tr>", otbl.group(1))) - 1 if otbl else 0
    if 5 <= orows <= 8:
        r.add("P1", "A25", True, "结构大纲 %d 行" % orows)
    else:
        r.add("P1", "A25", False, "结构大纲 %d 行，应为 5–8" % orows)

    mapsec = secs.get("map", "")
    branches = len(re.findall(r"<li><b>", mapsec))
    pills = len(re.findall(r'class="pill"', mapsec))
    if 3 <= branches <= 6 and 3 <= pills <= 10:
        r.add("P1", "A26", True, "导图 %d 支 / %d 个流程节点" % (branches, pills))
    else:
        r.add("P1", "A26", False, "导图 %d 支、%d 个流程节点（应为 3–6 支 / 3–10 节点）" % (branches, pills))

    # ---------- A28 本章人物容器 ----------
    m = re.search(r'<div[^>]*id="chapterPeople"[^>]*>', html)
    if m and get_attr(m.group(0), "data-chapter") == cid:
        r.add("P1", "A28", True, "chapterPeople 数据绑定正确")
    else:
        r.add("P1", "A28", False, "chapterPeople 缺失或 data-chapter 不匹配")

    output = r.render(os.path.basename(path))
    print(output)

    if args.report:
        os.makedirs(os.path.join(base, "reviews"), exist_ok=True)
        rp = os.path.join(base, "reviews", "%s.txt" % stem)
        with open(rp, "w", encoding="utf-8", newline="\n") as f:
            f.write(output + "\n")
        print("\n报告已写入 %s" % rp)

    if args.json:
        print(json.dumps({"items": r.items, "pass": not r.failed_p0()}, ensure_ascii=False, indent=2))

    return 0 if not r.failed_p0() else 1


if __name__ == "__main__":
    sys.exit(main())
