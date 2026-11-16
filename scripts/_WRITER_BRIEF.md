# 写手须知 · 二代流程内容 JSON（给并行写手）

## 你的任务
为指定书卷的每一章写一个内容 JSON，文件放到 `D:/圣经笔记/skill/<中文卷名>/_src/<id>.json`。
例如 `俄巴底亚书/_src/oba-01.json`、`约拿书/_src/jon-02.json`。

## 必读（先 Read 这三个）
1. `D:/圣经笔记/skill/scripts/content_schema.md` —— 字段契约、字段结构模板、字数预算
2. `D:/圣经笔记/skill/阿摩司书/_src/amo-04.json` —— 成品标杆，照抄字段结构、嵌套方式、语气、note 用法、篇幅密度
3. 本章经文 `D:/圣经笔记/skill/verses/<id>.json` —— 唯一经文来源，先读完再写

## 输出
每个 `<id>.json` 都是合法 JSON，字段与 amo-04.json 完全一致：
id / thesis / golden / minutes / genre / before / bg / overview / map / segs / key / theology / prayer / apply / tasks / review / refs。

## 铁律（违反会返工）
1. **全中文**。正文值里禁止任何英文单词混入（JSON 键名如 act/scene/christ/god/man 除外）。绝不出现 accum/sharp/fire/free 之类残留。
2. **引文纪律（最重要）**：qa_check.py 把正文里 `「...」` 内的文字当经文逐字核对。
   - 本章经文引用：必须与 verses/<id>.json 逐字一致；出处写成标准 "5:4" 格式，不要写 "4节"（会报"无法核对"）。
   - 跨书卷引用：要么先 Read 对应 verses 文件确认逐字一致，要么改写成转述且不加 `「」`。拿不准就不用 `「」`，用普通叙述。
   - review.nextText 提到下一章经文时不要加 `「」`，或确保逐字一致。
3. `segs` 的 `r` 字段必须连续覆盖该章全部节号（1 到 N），不重不漏，6-12 段。短章（如俄巴底亚 21 节）用 6-8 段。
4. 每段 `segs[].notes` 必须含一条 `["christ","与基督的关联",...]`；释经分歧用 `["warn",...]` 并列呈现、不裁判；等级只用 info/warn/christ。
5. thesis 60-100 字；golden 只写 "章:节"；minutes 25-40；genre 按体裁写，如 "叙事 · 古代传记" / "预言 · 审判宣告" / "书信 · 论证" / "诗歌 · 智慧文学"。
6. 字数以 build.py ✓ 为准，全章目标 8000-12000 字（短章可略低）；`segs[].p` 每段 200-500 字，不要为凑字压薄。
7. 段落标题 `t` 是 6-14 字判断句，不是"第一段/关于..."。
8. 禁止句式："神今天对你说""主要你""神绝不会让你""只要相信就一定会""家人们"等；禁占位符 TODO/??/{{}}。
9. apply.act 必须具体（对象+时间+动作+可验证）；tasks 的 ABCD 四组共 8-12 个复选框；review.q 恰好 3 组；bg 恰好 5 格；overview.outline 5-8 行；key 3-5 处每处四步。
10. 语气是耐心的老师；描述性≠规范性；推论可被读者分辨；释经分歧并列不裁判。

## 自检（必须做，否则不算完成）
每写一个 JSON 后，在 `D:/圣经笔记/skill` 运行：
  py scripts/build.py <id>
必须输出 ✓。若有字段错误或字数不合规，按提示修改 JSON 后重跑，直到 ✓。
全部章节写完后，再跑一次 `py scripts/build.py --book <书卷代码>` 确认整卷 ✓。

## 不要做
不要运行 merge_people / check_note / qa_check / reg_index / git（主会话统一做）。不要改 people.js / index.html / 其他章节文件。

## 汇报
报告：写了哪些章节 id、各自字数、build 是否全部 ✓、每章标 warn 分歧的地方。
