@echo off
cd D:\圣经笔记\skill
python analyze.py > output.txt 2>&1
type output.txt