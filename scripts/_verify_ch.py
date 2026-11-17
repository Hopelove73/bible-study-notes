# -*- coding: utf-8 -*-
import subprocess, sys, os, re, json
from _paths import chapter_file
PY = sys.executable
CHECK = os.path.join('.agents','skills','bible-study-note','scripts','check_note.py')
for cid in sys.argv[1:]:
    f = chapter_file(cid)
    r = subprocess.run([PY, CHECK, f, '--json'], capture_output=True, text=True, encoding='utf-8')
    i = r.stdout.find('{'); p0 = p1 = 0; msg = ''
    if i >= 0:
        d = json.loads(r.stdout[i:]); its = [x for x in d['items'] if not x['ok']]
        p0 = sum(1 for x in its if x['level']=='P0'); p1 = sum(1 for x in its if x['level']=='P1')
        msg = ' | '.join(x['code']+':'+x['msg'] for x in its)
    r2 = subprocess.run([PY, 'scripts/qa_check.py', cid], capture_output=True, text=True, encoding='utf-8')
    m = re.search(r'(\d+)\s*条不符，\s*(\d+)\s*条无法核对', r2.stdout)
    qa = (int(m.group(1)), int(m.group(2))) if m else (-1,-1)
    print(cid, 'P0=%d P1=%d QA不符=%d 无法核对=%d' % (p0, p1, qa[0], qa[1]), ('| '+msg) if (p0 or p1) else '')
