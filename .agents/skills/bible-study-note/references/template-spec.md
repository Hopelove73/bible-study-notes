# 模板规格 · Template Spec

> 这份文件是**验收标准**，不是建议。`check_note.py` 按它判定 P0/P1。

## 1. 文件契约

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>马可福音 第2章 · 圣经精读笔记</title>
  <link rel="stylesheet" href="assets/style.css">
  <script>/* 主题早读，防闪烁 */</script>
</head>
<body data-chapter="mark-02" data-verses="28">
```

- `data-chapter`：必须与文件名同 id
- `data-verses`：本章节数，用于校验逐节覆盖
- 顶栏固定五项：品牌链接、人物总表、总目录、`#themeBtn`、`#doneBtn`

## 2. 骨架顺序（不可增删、不可换序）

```
.hero                 章节封面
.layout
 ├ nav.toc-rail       12 条目目录（00–10 + 附）
 └ main
    section#before    00 读前准备
    section#bg        01 章节背景（五格）
    section#overview  02 章节概述（含结构大纲表）
    section#map       03 思维导图
    section#reading   04 分段精读
    section#key       05 五处重点经文
    section#theology  06 神学要点
    section#prayer    07 祷告
    section#apply     08 生活应用
    section#tasks     09 本章任务
    section#review    10 复习与预告
    section#refs      附 资料来源
footer
```

**任何新板块（地图、原文对照、年表、视频）都必须先问用户。**

## 3. 每个模块的字段与预算

预算单位：中文字符（不含标签）。软区间，超出记 P1，不阻断，但要在审查报告里说明理由。

| # | 模块 | 必含元素 | 预算 |
|---|---|---|---|
| — | `.hero` | crumb、`h1`（`.book` + 主标题 + `.num`）、`.hero-num`、`.thesis`、`.meta`（≥5 项）、`.golden`（金句 + 出处） | thesis 60–160 |
| 00 | `#before` | 一句 lead + 3 个观察问题（`table.tbl`）+ 「本章在全书的位置」`h3` + `ul.plain` | 150–500 |
| 01 | `#bg` | 恰好 5 个 `.bg-cell`，标签依次：历史 / 地理 / 文化 / 文学 / 救赎史 | 每格 120–320 |
| 02 | `#overview` | 概述（150–300 字）+ 一句话概括 + `table.tbl` 结构大纲（5–8 行） | 250–700 |
| 03 | `#map` | 一句导言 + `.mindmap`（3–6 主分支）+ `.flow`（5–7 节点）+ ≥1 条 note | 80–400 |
| 04 | `#reading` | 6–12 个 `.seg`，见 §3.1 | 2500–9500 |
| 05 | `#key` | 3–5 个 `.kv`，每个 4 步，见 §3.2 | 600–1600 |
| 06 | `#theology` | 3–5 个 `h3` 小节（神 / 人 / 基督 / 福音 / 门徒） | 300–900 |
| 07 | `#prayer` | 一段按经文结构写的祷告 + `.amen` + 1 条操练 note | 200–500 |
| 08 | `#apply` | 1 个 `.apply-main` + 3–5 个 `.scene` + 2 条辅助操练 | 400–900 |
| 09 | `#tasks` | 4 组任务（观察 / 记忆 / 关联 / 输出），共 8–12 项 + `#chapterPeople` + `#quickNote` | 300–1000 |
| 10 | `#review` | 3 个 `details` 自测 + 背诵经文 + 下一章预告 | 250–700 |
| 附 | `#refs` | 三级标注表（3 行）+ 版本与参考（≥4 条）+ 免责说明 | 200–500 |

### 3.1 每个 `.seg` 必须包含

```html
<article class="seg">
  <div class="seg-head">
    <span class="seg-idx">SEG 01</span>
    <h3>段落标题（6–14 字，要有判断，不要「关于…」）</h3>
    <span class="seg-ref">1:1</span>
  </div>
  <div class="scripture">…逐节，<sup>N</sup>…</div>
  <div class="kw">…2–5 个原文词…</div>
  <div class="body">…250–600 字…</div>
  <div class="note note--warn">🟨 …</div>
  <div class="note note--christ">🟧 …</div>
</article>
```

- `.scripture` 里的节号必须**连续且不重复**，合起来覆盖全章
- `kw` 用 `<span>希腊文/希伯来文 <i>中文</i></span>`，没有原文把握就整块省略（不许编）
- 每个 seg 至少 1 条 `note--christ`；`note--warn` 可选
- 段落标题是**判断句**，不是目录词

### 3.2 每个 `.kv` 必须包含

```html
<div class="kv">
  <div>
    <div class="kv-ref">MARK 1:11</div>
    <blockquote>经文原文</blockquote>
  </div>
  <ol class="steps">
    <li><b>上下文</b><span>…</span></li>
    <li><b>字词</b><span>…</span></li>
    <li><b>神学</b><span>…</span></li>
    <li><b>应用</b><span>…</span></li>
  </ol>
</div>
```

四步标签固定为：**上下文 / 字词 / 神学 / 应用**。每步 30–100 字。
「字词」没有原文依据时，改写为句式或修辞观察，不许硬编希腊文。

## 4. 三级标注（强制）

| 标注 | class | 含义 | 用法 |
|---|---|---|---|
| 🟦 经文直述 | `note--info` | 和合本直接支持 | 可下断言 |
| 🟨 注释书观点 | `note--warn` | 历代注释传统 | 必须写「有几种解释」 |
| 🟧 推论 | `note--christ` | 由经文推导 | 必须能被读者分辨 |

任何 `.note` 必须带且只带一个 emoji 标签。正文里出现「多数解经家认为」也算 🟨，要放进 note，不要混在正文冒充事实。

## 5. 允许使用的组件（不要发明新的）

`card` `grid` `grid-2` `grid-3` `bg-grid` `bg-cell` `scripture` `kw` `note(--info/--warn/--christ)` `seg` `seg-head` `seg-idx` `seg-ref` `mindmap` `mm-root` `flow` `kv` `steps` `tbl` `prayer` `amen` `apply-main` `scene` `taskbar` `taskgroup` `task` `people-grid` `pcard` `flip` `quiz` `match` `details` `note`

需要新组件 → 先问用户，改 `style.css`，再写进本文件。

## 6. 明确禁止

- 新增 section / 改 section 顺序
- 用 emoji 当图标（三级标注的 🟦🟨🟧 除外）
- 圆角卡片 + 左侧彩色边框 + 投影（这是被否掉的设计）
- 外部 CDN、网络字体、`<img>` 外链
- 把整章经文一次性贴完再解释（必须分段）
- 「待补充」「TODO」「Lorem」
- 每节平均分配字数（按文体分段，不按节数分段）

## 7. 索引与人物

- `index.html`：新增一行 `.bookrow`，`data-chapter-progress="<id>"`，链接到本章
- `assets/people.js`：追加本章人物，`chapters: ["<id>"]`，id 全局唯一
- 每章 `star: 1` 恰好 3 位

字段与判定见 `people-rules.md`。
