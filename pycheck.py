import json, os, re, sys

base = r"D:\圣经笔记\skill"

def normalize_verse(text):
    text = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)

for chap in ["ezk-08", "ezk-13", "ezk-14", "ezk-15"]:
    print(f"=== {chap} ===")
    
    vfile = os.path.join(base, "verses", chap + ".json")
    with open(vfile, encoding="utf-8") as f:
        vdata = json.load(f)
    remote = {v["n"]: v["text"] for v in vdata["verses"]}
    
    html_path = os.path.join(base, "\u8b1e\u8b3c\u658b", chap + ".html")
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
    
    bad = []
    for n, txt in remote.items():
        local = verse_map.get(n)
        if not local:
            bad.append(n)
            print(f"  Verse {n}: NOT FOUND")
            continue
        local_txt = local[0][1]
        norm_local = normalize_verse(local_txt)
        norm_remote = normalize_verse(txt)
        if norm_local != norm_remote:
            bad.append(n)
            print(f"  Verse {n}: MISMATCH")
            print(f"    Remote: {norm_remote}")
            print(f"    Local:  {norm_local}")
        else:
            print(f"  Verse {n}: OK")
    
    if not bad:
        print("  All verses match!")
    print()