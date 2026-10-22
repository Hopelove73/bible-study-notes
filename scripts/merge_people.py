# -*- coding: utf-8 -*-
"""把一批人物条目合并进 assets/people.js。

用法：
    py scripts\\merge_people.py people_batch.json
    py scripts\\merge_people.py people_batch.json --write

数据模型（务必记住）：
    star   —— 每张卡一个值（1=★★★，2=★★，3=★）
    chapters —— 这张卡出现的章节列表
    A17 要求「每一章恰好 3 位 ★★★」。

    因此本章专属人物必须是独立的一张卡（chapters 只含本章）；
    一张跨章的卡会把所有它覆盖的章的 ★★★ 名额一起占掉，
    是历史上人物表反复坏掉的原因。本脚本会拦住这种合并。

规则：
    id 已存在 → 合并 chapters（去重排序）并用新字段覆盖；
                 跨章合并只允许常驻卡（yahweh / isaiah / jesus 等）
                 或显式带 _replace_chapters 的条目。
    id 不存在 → 追加到末尾。
    合并完成后强制 A17：任何一章超过 3 位 ★★★ 就把多余的降为 ★★。

并发安全：写入前用 logs\\people.lock 做互斥锁（同一时刻只有一个进程能改 people.js），
并且在锁内重新读取文件，避免用旧快照覆盖别人的更新。
"""
import io
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEOPLE = os.path.join(ROOT, "assets", "people.js")
LOCK = os.path.join(ROOT, "logs", "people.lock")
REQUIRED = ("id", "name", "star", "role", "one", "avoid", "chapters")
LOCK_TIMEOUT = 120

# 允许跨章合并的常驻卡
RESIDENT = {"yahweh", "isaiah", "jesus", "john-baptist", "peter", "holy-spirit"}

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def acquire_lock():
    """取得互斥锁；拿不到就等，最多 LOCK_TIMEOUT 秒。"""
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    deadline = time.time() + LOCK_TIMEOUT
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            return True
        except OSError:
            # 清理僵死锁
            try:
                if time.time() - os.path.getmtime(LOCK) > 60:
                    os.remove(LOCK)
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                print("！等锁超时（%d 秒），继续执行" % LOCK_TIMEOUT)
                return False
            time.sleep(1.5)


def release_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def load():
    """在锁内重新读取 people.js，返回 (列表, 头, 尾)。"""
    raw = io.open(PEOPLE, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    if i == -1 or j == -1:
        raise SystemExit("people.js 里找不到数组")
    return json.loads(raw[i:j + 1]), raw[:i], raw[j + 1:]


def chapter_files():
    return sorted(n[:-5] for n in os.listdir(ROOT)
                  if re.match(r"^[a-z0-9]+-\d{2}\.html$", n))


def star1_map(people):
    m = {}
    for p in people:
        if p.get("star") == 1:
            for ch in p.get("chapters", []):
                m.setdefault(ch, []).append(p)
    return m


def enforce_a17(people, log):
    """把每章的 ★★★ 数量压回 3：超出的降为 ★★，不足的用本章专属卡补上。"""
    # 反复处理，因为降星会改变其他章的计数
    for _ in range(6):
        m = star1_map(people)
        changed = False
        for cid in sorted(m):
            cards = m[cid]
            if len(cards) <= 3:
                continue
            # 保留顺序：常驻卡 → 本章专属卡（chapters 只含本章）→ 其他
            def rank(p):
                if p["id"] in RESIDENT:
                    return 0
                chs = p.get("chapters", [])
                return 1 if len(chs) == 1 else 2
            cards.sort(key=rank)
            for p in cards[3:]:
                p["star"] = 2
                log.append("降星：%s（%s）在 %s 超出 3 位 ★★★ → ★★" % (p["id"], p.get("name"), cid))
                changed = True
        if not changed:
            break

    m = star1_map(people)
    for cid in sorted(m):
        if len(m[cid]) >= 3:
            continue
        # 找本章专属的候选卡（chapters 只含本章）来补位
        cands = [p for p in people
                 if p.get("star") == 2 and p.get("chapters", []) == [cid]]
        if cands:
            cands[0]["star"] = 1
            log.append("升星：%s（%s）补入 %s 的 ★★★ 名单" % (cands[0]["id"], cands[0].get("name"), cid))
    return log


def main():
    if len(sys.argv) < 2:
        raise SystemExit("需要 JSON 文件路径")
    batch = json.load(io.open(sys.argv[1], encoding="utf-8"))
    write = "--write" in sys.argv

    for p in batch:
        miss = [k for k in REQUIRED if k not in p]
        if miss:
            raise SystemExit("条目 %s 缺字段：%s" % (p.get("id"), miss))

    got = acquire_lock()
    try:
        cur, head, tail = load()
        by_id = {p["id"]: p for p in cur}
        added, updated, refused = [], [], []
        for p in batch:
            p = dict(p)
            replace_ch = p.pop("_replace_chapters", False)
            incoming = sorted(set(p.get("chapters", [])))
            if p["id"] in by_id:
                old = by_id[p["id"]]
                old_chs = set(old.get("chapters", []))
                new_chs = set(incoming) - old_chs
                if new_chs and not replace_ch and p["id"] not in RESIDENT:
                    refused.append("%s：拒绝把 %s 并进已有卡（该卡已有章节 %s）——"
                                   "本章专属人物要单独建卡"
                                   % (p["id"], ", ".join(sorted(new_chs)), ", ".join(sorted(old_chs))))
                    continue
                chs = sorted(incoming) if replace_ch else sorted(old_chs | set(incoming))
                if p["id"] in RESIDENT:
                    # 常驻卡只并入章节，不覆盖它的 prose（它是跨章的总卡）
                    old["chapters"] = chs
                    updated.append(p["id"])
                    continue
                for k, v in p.items():
                    if k != "chapters":
                        old[k] = v
                old["chapters"] = chs
                updated.append(p["id"])
            else:
                # 新卡也不许跨章（常驻卡除外）：跨章卡会同时占掉它覆盖的每一章的
                # ★★★ 名额，而且卡片只剩某一章的 prose，内容与章节对不上。
                if len(incoming) > 1 and p["id"] not in RESIDENT:
                    refused.append("%s：拒绝新建跨章卡（%s）——每章专属人物要单独建卡"
                                   % (p["id"], ", ".join(incoming)))
                    continue
                cur.append(p)
                by_id[p["id"]] = p
                added.append(p["id"])

        ids = [p["id"] for p in cur]
        dup = sorted({x for x in ids if ids.count(x) > 1})
        if dup:
            raise SystemExit("合并后出现重复 id：%s" % dup)

        log = []
        enforce_a17(cur, log)

        print("新增 %d：%s" % (len(added), ", ".join(added) or "-"))
        print("更新 %d：%s" % (len(updated), ", ".join(updated) or "-"))
        if refused:
            print("拒绝 %d：" % len(refused))
            for r in refused:
                print("  " + r)
        for line in log:
            print("  " + line)
        print("总人数：%d" % len(cur))

        # 合并后自检：把结果里的每章 ★★★ 数报出来
        m = star1_map(cur)
        touched = sorted({ch for p in batch for ch in p.get("chapters", [])})
        for cid in touched:
            names = [p.get("name") for p in m.get(cid, [])]
            flag = "" if len(names) == 3 else "  ← 不是 3 位，请补卡"
            print("  %-9s ★★★ %d：%s%s" % (cid, len(names), "、".join(names), flag))

        if write:
            text = json.dumps(cur, ensure_ascii=False, indent=2)
            tmp = PEOPLE + ".tmp"
            io.open(tmp, "w", encoding="utf-8", newline="\n").write(head + text + tail)
            os.replace(tmp, PEOPLE)
            print("已写入 people.js")
        else:
            print("（预览模式，加 --write 写回）")
    finally:
        if got:
            release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
