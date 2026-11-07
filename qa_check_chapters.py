import subprocess, os, sys

base = r"D:\圣经笔记\skill"

for chap in ["ezk-22", "ezk-31", "ezk-42", "ecc-02"]:
    result = subprocess.run(
        [sys.executable, "scripts/qa_check.py", chap],
        cwd=base,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace"
    )
    output = result.stdout
    # Extract JSON if present
    i = output.find("{")
    j = output.rfind("}")
    if i >= 0 and j > i:
        try:
            data = json.loads(output[i:j+1])
            codes = [x["code"] for x in data.get("items", []) if not x.get("ok", True)]
            print(f"{chap}: codes={codes}")
            for item in data.get("items", []):
                if not item.get("ok", True):
                    print(f"  {item['code']}: {item.get('msg','')}")
        except:
            print(f"{chap}: parsed but not JSON: {output[:300]}")
    else:
        print(f"{chap}: no JSON, stdout_len={len(output)}, stderr_len={len(result.stderr)}")
        print(f"  stdout: {output[:300]}")
        print(f"  stderr: {result.stderr[:300]}")
    print()