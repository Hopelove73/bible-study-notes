# -*- coding: utf-8 -*-
"""独立复核：把正文里每一个「」引文逐条到 verses/*.json 里比对。

规则：
  - 引文所属章 = 该 HTML 的章节（除非引文后紧跟「（书 卷:节）」形式的出处）
  - 省略号「……」按片段比对
  - 找不到对应经文文件的引文标记为 SKIP

用法：py scripts\\audit_quotes.py gen-21 gen-26 gen-27 isa-57
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

_cache = {}


def norm(t):
    t = re.sub(r"[〔〕]", "", t)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", t)


def chapter_text(book, ch):
    key = (book, ch)
    if key in _cache:
        return _cache[key]
    p = os.path.join(ROOT, "verses", "%s-%02d.json" % (book, ch))
    txt = None
    if os.path.exists(p):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
            txt = "".join(v["text"] for v in d["verses"])
        except Exception:
            txt = None
    _cache[key] = txt
    return txt


_corpus = None
_corpus_files = 0


def corpus():
    global _corpus, _corpus_files
    if _corpus is None:
        parts = []
        _corpus_files = 0
        for name in sorted(os.listdir(os.path.join(ROOT, "verses"))):
            if not name.endswith(".json"):
                continue
            # 逐个文件单独 try：并发写手正在写 verses 时，坏一个文件不能带累整库
            try:
                d = json.load(io.open(os.path.join(ROOT, "verses", name), encoding="utf-8"))
            except Exception:
                continue
            for v in d.get("verses", []):
                parts.append(v.get("text", ""))
            _corpus_files += 1
        _corpus = norm("".join(parts))
    return _corpus


CITE = re.compile(r"「([^」]{2,90})」\s*(?:[（(]\s*([\u4e00-\u9fff]{1,3})\s*(\d{1,3}):(\d{1,3}(?:[–\-]\d{1,3})?)\s*[）)])?")


def check_quote(q, book, ch):
    """返回 OK / MISMATCH / SKIP。"""
    frags = [f for f in re.split(r"…+", q) if len(norm(f)) >= 2]
    if not frags:
        return "SKIP"
    own = chapter_text(book, ch)
    if own:
        if all(norm(f) in norm(own) for f in frags):
            return "OK"
    else:
        return "SKIP"
    # 退一步：在全书经文里找
    if all(norm(f) in corpus() for f in frags):
        return "OK-ELSEWHERE"
    return "MISMATCH"


def main():
    ids = sys.argv[1:]
    out = []
    for cid in ids:
        path = os.path.join(ROOT, "%s.html" % cid)
        if not os.path.exists(path):
            continue
        h = io.open(path, encoding="utf-8").read()
        body = re.sub(r'<section id="refs".*?</section>', "", h, flags=re.S)
        cb = cid.rsplit("-", 1)[0]
        cn = int(cid.rsplit("-", 1)[1])
        ok = mis = skip = other = 0
        lines = []
        for m in CITE.finditer(body):
            q = m.group(1)
            bk = m.group(2)
            bv = m.group(3)
            if bk:
                b = BOOKS.get(bk)
                v = bv
                p = os.path.join(ROOT, "verses", "%s-%02d.json" % (b, cn)) if b else ""
                # 用出处给出的章
                chap = int(m.group(4).split("-")[0].split("–")[0])
                r = check_quote(q, b, chap)
            else:
                r = check_quote(q, cb, cn)
            if r == "OK":
                ok += 1
            elif r == "OK-ELSEWHERE":
                other += 1
                lines.append("  [他卷] 「%s」" % q[:50])
            elif r == "SKIP":
                skip += 1
            else:
                mis += 1
                lines.append("  ✗ 不符 「%s」" % q[:60])
        out.append("%s：共 %d 条引文，OK %d，他卷 %d，无法核对 %d，不符 %d" %
                   (cid, ok + other + skip + mis, ok, other, skip, mis))
        out.extend(lines)
        out.append("")
    txt = "\n".join(out)
    txt += "\n（全书经文语料：%d 个 verses 文件）\n" % _corpus_files
    io.open(os.path.join(ROOT, "logs", "audit_quotes.txt"), "w", encoding="utf-8", newline="\n").write(txt)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(txt)


if __name__ == "__main__":
    main()
