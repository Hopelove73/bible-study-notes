import subprocess, os, sys

base = r"D:\圣经笔记\skill"

for chap in ["ezk-22", "ezk-31", "ezk-42", "ecc-02"]:
    if chap.startswith("ezk"):
        html_path = os.path.join(base, "\u8b1e\u8b3c\u658b", f"{chap}.html")
    else:
        html_path = os.path.join(base, "\u4e transmission", f"{chap}.html")
    
    script_path = os.path.join(base, ".agents", "skills", "bible-study-note", "scripts", "people_card.py")
    result = subprocess.run(
        [sys.executable, script_path, chap, "--json", f"logs/people_{chap}.json"],
        cwd=base,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace"
    )
    print(f"{chap}: exit={result.returncode}")
    print(f"stdout: {result.stdout[:300]}")
    print(f"stderr: {result.stderr[:300]}")
    print()