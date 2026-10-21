# -*- coding: utf-8 -*-
"""人物表不变式工具：检查 / 自愈 / 快照。

不变式（A17）：**每一章恰好 3 位 ★★★**。
    people.js 里 star 是每张卡一个值，chapters 是这张卡出现的章节。
    所以本章专属人物必须是独立的一张卡（chapters 只含本章）；
    跨章的卡会同时占掉它覆盖的每一章的 ★★★ 名额。

用法：
    py scripts\\fix_people.py --check     # 只报告（有问题时退出码 1）
    py scripts\\fix_people.py --fix       # 就地修：超出 3 位的降星，不足 3 位的补星
    py scripts\\fix_people.py --snapshot  # 把当前 people.js 存为「已��样本」logs/people_good.json
    py scripts\\fix_people.py --repair    # 用「已知好样本」自愈：把被弄丢的 ★★★ 名单找回来

--repair 是并发写手的护栏：有人用旧快照覆盖 people.js 时，
样本可以把每一章的三人名单原样补回，而不会误删别的新卡。
"""
import io
import json
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEOPLE = os.path.join(ROOT, "assets", "people.js")
SNAPSHOT = os.path.join(ROOT, "logs", "people_good.json")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def chapter_files():
    return sorted(n[:-5] for n in os.listdir(ROOT)
                  if re.match(r"^[a-z0-9]+-\d{2}\.html$", n))


def load(path=PEOPLE):
    raw = io.open(path, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    if i == -1 or j == -1:
        raise SystemExit("%s 里找不到数组" % path)
    return json.loads(raw[i:j + 1]), raw[:i], raw[j + 1:]


def write(people, head, tail):
    text = json.dumps(people, ensure_ascii=False, indent=2)
    tmp = PEOPLE + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(head + text + tail)
    os.replace(tmp, PEOPLE)


def star1_map(people):
    m = {}
    for p in people:
        if p.get("star") == 1:
            for ch in p.get("chapters", []):
                m.setdefault(ch, []).append(p)
    return m


def report(people):
    m = star1_map(people)
    bad = []
    for cid in chapter_files():
        n = len(m.get(cid, []))
        if n != 3:
            bad.append((cid, n, [p.get("name") for p in m.get(cid, [])]))
    return bad


def fix_local(people):
    """就地修：多于 3 位降星，少于 3 位用本章专属卡补星。"""
    log = []
    for _ in range(6):
        m = star1_map(people)
        changed = False
        for cid in sorted(m):
            cards = m[cid]
            if len(cards) <= 3:
                continue
            def rank(p):
                chs = p.get("chapters", [])
                if len(chs) == 1:
                    return 0
                return 1
            cards.sort(key=rank)
            for p in cards[3:]:
                p["star"] = 2
                log.append("降星 %s（%s）：%s 超出 3 位 ★★★" % (p["id"], p.get("name"), cid))
                changed = True
        if not changed:
            break
    m = star1_map(people)
    for cid in sorted(m):
        if len(m[cid]) >= 3:
            continue
        cands = [p for p in people
                 if p.get("star") == 2 and p.get("chapters", []) == [cid]]
        if cands:
            cands[0]["star"] = 1
            log.append("升星 %s（%s）：补入 %s" % (cands[0]["id"], cands[0].get("name"), cid))
    return log


def repair(people):
    """用已知好样本把每一章的 ★★★ 名单补回。"""
    if not os.path.exists(SNAPSHOT):
        print("没有样本文件 %s，先跑 --snapshot" % SNAPSHOT)
        return []
    snap, _, _ = load(SNAPSHOT)
    sm = star1_map(snap)
    by_id = {p["id"]: p for p in people}
    snap_by = {p["id"]: p for p in snap}
    log = []
    for cid in chapter_files():
        want = sm.get(cid, [])
        if not want:
            continue
        want_ids = [p["id"] for p in want]
        cur = [p for p in people
               if p.get("star") == 1 and cid in p.get("chapters", [])]
        cur_ids = [p["id"] for p in cur]
        if cur_ids == want_ids:
            continue
        # 1) 把样本里该章的卡补进来（id 已存在就并入章节）
        for p in want:
            if p["id"] in by_id:
                tgt = by_id[p["id"]]
                if cid not in tgt.get("chapters", []):
                    tgt["chapters"] = sorted(set(tgt.get("chapters", [])) | {cid})
                    log.append("补入章节 %s → %s（%s）" % (cid, p["id"], p.get("name")))
                if tgt.get("star") != 1 and len(tgt.get("chapters", [])) == 1:
                    tgt["star"] = 1
            else:
                new = dict(p)
                new["chapters"] = [cid] if len(p.get("chapters", [])) > 1 else list(p.get("chapters", []))
                if cid not in new["chapters"]:
                    new["chapters"] = sorted(set(new["chapters"]) | {cid})
                people.append(new)
                by_id[new["id"]] = new
                log.append("补回卡片 %s（%s）→ %s" % (p["id"], p.get("name"), cid))
        # 2) 把多余的 ★★★ 降星
        m = star1_map(people)
        for p in m.get(cid, []):
            if p["id"] not in want_ids:
                p["star"] = 2
                log.append("降星 %s（%s）：%s 多人" % (p["id"], p.get("name"), cid))
    return log


def main():
    args = set(sys.argv[1:])
    if not args:
        args = {"--check"}
    people, head, tail = load()
    bad = report(people)

    if "--check" in args:
        print("人物卡 %d 张；有 HTML 的章 %d 个" % (len(people), len(chapter_files())))
        if not bad:
            print("A17 全部通过：每章恰好 3 位 ★★★")
            return 0
        print("A17 不合格 %d 章：" % len(bad))
        for cid, n, names in bad:
            print("  %-9s ★★★ %d 位：%s" % (cid, n, "、".join(names) or "（无）"))
        return 1

    if "--snapshot" in args:
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        shutil.copy2(PEOPLE, SNAPSHOT)
        print("已保存样本：%s（%d 张卡）" % (SNAPSHOT, len(people)))
        return 0

    if "--fix" in args:
        log = fix_local(people)
        if log:
            write(people, head, tail)
            for l in log:
                print("  " + l)
        else:
            print("无需修改")
        bad = report(people)
        print("A17 不合格 %d 章" % len(bad))
        for cid, n, names in bad:
            print("  %-9s ★★★ %d 位：%s" % (cid, n, "、".join(names) or "（无）"))
        return 1 if bad else 0

    if "--repair" in args:
        log = repair(people)
        if log:
            write(people, head, tail)
            for l in log:
                print("  " + l)
        else:
            print("无需修改")
        bad = report(people)
        print("A17 不合格 %d 章" % len(bad))
        for cid, n, names in bad:
            print("  %-9s ★★★ %d 位：%s" % (cid, n, "、".join(names) or "（无）"))
        return 1 if bad else 0

    print("未知参数：%s" % " ".join(sorted(args)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
