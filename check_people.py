import subprocess, os, sys

base = r"D:\圣经笔记\skill"

result = subprocess.run(
    [sys.executable, "scripts/fix_people.py", "--check"],
    cwd=base,
    capture_output=True,
    text=True,
    encoding="utf8",
    errors="replace"
)
print(f"exit: {result.returncode}")
print(f"stdout: {result.stdout[:500]}")
print(f"stderr: {result.stderr[:500]}")