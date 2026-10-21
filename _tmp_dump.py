import json, io, os
files = {'gen-29':None,'gen-08':[8],'gen-09':[9,10,11,12,13,14,15,16,17],'isa-62':[4,5],'isa-60':[1,2,3,19,20,21,22],'isa-53':[10,11,12],'isa-55':[8,9,10,11],'gen-25':[21,22,23],'judg-6':[3],'2ch-20':[17],'psa-103':[11,12],'psa-118':[6]}
out = []
for f, ns in files.items():
    p = 'verses/%s.json' % f
    if not os.path.exists(p):
        out.append('== %s MISSING' % f); continue
    d = json.load(io.open(p, encoding='utf-8'))
    out.append('== %s (count=%d)' % (f, len(d.get('verses',[]))))
    for v in d.get('verses',[]):
        if ns is None or v['n'] in ns:
            out.append('%d: %s' % (v['n'], v['text']))
io.open('_tmp_dump.txt','w',encoding='utf-8').write('\n'.join(out))
print('done')
