# 文案保真消融实验

## 实验一：三种 Prompt 策略（同一信息图任务，同模型同权重）

任务：高密度中文数据信息图（6 模块 · 17-21 条文字 · 真实统计口径，仅内部复盘，图不公开）

| 策略 | 文字传递路径 | 账本保真¹ | 期望文字命中² | 编造内容³ | 空壳模块⁴ |
|------|--------------|-----------|---------------|-----------|-----------|
| A：PE 预编译 + 常规 prompt | brief →(LLM 编译)→ Render JSON → 生图 | 17→8 条（**砍 53%**） | ~2/17 | 大量（自编百分比/年份/来源标注） | 0（用编造填满） |
| B：PE 预编译 + 硬反幻觉约束 | 同上 + "禁止虚构任何数字/年份/来源" | 17→8 条 | 6/17 | **0** | 3（账本外文字全部不画） |
| C：**手工 Render JSON 直投**（本项目默认） | 人工补全 visible_copy → 直接投喂 | **21/21 条** | **20/20** | **0** | 0 |

¹ 账本保真 = 编译环节保留的文字条数比。实测 LLM 预编译会把引用块文字砍半，图上"该有的字"物理性消失。
² 命中 = 图上渲染正确且与期望逐字一致。
³ 编造 = 清单外凭空出现的数字/年份/"数据来源"标注。
⁴ 空壳 = 有图形无文字的模块。

**结论**：文字保真瓶颈在 PE 编译环节而非生图模型。策略 C（visible_copy 穷举账本直投）
将命中率从 ~12%（A）提到 100%（C）。模型本身"照账本办事"的服从性极高——账本对，图就对。

## 实验二：Seed 抽奖（同一 Render JSON，仅换 seed，虚构数据任务）

图例：[v1](../examples/ablation/dunhuang_v1_decorative_garble.png) ·
[v2 定稿](../examples/dunhuang_infographic_v2.png) ·
[v3](../examples/ablation/dunhuang_v3_digits_mangled.png)

| seed | 账本命中 | 主要缺陷 |
|------|----------|----------|
| 44 | 18/18 | 经卷区出现 6-8 字伪文字装饰列（鬼画符）；飘带半遮 2 处数字 |
| 45 | 17/18 | "320 款"渲染为"32 款"（吞 0）；鬼画符清零 |
| 46 | ~13/18 | 数字糊成圈状符号/多字/吞数字，经卷区三行全损 |

**结论**：数字逐字渲染存在 seed 级随机性（约 1/3 概率出现数字层缺陷），VLM 验收 + 换 seed 重 roll
是必要闭环；虚构数据场景下"账本跟图走"（修正账本与成图一致）是零成本收敛手段。

## 实验三：Seed 稳定性边界（自检报告任务，双 seed 对照）

任务：工程蓝图风自检报告信息图（原始账本 20 条，含页脚装饰性日期「2026.09.09」）。
图例：[v1 (seed 42)](../examples/selftest_v1.png) · [v2 (seed 20260909)](selftest_v2_seed20260909.png)

| seed | 账本命中 | 编造 | 主要缺陷 |
|------|----------|------|----------|
| 42 | 19/20 | 0 | 页脚日期「2026.09.09」缺失 |
| 20260909 | 18/20 | 0 | 日期仍缺失；账本「验收 6 维」被模型意译为「六维」 |

**结论**：页脚小字日期跨两个 seed 稳定缺失——这不是实验二那种 seed 级随机抖动，而是该版式角落小字的**稳定渲染盲区**，换 seed 无解。按验收闭环的另一条分支收敛：从账本移除装饰性日期条目（现 `workflows/examples/selftest_report.json` 已修正为 19 条），对 v1 成图复验即满分。

**方法论：双 seed 判别法**——同一 Render JSON 换 seed 重 roll 一次：
- 缺陷随 seed **漂移**（如实验二的数字层缺陷，~1/3 概率）→ 随机性缺陷，换 seed 重 roll 即可；
- 缺陷跨 seed **稳定**（如本实验页脚日期）→ 版式性盲区，必须修账本（账本跟图走）。

VLM 验收闭环的「换 seed / 修账本」两条分支，由此有了可操作的判别依据。

## 复现

```bash
# 策略 C 复现（约 700s）
python scripts/generate.py workflows/examples/dunhuang_v2.json -o out.png --verify -s 45
# 换 seed 观察 N=3 的数字层随机性（实验二）
for s in 44 45 46; do python scripts/generate.py workflows/examples/dunhuang_v2.json -o out_$s.png -s $s; done
# 实验三复现：自检报告账本（19 条修正版）双 seed 对照
python scripts/generate.py workflows/examples/selftest_report.json -o out_s42.png -s 42
python scripts/generate.py workflows/examples/selftest_report.json -o out_v2.png -s 20260909
python scripts/verify_with_vlm.py out_s42.png --render-json workflows/examples/selftest_report.json
```
