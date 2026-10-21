# -*- coding: utf-8 -*-
"""章节占用标记（claim）——防止两个写手抢同一章。

用法：
    py scripts\\claim.py isa-21 isa-22      # 占用
    py scripts\\claim.py --release isa-21   # 释放
    py scripts\\claim.py --list             # 列出当前占用
    py scripts\\claim.py --mine             # 只看本机（按 owner 过滤）

约定：
  - 占用文件放在 logs\\claims\\<id>.claim，内容为 JSON：{"owner":..., "pid":..., "time":...}
  - status.py --next 会跳过仍被占用的章节，于是监督器的会话不会和手动会话抢章
  - 超过 CLAIM_TTL 秒（默认 3 小时）视为过期，锁自动失效，避免死锁
"""
import argparse
import io
import json
import os
import socket
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIM_DIR = os.path.join(ROOT, "logs", "claims")
CLAIM_TTL = 3 * 3600


def claim_path(cid):
    return os.path.join(CLAIM_DIR, "%s.claim" % cid)


def read_claim(cid):
    p = claim_path(cid)
    if not os.path.exists(p):
        return None
    try:
        data = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return None
    try:
        if time.time() - os.path.getmtime(p) > CLAIM_TTL:
            return None
    except OSError:
        return None
    return data


def owner_tag():
    """稳定的占用者标识。

    监督器会先后多次调用本脚本（占用、释放），若用本进程 pid 标识，
    两次调用的 pid 不同，就永远无法释放自己占的锁。
    因此允许通过环境变量 BIBLE_CLAIM_OWNER 传入稳定标识。
    """
    env = os.environ.get("BIBLE_CLAIM_OWNER")
    if env:
        return env
    return "pid-%d@%s" % (os.getpid(), socket.gethostname())


def do_claim(ids):
    os.makedirs(CLAIM_DIR, exist_ok=True)
    now = time.time()
    for cid in ids:
        old = read_claim(cid)
        if old:
            print("  已占用 %s（owner=%s）" % (cid, old.get("owner", "?")))
            continue
        data = {"owner": owner_tag(), "pid": os.getpid(), "time": now}
        with io.open(claim_path(cid), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("  已占用 %s" % cid)


def do_release(ids, force=False):
    mine = owner_tag()
    for cid in ids:
        p = claim_path(cid)
        if not os.path.exists(p):
            print("  未占用 %s" % cid)
            continue
        if not force:
            data = read_claim(cid)
            owner = (data or {}).get("owner", "")
            if owner != mine:
                # 别人的锁：只刷新时间戳（表示还在做），不夺走
                try:
                    os.utime(p, None)
                except OSError:
                    pass
                print("  跳过 %s（属于 %s）" % (cid, owner))
                continue
        os.remove(p)
        print("  已释放 %s" % cid)


def owner_alive(owner):
    """owner 形如 pid-1234@HOST 或 supervisor-1234@HOST；判断该进程是否还活着。"""
    if not owner:
        return False
    try:
        pid = int(owner.split("@")[0].split("-")[1])
    except Exception:
        return True  # 认不出来就保守地当它还活着
    if os.name == "nt":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            k = ctypes.windll.kernel32
            h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            code = ctypes.c_ulong()
            try:
                ok = k.GetExitCodeProcess(h, ctypes.byref(code))
            finally:
                k.CloseHandle(h)
            return bool(ok) and code.value == STILL_ACTIVE
        except Exception:
            return True
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def do_prune():
    """清掉属主进程已经不在的锁，避免死锁挡住后面的章节。"""
    if not os.path.isdir(CLAIM_DIR):
        print("没有可清理的占用")
        return
    removed = []
    for name in sorted(os.listdir(CLAIM_DIR)):
        if not name.endswith(".claim"):
            continue
        cid = name[:-6]
        p = os.path.join(CLAIM_DIR, name)
        try:
            data = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            data = {}
        owner = data.get("owner", "")
        if not owner_alive(owner):
            try:
                os.remove(p)
                removed.append("%s（属主 %s 已退出）" % (cid, owner))
            except OSError:
                pass
    print("清理了 %d 个失效占用" % len(removed))
    for r in removed:
        print("  " + r)


def do_list():
    if not os.path.isdir(CLAIM_DIR):
        print("（没有占用）")
        return
    rows = []
    for name in sorted(os.listdir(CLAIM_DIR)):
        if not name.endswith(".claim"):
            continue
        cid = name[:-6]
        data = read_claim(cid)
        if not data:
            rows.append("  %-10s （已过期）" % cid)
        else:
            age = int(time.time() - os.path.getmtime(claim_path(cid)))
            rows.append("  %-10s owner=%s  已占用 %d 秒" % (cid, data.get("owner", "?"), age))
    print("当前占用 %d 章" % len(rows))
    for r in rows:
        print(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--release", action="store_true", help="释放占用")
    ap.add_argument("--force", action="store_true", help="强制释放（无视归属）")
    ap.add_argument("--prune", action="store_true", help="清理属主进程已退出的失效占用")
    ap.add_argument("--list", action="store_true", help="列出占用")
    args = ap.parse_args()
    if args.prune:
        do_prune()
        return 0
    if args.list:
        do_list()
        return 0
    if not args.ids:
        ap.print_help()
        return 2
    if args.release:
        do_release(args.ids, force=args.force)
    else:
        do_claim(args.ids)
    return 0


if __name__ == "__main__":
    sys.exit(main())
