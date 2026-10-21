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


GIT = r"C:\Program Files\Git\cmd\git.exe"


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
    try:
        p = subprocess.run(cmd, capture_output=True, cwd=ROOT, timeout=10800)
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    out = decode(p.stdout)
    err = decode(p.stderr)
    return out + "\n" + err, ""


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
            os.kill(old, 0)          # 只探测存活，不杀
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
        # 每轮先重建目录，保证首页与 books/ 的章节网格不会滞后
        try:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "reg_index.py"), "--write"],
                               capture_output=True, cwd=ROOT, timeout=300)
            out = r.stdout.decode("utf-8", "ignore").strip().splitlines()
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
        log("round %d: calling cli with model %s" % (i, model))
        text, err = run_session(prompt, "bible-notes-round-%d" % i, model)
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
