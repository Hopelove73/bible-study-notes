# -*- coding: utf-8 -*-
"""全圣经章节笔记完成情况检查（以 assets/books.js 的 66 卷为准）。

判定一章「完成」需同时满足：
  1. <书卷id>-<章号>.html 存在
  2. check_note.py 的 P0 全部通过（含 A17：人物表已有本章恰好 3 位 ★★★）
  3. reviews/<书卷id>-<章号>.txt 审查报告存在

用法：
  py scripts\\status.py                 # 人看的进度报告
  py scripts\\status.py --next 8        # 输出接下来该做的 8 章（空格分隔的 id）
  py scripts\\status.py --books ot      # 只统计旧约
  py scripts\\status.py --next 8 --all  # 不跳过被占用的章节

退出码：0 = 全部完成；1 = 还有待办。
"""
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")
BOOKS_JS = os.path.join(ROOT, "assets", "books.js")
CACHE = os.path.join(ROOT, "logs", ".status_cache.json")
CLAIM_DIR = os.path.join(ROOT, "logs", "claims")
CLAIM_TTL = 3 * 3600
CURRENT_BOOK_PRIORITY = "isa"   # 当前正在写的书卷，优先做完

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_books():
    s = io.open(BOOKS_JS, encoding="utf-8").read()
    i, j = s.find("["), s.rfind("]")
    return json.loads(s[i:j + 1])


def load_cache():
    try:
        return json.load(io.open(CACHE, encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with io.open(CACHE, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass


def check_note(cid):
    """返回 (是否通过, 未过项列表)。"""
    path = os.path.join(ROOT, "%s.html" % cid)
    r = subprocess.run([sys.executable, CHECK, path, "--json"], capture_output=True, cwd=ROOT)
    out = r.stdout.decode("utf-8", "ignore")
    i, j = out.find("{"), out.rfind("}")
    if i == -1 or j <= i:
        return False, ["输出无法解析"]
    try:
        data = json.loads(out[i:j + 1])
    except Exception:
        return False, ["输出无法解析"]
    codes = [x["code"] for x in data["items"] if not x["ok"]]
    return (not codes), codes


def classify(cid, cache):
    path = os.path.join(ROOT, "%s.html" % cid)
    review = os.path.join(ROOT, "reviews", "%s.txt" % cid)
    if not os.path.exists(path):
        return "missing", "文件不存在"
    st = os.stat(path)
    key = "%d:%d" % (int(st.st_mtime), st.st_size)
    hit = cache.get(cid)
    if hit and hit.get("key") == key and hit.get("review"):
        return hit["status"], hit["msg"]
    passed, codes = check_note(cid)
    if not passed:
        if codes and all(c == "A17" for c in codes):
            status, msg = "need_people", "只差人物表"
        else:
            status, msg = "fail", ",".join(codes)
    elif not os.path.exists(review):
        status, msg = "no_review", "缺审查报告"
    else:
        status, msg = "ok", ""
    cache[cid] = {"key": key, "review": os.path.exists(review), "status": status, "msg": msg}
    return status, msg


def is_claimed(cid):
    """该章是否已被某个写手占用（避免两个会话抢同一章）。过期锁自动失效。"""
    p = os.path.join(CLAIM_DIR, "%s.claim" % cid)
    if not os.path.exists(p):
        return False
    try:
        if time.time() - os.path.getmtime(p) > CLAIM_TTL:
            return False
    except OSError:
        return False
    return True


def build_queue(books, scope):
    """按「当前书卷优先 → 旧约正典序 → 新约正典序」排好队。"""
    out = []
    cur = [b for b in books if b["id"] == CURRENT_BOOK_PRIORITY]
    rest_ot = [b for b in books if b["testament"] == "ot" and b["id"] != CURRENT_BOOK_PRIORITY]
    nt = [b for b in books if b["testament"] == "nt"]
    if scope == "ot":
        rest_ot += nt
    elif scope == "nt":
        cur = []
    else:
        rest_ot += nt
    for b in cur + rest_ot:
        for ch in range(1, b["chapters"] + 1):
            out.append((b, ch))
    return out


def main():
    args = sys.argv[1:]
    scope = "all"
    if "--books" in args:
        scope = args[args.index("--books") + 1]
    n_next = 12
    if "--next" in args:
        n_next = int(args[args.index("--next") + 1])
    only_next = "--next" in args
    skip_claimed = "--all" not in args

    books = load_books()
    cache = load_cache()
    queue = build_queue(books, scope)

    groups = {"ok": [], "missing": [], "need_people": [], "fail": [], "bad": [], "no_review": []}
    detail = {}
    todo = []
    for b, ch in queue:
        cid = "%s-%02d" % (b["id"], ch)
        status, msg = classify(cid, cache)
        groups.setdefault(status, []).append(cid)
        if msg and status in ("fail", "no_review"):
            detail[cid] = msg
        if status != "ok":
            todo.append((cid, status))
    save_cache(cache)

    if only_next:
        print(" ".join("%s:%s" % (cid, st) for cid, st in todo[:n_next]))
        return 0 if not todo else 1

    total = len(queue)
    print("全圣经章节笔记进度（旧约 39 卷 + 新约 27 卷，共 %d 章）" % total)
    print("  已完成        %d" % len(groups["ok"]))
    print("  文件缺失      %d" % len(groups["missing"]))
    print("  只差人物表    %d  %s" % (len(groups["need_people"]), fmt(groups["need_people"])))
    print("  缺审查报告    %d  %s" % (len(groups["no_review"]), fmt(groups["no_review"])))
    print("  有实质错误    %d  %s" % (len(groups["fail"]), fmt(groups["fail"])))
    print("  校验异常      %d  %s" % (len(groups["bad"]), fmt(groups["bad"])))
    for cid, msg in list(detail.items())[:20]:
        print("    %s: %s" % (cid, msg))
    print("完成度 %d / %d（%.1f%%）" % (len(groups["ok"]), total, 100.0 * len(groups["ok"]) / total))
    return 0 if not todo else 1

def fmt(lst):
    if not lst:
        return ""
    return ",".join(lst[:20]) + (" …" if len(lst) > 20 else "")


if __name__ == "__main__":
    sys.exit(main())
