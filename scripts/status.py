# -*- coding: utf-8 -*-
"""以赛亚书 1–66 章完成情况检查。

用法：
  py scripts\\status.py          # 人看的进度报告
  py scripts\\status.py --next   # 只输出待办章节号（空格分隔），供监督脚本使用

退出码：0 = 全部通过 P0；1 = 还有待办。
"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")
BOOK = "isa"
TOTAL = 66

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def classify(cid):
    """返回 (状态, 说明)。状态：ok / missing / need_people / fail / bad"""
    path = os.path.join(ROOT, "%s.html" % cid)
    if not os.path.exists(path):
        return "missing", "文件不存在"
    r = subprocess.run([sys.executable, CHECK, path, "--json"], capture_output=True, cwd=ROOT)
    out = r.stdout.decode("utf-8", "ignore")
    i, j = out.find("{"), out.rfind("}")
    if i == -1 or j <= i:
        return "bad", "校验输出无法解析"
    try:
        data = json.loads(out[i:j + 1])
    except Exception:
        return "bad", "校验输出无法解析"
    if data.get("pass"):
        return "ok", ""
    codes = [x["code"] for x in data["items"] if not x["ok"]]
    if codes and all(c == "A17" for c in codes):
        return "need_people", "只差人物表"
    return "fail", ",".join(codes)


def main():
    only_next = "--next" in sys.argv
    groups = {"ok": [], "missing": [], "need_people": [], "fail": [], "bad": []}
    detail = {}
    for ch in range(1, TOTAL + 1):
        cid = "%s-%02d" % (BOOK, ch)
        st, msg = classify(cid)
        groups[st].append(ch)
        detail[ch] = msg

    todo = groups["missing"] + groups["need_people"] + groups["fail"] + groups["bad"]
    todo = sorted(todo)

    if only_next:
        print(" ".join(str(x) for x in todo))
        return 0 if not todo else 1

    print("以赛亚书 1–%d 章状态" % TOTAL)
    print("  已完成        %d" % len(groups["ok"]))
    print("  文件缺失      %d  %s" % (len(groups["missing"]), fmt(groups["missing"])))
    print("  只差人物表    %d  %s" % (len(groups["need_people"]), fmt(groups["need_people"])))
    print("  有实质错误    %d  %s" % (len(groups["fail"]), fmt(groups["fail"])))
    print("  校验异常      %d  %s" % (len(groups["bad"]), fmt(groups["bad"])))
    for ch in groups["fail"] + groups["bad"]:
        print("    %s-%02d: %s" % (BOOK, ch, detail[ch]))
    print("完成度 %d / %d" % (len(groups["ok"]), TOTAL))
    print(" ".join(str(x) for x in todo))
    return 0 if not todo else 1


def fmt(lst):
    if not lst:
        return ""
    return ",".join(str(x) for x in lst[:20]) + (" …" if len(lst) > 20 else "")


if __name__ == "__main__":
    sys.exit(main())
