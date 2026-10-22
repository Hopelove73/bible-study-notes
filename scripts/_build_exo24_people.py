import json, io

with io.open('assets/people.js', encoding='utf-8') as f:
    text = f.read()
data = json.loads(text[text.index('['):text.rindex(']')+1])

out = []
for pid in ('yahweh', 'isaiah'):
    card = next(c for c in data if c['id'] == pid)
    card['chapters'] = ['exo-24']
    out.append(card)

out.append({
    "id": "moses-exo24",
    "name": "摩西（24 章洒血立约的人）",
    "aka": ["摩西", "立约的中保"],
    "star": 1,
    "role": "本章主角 · 立约中保 · 上山四十昼夜的人",
    "relation": "亚伦的哥哥；带七十位长老上山；把约书念给百姓听；亲手把血一半洒坛、一半洒民；最后独自进入云中。",
    "first": "出24:1",
    "key": ["出24:3-8", "出24:9-11", "出24:12-18"],
    "one": "他把血分成两半：一半归神，一半归人，然后举起盆说「你看，这是立约的血」——约的担保不是百姓的决心，是这盆他亲手洒出去的血。",
    "avoid": "不要把本章摩西读成立法者的高光时刻：他洒完血上山才四十天，山下百姓就铸了金牛犊（32 章）。本章的庄严与下一章的崩溃是同一约的两面。",
    "tags": ["旧约", "人物", "中保"],
    "chapters": ["exo-24"]
})

with io.open('logs/people_exo24.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('wrote logs/people_exo24.json with', len(out), 'cards')
