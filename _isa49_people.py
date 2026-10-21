# -*- coding: utf-8 -*-
import io, json

raw = io.open("assets/people.js", encoding="utf-8").read()
i, j = raw.find("["), raw.rfind("]")
d = json.loads(raw[i:j + 1])
out = []
for p in d:
    if "isa-49" in p.get("chapters", []):
        out.append(json.dumps(p, ensure_ascii=False, indent=2))
io.open("_isa49_people.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
