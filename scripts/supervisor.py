# -*- coding: utf-8 -*-
"""全圣经章节笔记 · 自动监督器（Python 版）。

循环：查状态 -> 调 opencode-cli 开一个新会话继续写 -> 限流就换模型退避重试
      -> 直到 status.py 报告全部章节完成。

用法：
    py scripts\\supervisor.py
    py scripts\\supervisor.py --batch 4 --max-rounds 2000
    py scripts\\supervisor.py --once          # 只跑一轮（调试用）

日志：logs/supervisor.log
PID ：logs/supervisor.pid
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, "logs")
LOG = os.path.join(LOG_DIR, "supervisor.log")
PIDF = os.path.join(LOG_DIR, "supervisor.pid")
TPL = os.path.join(ROOT, "scripts", "prompt_template.txt")
STATUS = os.path.join(ROOT, "scripts", "status.py")

CLI = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "@opencodedesktop",
                   "resources", "opencode-cli.exe")

MODELS = [
    "opencode/deepseek-v4.1-flash-free",
    "opencode/minimax-m3.1-flash-free",
    "opencode/glm-5.3-flash-free",
    "opencode/mimo-v2.6-flash-free",
    "opencode/beam-free",
    "opencode/longcat-2.5-preview-free",
    "opencode/flint-40b-free",
    "opencode/big-pickle",
]

BASE_DELAY = 60
MAX_DELAY = 900


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def read_todo(batch, scope):
    r = subprocess.run([sys.executable, STATUS, "--next", str(batch), "--books", scope],
                       capture_output=True, cwd=ROOT)
    raw = r.stdout.decode("utf-8", "ignore").strip().splitlines()
    raw = raw[-1].strip() if raw else ""
    ids = []
    for tok in raw.split():
        ids.append(tok.split(":")[0])
    return raw, " ".join(ids), r.returncode


def build_prompt(ids, raw):
    with open(TPL, encoding="utf-8") as f:
        tpl = f.read()
    return tpl.replace("{{CHAPTERS}}", ids).replace("{{STATES}}", raw)


CLAIM_SCRIPT = os.path.join(ROOT, "scripts", "claim.py")


def claim_ids(ids):
    """占住本轮要写的章节，避免另一个写手抢同一章。"""
    todo = [i for i in ids.split() if i and i != "(unknown)"]
    if not todo:
        return
    try:
        subprocess.run([sys.executable, CLAIM_SCRIPT] + todo, capture_output=True, cwd=ROOT)
        log("claimed: %s" % " ".join(todo))
    except Exception as e:
        log("claim failed: %s" % e)


def release_ids(ids):
    todo = [i for i in ids.split() if i and i != "(unknown)"]
    if not todo:
        return
    try:
        subprocess.run([sys.executable, CLAIM_SCRIPT, "--release"] + todo,
                       capture_output=True, cwd=ROOT)
    except Exception:
        pass


GIT = r"C:\Program Files\Git\cmd\git.exe"


def proc_alive(pid):
    """判断进程是否存活。

    注意：Windows 上 os.kill(pid, 0) 会 TerminateProcess（等于杀掉进程），
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


def wait_idle(max_wait=1800, quiet=120):
    """等所有章节文件静默，避免与残留的会话抢同一章。"""
    t0 = time.time()
    while time.time() - t0 < max_wait:
        newest = 0
        for name in os.listdir(ROOT):
            if name.endswith(".html") and re.match(r"^[a-z0-9]+-\d{2}\.html$", name):
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(ROOT, name)))
                except OSError:
                    pass
        if newest and (time.time() - newest) > quiet:
            return True
        time.sleep(15)
    return False


def sync_repo():
    """把本地改动提交并推送到 GitHub（网络到 github.com 常会 reset，故重试）。"""
    if not os.path.exists(GIT):
        return False
    try:
        subprocess.run([GIT, "add", "-A"], cwd=ROOT, capture_output=True, timeout=300)
        st = subprocess.run([GIT, "status", "--porcelain"], cwd=ROOT,
                            capture_output=True, timeout=120)
        if st.stdout.strip():
            subprocess.run([GIT, "-c", "user.name=Hopelove73",
                            "-c", "user.email=Hopelove73@users.noreply.github.com",
                            "commit", "-m", "bible notes: batch update"],
                           cwd=ROOT, capture_output=True, timeout=300)
        for i in range(8):
            p = subprocess.run([GIT, "push", "origin", "main"], cwd=ROOT,
                               capture_output=True, timeout=300)
            if p.returncode == 0:
                log("repo synced (push ok, attempt %d)" % (i + 1))
                return True
            log("push failed (attempt %d), retrying in 15s" % (i + 1))
            time.sleep(15)
        log("push still failing; will retry next round")
        return False
    except Exception as e:
        log("sync_repo error: %s" % e)
        return False


def decode(b):
    """CLI 输出可能是 UTF-8，也可能是 Windows 控制台编码（GBK）。"""
    for enc in ("utf-8", "gbk", "cp936", "latin-1"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", "ignore")


def run_session(prompt, title, model):
    cmd = [CLI, "run", "--auto", "--title", title]
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    session_pid_file = os.path.join(LOG_DIR, "session.pid")
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    except Exception as e:
        return "", "SPAWN FAIL: %s" % e
    try:
        with io.open(session_pid_file, "w") as f:
            f.write(str(p.pid))
    except Exception:
        pass
    try:
        out, _ = p.communicate(timeout=10800)
    except subprocess.TimeoutExpired:
        p.kill()
        try:
            p.communicate(timeout=30)
        except Exception:
            pass
        return "", "TIMEOUT"
    finally:
        try:
            os.remove(session_pid_file)
        except Exception:
            pass
    return decode(out or b""), ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--max-rounds", type=int, default=2000)
    ap.add_argument("--scope", default="all")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(CLI):
        log("opencode-cli.exe not found: %s" % CLI)
        return 1

    if args.probe:
        text, err = run_session("只回复两个字：可以", "probe", "")
        log("probe result: %s" % ((text or err or "empty")[:300].replace("\n", " | ")))
        return 0

    # duplicate guard
    if os.path.exists(PIDF):
        try:
            old = int(open(PIDF).read().strip())
            if proc_alive(old):     # 只探测存活，不杀
                log("supervisor already running (pid=%d), exiting." % old)
                return 0
        except Exception:
            pass
    with open(PIDF, "w") as f:
        f.write(str(os.getpid()))

    log("supervisor started pid=%d batch=%d scope=%s" % (os.getpid(), args.batch, args.scope))
    delay = BASE_DELAY
    model_i = 0
    prev_raw = ""

    for i in range(1, args.max_rounds + 1):
        wait_idle()

        # 每轮先重建目录，保证首页与 books/ 的章节网格不会滞后
        try:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "reg_index.py"), "--write"],
                               capture_output=True, cwd=ROOT, timeout=300)
            out = decode(r.stdout).strip().splitlines()
            if out:
                log("catalog rebuilt: %s" % out[0])
        except Exception as e:
            log("catalog rebuild failed: %s" % e)

        raw, ids, code = read_todo(args.batch, args.scope)
        if code == 0 and not raw:
            log("all chapters complete. exiting.")
            break
        if not ids:
            ids = "(unknown)"

        if raw == prev_raw:
            log("round %d: no progress on [%s], backoff %ds" % (i, raw, delay))
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)
        else:
            log("round %d: todo = %s" % (i, raw))
            prev_raw = raw
            delay = BASE_DELAY

        prompt = build_prompt(ids, raw)
        model = MODELS[model_i % len(MODELS)]
        claim_ids(ids)
        log("round %d: calling cli with model %s" % (i, model))
        text, err = run_session(prompt, "bible-notes-round-%d" % i, model)
        release_ids(ids)
        try:
            with open(LOG, "a", encoding="utf-8", newline="\n") as f:
                f.write(text + "\n")
        except Exception:
            pass

        low = (text or "").lower()
        if "rate limit" in low or "too many requests" in low or "429" in low or err == "TIMEOUT":
            model_i += 1
            log("round %d: rate limited / timeout. next model = %s, backoff %ds"
                % (i, MODELS[model_i % len(MODELS)], delay))
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)
        else:
            log("round %d: session finished (model=%s)" % (i, model))
            model_i = 0
            sync_repo()
            time.sleep(5)

        if args.once:
            break

    try:
        os.remove(PIDF)
    except Exception:
        pass
    log("supervisor exiting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
