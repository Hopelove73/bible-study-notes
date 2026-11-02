#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, json

root = r"D:\圣经笔记\skill"
people_path = os.path.join(root, "assets", "people.js")

# Read people.js
with open(people_path, encoding="utf-8") as f:
    content = f.read()

i, j = content.find("["), content.rfind("]")
people = json.loads(content[i:j+1])

# Find entries for dan-07, dan-08, dan-09, dan-10
for p in people:
    cid = p.get("chapters", [])
    if "dan-10" in cid or "dan-09" in cid or "dan-08" in cid or "dan-07" in cid:
        print("=" * 60)
        print(f"ID: {p.get('id')}")
        print(f"Name: {p.get('name')}")
        print(f"Star: {p.get('star')}")
        print(f"Chapters: {p.get('chapters')}")
        print(f"Role: {p.get('role')}")
        print(f"One: {p.get('one')}")
        print(f"Avoid: {p.get('avoid')}")
        print(f"Tags: {p.get('tags')}")
        print()