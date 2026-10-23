import sys,io,re
sys.stdout.reconfigure(encoding="utf-8")
s=io.open("job-10.html",encoding="utf-8").read()
for m in re.finditer(r'<div class="note note--warn">(.*?)</div>',s,re.S):
    print(re.sub(r"<[^>]+>","",m.group(1)).strip()[:260])
    print("---")
