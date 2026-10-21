# 资料来源 · Sources

## 1. 经文

| 项目 | 说明 |
|---|---|
| 版本 | 和合本（Chinese Union Version, 1919），**简体** |
| 来源 | `https://bible-api.com/data/cuv/<BOOK>/<章>`，返回繁体，脚本用 `zhconv` 转简体 |
| 校勘注 | API 文本里的 `〔有古卷…〕` 在入库时剥离，笔记正文不保留 |
| 版权 | 和合本已进入公有领域。仍建议在页脚注明「和合本 · 个人研读用途」 |
| 铁律 | 笔记里的经文只能从 `verses/<id>.json` 复制，**不许手打、不许凭记忆** |

书卷代码（bible-api）：`GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV`

## 2. 注释书与参考书

> **只写你真的知道存在的书。**不确定作者、版次、页码，就只写书名；连书名都不确定，就别写，改用「一般注释传统认为」。

### 福音书

| 书 | 作者 | 特点 | 中文版 |
|---|---|---|---|
| 《马可福音》（NICNT） | William L. Lane | 学术性最强，马可研究标准参考 | 有中文版（校园） |
| 《马可福音》（NICNT） | R. T. France | 较新，文学与神学并重 | 英文为主 |
| 《马可福音》（Pillar） | James R. Edwards | 释经与牧养平衡 | 英文 |
| 《马可福音》（TNTC） | Eckhard J. Schnabel | 篇幅适中，适合备课 | 英文 |
| 《马太福音》（EBC） | D. A. Carson | 希腊文与结构分析扎实 | 有中文版 |
| 《约翰福音》（Pillar） | D. A. Carson | 神学深度高 | 有中文版 |
| 《路加福音》（NICNT） | Joel B. Green | 社会文化背景丰富 | 英文 |

### 书信与神学

| 书 | 作者 | 用途 |
|---|---|---|
| 《罗马书》（BST） | John Stott | 讲道式，适合应用 |
| 《哥林多前书》（NICNT） | Gordon D. Fee | 释经细致 |
| 《腓立比书》（NICNT） | Gordon D. Fee | 同上 |
| 《新约导论》 | D. A. Carson / Douglas Moo | 背景、作者、日期 |
| 《认识神》 | J. I. Packer | 神论与敬虔 |
| 《系统神学》 | Wayne Grudem | 教义定位，注意其改革宗立场 |
| 《基督教神学导论》 | Alister McGrath | 多传统对照 |

### 旧约

| 书 | 作者 | 用途 |
|---|---|---|
| 《创世记》（NICOT） | Victor P. Hamilton | 文本与古代近东背景 |
| 《出埃及记》（NICOT） | Douglas K. Stuart | 律法与叙事 |
| 《诗篇》（NICOT） | Willem A. VanGemeren | 诗体与神学 |
| 《以赛亚书》（NICOT） | John N. Oswalt | 先知与圣洁 |
| 《旧约导论》 | R. K. Harrison / 或 Tremper Longman | 背景 |

### 工具

| 工具 | 用途 | 备注 |
|---|---|---|
| STEPBible / Bible Hub | 原文逐词、 Strong 编号 | 免费，可核对希腊文拼写 |
| 信望爱圣经原文 | 原文解析、字义 | 免费 |
| BDAG | 希腊文词典 | 学术标准，引用需注明 |
| TDNT | 新约神学词典 | 只查词条，不整段抄 |
| 《圣经新辞典》 | 人名、地名、主题 | 中文，适合快速核对 |

## 3. 引用格式

**正文内**（简洁）：

```html
<span class="src">参 Lane, Mark, NICNT</span>
```

或中文：`（参《马可福音》，NICNT）`

**参考资料区**（完整，仅在真查过时写）：

```
作者，《书名》，译者，出版社，年份，页码。
William L. Lane, The Gospel of Mark, NICNT, Eerdmans, 1974, pp. 45–47.
```

**规则**：
- 没查过 → 不写页码
- 只记得大意 → 「参」「一般注释传统认为」
- 同一本书在一章里只列一次
- 不把注释书的话当经文（必须 🟨）

## 4. 版权与使用边界

- 笔记是**个人研读材料**，不用于出版、售卖、课程收费
- 注释书观点**转述**，不整段翻译引用（单条不超过 100 字）
- 不复制注释书的原文段落、图表、大纲
- 和合本可自由引用；若用其他现代译本（新译本、ESV、NIV），注明版本并注意授权
- 图片一律不用外链；需要图示时用 CSS/SVG 自绘

## 5. 查证顺序

1. 经文 → `verses/<id>.json`（最高权威）
2. 原文词 → STEPBible / Bible Hub 核对拼写与词形
3. 背景史实 → 注释书或圣经词典；查不到就降级为「一般认为」
4. 教义 → 系统神学 + 大公信条（尼西亚、迦克墩）
5. 仍有争议 → 并列，标 🟨/🟧，不裁判

## 6. 网络核查命令

```bash
# 拉取并核对本章经文
python .agents/skills/bible-study-note/scripts/verify_verses.py --book MRK --chapter 2 --out verses/mark-02.json

# 只核对已有笔记（不覆盖 verses）
python .agents/skills/bible-study-note/scripts/verify_verses.py --book MRK --chapter 2 --check mark-02.html
```

拉取失败 → **停下来告诉用户**，不许用记忆补经文。
