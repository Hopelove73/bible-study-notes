import subprocess
import json
import os

root = r"D:\圣经笔记\skill"
cid = "dan-07"
path = os.path.join(root, cid + ".html")

# Run check_note.py
r = subprocess.run([os.path.join(root, ".agents", "skills", "bible-study-note", "scripts", "check_note.py"), path, "--json"], capture_output=True, cwd=root)
out = r.stdout.decode("utf-8", errors="ignore")

# Find JSON in output
i, j = out.find("{"), out.rfind("}")
if i == -1 or j <= i:
    print("No JSON found in output")
    print("Raw output:", out[:500])
else:
    data = json.loads(out[i:j + 1])
    codes = [x["code"] for x in data["items"] if not x["ok"]]
    print(f"Chapter: {cid}")
    print(f"Codes: {codes}")
    for item in data["items"]:
        print(f"  {item['code']}: {item['msg']} (ok={item['ok']})")