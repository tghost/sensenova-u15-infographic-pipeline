#!/usr/bin/env python3
"""SenseNova U1.5 信息图生成脚本（ComfyUI API 直投版）.

用法:
    python scripts/generate.py workflows/examples/jingdezhen.json -o out.png
    python scripts/generate.py render.json -o out.png --verify --seed 42

环境变量:
    COMFYUI_BASE   ComfyUI 服务地址 (默认 http://127.0.0.1:8188)
    COMFYUI_USER   Basic Auth 用户名 (可选)
    COMFYUI_PASS   Basic Auth 密码 (可选)
    RESOLUTION     分辨率档位 (默认 16:9, 见 RESOLUTIONS)
    STEPS          采样步数 (默认 50; think_mode 下 ~700s/张)
    THINK          1=开 think_mode (信息图必开, 默认) 0=关
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import base64
import uuid

RESOLUTIONS = {
    "1:1": "2048x2048|1:1", "16:9": "2720x1536|16:9", "9:16": "1536x2720|9:16",
    "3:2": "2496x1664|3:2", "2:3": "1664x2496|2:3", "4:3": "2368x1760|4:3",
    "3:4": "1760x2368|3:4", "1:2": "1440x2880|1:2", "2:1": "2880x1440|2:1",
    "1:3": "1152x3456|1:3", "3:1": "3456x1152|3:1",
}

BASE = os.environ.get("COMFYUI_BASE", "http://127.0.0.1:8188").rstrip("/")


def _auth_header():
    user, pwd = os.environ.get("COMFYUI_USER"), os.environ.get("COMFYUI_PASS")
    if user and pwd:
        tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return {"Authorization": f"Basic {tok}"}
    return {}


def _req(path, data=None, timeout=60):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=_auth_header(),
                               method="POST" if body else "GET")
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


def build_workflow(prompt_text: str, resolution: str, seed: int, steps: int, think: bool) -> dict:
    """Loader → SenseNovaU1LocalTextToImage → SaveImage（safetensors 正式版权重）."""
    return {
        "loader": {
            "class_type": "SenseNovaU1LocalLoader",
            "inputs": {
                "model_path": os.environ.get(
                    "U15_MODEL_PATH", "/data/llm/models/SenseNova-U1.5-8B-MoT"),
                "sensenova_u1_src": "",
                "device": "cuda", "dtype": "bfloat16",
                "attn_backend": "sdpa",  # 容器 flash_attn 有兼容问题，固定 sdpa
                "device_map": "none", "max_memory": "",
                "vram_mode": "balanced",  # 42G bf16 权重层卸载；GGUF 用 full
                "gguf_checkpoint": "",
            },
        },
        "t2i": {
            "class_type": "SenseNovaU1LocalTextToImage",
            "inputs": {
                "u1_model": ["loader", 0],
                "prompt": prompt_text,
                "resolution": RESOLUTIONS[resolution],
                "cfg_scale": 4.0, "cfg_norm": "none", "timestep_shift": 3.0,
                "cfg_interval_start": 0.0, "cfg_interval_end": 1.0,
                "num_steps": steps, "batch_size": 1, "seed": seed,
                "think_mode": think,
            },
        },
        "save": {"class_type": "SaveImage",
                 "inputs": {"images": ["t2i", 0], "filename_prefix": "U15_out"}},
    }


def wait_and_download(prompt_id: str, out_path: str, max_wait: int = 1500):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(10)
        hist = _req(f"/history/{prompt_id}")
        entry = hist.get(prompt_id, {})
        outputs = entry.get("outputs", {})
        if outputs:
            for node in outputs.values():
                for img in node.get("images", []):
                    if img.get("type") == "output":
                        q = urllib.parse.urlencode({
                            "filename": img["filename"],
                            "subfolder": img.get("subfolder", ""),
                            "type": "output"})
                        url = f"{BASE}/view?{q}"
                        req = urllib.request.Request(url, headers=_auth_header())
                        with urllib.request.urlopen(req, timeout=120) as resp, \
                                open(out_path, "wb") as f:
                            f.write(resp.read())
                        return out_path
        if entry.get("status", {}).get("status_str") == "error":
            sys.exit(f"❌ workflow 执行失败: {json.dumps(entry['status'], ensure_ascii=False)[:500]}")
        print(f"  ...等待中 {int(time.time()-t0)}s", flush=True)
    sys.exit("❌ 超时")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render_json", help="Render JSON 文件路径（或纯文本 prompt）")
    ap.add_argument("-o", "--output", default="out.png")
    ap.add_argument("-s", "--seed", type=int, default=42)
    ap.add_argument("-n", "--steps", type=int, default=50)
    ap.add_argument("-r", "--resolution", default="16:9", choices=list(RESOLUTIONS))
    ap.add_argument("--no-think", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="生成后调用 verify_with_vlm.py 逐字验收（需 VLM_API_BASE 等环境变量）")
    args = ap.parse_args()

    with open(args.render_json, encoding="utf-8") as f:
        raw = f.read()
    try:  # Render JSON 直投；不是 JSON 就当纯文本 prompt
        prompt_text = json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":"))
        print(f"📝 Render JSON 加载成功, visible_copy={len(json.loads(raw).get('visible_copy', []))} 条")
    except json.JSONDecodeError:
        prompt_text = raw
        print("📝 纯文本 prompt 模式（高密度文案建议用 Render JSON）")

    wf = build_workflow(prompt_text, args.resolution, args.seed, args.steps,
                        think=not args.no_think)
    client = str(uuid.uuid4())
    resp = _req("/prompt", {"prompt": wf, "client_id": client})
    pid = resp["prompt_id"]
    print(f"🚀 已提交 prompt_id={pid}（正式版权重约 700s/张）")
    wait_and_download(pid, args.output)
    print(f"✅ 已保存 {args.output}")

    if args.verify:
        rc = os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "verify_with_vlm.py")}" '
                       f'{args.output} --render-json {args.render_json}')
        sys.exit(0 if rc == 0 else 1)


if __name__ == "__main__":
    main()
