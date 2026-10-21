# -*- coding: utf-8 -*-
"""只提交通过校验的章节文件（跳过正在被写、尚未完成的文件）。

用法：py safe_commit.py "提交说明"
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\圣经笔记\skill"
CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")
GIT = r"C:\Program Files\Git\cmd\git.exe"


def run(args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, **kw)


def passes(cid):
    path = os.path.join(ROOT, cid + ".html")
    if not os.path.exists(path):
        return False
    r = subprocess.run([sys.executable, CHECK, path], capture_output=True, cwd=ROOT)
    return r.returncode == 0


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "bible notes: batch update"
    st = run([GIT, "status", "--porcelain"])
    files = [l[3:].strip().strip('"') for l in st.stdout.decode("utf-8", "ignore").splitlines() if l]
    good, skipped = [], []
    for f in files:
        if f.endswith(".html") and "/" not in f and "\\" not in f and f != "index.html":
            cid = os.path.splitext(os.path.basename(f))[0]
            if passes(cid):
                good.append(f)
            else:
                skipped.append(f)
        else:
            good.append(f)
    if not good:
        print("没有可提交的文件")
        return 0
    run([GIT, "add"] + good)
    st2 = run([GIT, "status", "--porcelain"])
    if not st2.stdout.strip():
        print("工作区已干净")
        return 0
    r = run([GIT, "-c", "user.name=Hopelove73",
             "-c", "user.email=Hopelove73@users.noreply.github.com",
             "commit", "-m", msg])
    print("提交结果：", r.stdout.decode("utf-8", "ignore").strip().splitlines()[-1] if r.stdout else r.stderr.decode("utf-8", "ignore")[:200])
    if skipped:
        print("跳过（未通过校验）：", ", ".join(skipped))
    for i in range(12):
        p = run([GIT, "push", "origin", "main"], timeout=300)
        if p.returncode == 0:
            print("推送成功（第 %d 次）" % (i + 1))
            return 0
        print("推送失败，重试 %d" % (i + 1))
        import time
        time.sleep(15)
    print("推送仍未成功")
    return 1


if __name__ == "__main__":
    sys.exit(main())
