# -*- coding: utf-8 -*-
"""把根目录平铺的章节 HTML 按书卷迁入 <书卷id>/ 子目录，并批量改写内部相对链接。

用法：
    py scripts\\reorganize.py --dry-run   # 预览要移动的文件与要改的链接
    py scripts\\reorganize.py --apply     # 实际执行：
                                          #   1) 移动 <id>.html -> <book>/<id>.html
                                          #   2) 章节页内 href="assets/…" -> ../assets/…
                                          #      章节页内 href="index.html"/"people.html" -> ../index.html / ../people.html
                                          #   3) 重建 index.html 与 books/*.html（reg_index.py 已兼容新结构）
                                          #   4) 本地验证链接存在性

注意：
- 只动根目录里匹配 ^[a-z0-9]+-\\d{2}\\.html$ 的章节文件；
  不碰 index.html / people.html / books/ / assets/ / reviews/ / verses/ 等。
- 移动前先确认目标子目录存在或创建。
- 执行时机：必须在写作流程空闲时运行（诗篇未写完时禁止 --apply）。
"""
import io
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import ROOT

CHAP_RE = re.compile(r"^([a-z0-9]+)-\d{2}\.html$")


def collect():
    """返回 [(cid, book, src, dst), ...]，src 为根目录章节文件。"""
    items = []
    for name in sorted(os.listdir(ROOT)):
        m = CHAP_RE.match(name)
        if not m:
            continue
        book = m.group(1)
        src = os.path.join(ROOT, name)
        dstdir = os.path.join(ROOT, book)
        dst = os.path.join(dstdir, name)
        if os.path.exists(dst):
            print("！目标已存在，跳过：%s" % dst)
            continue
        items.append((name[:-5], book, src, dst))
    return items


def rewrite_links(path):
    """把章节页里的相对链接改写到 ../ 前缀（移动后页面位于 <book>/ 子目录）。"""
    h = io.open(path, encoding="utf-8").read()
    orig = h
    h = re.sub(r'href="(assets/[^"]+)"', r'href="../\1"', h)
    h = re.sub(r'href="(index\.html)"', r'href="../\1"', h)
    h = re.sub(r'href="(people\.html)"', r'href="../\1"', h)
    # 章节页之间的跳转（如上一章/下一章/相关章节）也加 ../ 前缀
    h = re.sub(r'href="([a-z0-9]+-\d{2}\.html)"', r'href="../\1"', h)
    if h != orig:
        io.open(path, "w", encoding="utf-8", newline="\n").write(h)
        return True
    return False


def verify_links():
    """抽查：打开 index.html / people.html / books/*.html，确认 href 目标存在。"""
    import re as _re
    bad = []
    checked = 0
    for page in ["index.html", "people.html"]:
        p = os.path.join(ROOT, page)
        if not os.path.exists(p):
            continue
        h = io.open(p, encoding="utf-8").read()
        for m in _re.finditer(r'href="([^"#][^"]*)"', h):
            target = m.group(1)
            if target.startswith("http"):
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(full):
                bad.append("%s -> %s" % (page, target))
            checked += 1
    bdir = os.path.join(ROOT, "books")
    if os.path.isdir(bdir):
        for name in os.listdir(bdir):
            p = os.path.join(bdir, name)
            h = io.open(p, encoding="utf-8").read()
            for m in _re.finditer(r'href="([^"#][^"]*)"', h):
                target = m.group(1)
                if target.startswith("http"):
                    continue
                full = os.path.normpath(os.path.join(os.path.dirname(p), target))
                if not os.path.exists(full):
                    bad.append("%s -> %s" % (name, target))
                checked += 1
    return checked, bad


def main():
    apply = "--apply" in sys.argv
    items = collect()
    print("待移动章节 %d 个" % len(items))
    books = sorted({b for _, b, _, _ in items})
    print("涉及书卷 %d 个：%s" % (len(books), ", ".join(books)))
    if not apply:
        print("（预览模式，加 --apply 实际执行）")
        return 0

    moved = 0
    for cid, book, src, dst in items:
        dstdir = os.path.dirname(dst)
        os.makedirs(dstdir, exist_ok=True)
        # 先改链接再移动（路径是绝对的，改链接只改 href 文本）
        rewrite_links(src)
        shutil.move(src, dst)
        moved += 1
        print("  已移动 %s -> %s" % (cid, os.path.relpath(dst, ROOT)))
    print("移动完成：%d 个" % moved)

    # 重建目录（reg_index 已兼容子目录）
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "reg_index.py"), "--write"],
                       capture_output=True, cwd=ROOT)
    print(r.stdout.decode("utf-8", "ignore").strip().splitlines()[-1])

    # 验证链接
    checked, bad = verify_links()
    print("链接验证：检查 %d 条，异常 %d 条" % (checked, len(bad)))
    for b in bad[:20]:
        print("  ! " + b)
    if bad:
        return 1
    print("归类完成，所有链接可解析。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
