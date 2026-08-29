#!/usr/bin/env python3
"""VLM 逐字验收：对照 Render JSON 的 visible_copy 账本核对成图文字.

用法:
    python scripts/verify_with_vlm.py out.png --render-json workflows/examples/jingdezhen.json

环境变量（OpenAI 兼容多模态接口，本地/云均可）:
    VLM_API_BASE  如 https://api.example.com/v1
    VLM_API_KEY   密钥
    VLM_MODEL     模型名（需支持图像输入）

退出码: 0=全部命中且无编造  1=有缺失/编造/乱码
"""
import argparse
import base64
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("VLM_API_BASE", "").rstrip("/")
API_KEY = os.environ.get("VLM_API_KEY", "")
MODEL = os.environ.get("VLM_MODEL", "")

PROMPT_TMPL = """这是一张数据信息图。请严格验收：
1）逐模块列出图中实际出现的所有数字、百分比和文字；
2）对照下方期望清单，逐项标注 命中/缺失/被改动；
3）检查是否存在清单之外的编造数字、年份、数据来源；
4）检查乱码、伪汉字、错别字、重复渲染、文字被遮挡。

期望清单：
{checklist}

请以 JSON 输出：{{"hits": ["..."], "missing": ["..."], "altered": ["..."],
"fabricated": ["..."], "quality_issues": ["..."]}}，只输出 JSON。"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--render-json", required=True)
    args = ap.parse_args()

    if not (API_BASE and API_KEY and MODEL):
        sys.exit("❌ 需要设置 VLM_API_BASE / VLM_API_KEY / VLM_MODEL 环境变量")

    render = json.load(open(args.render_json, encoding="utf-8"))
    ledger = [v["text"] for v in render.get("visible_copy", [])]
    if not ledger:
        sys.exit("❌ Render JSON 无 visible_copy 账本")

    with open(args.image, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    body = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text",
                 "text": PROMPT_TMPL.format(checklist="\n".join(f"- {t}" for t in ledger))},
            ],
        }],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        f"{API_BASE}/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        out = json.loads(resp.read())

    text = out["choices"][0]["message"]["content"].strip()
    s, e = text.find("{"), text.rfind("}")
    try:
        result = json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        print(text)
        sys.exit("❌ VLM 输出非 JSON，请人工复核")

    print(f"账本 {len(ledger)} 条 | 命中 {len(result.get('hits', []))} | "
          f"缺失 {len(result.get('missing', []))} | 被改动 {len(result.get('altered', []))} | "
          f"编造 {len(result.get('fabricated', []))} | 质量问题 {len(result.get('quality_issues', []))}")
    for k in ("missing", "altered", "fabricated", "quality_issues"):
        for item in result.get(k, []):
            print(f"  [{k}] {item}")

    ok = not (result.get("missing") or result.get("altered")
              or result.get("fabricated"))
    print("✅ 验收通过" if ok else "🚫 验收未通过（换 seed 重 roll 或修正账本）")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
