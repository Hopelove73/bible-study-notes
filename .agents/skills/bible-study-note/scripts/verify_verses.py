#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_verses.py — 拉取和合本经文（简体），落盘为 verses/<id>.json；可选核对笔记。

用法：
  python verify_verses.py --book MRK --chapter 2 --out verses/mark-02.json
  python verify_verses.py --book MRK --chapter 2 --check mark-02.html

依赖：标准库；可选 zhconv（繁体转简体）。缺失时脚本仍可运行，但会在 stderr 提醒。
数据源：https://bible-api.com/data/cuv/<BOOK>/<章>（和合本，公有领域）
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request

BOOKS = {
    "GEN": ("创世记", "gen"), "EXO": ("出埃及记", "exo"), "LEV": ("利未记", "lev"),
    "NUM": ("民数记", "num"), "DEU": ("申命记", "deu"), "JOS": ("约书亚记", "jos"),
    "JDG": ("士师记", "jdg"), "RUT": ("路得记", "rut"), "1SA": ("撒母耳记上", "1sa"),
    "2SA": ("撒母耳记下", "2sa"), "1KI": ("列王纪上", "1ki"), "2KI": ("列王纪下", "2ki"),
    "1CH": ("历代志上", "1ch"), "2CH": ("历代志下", "2ch"), "EZR": ("以斯拉记", "ezr"),
    "NEH": ("尼希米记", "neh"), "EST": ("以斯帖记", "est"), "JOB": ("约伯记", "job"),
    "PSA": ("诗篇", "psa"), "PRO": ("箴言", "pro"), "ECC": ("传道书", "ecc"),
    "SNG": ("雅歌", "sng"), "ISA": ("以赛亚书", "isa"), "JER": ("耶利米书", "jer"),
    "LAM": ("耶利米哀歌", "lam"), "EZK": ("以西结书", "ezk"), "DAN": ("但以理书", "dan"),
    "HOS": ("何西阿书", "hos"), "JOL": ("约珥书", "jol"), "AMO": ("阿摩司书", "amo"),
    "OBA": ("俄巴底亚书", "oba"), "JON": ("约拿书", "jon"), "MIC": ("弥迦书", "mic"),
    "NAM": ("那鸿书", "nam"), "HAB": ("哈巴谷书", "hab"), "ZEP": ("西番雅书", "zep"),
    "HAG": ("哈该书", "hag"), "ZEC": ("撒迦利亚书", "zec"), "MAL": ("玛拉基书", "mal"),
    "MAT": ("马太福音", "mat"), "MRK": ("马可福音", "mark"), "LUK": ("路加福音", "luk"),
    "JHN": ("约翰福音", "jhn"), "ACT": ("使徒行传", "act"), "ROM": ("罗马书", "rom"),
    "1CO": ("哥林多前书", "1co"), "2CO": ("哥林多后书", "2co"), "GAL": ("加拉太书", "gal"),
    "EPH": ("以弗所书", "eph"), "PHP": ("腓立比书", "php"), "COL": ("歌罗西书", "col"),
    "1TH": ("帖撒罗尼迦前书", "1th"), "2TH": ("帖撒罗尼迦后书", "2th"),
    "1TI": ("提摩太前书", "1ti"), "2TI": ("提摩太后书", "2ti"), "TIT": ("提多书", "tit"),
    "PHM": ("腓利门书", "phm"), "HEB": ("希伯来书", "heb"), "JAS": ("雅各书", "jas"),
    "1PE": ("彼得前书", "1pe"), "2PE": ("彼得后书", "2pe"), "1JN": ("约翰一书", "1jn"),
    "2JN": ("约翰二书", "2jn"), "3JN": ("约翰三书", "3jn"), "JUD": ("犹大书", "jud"),
    "REV": ("启示录", "rev"),
}


def fetch(code, chapter):
    url = "https://bible-api.com/data/cuv/%s/%d" % (code, chapter)
    req = urllib.request.Request(url, headers={"User-Agent": "bible-study-note/1.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_simplified(text):
    try:
        import zhconv
        text = zhconv.convert(text, "zh-cn")
    except Exception:
        pass
    # 常见异体字归一（和合本旧版用字 → 简体通用字）
    return text.replace("痳", "麻").replace("麻疯", "麻风")


def strip_apparatus(text):
    """去掉 〔有古卷…〕 这类校勘注，保留正文。"""
    return re.sub(r"〔[^〕]*〕", "", text)


def norm(text):
    """比对用归一化：去校勘注、去标点空白，只留汉字与字母数字。"""
    text = strip_apparatus(text)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)


def load_note_verses(path):
    html = open(path, encoding="utf-8").read()
    out = {}
    for block in re.findall(r'<div class="scripture">(.*?)</div>', html, re.S):
        for m in re.finditer(r"<sup>(\d+)</sup>(.*?)(?=<sup>|$)", block, re.S):
            n = int(m.group(1))
            txt = re.sub(r"<[^>]+>", "", m.group(2))
            if n in out and norm(out[n]) != norm(txt):
                print("  ! 节号重复且内容不同：%d" % n)
            out[n] = txt.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, help="书卷代码，如 MRK / ROM / PSA")
    ap.add_argument("--chapter", required=True, type=int)
    ap.add_argument("--out", help="输出 JSON 路径，默认 verses/<id>.json")
    ap.add_argument("--check", help="核对已有笔记 HTML")
    ap.add_argument("--allow-count-mismatch", action="store_true")
    args = ap.parse_args()

    code = args.book.upper()
    if code not in BOOKS:
        print("未知书卷代码：%s" % code, file=sys.stderr)
        return 2
    cn, abbr = BOOKS[code]
    cid = "%s-%02d" % (abbr, args.chapter)

    if args.check:
        note_path = args.check
        if not os.path.exists(note_path):
            print("找不到笔记：%s" % note_path, file=sys.stderr)
            return 2
        try:
            data = fetch(code, args.chapter)
        except Exception as e:
            print("拉取失败：%s" % e, file=sys.stderr)
            print("不凭记忆核对。请检查网络后重试。", file=sys.stderr)
            return 2
        remote = {}
        for v in data.get("verses", []):
            remote[int(v["verse"])] = to_simplified(strip_apparatus(v["text"]))
        local = load_note_verses(note_path)
        bad = 0
        for n in sorted(remote):
            if n not in local:
                print("  ✗ 缺第 %d 节" % n)
                bad += 1
            elif norm(remote[n]) != norm(local[n]):
                print("  ✗ 第 %d 节不一致" % n)
                print("     笔记：%s" % local[n][:80])
                print("     经文：%s" % remote[n][:80])
                bad += 1
        extra = sorted(set(local) - set(remote))
        if extra:
            print("  ✗ 笔记里有经文没有的节号：%s" % extra)
            bad += len(extra)
        print("核对完成：%d 节，%d 处不一致" % (len(remote), bad))
        return 0 if bad == 0 else 1

    try:
        data = fetch(code, args.chapter)
    except Exception as e:
        print("拉取失败：%s" % e, file=sys.stderr)
        print("不要用记忆补经文。检查网络，或让用户提供经文文本。", file=sys.stderr)
        return 2

    verses = []
    conv = "zhconv"
    try:
        import zhconv  # noqa: F401
    except Exception:
        conv = "none"
        print("提示：未安装 zhconv，经文可能是繁体。pip install zhconv", file=sys.stderr)

    for v in data.get("verses", []):
        txt = strip_apparatus(v["text"]).strip()
        txt = to_simplified(txt)
        txt = re.sub(r"[ \t\u3000]+", "", txt)
        verses.append({"n": int(v["verse"]), "text": txt})

    out = args.out or os.path.join("verses", "%s.json" % cid)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    payload = {
        "id": cid,
        "book": cn,
        "book_code": code,
        "chapter": args.chapter,
        "count": len(verses),
        "source": "https://bible-api.com/data/cuv/%s/%d" % (code, args.chapter),
        "converted": conv,
        "fetched": datetime.date.today().isoformat(),
        "verses": verses,
    }
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("已保存 %s：%s %d 章，%d 节" % (out, cn, args.chapter, len(verses)))
    nums = [v["n"] for v in verses]
    if nums != list(range(1, len(verses) + 1)):
        print("提示：节号不连续，可能是 API 合并了某几节：%s" % nums[:20], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
