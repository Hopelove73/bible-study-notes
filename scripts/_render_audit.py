# -*- coding: utf-8 -*-
"""L1 渲染验证（只读）：无头 Chrome 加载每章，探针测量排版指标。

指标：
  overflowX  页面横向溢出
  tables     每张 .tbl 表格：首列宽度占比 share(%)、最高行高 maxRowH(px)
  mm         思维导图 ul.mm 的 li 数量（-1 = 页面没有 mm）
  mmBad      mm 文本里含 '<'（标签当文本渲染的残骸）
  jsErr      window.onerror 捕获到的脚本错误

用法：
  py scripts\\_render_audit.py --sample   # 每卷 1 章 + 近期修复章（快检）
  py scripts\\_render_audit.py            # 全量 1189 章
报告： logs\\render_audit.json / logs\\render_audit.txt
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import ROOT, chapter_file, scan_chapters, BOOK_DIRS

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LOG_JSON = os.path.join(ROOT, "logs", "render_audit.json")
LOG_TXT = os.path.join(ROOT, "logs", "render_audit.txt")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROBE = """<script>
window.__errs = [];
window.onerror = function(m){ window.__errs.push(String(m).slice(0,120)); };
window.addEventListener('load', function(){
  setTimeout(function(){
    try{
      var r = {};
      r.jsErr = window.__errs;
      r.sw = document.documentElement.scrollWidth;
      r.iw = window.innerWidth;
      r.overflowX = r.sw > r.iw + 1;
      r.tables = [];
      document.querySelectorAll('table.tbl').forEach(function(t){
        var fr = t.querySelector('tr');
        var share = null;
        if (fr && fr.cells.length > 1 && t.offsetWidth > 0)
          share = Math.round(fr.cells[0].offsetWidth / t.offsetWidth * 100);
        var mh = 0;
        t.querySelectorAll('tr').forEach(function(tr){ if (tr.offsetHeight > mh) mh = tr.offsetHeight; });
        r.tables.push({share: share, mh: mh, inBefore: !!t.closest('#before')});
      });
      var mm = document.querySelector('ul.mm');
      r.mm = mm ? mm.querySelectorAll('li').length : -1;
      r.mmBad = mm ? (mm.textContent.indexOf('<') >= 0) : false;
      document.title = 'PROBE:' + JSON.stringify(r);
    }catch(e){ document.title = 'PROBE:{"err":1}'; }
  }, 300);
});
</script>
</body>"""

TITLE_RE = re.compile(r"<title>PROBE:(\{.*?\})</title>", re.S)


def probe_one(cid, width, height):
    src = chapter_file(cid)
    d = os.path.dirname(src)
    tmp = os.path.join(d, ".__probe_%s.html" % cid)
    try:
        raw = io.open(src, encoding="utf-8", newline="").read()
        if "</body>" not in raw:
            return {"err": "no </body>"}
        io.open(tmp, "w", encoding="utf-8", newline="").write(raw.replace("</body>", PROBE, 1))
        url = "file:///" + tmp.replace("\\", "/")
        out = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
             "--virtual-time-budget=6000",
             "--window-size=%d,%d" % (width, height),
             "--dump-dom", url],
            capture_output=True, timeout=40)
        dom = out.stdout.decode("utf-8", "replace")
        m = TITLE_RE.search(dom)
        if not m:
            return {"err": "probe not found (title missing)"}
        return json.loads(m.group(1))
    except subprocess.TimeoutExpired:
        return {"err": "timeout"}
    except Exception as e:
        return {"err": str(e)[:120]}
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def evaluate(cid, r, mobile=False):
    """把指标转成问题清单。

    阈值依据 2026-11-17 抽样（76 章）基线标定：
    - 移动端模板统一 sw=540（toc-rail 溢出 8px，模板级问题另案处理），
      故移动端溢出阈值放宽到 >560 才算章节级异常
    - 桌面表格行高样本最大 96px；psa-71 型挤压 bug 的行高会超过一屏 → 500px 阈值
    - before 段观察问题表首列是长段落，正常 share 约 50-70%；>80% 说明第二列被挤没
    """
    probs = []
    if "err" in r:
        return ["渲染失败：%s" % r["err"]]
    if r.get("jsErr"):
        probs.append("JS 报错：%s" % "; ".join(r["jsErr"][:2]))
    overflow_limit = 560 if mobile else 1
    if mobile:
        if r.get("sw", 0) > overflow_limit:
            probs.append("横向溢出超基线：scrollWidth=%s" % r.get("sw"))
    elif r.get("overflowX"):
        probs.append("横向溢出：scrollWidth=%s > innerWidth=%s" % (r.get("sw"), r.get("iw")))
    if r.get("mmBad"):
        probs.append("思维导图把标签渲染成了文本")
    if r.get("mm") == -1:
        probs.append("缺少思维导图 ul.mm")
    elif r.get("mm") == 0:
        probs.append("思维导图没有 li 节点")
    for t in r.get("tables", []):
        if t.get("mh", 0) > 500:
            probs.append("表格存在超高行：%spx（before 段：%s）" % (t["mh"], t.get("inBefore")))
        if not mobile and t.get("inBefore") and t.get("share") is not None and t["share"] > 80:
            probs.append("before 段表格首列占比过高：%s%%" % t["share"])
    return probs


def main():
    sample = "--sample" in sys.argv
    ids = scan_chapters()
    if sample:
        picks = set()
        for code in BOOK_DIRS:
            for i in ids:
                if i.startswith(code + "-"):
                    picks.add(i)
                    break
        picks |= {"dan-11", "dan-12", "mat-04", "mat-07", "psa-86",
                  "psa-87", "psa-89", "1ch-15", "hos-04", "hos-05"}
        ids = sorted(picks)
    results = {}
    done = [0]

    def work(cid):
        r = {"desktop": probe_one(cid, 1280, 900),
             "mobile": probe_one(cid, 390, 844)}
        results[cid] = r
        done[0] += 1
        if done[0] % 50 == 0:
            print("...已渲染 %d/%d" % (done[0], len(ids)), file=sys.stderr)

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(work, ids))

    bad = {}
    for cid, r in results.items():
        probs = evaluate(cid, r.get("desktop", {}), mobile=False) + \
                ["[移动端] " + p for p in evaluate(cid, r.get("mobile", {}), mobile=True)]
        if probs:
            results[cid]["problems"] = sorted(set(probs))

    io.open(LOG_JSON, "w", encoding="utf-8", newline="\n").write(
        json.dumps(results, ensure_ascii=False, indent=1))

    lines = ["L1 渲染验证报告", "=" * 40,
             "渲染 %d 章（桌面 1280 + 移动 390）" % len(results), ""]
    n_bad = 0
    for cid in sorted(results):
        probs = results[cid].get("problems")
        if probs:
            n_bad += 1
            lines.append("■ %s" % cid)
            lines.extend("  " + p for p in probs)
    lines.insert(3, "异常章节 %d 个" % n_bad)
    io.open(LOG_TXT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("\n".join(lines[:10]))
    print("报告：%s" % LOG_TXT)


if __name__ == "__main__":
    main()
