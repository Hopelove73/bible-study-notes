import json, subprocess, os, sys

base = r"D:\圣经笔记\skill"
check_script = os.path.join(base, ".agents", "skills", "bible-study-note", "scripts", "check_note.py")

for chap in ["ezk-22", "ezk-31", "ezk-42", "ecc-02"]:
    if chap.startswith("ezk"):
        html_path = os.path.join(base, "\u8b1e\u8b3c\u658b", f"{chap}.html")
    else:
        html_path = os.path.join(base, "\u4e transmission", f"{chap}.html")
    
    # Run check_note.py with --json
    result = subprocess.run(
        [sys.executable, check_script, html_path, "--json"],
        cwd=base,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace"
    )
    output = result.stdout
    # Extract JSON from output
    i = output.find("{")
    j = output.rfind("}")
    if i >= 0 and j > i:
        data = json.loads(output[i:j+1])
        codes = [x["code"] for x in data["items"] if not x["ok"]]
        print(f"{chap}: codes={codes}")
        for item in data["items"]:
            if not item["ok"]:
                print(f"  {item['code']}: {item.get('msg','')}")
    else:
        print(f"{chap}: no JSON found, stdout={output[:200]}, stderr={result.stderr[:200]}")
    print()