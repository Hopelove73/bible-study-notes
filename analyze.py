import json, os, re

base = r"D:\圣经笔记\skill"

def normalize_verse(text):
    text = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)

for chap in ["ezk-08", "ezk-13", "ezk-14", "ezk-15"]:
    print(f"=== {chap} ===")
    
    # Load verses JSON
    vfile = os.path.join(base, "verses", chap + ".json")
    with open(vfile, encoding="utf-8") as f:
        vdata = json.load(f)
    remote = {v["n"]: v["text"] for v in vdata["verses"]}
    
    # Parse HTML reading section
    html_path = os.path.join(base, "以西结书", chap + ".html")
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    
    # Find the reading section
    reading_match = re.search(r'<section\s+id="reading"[^>]*>(.*?)</section>', html, re.S)
    if reading_match:
        reading_text = reading_match.group(1)
    else:
        reading_text = html
    
    segs = re.findall(r'<article class="seg.*?">(.*?)</article>', reading_text, re.S)
    
    # Build verse_map
    verse_map = {}
    for idx, seg in enumerate(segs, 1):
        blocks = re.findall(r'<div class="scripture">(.*?)</div>', seg, re.S)
        for block in blocks:
            for m in re.finditer(r"<sup>\s*(\d+)\s*</sup>(.*?)(?=<sup>|$)", block, re.S):
                n = int(m.group(1))
                txt = re.sub(r"&nbsp;", " ", m.group(2)).strip()
                verse_map.setdefault(n, []).append((idx, txt))
    
    # Check A20
    bad = []
    for n, txt in remote.items():
        local = verse_map.get(n)
        if not local:
            bad.append(n)
            print(f"  Verse {n}: NOT FOUND in HTML")
            continue
        local_txt = local[0][1]  # Take first occurrence
        norm_local = normalize_verse(local_txt)
        norm_remote = normalize_verse(txt)
        if norm_local != norm_remote:
            bad.append(n)
            print(f"  Verse {n}: MISMATCH")
            print(f"    Remote: {txt[:80]}")
            print(f"    Local:  {local_txt[:80]}")
            print(f"    Norm Remote: {norm_remote[:80]}")
            print(f"    Norm Local:  {norm_local[:80]}")
        else:
            print(f"  Verse {n}: OK")
    
    if not bad:
        print("  All verses match!")
    print()