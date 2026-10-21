# -*- coding: utf-8 -*-
"""修复人物表：把历史上出现过的条目并回当前版本，防止并发写入把条目覆盖丢失。

用法：
    py scripts\\repair_people.py            # 从 git 历史里找回丢失的条目
    py scripts\\repair_people.py --depth 20 # 回看最近 20 个版本（默认 20）

原理：
  1. 取当前 assets/people.js；
  2. 依次读 git 历史里最近 N 个版本的 assets/people.js；
  3. 按 id 做并集；同一 id 以「chapters 更多、字段更全」的一方为准，
     chapters 取并集，其它字段取非空值；
  4. 写回，并校验 id 唯一、每章 ★★★ 恰好 3 位。

退出码：0 = 无变化或有变化但已修好；1 = 修完仍有 ★★★ 数量不对的章节。
"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEOPLE = os.path.join(ROOT, "assets", "people.js")
GIT = r"C:\Program Files\Git\cmd\git.exe"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FIELDS = ("id", "name", "aka", "star", "role", "relation", "first", "key", "one", "avoid", "tags", "chapters")


def from_git(rev):
    r = subprocess.run([GIT, "show", "%s:assets/people.js" % rev],
                       capture_output=True, cwd=ROOT)
    t = r.stdout.decode("utf-8", "replace")
    i, j = t.find("["), t.rfind("]")
    if i == -1 or j <= i:
        return []
    try:
        return json.loads(t[i:j + 1])
    except Exception:
        return []


def merge_entry(old, new):
    """合并同一条目：chapters 取并集，其余取更完整的一方。"""
    out = dict(old)
    for k in FIELDS:
        if k == "chapters":
            continue
        ov, nv = old.get(k), new.get(k)
        if nv in (None, "", [], {}):
            continue
        if ov in (None, "", [], {}):
            out[k] = nv
        elif k == "star":
            # 星级：取较小者（1=★★★），避免同一 id 变成 4 位 ★★★
            out[k] = min(ov, nv)
        elif k == "avoid":
            out[k] = ov if len(str(ov)) >= len(str(nv)) else nv
        else:
            out[k] = nv if str(nv) not in ("", "None") else ov
    ch = set(old.get("chapters", []) or []) | set(new.get("chapters", []) or [])
    out["chapters"] = sorted(ch)
    return out


def main():
    depth = 20
    if "--depth" in sys.argv:
        depth = int(sys.argv[sys.argv.index("--depth") + 1])

    raw = io.open(PEOPLE, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    head, tail = raw[:i], raw[j + 1:]
    cur = json.loads(raw[i:j + 1])
    before = len(cur)

    r = subprocess.run([GIT, "log", "--format=%h", "-n", str(depth), "--", "assets/people.js"],
                       capture_output=True, cwd=ROOT)
    revs = r.stdout.decode("utf-8", "ignore").split()

    by_id = {p["id"]: p for p in cur}
    added = 0
    for rev in revs:
        for old in from_git(rev):
            oid = old.get("id")
            if not oid:
                continue
            if oid in by_id:
                merged = merge_entry(by_id[oid], old)
                if merged != by_id[oid]:
                    by_id[oid] = merged
            else:
                by_id[oid] = old
                added += 1

    people = list(by_id.values())
    ids = [p["id"] for p in people]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        print("！仍有重复 id：%s" % dup)
        return 1

    text = json.dumps(people, ensure_ascii=False, indent=2)
    io.open(PEOPLE, "w", encoding="utf-8", newline="\n").write(head + text + tail)
    print("人物表：%d → %d 条（从 git 历史找回 %d 条）" % (before, len(people), added))

    # 校验每章 ★★★ 恰好 3 位
    bad = []
    for p in people:
        if p.get("star") != 1:
            continue
        for cid in p.get("chapters", []):
            pass
    counts = {}
    for p in people:
        if p.get("star") == 1:
            for cid in p.get("chapters", []):
                counts[cid] = counts.get(cid, 0) + 1
    for cid, n in sorted(counts.items()):
        if n != 3:
            bad.append("%s=%d" % (cid, n))
    if bad:
        print("！以下章节 ★★★ 数量不是 3：%s" % ", ".join(bad[:30]))
    else:
        print("所有章节 ★★★ 均为 3 位")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
