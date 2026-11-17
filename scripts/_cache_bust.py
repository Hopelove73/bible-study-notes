# -*- coding: utf-8 -*-
"""给所有 HTML 的 assets/app.js、assets/style.css 引用加版本参数，做缓存击穿。
已带 ?v= 的会被替换为新版本号。保留原行尾。"""
import io, os, re, sys

ROOT = r"D:\圣经笔记\skill"
VER = sys.argv[1] if len(sys.argv) > 1 else "20261117b"
SKIP_DIRS = {"logs", "scripts", "verses", "skill", ".git", "node_modules"}

changed, skipped = 0, 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
    for fn in filenames:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(dirpath, fn)
        raw = io.open(p, encoding="utf-8", newline="").read()
        new = re.sub(r'(assets/app\.js)(?:\?v=[^"]*)?(")', r'\1?v=%s\2' % VER, raw)
        new = re.sub(r'(assets/style\.css)(?:\?v=[^"]*)?(")', r'\1?v=%s\2' % VER, new)
        if new != raw:
            io.open(p, "w", encoding="utf-8", newline="").write(new)
            changed += 1
        else:
            skipped += 1

print("updated files:", changed, " unchanged:", skipped)
