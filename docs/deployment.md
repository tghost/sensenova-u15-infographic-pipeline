# 部署指南

## 硬件要求

| 权重模式 | 显存 | 速度（2720×1536, 50步+think） | 说明 |
|----------|------|-------------------------------|------|
| safetensors bf16（正式版，默认） | 48G（balanced 层卸载） | ~700s/张 | 质量最优：背景纯净、文字锐利、数值全对 |
| GGUF Q4_0 v2（草稿版） | ~16G | ~230s/张 | 快但有背景杂色/机械条纹，仅用于迭代验证 |

## 安装步骤

1. **ComfyUI**：标准安装（ComfyUI 官方仓库），Python 3.10+
2. **自定义节点**：
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/OpenSenseNova/SenseNova-U1.git ComfyUI-SenseNova-U1
   pip install -r ComfyUI-SenseNova-U1/requirements.txt
   ```
3. **模型权重**：
   - 正式版 safetensors（~42G）放入模型目录；config/tokenizer 目录指向 `SenseNova-U1.5-8B-MoT`
   - （可选）GGUF `SenseNova-U1.5-8B-MoT-Preview-Q4_0-v2.gguf`（~10G）放入 gguf 模型目录
4. **Loader 关键参数**：`attn_backend=sdpa`（容器 flash_attn 有兼容问题）；safetensors 用
   `vram_mode=balanced` + `gguf_checkpoint=""`；GGUF 用 `vram_mode=full` + 指定 gguf 文件
5. 验证：跑通本仓库 `bash run_demo.sh`（约 700s 出图）

## 验收环境（可选）

`verify_with_vlm.py` 走 OpenAI 兼容多模态接口，本地 vLLM/Qwen-VL 或云端模型均可：

```bash
export VLM_API_BASE="http://your-vlm:8000/v1"
export VLM_API_KEY="..."
export VLM_MODEL="qwen2.5-vl-72b"
```
