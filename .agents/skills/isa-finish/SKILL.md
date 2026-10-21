---
name: isa-finish
description: "把以赛亚书 1–66 章的精读笔记全部做完，并保证每个会话结束前都有交付。监督型技能：任何时候接手这个项目，都要先盘点进度、派活写作、独立复核、合并人物表、重建目录、提交推送，然后继续下一批，直到 66 章全部通过校验。Used for: 继续写以赛亚书、finish Isaiah notes、接着上一批写、把这卷书写完、章节还没写完、supervise/监督、不要停、继续干活、重开一个会话继续。Triggers: 以赛亚书, 继续, 接着写, 写完这一卷, 监督, supervisor, continue, resume, next batch."
---

# 以赛亚书全书续写 · Supervisor

这个项目在 `D:\圣经笔记\skill`（Windows）。目标：**以赛亚书 1–66 章，每章一页 HTML 精读笔记，全部通过 `check_note.py` 的 P0 校验并上线**。

你在这里的角色是**总编 + 监工**。写作可以交给子代理，但验收、合并、登记、推送必须自己做，而且**不许在还有章节没写完的时候停下**。

## 0. 每次接手先做这三件事

```powershell
Set-Location "D:\圣经笔记\skill"
py scripts\status.py
```

`scripts/status.py` 会输出：已完成章数、缺哪几章、哪几章只差人物表（A17）、哪几章有实质错误。
**它的输出决定你这一轮要干什么。** 不要凭印象判断进度。

再读一次 `assets/books.js` 确认书卷 id（`isa` = 以赛亚书，66 章）与 `verses/isa-XX.json` 是否存在。

## 1. 铁律（与 bible-study-note 一致）

1. 经文只能逐字取自 `verses/isa-XX.json`，每节恰好一次。
2. 三级标注强制：`note--info`=🟦，`note--warn`=🟨，`note--christ`=🟧，每条 note 只有一个 emoji。
3. 禁用「神今天对你说」「主要你」「神绝不会让你」「只要相信就一定会」等句式。
4. 每章**恰好 3 位 ★★★**，且这 3 位的 `chapters` 必须含本章。
5. 12 个 section 顺序固定：`before / bg / overview / map / reading / key / theology / prayer / apply / tasks / review / refs`。
6. 释经分歧（童女/年轻女子、名号的两种读法、千年王国等）**并列呈现，不替读者裁判**，标 🟨。
7. 不虚构引文、不编造原文词（kw 用中文关键词 + 释义）。

细则看 `.agents/skills/bible-study-note/references/`，标杆成品看 `isa-01.html`。

## 2. 一轮的标准流程

### 第 1 步：派活（低并发！）

- **同时最多 2–3 个子代理**。超过 4 个会触发 API 限流（"Rate limit exceeded"），之前的批次就是这么失败的。
- 每个子代理只写**一个** `isa-XX.html`，**禁止**碰 `assets/people.js`、`index.html`、`books/`、其他章节。
- prompt 模板：给章节号、必须读的文件列表、本章要点（史实/释经分歧/易错点）、硬性要求、验收命令、交付报告格式。
- 子代理报「Rate limit exceeded」时：先看文件是否已落盘（多半已写完，只是最后汇报时断线），落盘了就直接进入验收；没落盘就**自己写这一章**，不要无限重试。

### 第 2 步：独立复核（不信子代理自述）

```powershell
py scripts\check_note.py isa-XX.html
```

只有 **A17（人物表）** 未过是允许的残留——那是第 3 步的事。其余任何 P0 不过都要修到过。
其他辅助脚本在 `C:\Users\admin\AppData\Local\Temp\opencode\`：`audit.py`（批量统计+扫可疑词）、`extract.py`（抽 section 纯文本供人工审查）。

### 第 3 步：合并人物表

- 写一个 JSON 数组（字段：`id / name / aka / star / role / relation / first / key / one / avoid / tags / chapters`）到临时目录。
- 合并：
  ```powershell
  py "C:\Users\admin\AppData\Local\Temp\opencode\merge_people.py" "<json路径>" --write
  ```
- `yahweh` 与 `isaiah` 作为常驻 ★★★，每章再加 1 位本章专属 ★★★。已有 id 不要新建重复条目；需要**替换**章节归属时在 JSON 里加 `"_replace_chapters": true`。
- 合并后重跑 `check_note.py`，A17 必须转绿。

### 第 4 步：审查报告 + 目录重建 + 提交

```powershell
py "C:\Users\admin\AppData\Local\Temp\opencode\gen_review.py" isa-XX ...
py scripts\reg_index.py --write
git add -A
git -c user.name="Hopelove73" -c user.email="Hopelove73@users.noreply.github.com" commit -m "..."
git push origin main
```

`scripts/reg_index.py --write` 会同时更新首页目录和 `books/<书卷id>.html` 的章节网格——**这一步不能省**，否则新章节不会出现在书卷页里。

git 不在 PATH 里，用绝对路径：`C:\Program Files\Git\cmd\git.exe`。网络不稳时重试；push 失败要重试到成功。

## 3. 停下来的条件

只有**全部 66 章都通过 P0**（`py scripts\status.py` 退出码 0）才允许结束。

如果一轮里做不完（限流、上下文接近上限），**不要停**：直接开始下一批派活。
如果你的会话即将结束，**先把已完成的部分提交推送**，然后在回复里写清楚「下一轮从第 N 章开始」，让新会话接手。

## 4. 自我监督（重要）

`scripts/continue_isa.ps1` 是本项目的自动续写监督器：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\continue_isa.ps1
```

它会循环：查状态 → 调 `opencode-cli.exe run --auto` 开新会话继续写 → 遇到限流就退避重试 → 直到 66 章全部完成。
**只要它还在跑，这个项目就不会停。** 你接手时先看看 `logs/continue_isa.log`，确认监督器状态；不要和监督器同时大批量派活，以免撞车与限流。
