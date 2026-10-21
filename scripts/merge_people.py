# -*- coding: utf-8 -*-
"""把一批人物条目合并进 assets/people.js。

用法：
    py merge_people.py people_batch.json
    py merge_people.py people_batch.json --write

规则：id 已存在 → 合并 chapters（去重排序）并用新字段覆盖；不存在 → 追加到末尾。

并发安全：写入前用 logs\\people.lock 做互斥锁（同一时刻只有一个进程能改 people.js），
避免两个写手同时合并导致互相覆盖（丢失更新）。
"""
import io
import json
import os
import sys
import time

ROOT = r"D:\圣经笔记\skill"
PEOPLE = os.path.join(ROOT, "assets", "people.js")
LOCK = os.path.join(ROOT, "logs", "people.lock")
REQUIRED = ("id", "name", "star", "role", "one", "avoid", "chapters")
LOCK_TIMEOUT = 120


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
    raw = io.open(PEOPLE, encoding="utf-8").read()
    i, j = raw.find("["), raw.rfind("]")
    if i == -1 or j == -1:
        raise SystemExit("people.js 里找不到数组")
    return json.loads(raw[i:j + 1]), raw[:i], raw[j + 1:]


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
        added, updated = [], []
        for p in batch:
            replace_ch = p.pop("_replace_chapters", False)
            if p["id"] in by_id:
                old = by_id[p["id"]]
                if replace_ch:
                    chs = sorted(set(p.get("chapters", [])))
                else:
                    chs = sorted(set(old.get("chapters", []) + p.get("chapters", [])))
                for k, v in p.items():
                    if k != "chapters":
                        old[k] = v
                old["chapters"] = chs
                updated.append(p["id"])
            else:
                cur.append(p)
                by_id[p["id"]] = p
                added.append(p["id"])

        ids = [p["id"] for p in cur]
        dup = sorted({x for x in ids if ids.count(x) > 1})
        if dup:
            raise SystemExit("合并后出现重复 id：%s" % dup)

        print("新增 %d：%s" % (len(added), ", ".join(added) or "-"))
        print("更新 %d：%s" % (len(updated), ", ".join(updated) or "-"))
        print("总人数：%d" % len(cur))

        if write:
            text = json.dumps(cur, ensure_ascii=False, indent=2)
            io.open(PEOPLE, "w", encoding="utf-8", newline="\n").write(head + text + tail)
            print("已写入 people.js")
        else:
            print("（预览模式，加 --write 写回）")
    finally:
        if got:
            release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
