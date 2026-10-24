# -*- coding: utf-8 -*-
"""检查 books/ 下所有 <书卷>-overview.html 概论页健康度。

用法：py scripts\\check_overview.py [--deep]
  默认：链接健康（外部依赖/404/章节子目录格式/assets 路径）
  --deep：额外检查结构性大标签配对、8 大板块齐全、UTF-8 编码
退出码：0 = 健康；1 = 有问题。
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 只查结构性大标签，避开 b/span/sup 等内联标签误报
STRONG = ["div", "section", "main", "article", "details", "summary", "table",
          "ul", "ol", "nav", "header", "footer"]
BLOCKS = ["本卷主题", "历史背景", "前后卷", "各章概要", "神要传达的心意",
          "正典中的", "人物关系", "神学要点"]


def check_pairing(h):
    h2 = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    stack = []
    for m in re.finditer(r"<(/?)(%s)((?:\"[^\"]*\"|[^>\"'])*)>" % "|".join(STRONG),
                         h2, re.I):
        close, tag = m.group(1), m.group(2).lower()
        if not close:
            stack.append((tag, m.start()))
        else:
            if not stack:
                return [("多余闭合", tag)]
            if stack[-1][0] != tag:
                return [("不匹配@%d" % m.start(),
                         "期望</%s>实际</%s>" % (stack[-1][0], tag))]
            stack.pop()
    if stack:
        return [("未闭合", ",".join(t for t, _ in stack[:10]))]
    return []


def main():
    deep = "--deep" in sys.argv
    files = sorted(glob.glob(os.path.join(ROOT, "books", "*-overview.html")))
    print("概论页总数: %d" % len(files))
    issues = []
    for f in files:
        name = os.path.basename(f)
        raw = io.open(f, "rb").read()
        try:
            h = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append((name, "非法UTF-8", ""))
            continue
        if "\ufffd" in h:
            issues.append((name, "含替换符", ""))
        # 1. 链接健康
        for m in re.finditer(r'(?:href|src)="([^"]+)"', h):
            u = m.group(1)
            if u.startswith(("http://", "https://")):
                issues.append((name, "外部依赖", u[:60]))
                continue
            if u.startswith(("#", "mailto:", "javascript:")):
                continue
            t = u.split("#")[0].split("?")[0]
            if not t:
                continue
            p = os.path.normpath(os.path.join(os.path.dirname(f), t))
            if not os.path.exists(p):
                issues.append((name, "链接404", u))
        for m in re.finditer(r'href="([^"]*-(\d{2})\.html)"', h):
            u = m.group(1)
            if u.startswith("../") and not re.search(
                    r"\.\./[a-z0-9]+/[a-z0-9]+-\d{2}\.html$", u):
                issues.append((name, "章节链接未指向子目录", u))
        for m in re.finditer(r'(?:href|src)="([^"]*assets/[^"]+)"', h):
            u = m.group(1)
            if not u.startswith("../assets/"):
                issues.append((name, "assets 路径错误", u))
        # 2. 深度检查
        if deep:
            for kind, msg in check_pairing(h):
                issues.append((name, kind, msg))
            missing = [b for b in BLOCKS if b not in h]
            if missing:
                issues.append((name, "缺板块", ",".join(missing)))
            if "<html" not in h.lower():
                issues.append((name, "无html根", ""))
    if not issues:
        print("全部 %d 页健康" % len(files))
        return 0
    print("问题数: %d" % len(issues))
    for it in issues[:60]:
        print("%s  %s  %s" % it)
    return 1


if __name__ == "__main__":
    sys.exit(main())
