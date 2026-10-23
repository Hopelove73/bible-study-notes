import re
html = open('2ki-16.html', encoding='utf-8').read()
key_match = re.search(r'<section id="key">(.*?)</section>', html, re.S)
key = key_match.group(1)
kvs = re.findall(r'<div class="kv">(.*?)</ol>', key, re.S)
kv3 = kvs[2]
# Find all <li> tags
lis = re.findall(r'<li>.*?</li>', kv3, re.S)
print(f"KV3 has {len(lis)} <li> tags")
for i, li in enumerate(lis):
    print(f"  LI {i+1}: {repr(li[:80])}")
# Check the 4th li specifically
if len(lis) >= 4:
    li4 = lis[3]
    print(f"\nLI4 full: {repr(li4)}")
    # Check if <b> is there
    b_match = re.search(r'<b>(.*?)</b>', li4)
    if b_match:
        print(f"LI4 <b> content: {repr(b_match.group(1))}")
    else:
        print("LI4 has no <b> tag!")
        # Check what's after <li>
        print(f"LI4 starts with: {repr(li4[:50])}")
