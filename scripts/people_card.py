# -*- coding: utf-8 -*-
"""为一个章节生成人物卡 JSON 骨架，降低写手合并人物表的成本。

用法：
    py scripts\\people_card.py isa-52                 # 只看候选人物
    py scripts\\people_card.py isa-52 --json out.json # 生成骨架并写入 out.json

做法：
  1. 扫描该章 HTML 的正文，统计常见圣经人名的出现次数，按频次排出候选；
  2. 为每个候选填好 id / name / star / chapters 等字段，
     留下 role / relation / first / key / one / avoid / tags 由写手补写；
  3. 写手补完后用 scripts\\merge_people.py 合并。
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 旧约常见人名（含部分别名），用于候选识别
NAMES = [
    "亚伯兰", "亚伯拉罕", "撒莱", "夏甲", "以实玛利", "以撒", "以扫", "雅各", "以色列",
    "约瑟", "摩西", "亚伦", "米利暗", "耶弗他", "参巴拉", "耶利", "以西结", "但以理",
    "尼希米", "以斯帖", "约伯", "大卫", "所罗门", "撒母耳", "扫罗", "约押",
    "摩押人", "亚捌人", "亚捌", "以东人", "亚述", "巴比伦", "波斯", "居鲁士", "古列",
    "尼尼微", "推罗", "西顿", "西顿人", "以撒哈顿", "西拿基立", "亚哈斯", "希西家",
    "耶罗波安", "罗波安", "耶洗别", "亚哈", "耶户", "耶斯别",
    "法老", "摩西", "亚伯拉罕", "罗得", "麦基洗德", "撒冷王", "基大老玛",
    "所多玛人", "蛾摩拉人", "以利以谢", "幔利", "以实各", "亚乃", "以撒", "以诺",
    "玛土撒拉", "拉麦", "闪", "含", "雅弗", "该南", "该隐", "塞特",
    "尼希米", "以斯拉", "尼利基米", "尼利巨", "基大老玛",
]

RESIDENT = {"yahweh": ("耶和华（万军之耶和华）", "立约之神 · 万军之主 · 全卷的说话者"),
            "isaiah": ("以赛亚", "南国先知 · 以赛亚书作者 · 全卷的传话人")}

TAGS = {
    "亚伯兰": ["旧约", "人物", "先祖"], "撒莱": ["旧约", "人物", "先祖"],
    "夏甲": ["旧约", "人物", "使女"], "以实玛利": ["旧约", "人物", "先祖"],
    "摩西": ["旧约", "人物", "先知"], "亚伦": ["旧约", "人物", "祭司"],
    "大卫": ["旧约", "人物", "君王"], "所罗门": ["旧约", "人物", "君王"],
    "约瑟": ["旧约", "人物", "先祖"], "雅各": ["旧约", "人物", "先祖"],
    "以撒": ["旧约", "人物", "先祖"], "以扫": ["旧约", "人物", "先祖"],
    "尼尼微": ["旧约", "国家", "列国"], "推罗": ["旧约", "城邑", "列国"],
    "西顿": ["旧约", "城邑", "列国"], "巴比伦": ["旧约", "国家", "列国"],
    "亚述": ["旧约", "国家", "列国"], "波斯": ["旧约", "国家", "列国"],
    "居鲁士": ["旧约", "君王", "列国"], "法老": ["旧约", "君王", "列国"],
    "希西家": ["旧约", "君王", "犹大"], "西拿基立": ["旧约", "君王", "列国"],
    "耶洗别": ["旧约", "人物", "王后"], "所多玛人": ["旧约", "群体", "列国"],
    "麦基洗德": ["旧约", "人物", "祭司"], "以诺": ["旧约", "人物", "先祖"],
    "挪亚": ["旧约", "人物", "先祖"], "以利以谢": ["旧约", "人物", "无名者"],
}


def slug(name):
    s = re.sub(r"[（(].*?[)）]", "", name)
    s = re.sub(r"[^0-9a-zA-Z一-鿿]", "", s).lower()
    return s or "x"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("--json", help="把骨架写到该文件")
    args = ap.parse_args()
    cid = args.cid
    path = os.path.join(ROOT, "%s.html" % cid)
    if not os.path.exists(path):
        raise SystemExit("找不到 %s" % path)
    h = io.open(path, encoding="utf-8").read()
    body = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    body = re.sub(r"<[^>]+>", "", body)

    freq = []
    for n in set(NAMES):
        c = body.count(n)
        if c:
            freq.append((c, n))
    freq.sort(reverse=True)

    print("=== %s 的候选人物（按出现次数）===" % cid)
    for c, n in freq[:10]:
        print("  %-6s %d 次" % (n, c))
    if not freq:
        print("  （未匹配到常见人名；请自行判断本章的核心人物）")

    if not args.json:
        return

    cards = []
    for rid, (name, role) in RESIDENT.items():
        cards.append({
            "id": rid, "name": name, "aka": [], "star": 1, "role": role,
            "relation": "【待补：与本章核心人物的亲属、师承或敌对关系，一行讲清】",
            "first": "【待补：首次出现的书卷缩写 + 章:节】",
            "key": ["【待补：2–4 处关键经节，格式如 赛40:1】"],
            "one": "【待补：≤60 字，一句话记住他，要带张力，不要履历】",
            "avoid": "【待补：最容易被混同的地方，指向要具体】",
            "tags": ["旧约", "神", "核心"] if rid == "yahweh" else ["旧约", "先知", "核心"],
            "chapters": [cid],
        })
    for c, n in freq[:4]:
        nm = n
        cards.append({
            "id": "%s-%s" % (slug(nm), cid.split("-")[1]),
            "name": nm, "aka": [], "star": 1,
            "role": "【待补：12 字以内，身份 + 在本章的作用】",
            "relation": "【待补：亲属、师承、敌对或对立关系，一行讲清】",
            "first": "【待补：首次出现的书卷缩写 + 章:节】",
            "key": ["【待补：2–4 处关键经节】"],
            "one": "【待补：≤60 字，一句话记住他，要带张力】",
            "avoid": "【待补：最容易被混同的地方】",
            "tags": TAGS.get(nm, ["旧约", "群体", "列国"]),
            "chapters": [cid],
        })

    with io.open(args.json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print()
    print("骨架已写入 %s：%d 条（yahweh / isaiah 为常驻 ★★★，另 %d 条候选待你补写 prose 字段）"
          % (args.json, len(cards), len(cards) - 2))
    print("补完后合并：py scripts\\merge_people.py %s --write" % args.json)


if __name__ == "__main__":
    main()
