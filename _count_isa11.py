import re, io, sys

h = io.open('isa-11.html', encoding='utf-8').read()
secs = re.findall(r'<section id="([a-z]+)"[^>]*>(.*?)</section>', h, re.S)
BUDGET = {
    'before': (120, 700), 'bg': (600, 1800), 'overview': (250, 900), 'map': (80, 900),
    'reading': (2500, 9500), 'key': (500, 2200), 'theology': (250, 1200), 'prayer': (150, 700),
    'apply': (300, 1300), 'tasks': (250, 1200), 'review': (200, 900), 'refs': (150, 900),
}
tot = 0
for k, v in secs:
    txt = re.sub(r'<[^>]+>', '', v)
    n = len(re.findall(r'[\u4e00-\u9fff]', txt))
    tot += n
    lo, hi = BUDGET.get(k, (0, 99999))
    flag = 'OK ' if lo <= n <= hi else ('LOW' if n < lo else 'HIGH')
    print(f'{k:9s} {n:6d}  {flag}  budget {lo}-{hi}')
alltxt = re.sub(r'<[^>]+>', '', h)
tn = len(re.findall(r'[\u4e00-\u9fff]', alltxt))
print('SUM(sections)=', tot, ' TOTAL(doc incl. head/body attrs)=', tn)

# per-seg body word counts
for m in re.finditer(r'<div class="seg">(.*?)</div>\s*</article>|<article class="seg"[^>]*>(.*?)</article>', h, re.S):
    pass
segs = re.findall(r'<article class="seg"[^>]*>(.*?)</article>', h, re.S)
print('segs:', len(segs))
for i, s in enumerate(segs, 1):
    b = re.search(r'<div class="body">(.*?)</div>', s, re.S)
    if b:
        n = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', b.group(1))))
        print(f'  seg{i:02d} body={n}')
    else:
        print(f'  seg{i:02d} body=? (regex)')
