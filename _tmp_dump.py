import json, io
d = json.load(io.open('verses/luk-01.json', encoding='utf-8'))
out = []
for v in d['verses']:
    if v['n'] in (67,68,69,70,71,72,73):
        out.append('%d: %s' % (v['n'], v['text']))
d2 = json.load(io.open('verses/eph-06.json', encoding='utf-8')) if False else None
io.open('_tmp_dump.txt','w',encoding='utf-8').write('\n'.join(out))
print('ok')
