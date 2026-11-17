# -*- coding: utf-8 -*-
"""全库并行体检：check_note(P0/P1) + qa_check(引文) + 审查报告存在性。

用法：
    py scripts/_audit_all.py                # 查全部 1189 章
    py scripts/_audit_all.py gen-01 exo-02  # 只查指定章

输出：每个有问题的章节一行；最后汇总。退出码 0=全干净。
并行 8 路子进程，加速全库扫描。
"""
import io, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
from _paths import chapter_file, scan_chapters

CHECK = os.path.join(ROOT, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")
QA = os.path.join(SCRIPTS, "qa_check.py")
PY = sys.executable

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def audit_one(cid):
    problems = []
    path = chapter_file(cid)
    if not os.path.exists(path):
        return cid, ["NO_HTML"]
    # check_note
    r = subprocess.run([PY, CHECK, path, "--json"], capture_output=True, cwd=ROOT)
    out = r.stdout.decode("utf-8", "ignore")
    i, j = out.find("{"), out.rfind("}")
    if i < 0 or j <= i:
        problems.append("CHECK_PARSE_FAIL")
    else:
        try:
            data = json.loads(out[i:j + 1])
            bad = [x for x in data["items"] if not x["ok"]]
            for x in bad:
                problems.append("%s:%s(%s)" % (x["level"], x["code"], x["msg"][:40]))
        except Exception as e:
            problems.append("CHECK_JSON_ERR:%s" % str(e)[:30])
    # qa_check
    r2 = subprocess.run([PY, QA, cid], capture_output=True, cwd=ROOT)
    out2 = (r2.stdout + r2.stderr).decode("utf-8", "ignore")
    m = re.search(r"(\d+)\s*条不符，\s*(\d+)\s*条无法核对", out2)
    if not m:
        problems.append("QA_PARSE_FAIL:" + out2.strip()[-40:])
    elif int(m.group(1)) > 0 or int(m.group(2)) > 0:
        problems.append("QA:不符%s/无法核对%s" % (m.group(1), m.group(2)))
    # review 存在性
    if not os.path.exists(os.path.join(ROOT, "reviews", cid + ".txt")):
        problems.append("NO_REVIEW")
    return cid, problems


def main():
    args = sys.argv[1:]
    ids = args if args else scan_chapters()
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(audit_one, c): c for c in ids}
        done = 0
        for f in as_completed(futs):
            cid, probs = f.result()
            results[cid] = probs
            done += 1
            if done % 100 == 0:
                print("...已体检 %d/%d" % (done, len(ids)), file=sys.stderr)
    bad = {c: p for c, p in results.items() if p}
    for c in sorted(bad):
        print("%-10s %s" % (c, " | ".join(bad[c])))
    print("=== 体检 %d 章，问题 %d 章，干净 %d 章 ===" % (len(ids), len(bad), len(ids) - len(bad)))
    # 落盘 JSON 便于后续修正
    outp = os.path.join(SCRIPTS, "_audit_result.json")
    io.open(outp, "w", encoding="utf-8", newline="\n").write(
        json.dumps(bad, ensure_ascii=False, indent=2))
    print("详细结果已写入", outp)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
