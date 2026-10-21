# -*- coding: utf-8 -*-
"""批量抓取缺失的经文 JSON：verses/<书卷id>-<章号>.json。

为「全圣经逐章写作」预先备好经文，写作时直接读取，不必现抓。
复用 verify_verses.py 的书卷代码表与取数逻辑，输出格式保持一致。

用法：
  py scripts\\fetch_all_verses.py            # 抓所有缺失的
  py scripts\\fetch_all_verses.py --limit 40 # 只抓前 40 章（用于试跑）
"""
import io
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts"))
import verify_verses as vv  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def book_chapters():
    s = io.open(os.path.join(ROOT, "assets", "books.js"), encoding="utf-8").read()
    i, j = s.find("["), s.rfind("]")
    return {b["id"]: b["chapters"] for b in json.loads(s[i:j + 1])}


def fetch_with_retry(code, chapter, tries=5):
    last = None
    for attempt in range(tries):
        try:
            return vv.fetch(code, chapter)
        except Exception as e:
            last = e
            if attempt == tries - 1:
                raise
            time.sleep(5 * (2 ** attempt))   # 5s, 10s, 20s, 40s
    raise last


def write_json(cid, cn, code, chapter, data):
    verses = []
    for v in data.get("verses", []):
        txt = vv.strip_apparatus(v["text"]).strip()
        txt = vv.to_simplified(txt)
        import re
        txt = re.sub(r"[ \t\u3000]+", "", txt)
        verses.append({"n": int(v["verse"]), "text": txt})
    payload = {
        "id": cid,
        "book": cn,
        "book_code": code,
        "chapter": chapter,
        "count": len(verses),
        "source": "https://bible-api.com/data/cuv/%s/%d" % (code, chapter),
        "converted": "zhconv",
        "fetched": time.strftime("%Y-%m-%d"),
        "verses": verses,
    }
    path = os.path.join(ROOT, "verses", "%s.json" % cid)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2))
        f.write("\n")
    os.replace(tmp, path)   # 原子替换，避免与写作会话并发时读到半截文件
    return len(verses)


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    counts = book_chapters()
    todo = []
    for code, (cn, abbr) in vv.BOOKS.items():
        if abbr not in counts:
            continue
        for ch in range(1, counts[abbr] + 1):
            cid = "%s-%02d" % (abbr, ch)
            if os.path.exists(os.path.join(ROOT, "verses", "%s.json" % cid)):
                continue
            todo.append((code, cn, abbr, ch, cid))
    if limit:
        todo = todo[:limit]
    print("待抓取 %d 章经文" % len(todo), flush=True)
    ok = fail = 0
    for n, (code, cn, abbr, ch, cid) in enumerate(todo, 1):
        try:
            data = fetch_with_retry(code, ch)
            n_verses = write_json(cid, cn, code, ch, data)
            ok += 1
            if n % 20 == 0 or n <= 3:
                print("[%d/%d] %s  %d 节" % (n, len(todo), cid, n_verses), flush=True)
        except Exception as e:
            fail += 1
            print("  ! %s 拉取失败：%s" % (cid, e), flush=True)
        time.sleep(0.8)
    print("完成：成功 %d，失败 %d" % (ok, fail), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
