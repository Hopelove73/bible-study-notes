# -*- coding: utf-8 -*-
"""全库体检：一次性列出所有需要修的章节，方便统一收尾。

用法：
    py scripts\\doctor.py            # 查全部已写出的章节
    py scripts\\doctor.py isa-11     # 只查指定章节

输出：每个有问题的章节一行，写清问题代码与一句话说明。
退出码：0 = 全部干净；1 = 还有问题。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def chapter_ids(ids):
    if ids:
        return list(ids)
    out = []
    for name in os.listdir(ROOT):
        if re.match(r"^[a-z0-9]+-\d{2}\.html$", name):
            out.append(name[:-5])
    return sorted(out)


def main():
    ids = chapter_ids(sys.argv[1:])
    problems = []
    ok = 0
    for cid in ids:
        path = os.path.join(ROOT, "%s.html" % cid)
        if not os.path.exists(path):
            continue
        r = subprocess.run([sys.executable, CHECK, path, "--json"],
                           capture_output=True, cwd=ROOT)
        out = r.stdout.decode("utf-8", "ignore")
        i, j = out.find("{"), out.rfind("}")
        if i == -1 or j <= i:
            problems.append("%-9s  校验脚本无法解析输出" % cid)
            continue
        data = json.loads(out[i:j + 1])
        bad = [x for x in data["items"] if not x["ok"]]
        if not bad:
            ok += 1
            continue
        p0 = [x for x in bad if x["level"] == "P0"]
        p1 = [x for x in bad if x["level"] == "P1"]
        tag = "P0" if p0 else "P1"
        codes = ",".join(x["code"] for x in bad)
        msg = (p0 or p1)[0]["msg"]
        problems.append("%-9s  [%s] %-18s %s" % (cid, tag, codes, msg[:60]))

    print("已检查 %d 章，其中 %d 章干净。" % (len(ids), ok))
    if problems:
        print("")
        print("需要处理 %d 章：" % len(problems))
        for p in problems:
            print("  " + p)
        print("")
        print("提示：A17 = 缺人物表条目；A20 = 经文与 verses 不一致；A24 = 禁用句式；")
        print("      A27 = 某 section 字数超/不足预算；A01/A08/A10 = section 缺失或标签不符。")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
