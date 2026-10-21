# -*- coding: utf-8 -*-
"""shim：禁止把「每章一张专属卡」的人物表合并成「一个人一张跨章卡」。

理由（数据模型，不是口味问题）：
    people.js 里 star 是每张卡一个值，chapters 是这张卡出现的章节。
    A17 要求每章恰好 3 位 ★★★。
    把同一个人跨章的专属卡合并成一张跨章卡，就会同时占掉它覆盖的每一章的
    ★★★ 名额；而且合并后卡片只剩一章的 prose（例如「亚伯拉罕」那张卡里
    写着以赛亚书 41 章的话，却挂着创世记 12–23 章），内容就是错的。

正确的做法：
    每章专属人物单独建卡（id 用 <人物>-<章号>，chapters 只含本章）；
    两位常驻卡 yahweh / isaiah 的 chapters 可以跨章。

检查与修复：
    py scripts\\fix_people.py --check     查 A17
    py scripts\\fix_people.py --repair    用已知好样本自愈
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(
    "[已停用] consolidate_people.py 已被停用：人物表采用「每章一张专属卡 + 两位常驻」模型，\n"
    "        跨章合并会让每章的 ★★★ 名单超员或缺失，并且把卡片内容写错。\n"
    "        需要检查/修复请用：D:\\圣经笔记\\skill\\scripts\\fix_people.py --check / --repair",
    file=sys.stderr,
)
sys.exit(2)
