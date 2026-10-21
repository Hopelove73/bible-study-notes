# -*- coding: utf-8 -*-
import io, re, json, os
os.chdir(r'D:\圣经笔记\skill')

SECTIONS = ["before","bg","overview","map","reading","key","theology","prayer","apply","tasks","review","refs"]
BUDGET = {"before":(120,700),"bg":(600,1800),"overview":(250,900),"map":(80,900),
          "reading":(2500,9500),"key":(500,2200),"theology":(250,1200),"prayer":(150,700),
          "apply":(300,1300),"tasks":(250,1200),"review":(200,900),"refs":(150,900)}

def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))

def strip_tags(text):
    text = re.sub(r"<script\b.*?</script>", "", text, flags=re.S|re.I)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.S|re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;"," ").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")

h = io.open('isa-45.html', encoding='utf-8').read()
out = []
out.append("全章汉字: %d" % cjk(strip_tags(h)))
out.append("感叹号(！): %d ;  ASCII '!' : %d" % (h.count("！"), h.count("!")))

secs = {}
order = []
for m in re.finditer(r'<section\s+id="([^"]+)"[^>]*>', h):
    sid = m.group(1); start = m.end(); end = h.find("</section>", start)
    secs[sid] = h[start:end]; order.append(sid)
for s in SECTIONS:
    n = cjk(strip_tags(secs[s]))
    lo, hi = BUDGET[s]
    flag = "OK " if lo <= n <= hi else "!! "
    out.append("%s section %-9s %5d  (预算 %d-%d)" % (flag, s, n, lo, hi))

# seg details
reading = secs['reading']
segs = re.findall(r'<article class="seg">(.*?)</article>', reading, re.S)
out.append("")
out.append("段落数: %d" % len(segs))
for i, s in enumerate(segs, 1):
    title = re.search(r'<h3>(.*?)</h3>', s, re.S).group(1)
    tc = cjk(strip_tags(title))
    body = re.search(r'<div class="body">(.*?)</div>', s, re.S).group(1)
    bc = cjk(strip_tags(body))
    kws = len(re.findall(r'<span>', re.search(r'<div class="kw">(.*?)</div>', s, re.S).group(1)))
    nc = len(re.findall(r'<div class="note note--christ">', s))
    sup = [int(x) for x in re.findall(r'<sup>(\d+)</sup>', s)]
    out.append("SEG %02d | 标题%d字 | body %d字 | kw %d | christ %d | 节 %s | %s" % (i, tc, bc, kws, nc, "%d-%d"%(min(sup),max(sup)), title))

# kv steps
key = secs['key']
kvs = re.findall(r'<div class="kv">(.*?)</ol>', key, re.S)
out.append("")
out.append("kv 数: %d" % len(kvs))
for i, kv in enumerate(kvs, 1):
    ref = re.search(r'<div class="kv-ref">(.*?)</div>', kv, re.S).group(1)
    bq = re.search(r'<blockquote>(.*?)</blockquote>', kv, re.S).group(1)
    steps = re.findall(r'<li><b>.*?</b><span>(.*?)</span></li>', kv, re.S)
    out.append("KV%d %s | bq %d字 | steps %s" % (i, ref.strip(), cjk(strip_tags(bq)), [cjk(strip_tags(s)) for s in steps]))

# counts
out.append("")
out.append("bg-cell: %d" % len(re.findall(r'<div class="bg-cell">', secs['bg'])))
out.append("tasks checkbox: %d  group: %d" % (len(re.findall(r'type="checkbox"', secs['tasks'])), len(re.findall(r'class="taskgroup"', secs['tasks']))))
out.append("details: %d" % len(re.findall(r"<details", secs['review'])))
out.append("scene: %d" % len(re.findall(r'<div class="scene">', secs['apply'])))
out.append("apply-main: %d" % len(re.findall(r'<div class="apply-main">', secs['apply'])))
out.append("theology h3: %d" % len(re.findall(r'<h3>', secs['theology'])))
out.append("notes total: %d" % len(re.findall(r'<div class="note([^"]*)">', h)))
out.append("pill: %d  li><b: %d" % (len(re.findall(r'class="pill"', secs['map'])), len(re.findall(r'<li><b>', secs['map']))))
out.append("overview tbl rows: %d" % (len(re.findall(r'<tr>', re.search(r'<table class="tbl">(.*?)</table>', secs['overview'], re.S).group(1))) - 1))
out.append("refs tbl rows: %d  refs li: %d" % (len(re.findall(r'<tr>', re.search(r'<table class="tbl">(.*?)</table>', secs['refs'], re.S).group(1))) - 1, len(re.findall(r'<li>', secs['refs']))))
out.append("kv step labels: %s" % re.findall(r'<li><b>(.*?)</b>', key))

# quote audit: every quoted fragment in body must be in isa-45 (or a valid cross-ref handled earlier)
d = json.load(io.open('verses/isa-45.json', encoding='utf-8'))
full = "".join(v['text'] for v in d['verses'])
nf = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', full)
body_only = re.sub(r'<section id="refs".*?</section>', '', h, flags=re.S)
body_only = re.sub(r'<section id="review".*?</section>', '', body_only, flags=re.S)
out.append("")
out.append("--- 正文（不含 review/refs）中未标注出处的引文 ---")
for q in re.findall(r'「([^」]{2,})」', body_only):
    nq = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', q)
    if nq and nq in nf:
        continue
    out.append("  NOT-IN-ISA45: 「%s」" % q[:50])

io.open('tmp_measure_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
