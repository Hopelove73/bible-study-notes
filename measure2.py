import sys,io,re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,".agents/skills/bible-study-note/scripts")
import check_note as c
html=io.open("job-10.html",encoding="utf-8").read()
print("total",c.cjk(c.strip_tags(html)))
