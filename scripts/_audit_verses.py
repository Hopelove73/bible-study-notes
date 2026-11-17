# -*- coding: utf-8 -*-
"""经文基准库体检（只读）：verses/*.json 完整性 + 乱码检测 + 抽样对照。

用法： py scripts\\_audit_verses.py
报告： logs\\verses_audit.txt
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = os.path.join(ROOT, "verses")
LOG = os.path.join(ROOT, "logs", "verses_audit.txt")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 66 卷标准章数（顺序即正典顺序）
CANON = [
    ("gen", 50), ("exo", 40), ("lev", 27), ("num", 36), ("deu", 34),
    ("jos", 24), ("jdg", 21), ("rut", 4), ("1sa", 31), ("2sa", 24),
    ("1ki", 22), ("2ki", 25), ("1ch", 29), ("2ch", 36), ("ezr", 10),
    ("neh", 13), ("est", 10), ("job", 42), ("psa", 150), ("pro", 31),
    ("ecc", 12), ("sng", 8), ("isa", 66), ("jer", 52), ("lam", 5),
    ("ezk", 48), ("dan", 12), ("hos", 14), ("jol", 3), ("amo", 9),
    ("oba", 1), ("jon", 4), ("mic", 7), ("nam", 3), ("hab", 3),
    ("zep", 3), ("hag", 2), ("zec", 14), ("mal", 4),
    ("mat", 28), ("mark", 16), ("luk", 24), ("jhn", 21),
    ("act", 28), ("rom", 16), ("1co", 16), ("2co", 13), ("gal", 6),
    ("eph", 6), ("php", 4), ("col", 4), ("1th", 5), ("2th", 3),
    ("1ti", 6), ("2ti", 4), ("tit", 3), ("phm", 1), ("heb", 13),
    ("jas", 5), ("1pe", 5), ("2pe", 3), ("1jn", 5), ("2jn", 1),
    ("3jn", 1), ("jud", 1), ("rev", 22),
]

# 乱码特征：UTF-8 被按 latin-1 误解码后的典型字节序列
MOJIBAKE = re.compile(r"[ÃÃ¤Ã¥Ã¦Ã§Ã¨Ã©â€œâ€\ufffd]|â€œ|â€|Ã¨|Ã©")

# 抽样对照：和合本（简体、神版）名节。
# 注意保持与 bible-api CUV 源一致的细节：神谕段带前引号“、诗篇带题注（大卫的诗）、
# 引中引用‘、和合本作「撒玛利亚」（非「撒马利亚」）。
SPOT = {
    ("gen", 1, 1): "起初神创造天地。",
    ("gen", 1, 3): "神说：“要有光”，就有了光。",
    ("exo", 20, 3): "“除了我以外，你不可有别的神。",
    ("psa", 23, 1): "（大卫的诗）耶和华是我的牧者，我必不至缺乏。",
    ("pro", 3, 5): "你要专心仰赖耶和华，不可倚靠自己的聪明，",
    ("isa", 53, 5): "哪知他为我们的过犯受害，为我们的罪孽压伤。因他受的刑罚，我们得平安；因他受的鞭伤，我们得医治。",
    ("mat", 6, 9): "所以，你们祷告要这样说：‘我们在天上的父：愿人都尊你的名为圣。",
    ("jhn", 1, 1): "太初有道，道与神同在，道就是神。",
    ("jhn", 3, 16): "神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。",
    ("act", 1, 8): "但圣灵降临在你们身上，你们就必得着能力，并要在耶路撒冷、犹太全地，和撒玛利亚，直到地极，作我的见证。”",
    ("rom", 8, 28): "我们晓得万事都互相效力，叫爱神的人得益处，就是按他旨意被召的人。",
    ("rev", 22, 20): "证明这事的说：“是了，我必快来！”阿们！主耶稣啊，我愿你来！",
}


def main():
    problems = []
    stats = {"files": 0, "verses": 0}
    seen = {}
    for name in sorted(os.listdir(VDIR)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(VDIR, name)
        stem = name[:-5]
        stats["files"] += 1
        try:
            d = json.load(io.open(path, encoding="utf-8"))
        except Exception as e:
            problems.append("%s  JSON 解析失败：%s" % (stem, e))
            continue
        vs = d.get("verses")
        if not isinstance(vs, list) or not vs:
            problems.append("%s  verses 字段缺失或为空" % stem)
            continue
        cnt = d.get("count")
        if cnt != len(vs):
            problems.append("%s  count=%s 与实际 %d 节不符" % (stem, cnt, len(vs)))
        for i, v in enumerate(vs, 1):
            n = v.get("n")
            t = v.get("text", "")
            if n != i:
                problems.append("%s  节号不连续：第 %d 位 n=%s" % (stem, i, n))
                break
            if not t or not t.strip():
                problems.append("%s  第 %s 节文本为空" % (stem, n))
            if MOJIBAKE.search(t):
                problems.append("%s  第 %s 节疑似乱码：%s" % (stem, n, t[:30]))
            stats["verses"] += 1
        m = re.match(r"^([a-z0-9]+)-(\d+)$", stem)
        if m:
            seen.setdefault(m.group(1), set()).add(int(m.group(2)))

    # 卷章完整性（mark 即马可福音；mrk 为别名，若两边都有文件也算齐）
    for book, chapters in CANON:
        have = seen.get(book, set()) | (seen.get("mrk", set()) if book == "mark" else set())
        missing = [c for c in range(1, chapters + 1) if c not in have]
        if missing:
            problems.append("书卷 %s 缺章：%s" % (book, missing))

    # 抽样对照
    spot_bad = []
    for (book, ch, n), expect in SPOT.items():
        path = None
        for stem in ("%s-%02d" % (book, ch),):
            p = os.path.join(VDIR, stem + ".json")
            if os.path.exists(p):
                path = p
        if not path:
            spot_bad.append("%s-%d:%d 无文件" % (book, ch, n))
            continue
        d = json.load(io.open(path, encoding="utf-8"))
        got = next((v["text"] for v in d["verses"] if v["n"] == n), None)
        if got != expect:
            spot_bad.append("%s-%d:%d 不符\n  期望：%s\n  实际：%s" % (book, ch, n, expect, got))

    out = ["经文基准库体检报告", "=" * 40,
           "文件 %d 个，经节 %d 条" % (stats["files"], stats["verses"]), ""]
    out.append("【完整性/乱码】%d 个问题" % len(problems))
    out.extend(problems[:200])
    out.append("")
    out.append("【名节抽样对照】%d/%d 通过" % (len(SPOT) - len(spot_bad), len(SPOT)))
    out.extend(spot_bad)
    io.open(LOG, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("\n".join(out[:12]))
    print("...")
    print("报告：%s" % LOG)
    return 1 if problems or spot_bad else 0


if __name__ == "__main__":
    sys.exit(main())
