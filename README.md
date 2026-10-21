# 圣经精读笔记

一章一页的离线 HTML 笔记。双击 `index.html` 即可阅读，不需要服务器、不需要联网。

**在线阅读：** <https://hopelove73.github.io/bible-study-notes/>

## 目录

```
index.html                 总目录（旧约 39 卷 / 新约 27 卷）
books/                     66 卷书卷页（每卷一张章节进度表，脚本生成）
mark-01.html               马可福音 1 章
isa-01.html ~ isa-66.html  以赛亚书 1–66 章（逐章）
people.html                人物总表（跨章共用）
assets/                    style.css / app.js / people.js / books.js
scripts/                   目录与书卷页生成脚本
verses/                    已核对的和合本经文（只读）
_brief/                    每章立项卡
reviews/                   每章审查报告
.agents/skills/bible-study-note/    生成这一页的技能
```

## 目录怎么归类

首页和 `books/` 下的 66 个书卷页不是手写的，由 `scripts/reg_index.py` 扫描章节文件生成：

```powershell
py scripts\reg_index.py --write
```

规则只有一条：章节文件名必须是 `书卷id-章号.html`，例如 `isa-10.html`、`mark-03.html`。
书卷 id 与章数登记在 `assets/books.js`（旧约 39 卷 + 新约 27 卷，共 1189 章）。
脚本会：

- 把新章节自动补进首页对应书卷的章节条；
- 更新 `books/<书卷id>.html` 的章节网格（实线已上线，虚线待写）；
- 刷新首页的「已上线 / 收录书卷 / 人物档案」统计。

所以以后写完任何一卷的任何一章，只要文件名对，跑一次脚本就自动归位。

## 三级标注

| 标记 | 含义 |
|---|---|
| 🟦 经文直述 | 和合本直接支持 |
| 🟨 注释书观点 | 历代注释传统，会注明分歧 |
| 🟧 推论 | 由经文推导，需自行分辨 |

## 加一章（用技能）

在**本目录**打开 OpenCode，说「写马可福音第 3 章」即可。技能会自动走：
立项卡 → 取真经文 → 写正文 → 机械校验 → 44 条审查清单 → 更新索引与人物表。

手动跑也可以：

```bash
# 1. 建骨架（先不登记索引）
python .agents/skills/bible-study-note/scripts/new_chapter.py \
  --id mark-03 --book 马可福音 --book-en "THE GOSPEL OF MARK" \
  --chapter 3 --verses 35 --genre "叙事 · 古代传记" --segments 6 \
  --thesis "一句话主旨" --minutes 30 --no-index

# 2. 拉取并核对经文
python .agents/skills/bible-study-note/scripts/verify_verses.py \
  --book MRK --chapter 3 --out verses/mark-03.json

# 3. 写内容后校验
python .agents/skills/bible-study-note/scripts/check_note.py mark-03.html
python .agents/skills/bible-study-note/scripts/check_note.py mark-03.html --report
```

`check_note.py` 退出码为 0 才允许交付；报告写到 `reviews/<id>.txt`。

## 技能位置

技能本体在本目录 `.agents/skills/bible-study-note/`，并已通过目录联接挂到
`%USERPROFILE%\.agents\skills\bible-study-note`，所以在任何项目里都能调用；改一处，两边同步。

链接失效（例如移动了本目录）时重建：

```powershell
Remove-Item "$env:USERPROFILE\.agents\skills\bible-study-note" -Force
New-Item -ItemType Junction -Path "$env:USERPROFILE\.agents\skills\bible-study-note" `
  -Target "D:\圣经笔记\skill\.agents\skills\bible-study-note"
```

## 边界

- 和合本经文属公有领域，本笔记仅供个人研读，不用于出版或收费课程。
- 注释书观点一律转述并标 🟨，不整段复制。
- 凡标 🟧 的内容是推论，不是教义。
