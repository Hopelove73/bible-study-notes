import json, os
os.chdir('D:/圣经笔记/skill')
people = json.load(open('assets/people.js'))
m = {}
for p in people:
    if p.get('star') == 1:
        for ch in p.get('chapters', []):
            m.setdefault(ch, []).append(p)
for cid in ['dan-07', 'dan-08', 'dan-09', 'dan-10']:
    entries = m.get(cid, [])
    names = [p.get('name') + '(' + p.get('id') + ')' for p in entries]
    print(cid + ': ' + str(len(entries)) + ' star:1 entries: ' + str(names))