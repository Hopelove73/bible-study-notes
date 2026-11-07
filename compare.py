import json, os, re

base = r"D:\圣经笔记\skill"

def normalize_verse(text):
    # Remove 【】 brackets and similar
    text = re.sub(r"\[[^\]]*\]", "", text)
    # Remove parentheses content
    text = re.sub(r"\([^)]*\)", "", text)
    # Keep only CJK and basic ASCII
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)

# ===== EZK-08 =====
print("=" * 60)
print("EZK-08")
print("=" * 60)

vfile = os.path.join(base, "verses", "ezk-08.json")
with open(vfile, encoding="utf-8") as f:
    vdata = json.load(f)
remote = {v["n"]: v["text"] for v in vdata["verses"]}

html_path = os.path.join(base, "以西结书", "ezk-08.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()

# Find scripture blocks in reading section
reading_match = re.search(r'<section\s+id="reading"[^>]*>(.*?)</section>', html, re.S)
if reading_match:
    reading_text = reading_match.group(1)
else:
    reading_text = html

segs = re.findall(r'<article class="seg.*?">(.*?)</article>', reading_text, re.S)

verse_map = {}
for idx, seg in enumerate(segs, 1):
    blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
    for block in blocks:
        for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
            n = int(m.group(1))
            txt = re.sub(r"&nbsp;", " ", m.group(2)).strip()
            verse_map.setdefault(n, []).append((idx, txt))

print("Current verse_map (verses found in HTML):")
for n in sorted(verse_map.keys()):
    local_txt = verse_map[n][0][1]
    norm_local = normalize_verse(local_txt)
    norm_remote = normalize_verse(remote.get(n, ""))
    match = "OK" if norm_local == norm_remote else "MISMATCH"
    print(f"  Verse {n}: {match}")
    if norm_local != norm_remote:
        print(f"    Remote: {remote[n][:60]}")
        print(f"    Local:  {local_txt[:60]}")

# ===== EZK-13 =====
print("\n" + "=" * 60)
print("EZK-13")
print("=" * 60)

vfile = os.path.join(base, "verses", "ezk-13.json")
with open(vfile, encoding="utf-8") as f:
    vdata = json.load(f)
remote = {v["n"]: v["text"] for v in vdata["verses"]}

html_path = os.path.join(base, "以西结书", "ezk-13.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()

reading_match = re.search(r'<section\s+id="reading"[^>]*>(.*?)</section>', html, re.S)
if reading_match:
    reading_text = reading_match.group(1)
else:
    reading_text = html

segs = re.findall(r'<article class="seg.*?">(.*?)</article>', reading_text, re.S)

verse_map = {}
for idx, seg in enumerate(segs, 1):
    blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
    for block in blocks:
        for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
            n = int(m.group(1))
            txt = re.sub(r"&nbsp;", " ", m.group(2)).strip()
            verse_map.setdefault(n, []).append((idx, txt))

print("Current verse_map (verses found in HTML):")
for n in sorted(verse_map.keys()):
    local_txt = verse_map[n][0][1]
    norm_local = normalize_verse(local_txt)
    norm_remote = normalize_verse(remote.get(n, ""))
    match = "OK" if norm_local == norm_remote else "MISMATCH"
    print(f"  Verse {n}: {match}")
    if norm_local != norm_remote:
        print(f"    Remote: {remote[n][:60]}")
        print(f"    Local:  {local_txt[:60]}")

# ===== EZK-14 =====
print("\n" + "=" * 60)
print("EZK-14")
print("=" * 60)

vfile = os.path.join(base, "verses", "ezk-14.json")
with open(vfile, encoding="utf-8") as f:
    vdata = json.load(f)
remote = {v["n"]: v["text"] for v in vdata["verses"]}

html_path = os.path.join(base, "以西结书", "ezk-14.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()

reading_match = re.search(r'<section\s+id="reading"[^>]*>(.*?)</section>', html, re.S)
if reading_match:
    reading_text = reading_match.group(1)
else:
    reading_text = html

segs = re.findall(r'<article class="seg.*?">(.*?)</article>', reading_text, re.S)

verse_map = {}
for idx, seg in enumerate(segs, 1):
    blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
    for block in blocks:
        for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
            n = int(m.group(1))
            txt = re.sub(r"&nbsp;", " ", m.group(2)).strip()
            verse_map.setdefault(n, []).append((idx, txt))

print("Current verse_map (verses found in HTML):")
for n in sorted(verse_map.keys()):
    local_txt = verse_map[n][0][1]
    norm_local = normalize_verse(local_txt)
    norm_remote = normalize_verse(remote.get(n, ""))
    match = "OK" if norm_local == norm_remote else "MISMATCH"
    print(f"  Verse {n}: {match}")
    if norm_local != norm_remote:
        print(f"    Remote: {remote[n][:60]}")
        print(f"    Local:  {local_txt[:60]}")

# Check which verses 1-23 are missing
have = set(verse_map.keys())
want = set(range(1, 24))
lack = sorted(want - have)
print(f"\nMissing verses 1-23: {lack}")

# ===== EZK-15 =====
print("\n" + "=" * 60)
print("EZK-15")
print("=" * 60)

vfile = os.path.join(base, "verses", "ezk-15.json")
with open(vfile, encoding="utf-8") as f:
    vdata = json.load(f)
remote = {v["n"]: v["text"] for v in vdata["verses"]}

html_path = os.path.join(base, "以西结书", "ezk-15.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()

reading_match = re.search(r'<section\s+id="reading"[^>]*>(.*?)</section>', html, re.S)
if reading_match:
    reading_text = reading_match.group(1)
else:
    reading_text = html

segs = re.findall(r'<article class="seg.*?">(.*?)</article>', reading_text, re.S)

verse_map = {}
for idx, seg in enumerate(segs, 1):
    blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
    for block in blocks:
        for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
            n = int(m.group(1))
            txt = re.sub(r"&nbsp;", " ", m.group(2)).strip()
            verse_map.setdefault(n, []).append((idx, txt))

print("Current verse_map (verses found in HTML):")
for n in sorted(verse_map.keys()):
    local_txt = verse_map[n][0][1]
    norm_local = normalize_verse(local_txt)
    norm_remote = normalize_verse(remote.get(n, ""))
    match = "OK" if norm_local == norm_remote else "MISMATCH"
    print(f"  Verse {n}: {match}")
    if norm_local != norm_remote:
        print(f"    Remote: {remote[n][:60]}")
        print(f"    Local:  {local_txt[:60]}")

# Check which verses 1-8 are missing
have = set(verse_map.keys())
want = set(range(1, 9))
lack = sorted(want - have)
print(f"\nMissing verses 1-8: {lack}")