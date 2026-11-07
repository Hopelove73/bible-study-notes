import subprocess, os, sys

base = r"D:\圣经笔记\skill"

for chap in ["ezk-22", "ezk-31", "ezk-42", "ecc-02"]:
    result = subprocess.run(
        [sys.executable, "scripts/claim.py", chap, "--claim"],
        cwd=base,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace"
    )
    print(f"{chap}: exit={result.returncode}")
    print(f"stdout: {result.stdout[:200]}")
    print(f"stderr: {result.stderr[:200]}")
    print()