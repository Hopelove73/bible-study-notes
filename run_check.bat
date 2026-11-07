@echo off
chcp 65001 >nul
python .agents\skills\bible-study-note\scripts\check_note.py "%1" --json > out.txt 2>&1
type out.txt