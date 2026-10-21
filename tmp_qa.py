# -*- coding: utf-8 -*-
import io, re, json, os
os.chdir(r'D:\圣经笔记\skill')
BOOKS = {'创':'gen','出':'exo','利':'lev','民':'num','申':'deu','书':'jos','士':'jdg','得':'rut','撒上':'1sa','撒下':'2sa','王上':'1ki','王下':'2ki','代上':'1ch','代下':'2ch','拉':'ezr','尼':'neh','斯':'est','约':'job','诗':'psa','箴':'pro','传':'ecc','歌':'sng','赛':'isa','耶':'jer','哀':'lam','结':'ezk','但':'dan','何':'hos','珥':'jol','摩':'amo','俄':'oba','拿':'jon','弥':'mic','鸿':'nam','哈':'hab','番':'zep','该':'hag','亚':'zec','玛':'mal','太':'mat','可':'mark','路':'luk','约':'jhn','徒':'act','罗':'rom','林前':'1co','林后':'2co','加':'gal','弗':'eph','腓':'php','西':'col','帖前':'1th','帖后':'2th','提前':'1ti','提后':'2ti','多':'tit','门':'phm','来':'heb','希':'heb','雅':'jas','彼前':'1pe','彼后':'2pe','约一':'1jn','约二':'2jn','约三':'3jn','犹':'jud','启':'rev'}
CITE = re.compile(r'「([^」]{3,80})」\s*[（(]\s*([^（）()]{1,40}?)\s*[）)]')
def norm(t):
    return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', t)
h = io.open('isa-45.html', encoding='utf-8').read()
body = re.sub(r'<section id="refs".*?</section>', '', h, flags=re.S)
out = []
for q, ref in CITE.findall(body):
    m = re.match(r'^\s*([\u4e00-\u9fff]{1,4})\s*(\d{1,3})\s*[:：]\s*(\d{1,3})(?:\s*[-–—~]\s*(\d{1,3}))?', ref)
    if not m:
        out.append('UNPARSED: 「%s」（%s）' % (q, ref)); continue
    name = m.group(1); b = BOOKS.get(name)
    if not b:
        out.append('NOBOOK: 「%s」（%s）' % (q, ref)); continue
    ch = int(m.group(2)); v1 = int(m.group(3)); v2 = int(m.group(4)) if m.group(4) else v1
    p = os.path.join('verses', '%s-%02d.json' % (b, ch))
    if not os.path.exists(p):
        out.append('NOFILE: 「%s」（%s）' % (q, ref)); continue
    d = json.load(io.open(p, encoding='utf-8'))
    txt = {v['n']: v['text'] for v in d['verses']}
    qn = norm(q); ok = False
    for n in range(v1, v2 + 1):
        if n in txt and qn in norm(txt[n]): ok = True; break
    if not ok:
        alt = norm(re.sub(r'[，、；：]…—\s]', '', q))
        for n in range(v1, v2 + 1):
            if n in txt and alt and alt in norm(txt[n]): ok = True; break
    if not ok:
        frags = [f for f in re.split(r'…+', q) if len(norm(f)) >= 4]
        if len(frags) > 1:
            for n in range(v1, v2 + 1):
                if n in txt and all(norm(f) in norm(txt[n]) for f in frags): ok = True; break
    out.append(('OK   ' if ok else 'FAIL ') + ref + ' | ' + q[:50])
io.open('tmp_qa_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(len(out))
