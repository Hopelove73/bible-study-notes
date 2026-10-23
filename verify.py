import sys,io,re
sys.stdout.reconfigure(encoding="utf-8")
s=io.open("job-10.html",encoding="utf-8").read()
print("segs",len(re.findall(r'<article class="seg">',s)))
print("notes",len(re.findall(r'class="note ',s)))
bad=[]
for m in re.finditer(r'<div class="note[^"]*">(.*?)</div>',s,re.S):
    t=m.group(1)
    n=len(re.findall("[\U0001F7E6\U0001F7E8\U0001F7E7]",t))
    if n!=1: bad.append((n,t[:40]))
print("bad emoji",bad)
print("christ notes",len(re.findall(r'note--christ',s)))
print("warn",len(re.findall(r'note--warn',s)),"info",len(re.findall(r'note--info',s)))
for m in re.finditer(r'<article class="seg">(.*?)</article>',s,re.S):
    print("christ in seg", m.group(1).count("note--christ"))
print("refs li",len(re.findall(r'<li>',re.search(r'<section id="refs">(.*?)</section>',s,re.S).group(1))))
print("details",len(re.findall(r'<details>',s)))
print("tasks cb",len(re.findall(r'type="checkbox"',s)))
print("taskgroup",len(re.findall(r'class="taskgroup"',s)))
print("pills",len(re.findall(r'class="pill"',s)))
print("mm li",len(re.findall(r'<li>',re.search(r'<div class="mindmap">(.*?)</div>\s*</div>',s,re.S).group(1))))
for tag in ["p","div","span","article","section","ul","li","ol","table","details","label","blockquote","h3","h4"]:
    o=len(re.findall(r'<%s[\s>]'%tag,s)); c=len(re.findall(r'</%s>'%tag,s))
    if o!=c: print("TAG MISMATCH",tag,o,c)
print("amen","阿们。" in s)
print("quickNote","textarea id=\"quickNote\"" in s or 'id="quickNote"' in s)
print("peoplegrid",'id="chapterPeople" data-chapter="job-10"' in s)
