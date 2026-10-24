# -*- coding: utf-8 -*-
"""内容体检：核对正文引文与「下一章预告」引文是否与和合本一致。

用法：
    py scripts\\qa_check.py                 # 查全书
    py scripts\\qa_check.py isa-11 isa-17   # 只查指定章节

两类检查：
  1. 带出处的引文：形如 「引文」（赛 47:2）
     → 到 verses/<书卷>-<章>.json 里查该节，逐字比对
  2. 「下一章预告」段落里的引文
     → 到目标章的经文里比对（目标章从预告标题的章号取）

退出码：0 = 没有对不上的引文；1 = 有（需要修）。
报告写入 logs\\qa_report.txt。
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import chapter_file, scan_chapters

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "logs", "qa_report.txt")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BOOKS = {
    "创": "gen", "出": "exo", "利": "lev", "民": "num", "申": "deu",
    "书": "jos", "士": "jdg", "得": "rut", "撒上": "1sa", "撒下": "2sa",
    "王上": "1ki", "王下": "2ki", "代上": "1ch", "代下": "2ch",
    "拉": "ezr", "尼": "neh", "斯": "est", "约": "job", "诗": "psa",
    "箴": "pro", "传": "ecc", "歌": "sng", "赛": "isa", "耶": "jer",
    "哀": "lam", "结": "ezk", "但": "dan", "何": "hos", "珥": "jol",
    "摩": "amo", "俄": "oba", "拿": "jon", "弥": "mic", "鸿": "nam",
    "哈": "hab", "番": "zep", "该": "hag", "亚": "zec", "玛": "mal",
    "太": "mat", "可": "mark", "路": "luk", "约": "jhn", "徒": "act",
    "罗": "rom", "林前": "1co", "林后": "2co", "加": "gal", "弗": "eph",
    "腓": "php", "西": "col", "帖前": "1th", "帖后": "2th", "提前": "1ti",
    "提后": "2ti", "多": "tit", "门": "phm", "来": "heb", "希": "heb",
    "雅": "jas", "彼前": "1pe", "彼后": "2pe", "约一": "1jn",
    "约二": "2jn", "约三": "3jn", "犹": "jud", "启": "rev",
}

CITE = re.compile(r"「([^」]{3,80})」\s*[（(]\s*([^（）()]{1,40}?)\s*[）)]")
PREVIEW_H = re.compile(r'<h3>下一章预告[^<]*</h3>')
VERSE_REF = re.compile(r"(\d{1,3})\s*章")


def norm(t):
    t = re.sub(r"[〔〕]", "", t)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", t)


_vcache = {}

_corpus = None


def corpus_text():
    """全库经文拼成一个大串，用于「预告里引了别卷经文」的兜底核对。"""
    global _corpus
    if _corpus is None:
        parts = []
        try:
            for name in os.listdir(os.path.join(ROOT, "verses")):
                if not name.endswith(".json"):
                    continue
                d = json.load(io.open(os.path.join(ROOT, "verses", name), encoding="utf-8"))
                for v in d.get("verses", []):
                    parts.append(v.get("text", ""))
        except Exception:
            pass
        _corpus = norm("".join(parts))
    return _corpus


def in_corpus(quote):
    return norm(quote) in corpus_text()


def chapter_text(book, ch):
    key = (book, ch)
    if key in _vcache:
        return _vcache[key]
    p = os.path.join(ROOT, "verses", "%s-%02d.json" % (book, ch))
    txt = None
    if os.path.exists(p):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
            txt = "".join(v["text"] for v in d["verses"])
        except Exception:
            txt = None
    _vcache[key] = txt
    return txt


def has_file(book, ch):
    return os.path.exists(os.path.join(ROOT, "verses", "%s-%02d.json" % (book, ch)))


def parse_ref(ref, self_book=None, self_ch=None):
    """解析出处，支持「赛 47:2」「约 1:1、14」「徒 3:18、21–22」「创 10:11-12」。

    也支持省略书卷名的「18:18」「18:1-3」——那是本章的经节；
    若是别章（如在赛 21 章里写「22:9–11」），由 check_cite 另行尝试。

    返回 (book, ch, [(v1, v2), ...])；解析不出来返回 None。
    """
    ref = ref.strip()
    m = re.match(r"^([\u4e00-\u9fff]{1,4})\s*(\d{1,3})\s*[:：]\s*(.+)$", ref)
    if m:
        name, ch, rest = m.group(1), int(m.group(2)), m.group(3)
        book = BOOKS.get(name)
        if not book:
            return None
    else:
        # 章内自引：18:18 / 18:1-3
        m2 = re.match(r"^(\d{1,3})\s*[:：]\s*(.+)$", ref)
        if not m2 or not self_book or not self_ch:
            return None
        book, ch, rest = self_book, self_ch, m2.group(2)
    ranges = []
    for part in re.split(r"[、,，;；]", rest):
        part = part.strip()
        if not part:
            continue
        vm = re.match(r"^(\d{1,3})(?:\s*[-–—~]\s*(\d{1,3}))?$", part)
        if not vm:
            return None
        v1 = int(vm.group(1))
        v2 = int(vm.group(2)) if vm.group(2) else v1
        ranges.append((v1, v2))
    if not ranges:
        return None
    return book, ch, ranges


def _match(quote, book, ch, ranges, ch_verses):
    """把引文与某书某章的经节比对：True 相符 / False 不符 / None 无法核对。"""
    if not has_file(book, ch):
        return None
    verses = []
    for v1, v2 in ranges:
        if v2 - v1 > 8:
            return None
        verses.extend(range(v1, v2 + 1))
    qn = norm(quote)
    if not qn:
        return None
    texts = [ch_verses(book, ch, n) for n in verses]
    # 1. 整段落在某一节里
    for t in texts:
        if t and qn in norm(t):
            return True
    # 2. 允许用「……」省略中间部分：逐段比对
    frags = [f for f in re.split(r"…+", quote) if len(norm(f)) >= 4]
    if len(frags) > 1:
        for f in frags:
            if not any(t and norm(f) in norm(t) for t in texts):
                break
        else:
            return True
    # 3. 跨节连读：去掉标点后仍能对上
    alt = norm(re.sub(r"[，、；：]…—\s]", "", quote))
    for t in texts:
        if t and alt and alt in norm(t):
            return True
    return False


def check_cite(quote, ref, ch_verses, self_book=None, self_ch=None):
    """返回 True 表示相符 / False 表示不符 / None 表示无法核对。

    省略书卷名的出处先按本章解释；本章对不上时，再按「同一卷的该章」试一次
    （例如在赛 21 章里写「22:9–11」，指的是赛 22 章）。
    """
    pr = parse_ref(ref, self_book, self_ch)
    if not pr:
        return None
    book, ch, ranges = pr
    cands = [(book, ch)]
    m2 = re.match(r"^\s*(\d{1,3})\s*[:：]", ref.strip())
    if m2 and self_book:
        alt_ch = int(m2.group(1))
        if alt_ch != ch:
            cands.append((self_book, alt_ch))
    seen = False
    for bk, cc in cands:
        r = _match(quote, bk, cc, ranges, ch_verses)
        if r is True:
            return True
        if r is False:
            seen = True
    return False if seen else None


def verse_text(book, ch, n):
    key = (book, ch, n)
    if key in _vcache:
        return _vcache[key]
    p = os.path.join(ROOT, "verses", "%s-%02d.json" % (book, ch))
    txt = None
    if os.path.exists(p):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
            for v in d["verses"]:
                if v["n"] == n:
                    txt = v["text"]
                    break
        except Exception:
            pass
    _vcache[key] = txt
    return txt


def run(ids):
    bad = []
    skip = []
    total = 0
    for cid in ids:
        p = chapter_file(cid)
        if not os.path.exists(p):
            continue
        h = io.open(p, encoding="utf-8").read()
        body = re.sub(r'<section id="refs".*?</section>', "", h, flags=re.S)

        # 1. 带出处的引文
        cid_book = cid.rsplit("-", 1)[0]
        cid_ch = int(cid.rsplit("-", 1)[1])
        for quote, ref in CITE.findall(body):
            r = check_cite(quote, ref, verse_text, cid_book, cid_ch)
            if r is None:
                skip.append("%s  「%s」（%s）→ 出处解析不了或无经文文件" % (cid, quote[:36], ref))
                continue
            total += 1
            if r is False:
                bad.append("%s  【引文不符】「%s」（%s）" % (cid, quote[:40], ref))

        # 2. 下一章预告
        m = PREVIEW_H.search(h)
        if not m:
            continue
        tail = h[m.end():]
        pm = re.search(r'<p class="prose">(.*?)</p>', tail, re.S)
        if not pm:
            continue
        nm = VERSE_REF.search(m.group(0))
        if not nm:
            continue
        try:
            nxt = int(nm.group(1))
        except ValueError:
            continue
        tgt_book = cid.rsplit("-", 1)[0]
        txt = re.sub(r"<[^>]+>", "", pm.group(1))
        for quote in re.findall(r"「([^」]{4,})」", txt):
            if not re.match(r"^[A-Za-z0-9\s:]+$", quote):
                total += 1
                t = chapter_text(tgt_book, nxt)
                ctext = chapter_text(cid.rsplit("-", 1)[0], int(cid.rsplit("-", 1)[1]))
                if t and norm(quote) in norm(t):
                    continue
                if ctext and norm(quote) in norm(ctext):
                    continue
                frags = [f for f in re.split(r"…+", quote) if len(norm(f)) >= 4]
                if frags and t and all(norm(f) in norm(t) for f in frags):
                    continue
                if frags and ctext and all(norm(f) in norm(ctext) for f in frags):
                    continue
                # 预告里常引用下一卷（甚至别卷）的经文：全库再找一次
                if in_corpus(quote) or (frags and all(in_corpus(f) for f in frags)):
                    continue
                bad.append("%s  【预告引文不符】「%s」→ %s-%02d" % (cid, quote[:40], tgt_book, nxt))

        # 3. 重点经文 blockquote 与「本周背诵」必须逐字出自本章经文
        full = chapter_text(cid_book, cid_ch)
        if full:
            nf = norm(full)
            for bq in re.findall(r"<blockquote>(.*?)</blockquote>", body, re.S):
                q = norm(re.sub(r"<[^>]+>", "", bq))
                if len(q) < 4:
                    continue
                total += 1
                # 允许用「……」省略中间部分：逐段比对
                frags = [f for f in re.split(r"…+", re.sub(r"<[^>]+>", "", bq)) if len(norm(f)) >= 4]
                if frags and all(norm(f) in nf for f in frags):
                    continue
                if q in nf:
                    continue
                bad.append("%s  【重点经文非本章原文】「%s」" % (cid, q[:44]))
            # 本周背诵（review 段里的 scripture）
            rv = re.search(r'<section id="review".*?</section>', body, re.S)
            if rv:
                for sc in re.findall(r'<div class="scripture">(.*?)</div>', rv.group(0), re.S):
                    txt = re.sub(r"<sup>\s*\d+\s*</sup>", "", sc)
                    q = norm(re.sub(r"<[^>]+>", "", txt))
                    if len(q) < 4:
                        continue
                    total += 1
                    if q not in nf:
                        bad.append("%s  【背诵段非本章原文】「%s」" % (cid, q[:44]))

    out = []
    for b in bad:
        out.append(b)
    if skip:
        out.append("")
        out.append("—— 无法核对的引文（出处解析不了或没有经文文件）——")
        for b in skip:
            out.append(b)
    out.append("")
    out.append("核对 %d 条引文：%d 条不符，%d 条无法核对" % (total, len(bad), len(skip)))
    # 报告文件名带上章节号与进程号，避免多个写手同时跑时互相覆盖
    tag = "_".join(i.replace("-", "") for i in ids[:4]) if ids else "all"
    path = os.path.join(ROOT, "logs", "qa_report_%s_%d.txt" % (tag, os.getpid()))
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    except Exception:
        pass
    print("核对 %d 条引文：%d 条不符，%d 条无法核对（详见 %s）"
          % (total, len(bad), len(skip), os.path.basename(path)))
    return 1 if bad else 0
    return len(bad)


def main():
    ids = sys.argv[1:]
    if not ids:
        ids = scan_chapters()
    return 1 if run(ids) else 0


if __name__ == "__main__":
    sys.exit(main())
