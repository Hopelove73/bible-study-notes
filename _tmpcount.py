import re, sys
sys.stdout.reconfigure(encoding='utf-8')
h = open('isa-32.html', encoding='utf-8').read()
secs = {}
for m in re.finditer(r'<section\s+id="([^"]+)"[^>]*>', h):
    s = m.end(); e = h.find('</section>', s); secs[m.group(1)] = h[s:e]
def st(x):
    x = re.sub(r'<script\b.*?</script>', '', x, flags=re.S | re.I)
    return re.sub(r'<[^>]+>', '', x)
for k, v in secs.items():
    print(k, len(re.findall(r'[\u4e00-\u9fff]', st(v))))
print('--- segs ---')
reading = secs['reading']
for i, seg in enumerate(re.findall(r'<article class="seg">(.*?)</article>', reading, re.S), 1):
    b = re.search(r'<div class="body">(.*?)</div>\s*<div class="note', seg, re.S)
    bb = b.group(1) if b else ''
    print('SEG%02d' % i, 'body', len(re.findall(r'[\u4e00-\u9fff]', st(bb))))
