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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import chapter_file, scan_chapters

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, "logs")
LOG = os.path.join(LOG_DIR, "supervisor.log")
PIDF = os.path.join(LOG_DIR, "supervisor.pid")
TPL = os.path.join(ROOT, "scripts", "prompt_template.txt")
STATUS = os.path.join(ROOT, "scripts", "status.py")

CLI = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "@opencodedesktop",
                   "resources", "opencode-cli.exe")

MODELS = [
    # 以 `opencode models` 实时清单为准（2026-10-31 核查）；已下架的 nemotron-3-ultra-free 移除
    # 已实测可正常进会话（不秒退）的模型优先；deepseek flash-free 长上下文易秒退，放最后
    "opencode/nemotron-3.5-lightning-free",
    "opencode/mimo-v2.6-flash-free",
    "opencode/glm-5.3-flash-free",
    "opencode/flint-40b-free",
    "opencode/beam-free",
    "opencode/big-pickle",
    "opencode/nemotron-3.5-super-vl-free",
    "opencode/deepseek-v4.1-flash-free",
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


def claim_env():
    """给占用脚本一个稳定的属主标识，使它能释放自己占的锁。"""
    import socket
    env = dict(os.environ)
    env["BIBLE_CLAIM_OWNER"] = "supervisor-%d@%s" % (os.getpid(), socket.gethostname())
    return env


def claim_ids(ids):
    """占住本轮要写的章节，避免另一个写手抢同一章。"""
    todo = [i for i in ids.split() if i and i != "(unknown)"]
    if not todo:
        return
    try:
        subprocess.run([sys.executable, CLAIM_SCRIPT] + todo, capture_output=True,
                       cwd=ROOT, env=claim_env())
        log("claimed: %s" % " ".join(todo))
    except Exception as e:
        log("claim failed: %s" % e)


def release_ids(ids):
    todo = [i for i in ids.split() if i and i != "(unknown)"]
    if not todo:
        return
    try:
        subprocess.run([sys.executable, CLAIM_SCRIPT, "--release"] + todo,
                       capture_output=True, cwd=ROOT, env=claim_env())
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


def wait_idle(max_wait=1800, quiet=60):
    """等所有章节文件静默，避免与残留的会话抢同一章。

    quiet 从 120 秒降到 60 秒：章节占用机制（scripts\\claim.py）已经保证不同写手
    不会碰同一章，这里不需要再等太久，否则手动会话一直在写时监督器会被饿死。
    """
    t0 = time.time()
    while time.time() - t0 < max_wait:
        newest = 0
        for cid in scan_chapters():
            try:
                newest = max(newest, os.path.getmtime(chapter_file(cid)))
            except OSError:
                pass
        if newest and (time.time() - newest) > quiet:
            return True
        time.sleep(15)
    return False


CHECK_NOTE = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")


def repo_p0_gate():
    """提交前门禁：扫描全部章节，若存在除人物表 A17 外的 P0 失败，则阻止提交。
    返回 (是否放行, 失败列表)。仅 A17 残留不阻断（人物表由收尾环节统一合并）。"""
    import json
    blocked = []
    for cid in scan_chapters():
        p = chapter_file(cid)
        if not os.path.exists(p):
            continue
        r = subprocess.run([sys.executable, CHECK_NOTE, p, "--json"],
                           capture_output=True, cwd=ROOT, timeout=120)
        out = decode(r.stdout)
        i, j = out.find("{"), out.rfind("}")
        if i == -1 or j <= i:
            continue
        try:
            data = json.loads(out[i:j + 1])
        except Exception:
            continue
        p0bad = [x["code"] for x in data.get("items", [])
                 if not x["ok"] and x["level"] == "P0" and x["code"] != "A17"]
        if p0bad:
            blocked.append((cid, ",".join(p0bad)))
    return (not blocked), blocked


def sync_repo():
    """把本地改动提交并推送到 GitHub（网络到 github.com 常会 reset，故重试）。"""
    if not os.path.exists(GIT):
        return False
    ok_gate, blocked = repo_p0_gate()
    if not ok_gate:
        log("【提交门禁】%d 章存在 P0 失败，本轮不提交、不推送：%s"
            % (len(blocked), " ".join(c for c, _ in blocked[:12])))
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
        out, _ = p.communicate(timeout=720)
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
            model_i += 1
            log("round %d: no progress on [%s], switch to next model=%s, backoff %ds"
                % (i, raw, MODELS[model_i % len(MODELS)], delay))
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
        try:
            text, err = run_session(prompt, "bible-notes-round-%d" % i, model)
        finally:
            # 无论会话成功、限流还是异常，都必须把本轮的占用释放掉
            release_ids(ids)
        try:
            with open(LOG, "a", encoding="utf-8", newline="\n") as f:
                f.write(text + "\n")
        except Exception:
            pass

        low = (text or "").lower()
        failure_marks = ("rate limit", "too many requests", "429",
                         "unavailable", "upstream request failed",
                         "model not found", "spawn fail")
        if any(m in low for m in failure_marks) or err == "TIMEOUT":
            model_i += 1
            log("round %d: model unavailable / rate limited / timeout. next model = %s, backoff %ds"
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
