# Render JSON 编写指南（文案保真五条铁律）

SenseNova U1.5 训练时接受结构化 Render JSON（subjects/scene/composition/visible_copy/negative 等），
直投该格式比自然语言 prompt 的版式控制力与文字保真都显著更强。

## Schema 速览

```jsonc
{
  "subjects": [{            // 每个视觉模块一条
    "description": "左列上模块'承保总览'：三层石阶柱状图",
    "appearance_action": "青灰条石堆叠，砖面刻鎏金汉字，砖缝生细草",   // ← 绑定"在哪刻什么字"
    "relationship_position": "左列第一行，紧贴大字左侧",
    "count_anatomy": "一座三层石阶"                                    // ← 精确数量，防多画/少画
  }],
  "scene":   { "setting": "...", "spatial_layers": "前/中/背景", "supporting_details": ["非文字装饰"] },
  "lighting":{ "conditions": "...", "direction": "...", "shadow_effect": "投影极浅保持平整" },
  "composition": { "framing": "满版紧凑：六模块左三右三网格…",       // ← 版式写死
                   "hierarchy_flow": "视线动线", "negative_space": "压到最小" },
  "style":   { "medium": "青花瓷风数据信息图", "art_direction": "配色/材质", "palette_materials": "..." },
  "camera":  { "viewpoint": "正面平视满版", "lens_focus": "全画面均匀清晰" },
  "visible_copy": [                                          // ⭐ 文字穷举账本
    { "text": "3800 家瓷企", "category": "数据",
      "placement": "石阶柱最底层石面", "appearance": "鎏金刻字" }
  ],
  "structure": { "type": "", "members": [] },                // 显式分面板时才用
  "image_description": "一段自然语言总述（不逐字段重复）",
  "canvas":  { "aspect_ratio": "16:9", "orientation": "landscape", "resolution": "2720x1536" },
  "negative": "大面积留白, 模块重叠遮挡文字, 编造清单外的数字年份来源, 伪文字乱码"
}
```

## 五条铁律

1. **visible_copy 穷举**：每一条要渲染的字（标题/副题/数据/落款）各一条 entry。模型服从性极高——
   账本里的字几乎 100% 正确渲染，账本外的字几乎 100% 不画。**图上文字 = 账本**。
2. **composition 写死版式**：网格/横卷/环绕 + 负空间策略（"压到最小，仅文字四周留窄边"）。
3. **subjects 绑定刻字动作**：每个数据模块的 appearance 里写明"石面刻字/木牌刻字/匾额刻字/环心三行数据"，
   与 visible_copy 的 placement 互为锚定；纯装饰件显式写"素面无字"。
4. **negative 列禁忌**：大面积留白 / 重叠遮挡文字 / 清单外数字年份来源 / 伪文字乱码。
5. **生成后 VLM 逐字验收**：对照账本核对命中/缺失/编造/乱码/遮挡/加总逻辑（本仓库 `verify_with_vlm.py`），
   不过就换 seed 重 roll。

## 换主题复用三步

1. 复制一份 `workflows/examples/*.json`
2. 改 `subjects`（换当地风物载体：石阶/瓷瓶/驼队/灯笼/梯田…）+ `visible_copy`（换数字）+ `style`（换配色）
3. 直投：`python scripts/generate.py your.json --verify`

> ⚠️ 不要走 LLM 预编译（PE）：实测编译环节会把 17 条文字砍到 8 条进账本（见
> [ablation/results.md](../ablation/results.md) 实验一）。想用 PE 拿骨架可以，但必须人工核对
> 编译产物的 visible_copy 是否穷举。
