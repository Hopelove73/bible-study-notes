import re, io

h = io.open('isa-11.html', encoding='utf-8').read()

def c(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))

def st(t):
    return re.sub(r'<[^>]+>', '', t)

sec = re.search(r'<section id="reading">(.*?)</section>', h, re.S).group(1)
segs = re.findall(r'<article class="seg">(.*?)</article>', sec, re.S)
tot_s = tot_k = tot_b = tot_w = tot_c = 0
for i, s in enumerate(segs, 1):
    sc = sum(c(st(x)) for x in re.findall(r'<div class="scripture">(.*?)</div>', s, re.S))
    kw = sum(c(st(x)) for x in re.findall(r'<div class="kw">(.*?)</div>', s, re.S))
    bd = sum(c(st(x)) for x in re.findall(r'<div class="body">(.*?)</div>', s, re.S))
    wn = sum(c(st(x)) for x in re.findall(r'<div class="note note--warn">(.*?)</div>', s, re.S))
    cn = sum(c(st(x)) for x in re.findall(r'<div class="note note--christ">(.*?)</div>', s, re.S))
    hd = c(st(re.search(r'<div class="seg-head">(.*?)</div>', s, re.S).group(1)))
    tot_s += sc; tot_k += kw; tot_b += bd; tot_w += wn; tot_c += cn
    print(f'SEG{i:02d} head={hd:3d} scr={sc:3d} kw={kw:3d} body={bd:3d} warn={wn:3d} christ={cn:3d}')
print(f'TOTAL scripture={tot_s} kw={tot_k} body={tot_b} warn={tot_w} christ={tot_c} sum={tot_s+tot_k+tot_b+tot_w+tot_c}')

# bg cells
bg = re.search(r'<section id="bg">(.*?)</section>', h, re.S).group(1)
for m in re.finditer(r'<div class="bg-cell">(.*?)</div>\s*</div>', bg, re.S):
    print('bgcell', c(st(m.group(1))), st(re.search(r'<h4>(.*?)</h4>', m.group(1), re.S).group(1)))

# key steps
key = re.search(r'<section id="key">(.*?)</section>', h, re.S).group(1)
kvs = re.findall(r'<div class="kv">(.*?)</ol>', key, re.S)
for i, kv in enumerate(kvs, 1):
    steps = re.findall(r'<li><b>.*?</b><span>(.*?)</span></li>', kv, re.S)
    print('kv%d' % i, [c(st(x)) for x in steps], 'sum', sum(c(st(x)) for x in steps))
