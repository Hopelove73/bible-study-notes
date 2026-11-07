# -*- coding: utf-8 -*-
"""章节文件路径定位：兼容「根目录平铺」「书卷代码子目录」「中文书卷子目录」三种结构。

归类改造（2026-10-24）：章节 HTML 从根目录逐步迁入 <书卷id>/ 子目录。
中文目录改造（2026-11-07）：书卷子目录改用中文卷名，如「雅歌/sng-02.html」。
所有脚本通过本模块定位章节文件，避免在多种结构之间反复修改。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHAP_RE = re.compile(r"^([a-z0-9]+)-\d{2,3}\.html$")
# 顶层非书卷目录（扫描章节时跳过）
_SKIP_DIRS = {
    "assets", "books", "reviews", "verses", "logs", "scripts",
    "_brief", ".agents", ".opencode", ".git", "node_modules",
}

# 书卷代码 -> 中文卷名（与 assets/books.js 的 name 字段一致）
BOOK_DIRS = {
    "gen": "创世记", "exo": "出埃及记", "lev": "利未记", "num": "民数记",
    "deu": "申命记", "jos": "约书亚记", "jdg": "士师记", "rut": "路得记",
    "1sa": "撒母耳记上", "2sa": "撒母耳记下", "1ki": "列王纪上", "2ki": "列王纪下",
    "1ch": "历代志上", "2ch": "历代志下", "ezr": "以斯拉记", "neh": "尼希米记",
    "est": "以斯帖记", "job": "约伯记", "psa": "诗篇", "pro": "箴言",
    "ecc": "传道书", "sng": "雅歌", "isa": "以赛亚书", "jer": "耶利米书",
    "lam": "耶利米哀歌", "ezk": "以西结书", "dan": "但以理书", "hos": "何西阿书",
    "jol": "约珥书", "amo": "阿摩司书", "oba": "俄巴底亚书", "jon": "约拿书",
    "mic": "弥迦书", "nam": "那鸿书", "hab": "哈巴谷书", "zep": "西番雅书",
    "hag": "哈该书", "zec": "撒迦利亚书", "mal": "玛拉基书", "mat": "马太福音",
    "mark": "马可福音", "luk": "路加福音", "jhn": "约翰福音", "act": "使徒行传",
    "rom": "罗马书", "1co": "哥林多前书", "2co": "哥林多后书", "gal": "加拉太书",
    "eph": "以弗所书", "php": "腓立比书", "col": "歌罗西书",
    "1th": "帖撒罗尼迦前书", "2th": "帖撒罗尼迦后书",
    "1ti": "提摩太前书", "2ti": "提摩太后书", "tit": "提多书", "phm": "腓利门书",
    "heb": "希伯来书", "jas": "雅各书", "1pe": "彼得前书", "2pe": "彼得后书",
    "1jn": "约翰一书", "2jn": "约翰二书", "3jn": "约翰三书", "jud": "犹大书",
    "rev": "启示录",
}


def book_dir(code):
    """书卷代码对应的目录名（中文卷名；未知代码原样返回）。"""
    return BOOK_DIRS.get(code, code)


def chapter_file(cid):
    """返回章节 HTML 的绝对路径。

    查找顺序：中文卷名子目录 -> 根目录临时文件 -> 旧书卷代码子目录。
    返回的路径可能不存在（调用方自行判断），但优先返回实际存在的位置。
    """
    book = cid.split("-")[0]
    for d in (book_dir(book), "", book):
        p = os.path.join(ROOT, d, "%s.html" % cid) if d else os.path.join(ROOT, "%s.html" % cid)
        if os.path.exists(p):
            return p
    return os.path.join(ROOT, book_dir(book), "%s.html" % cid)


def scan_chapters():
    """扫描全部章节文件 id（根目录 + 各书卷子目录），去重后排序。"""
    ids = set()
    for n in os.listdir(ROOT):
        if _CHAP_RE.match(n):
            ids.add(n[:-5])
    for d in os.listdir(ROOT):
        dp = os.path.join(ROOT, d)
        if not os.path.isdir(dp) or d in _SKIP_DIRS:
            continue
        try:
            names = os.listdir(dp)
        except OSError:
            continue
        for n in names:
            if _CHAP_RE.match(n):
                ids.add(n[:-5])
    return sorted(ids)


def rel_chapter_href(cid, from_dir):
    """生成从 from_dir（index.html 所在目录或 books/ 目录）指向章节文件的相对 href。"""
    f = chapter_file(cid)
    return os.path.relpath(f, from_dir).replace("\\", "/")
