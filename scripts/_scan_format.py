# -*- coding: utf-8 -*-
"""L0 结构扫描（只读）：全库章节 HTML 格式体检。

检查项：
  F1 单字符行：>=3 行连续、strip 后长度 1-2、同缩进（build.py 逐字符拆标签残骸的特征）
  F2 标签配对：html.parser 栈式校验，抓未闭合/多余闭合/交叉嵌套
  F3 转义泄漏：可见文本中出现 &lt;li&gt; 这类「标签被转义成文本」的残骸
  F4 链接/资源有效性：相对 href/src 指向的文件存在；页内锚点 #id 存在

用法： py scripts\\_scan_format.py
报告： logs\\format_scan.txt
"""
import io
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import ROOT, chapter_file, scan_chapters

LOG = os.path.join(ROOT, "logs", "format_scan.txt")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

ESC_LEAK = re.compile(r"&lt;\s*/?\s*(ul|ol|li|em|sup|sub|span|div|p|h[1-6]|strong|blockquote|table|tr|td|th)\b", re.I)
ATTR = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')


def scan_char_runs(lines):
    """返回 [(起始行, 长度, 样例)]：连续 >=3 行的单字符行段。"""
    runs = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if 0 < len(s) <= 2 and re.match(r"^[\s<>&/;=a-zA-Z-]{1,2}$", s) and not s.startswith("--"):
            indent = len(lines[i]) - len(lines[i].lstrip())
            j = i
            while j < len(lines):
                s2 = lines[j].strip()
                ind2 = len(lines[j]) - len(lines[j].lstrip())
                if 0 < len(s2) <= 2 and ind2 == indent and re.match(r"^[\s<>&/;=a-zA-Z-]{1,2}$", s2):
                    j += 1
                else:
                    break
            if j - i >= 3:
                sample = "".join(lines[k].strip() for k in range(i, min(j, i + 20)))
                runs.append((i + 1, j - i, sample))
            i = j
        else:
            i += 1
    return runs


class PairChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # 容错：浏览器会自动闭合 p/li/td 等，这里只对栈顶精确匹配，
        # 找不到时报错但不弹栈（避免级联误报）
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            return
        # 向内找：若有匹配说明中间有未闭合标签
        for k in range(len(self.stack) - 1, -1, -1):
            if self.stack[k][0] == tag:
                unclosed = self.stack[k + 1:]
                self.errors.append("第 %d 行 </%s> 闭合时，内有未闭合：%s"
                                   % (self.getpos()[0], tag,
                                      ", ".join("<%s>(第%d行)" % (t, p[0]) for t, p in unclosed[:4])))
                del self.stack[k:]
                return
        self.errors.append("第 %d 行多余的 </%s>（无对应开标签）" % (self.getpos()[0], tag))


def check_file(path):
    """返回 [(级别, 规则, 描述)]。级别：严重/提示。"""
    probs = []
    raw = io.open(path, encoding="utf-8", newline="").read()
    lines = raw.split("\n")

    # F1 单字符行
    for start, ln, sample in scan_char_runs(lines):
        probs.append(("严重", "F1", "第 %d 行起 %d 行单字符碎片（疑似标签被逐字符拆行）：%s..."
                      % (start, ln, sample[:30])))

    # F2 标签配对
    pc = PairChecker()
    try:
        pc.feed(raw)
        pc.close()
    except Exception as e:
        probs.append(("严重", "F2", "HTML 解析异常：%s" % e))
    for e in pc.errors[:10]:
        probs.append(("严重", "F2", e))
    for t, pos in pc.stack:
        probs.append(("严重", "F2", "<%s>（第 %d 行）到文件尾未闭合" % (t, pos[0])))

    # F3 转义泄漏
    for m in ESC_LEAK.finditer(raw):
        ln = raw.count("\n", 0, m.start()) + 1
        probs.append(("严重", "F3", "第 %d 行转义泄漏：%s" % (ln, m.group(0)[:30])))

    # F4 链接/资源
    fdir = os.path.dirname(path)
    ids_in_page = set(re.findall(r'id\s*=\s*"([^"]+)"', raw))
    for m in ATTR.finditer(raw):
        url = m.group(1)
        if re.match(r"^(https?:|mailto:|javascript:|data:)", url):
            continue
        ln = raw.count("\n", 0, m.start()) + 1
        if url.startswith("#"):
            if url[1:] and url[1:] not in ids_in_page:
                probs.append(("提示", "F4", "第 %d 行页内锚点 %s 不存在" % (ln, url)))
            continue
        target, _, frag = url.partition("#")
        tpath = os.path.normpath(os.path.join(fdir, target))
        if not os.path.exists(tpath):
            probs.append(("严重", "F4", "第 %d 行链接失效：%s" % (ln, url)))
        elif frag:
            try:
                traw = io.open(tpath, encoding="utf-8", newline="").read()
                if 'id="%s"' % frag not in traw and "id='%s'" % frag not in traw:
                    probs.append(("提示", "F4", "第 %d 行 %s 的目标锚点 #%s 不存在" % (ln, url, frag)))
            except Exception:
                pass
    return probs


def main():
    ids = scan_chapters()
    all_probs = {}
    for cid in ids:
        p = chapter_file(cid)
        if not os.path.exists(p):
            all_probs[cid] = [("严重", "F0", "章节文件不存在：%s" % p)]
            continue
        probs = check_file(p)
        if probs:
            all_probs[cid] = probs

    out = ["L0 结构扫描报告", "=" * 40,
           "扫描章节 %d 个，异常章节 %d 个" % (len(ids), len(all_probs)), ""]
    n_sev = sum(1 for ps in all_probs.values() for p in ps if p[0] == "严重")
    n_tip = sum(1 for ps in all_probs.values() for p in ps if p[0] == "提示")
    out.append("严重 %d 条 / 提示 %d 条" % (n_sev, n_tip))
    out.append("")
    for cid in sorted(all_probs):
        out.append("■ %s" % cid)
        for sev, rule, desc in all_probs[cid]:
            out.append("  [%s][%s] %s" % (sev, rule, desc))
    io.open(LOG, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("\n".join(out[:8]))
    print("报告：%s" % LOG)


if __name__ == "__main__":
    main()
