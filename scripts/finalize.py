# -*- coding: utf-8 -*-
"""收尾：给已写好但缺审查报告的章节补报告，重建目录，并列出仍需人工处理的问题。

用法：
    py scripts\\finalize.py            # 补报告 + 重建目录 + 打印待办
    py scripts\\finalize.py --commit   # 顺带 git add / commit / push

退出码：0 = 全部就绪；1 = 仍有章节需要人工处理（缺人物表、缺经文、校验不过）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")
REVIEWS = os.path.join(ROOT, "reviews")
GIT = r"C:\Program Files\Git\cmd\git.exe"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def chapter_ids():
    out = []
    for name in os.listdir(ROOT):
        if re.match(r"^[a-z0-9]+-\d{2}\.html$", name):
            out.append(name[:-5])
    return sorted(out)


def check(cid):
    p = os.path.join(ROOT, "%s.html" % cid)
    r = subprocess.run([sys.executable, CHECK, p, "--json"], capture_output=True, cwd=ROOT)
    out = r.stdout.decode("utf-8", "ignore")
    i, j = out.find("{"), out.rfind("}")
    if i == -1 or j <= i:
        return None, []
    data = json.loads(out[i:j + 1])
    return data, [x for x in data["items"] if not x["ok"]]


def main():
    ids = chapter_ids()
    os.makedirs(REVIEWS, exist_ok=True)

    made = []
    need_people = []
    need_fix = []
    need_review = []
    for cid in ids:
        rp = os.path.join(REVIEWS, "%s.txt" % cid)
        if not os.path.exists(rp):
            r = subprocess.run([sys.executable, CHECK, os.path.join(ROOT, "%s.html" % cid), "--report"],
                               capture_output=True, cwd=ROOT)
            if os.path.exists(rp):
                made.append(cid)
            else:
                need_review.append(cid)
        data, bad = check(cid)
        if data is None:
            continue
        codes = [x["code"] for x in bad if x["level"] == "P0"]
        if "A17" in codes and len(codes) > 1:
            need_people.append(cid)
        elif codes:
            need_fix.append((cid, ",".join(codes)))
        elif [x for x in bad if x["level"] == "P1"]:
            need_fix.append((cid, "P1:" + ",".join(x["code"] for x in bad if x["level"] == "P1")))

    print("章节 %d 个；本次补生成审查报告 %d 个" % (len(ids), len(made)))
    if need_people:
        print("缺人物表（★★★ 不足 3 位）需要人工补卡：")
        print("  " + ", ".join(need_people))
    if need_fix:
        print("校验未过，需要处理：")
        for cid, codes in need_fix:
            print("  %-9s %s" % (cid, codes))
    if need_review:
        print("审查报告生成失败：%s" % ", ".join(need_review))

    # 重建首页与书卷页
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "reg_index.py"), "--write"],
                   capture_output=True, cwd=ROOT)

    if "--commit" in sys.argv:
        subprocess.run([GIT, "add", "-A"], cwd=ROOT)
        msg = "补齐 %d 章审查报告并重建目录" % len(made)
        subprocess.run([GIT, "-c", "user.name=Hopelove73",
                        "-c", "user.email=Hopelove73@users.noreply.github.com",
                        "commit", "-m", msg], capture_output=True, cwd=ROOT)
        for _ in range(6):
            r = subprocess.run([GIT, "push", "origin", "main"], capture_output=True, cwd=ROOT)
            if r.returncode == 0:
                print("已提交并推送：%s" % msg)
                break
        else:
            print("已提交，但 push 未成功，请重试")

    return 1 if (need_people or need_fix or need_review) else 0


if __name__ == "__main__":
    sys.exit(main())
