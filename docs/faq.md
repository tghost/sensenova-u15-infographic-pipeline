# 踩坑 FAQ（按翻车频率排序）

## 1. 图上该有的字没画 / 模块空壳
**原因**：LLM 预编译（PE）把 visible_copy 账本砍半（实测 17→8 条）。
**解法**：高密度文案场景手工 Render JSON 直投（本仓库默认路线），PE 只用来拿骨架且必须人工核对账本。

## 2. 数字渲染错（吞 0/糊成圈/多字）
**原因**：seed 级随机性，约 1/3 概率出现数字层缺陷。
**解法**：VLM 逐字验收不过 → 换 seed 重 roll；虚构数据可"账本跟图走"零成本收敛。

## 3. 装饰区域冒出伪文字（鬼画符）
**解法**：subjects 里纯装饰件显式写"素面无字"；negative 加"伪文字乱码/类文字符号"。

## 4. ImageEdit 节点 AttributeError（v0.2.0）
**现象**：`'SenseNovaU1LocalModel' object has no attribute 'model'`，safetensors/GGUF 双模式均复现。
**解法**：局部修图需求改走"改 Render JSON 重 roll"，别用 --edit（截至 v0.2.0）。

## 5. 背景出现杂色/机械条纹
**原因**：GGUF Q4_0 量化损失平坦色场表达能力。
**解法**：正式出图用 safetensors bf16；GGUF 仅做快速草稿。

## 6. flash_attn 报错/崩
**解法**：Loader `attn_backend` 硬编码 `sdpa`。

## 7. 文字被装饰元素遮挡
**解法**：subjects 写"丝带/飘带一律绕开文字"；验收时专查遮挡项。
