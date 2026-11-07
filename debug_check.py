#!/usr/bin/env python
import subprocess, sys, os, json

root = r"D:\圣经笔记\skill"
cid = "ezk-08"
path = os.path.join(root, f"以西结书\{cid}.html")

r = subprocess.run(
    [sys.executable, ".agents\skills\bible-study-note\scripts\check_note.py", path, "--json"],
    capture_output=True, cwd=root
)
stdout = r.stdout.decode("utf-8", errors="replace")
stderr = r.stderr.decode("utf-8", errors="replace")

print("RC:", r.returncode)
print("STDOUT:", repr(stdout[:500]))
print("STDERR:", repr(stderr[:500]))

i, j = stdout.find("{"), stdout.rfind("}")
if i == -1 or j <= i:
    print("No JSON found")
    sys.exit(0)

data = json.loads(stdout[i:j+1])
codes = [x["code"] for x in data["items"] if not x["ok"]]
ok_codes = [x["code"] for x in data["items"] if x["ok"]]

print(f"\nP0 ok: {ok_codes}")
print(f"P0 failed: {codes}")
a17 = [c for c in codes if c == "A17"]
other = [c for c in codes if c != "A17"]
print(f"A17: {a17}")
print(f"Other: {other}")
print(f"\nAll items count: {len(data['items'])}")
for item in data["items"][:10]:
    print(f"  {item}")