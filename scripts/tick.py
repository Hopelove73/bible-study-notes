# -*- coding: utf-8 -*-
"""心跳脚本：确保监督器在跑。

设计要点：计划任务只跑这个几秒就退出的脚本，绝不让任务实例长时间挂住
（长挂的任务实例一旦被终止，Windows 会把后续触发全部排队，任务就废了）。
真正的长跑进程（supervisor.py）由本脚本以分离进程方式拉起。

判定顺序：
  1. logs/supervisor.pid 里的进程还活着 → 什么都不做
  2. logs/session.pid 里的 CLI 会话还活着 → 会话仍在写，等它收工
  3. 否则 → 分离启动 supervisor.py
"""
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, "logs")
WORKER_PID = os.path.join(LOG_DIR, "supervisor.pid")
SESSION_PID = os.path.join(LOG_DIR, "session.pid")
WORKER = os.path.join(ROOT, "scripts", "supervisor.py")
LOG = os.path.join(LOG_DIR, "supervisor.log")


def log(msg):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
            f.write("[%s] tick: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def alive(pid):
    """判断进程是否存活。

    注意：Windows 上 os.kill(pid, 0) 会 TerminateProcess，等于把进程杀掉，
    绝不能拿来当探针。这里用 OpenProcess + GetExitCodeProcess 判断。
    """
    if not pid:
        return False
    try:
        pid = int(pid)
    except Exception:
        return False
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
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def read_pid(path):
    try:
        return int(io.open(path).read().strip())
    except Exception:
        return None


def main():
    # 先清理失效占用：属主进程已退出的锁会把后面的章节堵住
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "claim.py"), "--prune"],
                           capture_output=True, cwd=ROOT)
        out = r.stdout.decode("utf-8", "ignore").strip()
        if out:
            log("pruned stale claims:\n" + out)
    except Exception as e:
        log("prune failed: %s" % e)

    # 人物表自愈：并发写手偶尔会用旧快照覆盖 assets/people.js，
    # 害得每章的 ★★★ 名单缺失或超员。用「已知好样本」把名单补回来。
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "fix_people.py"), "--repair"],
                           capture_output=True, cwd=ROOT)
        out = r.stdout.decode("utf-8", "ignore").strip()
        if out and ("补回" in out or "降星" in out or "补入" in out or "不合格" in out):
            log("people repair:\n" + out)
    except Exception as e:
        log("people repair failed: %s" % e)

    wp = read_pid(WORKER_PID)
    if alive(wp):
        log("worker alive (pid=%d), nothing to do" % wp)
        return 0
    sp = read_pid(SESSION_PID)
    if alive(sp):
        log("cli session alive (pid=%d), waiting for it to finish" % sp)
        return 0

    # 清理失效的 pid 文件
    for p in (WORKER_PID, SESSION_PID):
        try:
            os.remove(p)
        except Exception:
            pass

    flags = 0
    for name in ("DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"):
        flags |= getattr(subprocess, name, 0)
    out = open(os.path.join(LOG_DIR, "worker.log"), "ab")
    try:
        subprocess.Popen([sys.executable, WORKER], cwd=ROOT, stdout=out, stderr=out,
                         stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
        log("worker started")
    except Exception as e:
        log("failed to start worker: %s" % e)
        return 1
    finally:
        out.close()
    time.sleep(3)
    wp = read_pid(WORKER_PID)
    log("worker pid now %s" % wp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
