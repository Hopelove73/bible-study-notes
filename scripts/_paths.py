# -*- coding: utf-8 -*-
"""章节文件路径定位：兼容「根目录平铺」与「<书卷>/ 子目录」两种结构。

归类改造（2026-10-24）：章节 HTML 从根目录逐步迁入 <书卷id>/ 子目录后，
所有脚本通过本模块定位章节文件，避免在两种结构之间反复修改。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHAP_RE = re.compile(r"^([a-z0-9]+)-\d{2}\.html$")
# 顶层非书卷目录（扫描章节时跳过）
_SKIP_DIRS = {
    "assets", "books", "reviews", "verses", "logs", "scripts",
    "_brief", ".agents", ".opencode", ".git",
}


def chapter_file(cid):
    """返回章节 HTML 的绝对路径。

    优先根目录（旧结构，写作流程仍在写根目录时使用）；找不到再查 <书卷>/ 子目录。
    返回的路径可能不存在（调用方自行判断），但优先返回实际存在的位置。
    """
    p = os.path.join(ROOT, "%s.html" % cid)
    if os.path.exists(p):
        return p
    book = cid.split("-")[0]
    p2 = os.path.join(ROOT, book, "%s.html" % cid)
    if os.path.exists(p2):
        return p2
    return p


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
        if not re.match(r"^[a-z0-9]+$", d):
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
