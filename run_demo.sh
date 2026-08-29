#!/usr/bin/env bash
# 一键演示：Render JSON 直投 → 生成 → VLM 验收
set -e
JSON="${1:-workflows/examples/jingdezhen.json}"
OUT="${2:-demo_output.png}"
python3 scripts/generate.py "$JSON" -o "$OUT" --verify && echo "完成：$OUT"
