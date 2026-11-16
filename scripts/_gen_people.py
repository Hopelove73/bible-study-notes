# -*- coding: utf-8 -*-
"""给一章生成并合并人物卡（常驻 yahweh+isaiah + 本章专属卡），然后跑校验。

用法：
  py scripts\_gen_people.py amo-04 "阿摩司（4 章）" "role" "relation" "first ref" "one 句子" "avoid" "key1,key2" [--no-check]

默认：生成 logs/people_<id>.json → merge_people 写入 → check_note + qa_check。
"""
import argparse
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def run(cmd):
    print(">>", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("cardid", help="专属卡 id，如 amos-amo04")
    ap.add_argument("name")
    ap.add_argument("role")
    ap.add_argument("relation")
    ap.add_argument("first")
    ap.add_argument("one")
    ap.add_argument("avoid")
    ap.add_argument("keys", help="逗号分隔的关键经节，如 amo-04:1,amo-04:2")
    ap.add_argument("--aka", default="提哥亚牧人")
    ap.add_argument("--tags", default="旧约,先知,核心")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()

    cards = [
        {"id": "yahweh", "chapters": [a.cid]},
        {"id": "isaiah", "chapters": [a.cid]},
        {
            "id": a.cardid,
            "name": a.name, "aka": [a.aka], "star": 1, "role": a.role,
            "relation": a.relation, "first": a.first,
            "key": [k.strip() for k in a.keys.split(",") if k.strip()],
            "one": a.one, "avoid": a.avoid,
            "tags": [t.strip() for t in a.tags.split(",")],
            "chapters": [a.cid],
        },
    ]
    pj = os.path.join(ROOT, "logs", "people_%s.json" % a.cid)
    io.open(pj, "w", encoding="utf-8", newline="\n").write(
        json.dumps(cards, ensure_ascii=False, indent=2))
    print("人物 JSON:", pj)

    rc = run([sys.executable, os.path.join(SCRIPTS, "merge_people.py"),
              os.path.relpath(pj, ROOT), "--write"])
    if rc:
        return rc

    if a.no_check:
        return 0
    # 找章节 html：中文目录
    from glob import glob
    hs = glob(os.path.join(ROOT, "*", a.cid + ".html"))
    if not hs:
        print("找不到 %s.html，跳过 check_note" % a.cid)
        return 0
    rel = os.path.relpath(hs[0], ROOT)
    rc = run([sys.executable, os.path.join(ROOT, ".agents", "skills", "bible-study-note",
                                           "scripts", "check_note.py"), rel])
    rc |= run([sys.executable, os.path.join(SCRIPTS, "qa_check.py"), a.cid])
    return rc


if __name__ == "__main__":
    sys.exit(main())
