#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to check dan-10 errors"""
import sys
sys.path.insert(0, r'D:\圣经笔记\skill')

import subprocess, json, os

root = r'D:\圣经笔记\skill'
p = os.path.join(root, 'dan', 'dan-10.html')

# Try running check_note.py directly
cmd = [r'C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe', 
       os.path.join(root, '.agents', 'skills', 'bible-study-note', 'scripts', 'check_note.py'), 
       p, '--json']
r = subprocess.run(cmd, capture_output=True, cwd=root, timeout=30)
out = r.stdout.decode('utf-8', errors='replace')
err = r.stderr.decode('utf-8', errors='replace')
print('RC:', r.returncode)
print('STDOUT:', out[:5000])
print('STDERR:', err[:500])