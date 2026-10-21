---
name: bible-finish
description: "把圣经每一卷每一章的精读笔记全部做完，并保证每个会话结束前都有交付。监督型技能：任何时候接手这个项目，都要先盘点进度、派活写作、独立复核、合并人物表、重建目录、提交推送，然后继续下一批，直到 1189 章全部通过校验。Used for: 继续写圣经笔记、finish Bible notes、接着上一批写、把这本书写完、还没写完、监督、supervisor、不要停、继续干活、重开一个会话继续、over night 继续。Triggers: 继续, 接着写, 写完, 监督, supervisor, continue, resume, next batch, 圣经笔记, 以赛亚书, 旧约."
---

# 圣经精读笔记全书续写 · Supervisor

项目在 `D:\圣经笔记\skill`（Windows）。目标：**圣经 66 卷、1189 章，每章一页 HTML 精读笔记，全部通过 P0 校验 + 每章都有审查报告，并上线**。

你在这里的角色是**总编 + 监工**。写作可以交给子代理，但验收、合并、登记、推送必须自己做，而且**不许在还有章节没写完的时候停下**。

## 0. 每次接手先做这两件事

```powershell
Set-Location "D:\圣经笔记\skill"
py scripts\status.py
```

输出会告诉你：已完成多少章、缺哪些、哪些只差人物表、哪些缺审查报告、哪些有实质错误。
**以它的输出为准**，不要凭印象判断进度。

## 0b. 接手时先看这几样（都已自动化）

| 命令 | 作用 |
|---|---|
| `py scripts\doctor.py` | 全库体检：一次列出所有没过的章节与问题代码 |
| `py scripts\qa_check.py` | 内容体检：把正文里带出处的引文、`.kv` 重点经文、本周背诵段、下一章预告里的引文，逐条到 `verses\*.json` 里比对 |
| `py scripts\fix_verses.py --write` | 自动把 scripture 区块与 `verses\<id>.json` 对齐（修 A20） |
| `py scripts\fix_quotes.py` | 逐字校正正文里的引文（修 A24/A20 之外的口误） |
| `py scripts\claim.py <id>…` / `--release` / `--prune` / `--list` | 章节占用：派活前占住，避免两个写手抢同一章；`--prune` 清掉属主进程已退出的死锁 |
| `py scripts\people_card.py <id> --json <file>` | 列出本章人名候选并生成人物卡骨架（prose 字段自己补） |
| `py scripts\finalize.py --commit` | 补齐缺失的审查报告、重建目录、提交并推送 |
| `py scripts\extend_bg.py <id> <格名> <句子>` | 给背景格补字（修 A27） |

**纪律**：写手只写自己的 `<id>.html`；`assets\people.js`、`index.html`、`books\`、`reviews\` 由收尾环节统一处理。


## 1. 铁律

1. 经文只能逐字取自 `verses/<id>.json`，每节恰好一次。**任务书里给的要点可能与和合本原文不一致（出题的人也会记错），一律以 JSON 为准**；发现不一致就按 JSON 写，并在报告里指出。
2. 三级标注强制：`note--info`=🟦，`note--warn`=🟨，`note--christ`=🟧，每条 note 只有一个 emoji。
3. 禁用「神今天对你说」「主要你」「神绝不会让你」「只要相信就一定会」等句式。
4. 每章**恰好 3 位 ★★★**，且这 3 位的 `chapters` 必须含本章。
5. 12 个 section 顺序固定：`before / bg / overview / map / reading / key / theology / prayer / apply / tasks / review / refs`。
6. 释经分歧必须并列呈现、标 🟨，不替读者裁判。
7. 不虚构引文、不编造原文词。
8. **每章都要有 `reviews/<id>.txt` 审查报告**——`status.py` 会检查，缺了就算没做完。
9. 写作密度：段数宁少勿多（长章 6–8 段），但每段 `.body` 要写满 250 字以上；不要为凑总字数而把每段压薄。

细则见 `.agents/skills/bible-study-note/references/`，标杆成品见 `isa-01.html`（或任一已完成的卷）。

## 2. 一轮的标准流程

### 第 1 步：备经文

```powershell
py .agents\skills\bible-study-note\scripts\verify_verses.py --book GEN --chapter 1
```

书卷代码见该脚本里的 `BOOKS` 字典（GEN/EXO/…/REV）。落盘为 `verses/<id>.json`。
**不要凭记忆写经文。**

### 第 2 步：派活（低并发！）

- **同时最多 2–3 个子代理**。超过 4 个会触发 API 限流（"Rate limit exceeded"），之前 6 个并行就整批失败过。
- 每个子代理只写**一个** `<id>.html`；**禁止**碰 `assets/people.js`、`index.html`、`books/`、其他章节。
- **先占章再派活**：`py scripts\claim.py <id>…` 把本轮章节标为占用（`status.py --next` 会跳过被占用的章，监督器因此不会抢同一章），写完 `py scripts\claim.py --release <id>…` 释放。
- prompt 要给：章节号、必读文件、本章要点（史实 / 释经分歧 / 易错点）、硬性要求、验收命令、交付报告格式。
- 子代理报限流时：先看文件是否已落盘（多半已写完，只是最后汇报断线），落盘就直接进入验收；没落盘就**自己写这一章**，不要死磕重试。

### 第 3 步：独立复核（不信子代理自述）

```powershell
py .agents\skills\bible-study-note\scripts\check_note.py isa-XX.html
py scripts\qa_check.py isa-XX
```

`qa_check.py` 会把正文里带出处的引文、`.kv` 的重点经文、本周背诵段、下一章预告里的引文，逐条到 `verses\*.json` 里比对。凡报「引文不符」的**一律按和合本改准**——这是本项目最容易出错、也最伤信誉的地方。

只有 **A17（人物表）** 未过是允许的残留——那是下一步的事。其余任何 P0 不过都要修到过。
辅助脚本在 `C:\Users\admin\AppData\Local\Temp\opencode\`：`audit.py`（批量统计 + 扫可疑词）、`extract.py`（抽 section 纯文本供人工审查）。

### 第 4 步：合并人物表

- 写 JSON 数组（字段 `id / name / aka / star / role / relation / first / key / one / avoid / tags / chapters`）。
- 合并：`py scripts\merge_people.py "<json>" --write`（脚本自带互斥锁，可并发安全）
- `yahweh` 与 `isaiah` 为常驻 ★★★，每章再加 1 位本章专属 ★★★。已有 id 不要重复建条目；要**替换**章节归属时加 `"_replace_chapters": true`。
- 卡片的 `one` 要有观察力（≤60 字、带张力），`avoid` 要具体指出最易混同处——这两栏是人物表的价值所在，不要写套话。
- 骨架可以用 `py scripts\people_card.py <id> --json logs\people_<id>.json` 生成（它会列出本章人名候选），补实 prose 字段后再合并。
- 合并后重跑 `check_note.py`，A17 必须转绿。

### 第 5 步：审查报告 + 目录 + 提交

一条命令做完（补审查报告 + 重建目录 + 提交 + 推送，push 失败自动重试）：

```powershell
py scripts\finalize.py --commit
```

它会：把 scripture 区块与 `verses\*.json` 对齐 → 给没写审查报告的章节补上 `reviews\<id>.txt` → 重建首页与 `books\<书卷id>.html` → 提交并推送。

`reg_index.py --write` 会同时更新首页目录和 `books/<书卷id>.html` 的章节网格——**不能省**，否则新章节不会出现在书卷页里。
git 不在 PATH，用 `C:\Program Files\Git\cmd\git.exe`；网络不稳就重试，push 失败要重试到成功。
**若 push 报「Recv failure: Connection was reset」或「Failed to connect」**：多半是直连 github.com:443 不通而 git 没走系统代理，检查并设置 `git config --global http.proxy http://127.0.0.1:7897`（端口见 Internet Settings 的 ProxyServer），再重试。


## 3. 停下来的条件

只有**全部 1189 章都通过 P0 且都有审查报告**（`py scripts\status.py` 退出码 0）才允许结束。

一轮做不完（限流、上下文将满）时：**先把已完成的部分提交推送**，然后立刻开始下一批。
会话即将结束时：提交推送，在回复里写清「下一轮从 X 开始」。

## 4. 自动监督器（项目不会停）

```powershell
py scripts\supervisor.py            # 前台跑（Python 版，稳）
scripts\supervisor.cmd               # 计划任务入口
```

它会循环：查状态 → 调 `opencode-cli.exe run --auto` 开新会话继续写 → 限流就换模型退避 → 直到全部完成。
日志在 `logs/supervisor.log`，PID 在 `logs/supervisor.pid`。

Windows 计划任务 `BibleNotesSupervisor` 每 5 分钟跑一次 `scripts\supervisor.cmd`（实际由 `scripts\tick.py` 负责心跳：先 `claim.py --prune` 清掉死锁，再确认监督器活着，没有就把它拉起来）。
监督器活着时它会自动退出（PID 守卫），监督器死了就把它拉起来。**这台机器上，项目不靠任何对话也能自己往前走。**

**它跑着的时候，不要和它同时大批量派活**，以免撞车与限流——但**章节占用（claim）已经解决了撞车**：派活前先 `py scripts\claim.py <id>…` 占住，监督器会自动跳过这些章。

