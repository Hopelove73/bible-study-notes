import re, glob
for f in sorted(glob.glob("isa-*.html")):
    h = open(f, encoding="utf-8").read()
    print(f, len(re.findall(r"[\u4e00-\u9fff]", h)))
