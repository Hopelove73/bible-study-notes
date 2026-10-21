# 写手规格 · Writer Spec

写一章精读笔记时必须遵守的全部技术规格。**先读这份，再读模板标杆。**

## 0. 必读

1. `D:\圣经笔记\skill\.agents\skills\bible-study-note\SKILL.md`
2. `D:\圣经笔记\skill\.agents\skills\bible-study-note\references\template-spec.md`（验收标准）
3. `D:\圣经笔记\skill\.agents\skills\bible-study-note\references\content-rules.md`
4. `D:\圣经笔记\skill\.agents\skills\bible-study-note\references\genre-rules.md`
5. `D:\圣经笔记\skill\.agents\skills\bible-study-note\references\review-checklist.md`
6. **标杆成品**：`D:\圣经笔记\skill\isa-16.html`（整份读完，DOM 结构、class 名、排版、语气全部照它）
7. 经文源：`verses\<id>.json`

## 1. 只写一个文件

只写 `<id>.html`。**禁止**改动 `assets\people.js`、`index.html`、`books\`、`verses\`、`reviews\`、其他任何章节文件。不要跑 git 命令，不要给别的文件加只读属性。

## 2. 文件骨架

- 文件名 `<id>.html`；`<body data-chapter="<id>" data-verses="<N>">`（N = 本章节数）
- 12 个 `<section id="...">` 齐全且**顺序固定**：
  `before / bg / overview / map / reading / key / theology / prayer / apply / tasks / review / refs`
- 顶栏五项（品牌链接、人物总表、总目录、`#themeBtn`、`#doneBtn`）
- `.hero` 内：`<h1>`（含 `class="book"` 与 `class="num"`）、`class="thesis"`、**恰好一个** `class="meta"`（内含 ≥5 个 `<span>`）、`class="golden"`（金句 + 出处）
- `nav.toc-rail` 内 12 个 `<a href="#...">`，锚点顺序与 section 一致
- 文末 `<script src="assets/people.js"></script>` 与 `<script src="assets/app.js"></script>`
- `<footer>` 照标杆

## 3. 各模块硬要求

| 模块 | 要求 |
|---|---|
| `#before` | 一句 lead + 3 个观察问题（`table.tbl`）+ 「本章在全书的位置」`h3` + `ul.plain` |
| `#bg` | **恰好 5 个** `<div class="bg-cell">`，`<h4>` 依次为：历史 / 地理 / 文化 / 文学 / 救赎史；每格 120–320 字，**整节 ≥600 字** |
| `#overview` | 概述 + 一句话概括 + **一个** `<table class="tbl">`（5–8 行数据行） |
| `#map` | 导言 + `.mindmap` 内 3–6 条 `<li><b>` + `.flow` 内 3–10 个 `class="pill"`（箭头 `<span class="arrow">→</span>`）+ ≥1 条 note |
| `#reading` | **6–12 个** `<article class="seg">`（见下） |
| `#key` | **3–5 个** `<div class="kv">`（见下） |
| `#theology` | 3–5 个 `<h3>`（神 / 人 / 基督 / 福音 / 门徒） |
| `#prayer` | `<div class="prayer">` 内若干 `<p>` + `<p class="amen">阿们。</p>` + 1 条 note |
| `#apply` | **1 个** `<div class="apply-main">`（`<h3>本周一个行动</h3>` + 对象/时间/动作/可验证）+ **3–5 个** `<div class="scene">` + **2 条** 辅助操练 note |
| `#tasks` | **恰好 4 个** `<div class="taskgroup">`，共 **8–12 个** `<input type="checkbox">`；末尾 `<textarea id="quickNote">` + `<div class="people-grid" id="chapterPeople" data-chapter="<id>">` |
| `#review` | **恰好 3 个** `<details>`（`<summary>` + `<div class="ans">`）+ 本周背诵（`<div class="scripture">`）+ 下一章预告 |
| `#refs` | 三级标注表 `<table class="tbl">`（**恰好 3 行**数据行）+ `<ul class="plain">` 内 **≥4 条** `<li>` + 免责说明 |

### `.seg` 结构

```html
<article class="seg">
  <div class="seg-head"><span class="seg-idx">SEG 01</span><h3>判断句标题（6–14 字）</h3><span class="seg-ref">章:节</span></div>
  <div class="scripture"><p><sup>1</sup>经文…</p>…</div>
  <div class="kw"><span>「关键词」<i>中文释义</i></span>…</div>
  <div class="body"><p>…250–600 字…</p></div>
  <div class="note note--christ"><span class="tag">🟧 与基督的关联</span><p>…</p></div>
  <div class="note note--warn"><span class="tag">🟨 注释书观点 · …</span><p>…</p></div>
</article>
```

- 每节必须含：seg-head / scripture / kw / body / **至少 1 条 note--christ**
- scripture 的节号**连续、不重复**，合起来覆盖全章；经文**逐字**取自 `verses\<id>.json`
- 段落标题是**判断句**，不许「关于…」「第一段…」
- `kw` 用中文关键词 + 中文释义，**不要编造希伯来文/希腊文**

### `.kv` 结构

```html
<div class="kv">
  <div><div class="kv-ref">GENESIS 28:13</div><blockquote>经文原文</blockquote></div>
  <ol class="steps">
    <li><b>上下文</b><span>…</span></li>
    <li><b>字词</b><span>…</span></li>
    <li><b>神学</b><span>…</span></li>
    <li><b>应用</b><span>…</span></li>
  </ol>
</div>
```

四步标签顺序固定：上下文 / 字词 / 神学 / 应用；每步 30–100 字；blockquote 必须逐字取自本章经文。

## 4. 三级标注

| class | emoji | 含义 |
|---|---|---|
| `note--info` | 🟦 | 经文直述，和合本直接支持 |
| `note--warn` | 🟨 | 注释书观点，**必须并列呈现分歧**，不替读者裁判 |
| `note--christ` | 🟧 | 由经文推导的推论，必须能被读者分辨 |

每条 note 内**恰好一个** emoji，用 `<span class="tag">🟦 标签名</span><p>…</p>`。

## 5. 内容纪律

- **描述性 ≠ 规范性**：历史记载不是对读者的命令
- **引文纪律（最重要）**：正文里凡是加引号的经文，必须与 `verses\<id>.json` **逐字一致**；需要省略就用「……」标出
- **推论 ≠ 神的话**：禁用「神今天对你说」「主要你」「神绝不会让你」「只要相信就一定会」「家人们」「宝子们」「绝绝子」「不得不说」「说实话」
- 禁占位符（TODO / 待补充 / Lorem / XXX / {{ }}）
- 禁外部链接（任何 `http://` `https://`）、禁外链 `<img>`、禁新 CSS 类、禁 emoji 图标
- 本地链接只能指向真实存在的文件（`index.html`、`people.html`、`assets/style.css`）
- 释经分歧必须**并列**呈现并标 🟨，不得替读者裁决
- 语气：耐心的老师；全书最多 2 个感叹号；用「你」不用「我们大家」；引用经文用「」
- 字数：短章（≤25 节）5500–9000；标准章（26–50 节）7000–11000；长章（>50 节）9000–12000

## 6. 人物表

- 每章**恰好 3 位 ★★★**（`star: 1`）：`yahweh`、`isaiah` 为常驻，另加本章专属 1 位
- 卡片字段：`id / name / aka / star / role / relation / first / key / one / avoid / tags / chapters`
- `one` ≤60 字，带张力不要履历；`avoid` 要具体指向最易混同处
- 合并前先 grep 已有 id，**同一 id 不要重复建卡**
- 骨架可以用：`py scripts\people_card.py <id> --json logs\people_<id>.json`（它会列出本章人名候选并生成待填字段的骨架），补实后：
  `py scripts\merge_people.py logs\people_<id>.json --write`

## 7. 验收（两个都要过）

```
cd D:\圣经笔记\skill
py .agents\skills\bible-study-note\scripts\check_note.py <id>.html
py scripts\qa_check.py <id>
```

- `check_note.py`：**除 A17（人物表）外所有 P0 必须全过**；A17 要在合并人物后转绿
- `qa_check.py`：凡报「引文不符」的**必须全部改准**；报告在 `logs\qa_report_*.txt`
- 收尾前跑一次全库体检 `py scripts\doctor.py`，确认自己这一章干净了再交付
