# -*- coding: utf-8 -*-
"""全库错别字/笔误扫描（只读）。

检查规则：
  T1 叠字：功能字叠用（的的/了了/是是……）——排除合法叠词
  T2 相邻重复串：2-6 字片段紧挨着重复（如「的以色列的以色列」）
  T3 易错词表：高置信错词 -> 正词（含和合本用字规范：撒但/马利亚/阿们…）
  T4 连续标点：。。 ，， 、、 ；； ：： ！！ ？？
  T5 「」配对：段内引号数不平衡

跳过区域：<div class="scripture">、<blockquote>（经文，另有 qa_check 兜底）
用法： py scripts\\_typo_scan.py [章节id...]
报告： logs\\typo_scan.txt
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import ROOT, chapter_file, scan_chapters

LOG = os.path.join(ROOT, "logs", "typo_scan.txt")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# T1：功能字叠用（这些叠用几乎必然是笔误）
DOUBLED = ["的的", "了了", "是是", "在在", "和和", "与与", "也也", "都都",
           "就就", "要要", "我我", "你你", "他他", "她她", "它它", "们们",
           "不不", "很很", "又又", "还还", "却却", "但但", "而而", "或或",
           "被被", "把把", "让让", "向向", "从从", "对对", "为为", "已已",
           "才才", "再再", "越越", "只只", "并并", "且且", "即即", "既既"]
T1_RE = re.compile("|".join(DOUBLED))

# T2：相邻重复串（2-6 字）
REP_RE = re.compile(r"([\u4e00-\u9fff]{2,6})\1")
# 合法重复（叠词/修辞）白名单
REP_OK = {
    "一个一个", "一件一件", "一章一章", "一节一节", "一天一天", "一年一年",
    "一代一代", "一步一步", "一句一句", "一段一段", "一点一点", "一样一样",
    "一批一批", "一群一群", "一家一家", "一户一户", "一座一座", "一层一层",
    "一对一对", "一双一双", "两次两次", "三番五次", "思想思想", "讨论讨论",
    "研究研究", "考虑考虑", "商量商量", "彼此彼此", "意思意思", "活动活动",
    "看看", "想想", "试试",
}

# T3：易错词表（错 -> 对）。只收高置信、本项目语境下几乎不会误伤的。
# 已剔除的误报规则（2026-11-17 全库复核，命中全为跨词边界）：
#   利末（耶利末/米利末人名）、在来（在来世/在来 12:1 希伯来书）、在次（在次序/在次子）、
#   在也（现在也/同在也）、既使（既+使，和合本赛 66:9 原有用法）、做下（做下一件事）、
#   周未（本周未做到）、末来（终末来）、自已（来自已）、安照（罗波安照）、
#   己经（自己经过）、阿门（《阿门尼莫普训言》）
TYPO_MAP = [
    ("按装", "安装"), ("按排", "安排"),
    ("座落", "坐落"),   # 注意「宝座落定」类误报需人工分辨
    ("那怕", "哪怕"),
    ("帐蓬", "帐篷"),
]
# 正名归一（正则，带守卫）：和合本用字
TYPO_RE = [
    (re.compile(r"(?<!撒)(?<!亚)玛利亚"), "马利亚"),
    (re.compile(r"撒马利亚"), "撒玛利亚"),
    (re.compile(r"撒旦"), "撒但"),
    (re.compile(r"尼哥底姆"), "尼哥底母"),
    (re.compile(r"法利塞"), "法利赛"),
    (re.compile(r"吕便"), "流便"),
]

# T4：连续标点
PUNCT_RE = re.compile(r"。。|，，|、、|；；|：：|！！|？？")

STRIP_ZONES = [
    re.compile(r'<div class="scripture">.*?</div>', re.S),
    re.compile(r"<blockquote>.*?</blockquote>", re.S),
    re.compile(r"<script>.*?</script>", re.S),
    re.compile(r"<style>.*?</style>", re.S),
]


def visible_prose(html):
    """去经文区块、去标签后的可见散文文本。"""
    for z in STRIP_ZONES:
        html = z.sub(" ", html)
    return re.sub(r"<[^>]+>", " ", html)


def scan_text(text):
    """返回 [(规则, 位置片段, 建议)]。"""
    hits = []
    for m in T1_RE.finditer(text):
        ctx = text[max(0, m.start() - 12):m.end() + 12]
        hits.append(("T1", ctx, "叠字「%s」" % m.group(0)))
    for m in REP_RE.finditer(text):
        if m.group(0) in REP_OK:
            continue
        ctx = text[max(0, m.start() - 10):m.end() + 10]
        hits.append(("T2", ctx, "相邻重复「%s」" % m.group(0)))
    for wrong, right in TYPO_MAP:
        for m in re.finditer(re.escape(wrong), text):
            ctx = text[max(0, m.start() - 10):m.end() + 10]
            hits.append(("T3", ctx, "「%s」应为「%s」" % (wrong, right)))
    for rx, right in TYPO_RE:
        for m in rx.finditer(text):
            ctx = text[max(0, m.start() - 10):m.end() + 10]
            hits.append(("T3", ctx, "「%s」应为「%s」" % (m.group(0), right)))
    for m in PUNCT_RE.finditer(text):
        ctx = text[max(0, m.start() - 12):m.end() + 12]
        hits.append(("T4", ctx, "连续标点「%s」" % m.group(0)))
    return hits


def check_quotes(text):
    """T5：按段落检查「」配对。"""
    hits = []
    for para in re.split(r"\s{2,}", text):
        if para.count("「") != para.count("」"):
            hits.append(("T5", para[:60], "「」不配对（%d 开 / %d 合）"
                         % (para.count("「"), para.count("」"))))
    return hits


def main():
    ids = sys.argv[1:] or scan_chapters()
    out = ["错别字扫描报告", "=" * 40, ""]
    total = 0
    bad_ch = 0
    for cid in ids:
        p = chapter_file(cid)
        if not os.path.exists(p):
            continue
        html = io.open(p, encoding="utf-8", newline="").read()
        text = visible_prose(html)
        hits = scan_text(text) + check_quotes(text)
        if hits:
            bad_ch += 1
            out.append("■ %s（%d 条）" % (cid, len(hits)))
            for rule, ctx, msg in hits:
                out.append("  [%s] %s｜…%s…" % (rule, msg, ctx.strip()))
                total += 1
    out.insert(2, "扫描 %d 章，命中 %d 章，共 %d 条" % (len(ids), bad_ch, total))
    io.open(LOG, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("\n".join(out[:6]))
    print("报告：%s" % LOG)


if __name__ == "__main__":
    main()
