import sys,io,re
sys.stdout.reconfigure(encoding="utf-8")
s=io.open("job-10.html",encoding="utf-8").read()
def han(t): return len(re.findall("[\u4e00-\u9fff]",t))
def sect(id_):
    m=re.search(r'<section id="%s">(.*?)</section>'%id_,s,re.S)
    return m.group(1)
tot=han(s)
print("TOTAL",tot)
for i in ["before","bg","overview","map","reading","key","theology","prayer","apply","tasks","review","refs"]:
    print(i,han(sect(i)))
print("--- seg bodies")
for m in re.finditer(r'<article class="seg">(.*?)</article>',s,re.S):
    a=m.group(1)
    b=re.search(r'<div class="body">(.*?)</div>',a,re.S).group(1)
    h=re.search(r'<h3>(.*?)</h3>',a).group(1)
    print(han(b),h)
print("--- bg cells")
for m in re.finditer(r'<div class="bg-cell"><h4>(.*?)</h4><div class="body">(.*?)</div></div>',s,re.S):
    print(m.group(1),han(m.group(2)))
print("--- kv steps")
for m in re.finditer(r'<div class="kv">(.*?)</ol>',s,re.S):
    a=m.group(1)
    ref=re.search(r'kv-ref">(.*?)<',a).group(1)
    print("KV",ref)
    for st in re.finditer(r'<li><b>(.*?)</b><span>(.*?)</span></li>',a,re.S):
        print("  ",st.group(1),han(st.group(2)))
