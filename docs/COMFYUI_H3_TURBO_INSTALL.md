# ComfyUI 服务器：H3 Turbo 加速链安装清单

> 症状：ComfyUI 日志 `invalid prompt: Node 'MiniMax-H3 Turbo LoRA' not found`。
> 控制台 v0.13.24 已支持缺节点自动降级（慢但可跑），本文是**根治方案**：把加速节点
> 和权重装齐。示例路径按生产服务器 `/opt/app/ComfyUI`（Python 3.10，
> pip 即系统 pip）书写，换环境时替换前缀即可。

## 1. 三个工作流引用的加速节点 → 来源对照

| class_type（提交图里的名字） | 来源 | 安装方式 |
|---|---|---|
| `MiniMaxH3TurboLoRA` | **Larryvrh/ComfyUI-MiniMax-H3-Turbo** | 手动 clone（见 §2） |
| `MiniMaxH3TurboSampler` | 同上 | 同上 |
| `MiniMaxH3MemoryEfficientSageAttentionPatch` | **kijai/ComfyUI-KJNodes** | 手动 clone + sageattention（见 §3） |
| `EasyCache` | ComfyUI **原生内置**（comfy_extras/nodes_easycache） | 升级 ComfyUI 核心（见 §4） |

### 页面显示缺失、但控制台链路"不需要"的两个节点

`MiniMaxH3PromptEnhancer`、`MiniMaxH3GenerationTailLoader`（均来自
**ethanfel/ComfyUI-MiniMax-H3-Guide**，尾权重
`qwen3vl_32b_h3_generation_tail_50_63_int8_convrot.safetensors` 放 models/text_encoders）。
I2V 队列快照里含有它们，但 `build_api_graphs.build_i2v()` 装配时**固定剔除**
（节点 105:121~124）——本项目用自家规则化提示词直喂 H3，刻意绕过官方增强器。
ComfyUI-Manager 扫描工作流按节点全集比对，所以页面仍提示缺失；实际提交不受影响，
可忽略。**仅当**要在 ComfyUI 界面手动打开原始工作流实验增强器时才需要装：

```bash
cd /opt/app/ComfyUI/custom_nodes
git clone https://github.com/ethanfel/ComfyUI-MiniMax-H3-Guide
```

其余节点（`MiniMaxH3ImageToVideo` / `MiniMaxH3ReferenceToVideo` / `ComfyMathExpression` /
`ResolutionSelector` / `CreateVideo` / `SaveVideo` 等）服务器已验证可用（R2V 成片
`麦田十年_01` 跑通过 20 分钟全步数链路），无需处理。

## 2. Turbo LoRA 节点包

```bash
cd /opt/app/ComfyUI/custom_nodes
git clone https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo
pip install -r ComfyUI-MiniMax-H3-Turbo/requirements.txt
```

## 3. SageAttention 加速补丁（KJNodes）

```bash
cd /opt/app/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-KJNodes
pip install -r ComfyUI-KJNodes/requirements.txt
pip install -U sageattention
```

注意：
- 节点要求 **sageattention ≥ 2.2.0** 且与本机 PyTorch/CUDA 版本匹配（NVIDIA 专用，
  sm80+）。pip 装不上预编译包时，按 `python -c "import torch;print(torch.__version__, torch.version.cuda)"`
  输出去 GitHub Releases 找对应 wheel。
- 版本不够时报错是响亮失败：`sageattention is not new enough version ...`。
- ComfyUI 启动参数若带 `--use-sage-attention` 与旧版 sageattention 冲突，二选一。

## 4. EasyCache（原生节点，升级核心即可）

```bash
cd /opt/app/ComfyUI && git pull
# 验证：
ls comfy_extras/ | grep -i easycache
```

EasyCache 是较新版本 ComfyUI 内置（与 H3 原生支持同批引入，H3 需要 ≥0.31）。
服务器既然已能加载 MiniMaxH3VideoVAE / MiniMaxH3 模型，通常只需 `git pull` 跟进最新。

## 5. LoRA 权重（models/loras/）

模板里写死的文件名必须**一字不差**（前端下拉按文件名匹配）：

| 文件名 | 用途 | 来源（HF 仓库） |
|---|---|---|
| `minimax_h3_turbo_v4_step600_ema.safetensors` | I2V 模板 / R2V 低步数链式（0.75 强度） | `larryvrh/MiniMax-H3-Turbo-Lora` |
| `minimax_h3_turbo_4步加速ema_comfyui.safetensors` | T2V 模板（强度 1.0，pruned 兼容转换版） | `drbaph/MiniMax-H3-Turbo-Lora-ComfyUI` 或 `QrusherZA/H3_Turbo_ComfyUI`（下载后重命名成该文件名） |

```bash
# 国内用 hf-mirror：export HF_ENDPOINT=https://hf-mirror.com
pip install -U "huggingface_hub[cli]"
hf download larryvrh/MiniMax-H3-Turbo-Lora minimax_h3_turbo_v4_step600_ema.safetensors \
  --local-dir /opt/app/ComfyUI/models/loras
```

基座权重兼容性：pruned 版 UNET（`*_pruned_int8_convrot`）必须配
**pruned 兼容转换**的 LoRA（文件名带 `comfyui`/`pruned`）；官方文档明确原版
4step LoRA 与 pruned 基座不兼容。

## 6. 全量模型清单（对照 ls 检查，缺什么补什么）

| 目录 | 文件 | 用在 |
|---|---|---|
| models/diffusion_models | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | R2V（config `models.r2v.unet`，提交端有预检回退） |
| models/diffusion_models | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | I2V 模板 / R2V 回退档 |
| models/diffusion_models | `minimax_h3_fl2va_int8_convrot.safetensors` | T2V 模板 |
| models/text_encoders | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 全部（官方） |
| models/text_encoders | `qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors` | config `models.r2v.clip` 指定时用 |
| models/vae | `minimax_h3_video_vae_fp16.safetensors` / `minimax_h3_audio_vae_fp32.safetensors` | 全部（服务器日志已见加载成功） |

来源：MiniMax 官方 HF `MiniMax-MiniMax-H3` 系列仓库（docs.comfy.org 的 H3 教程页有
完整下载链接与 SHA256）。

## 7. 安装后验证

```bash
# 重启 ComfyUI（有 comfyui-auth 的话控制台会自动重登，无需重启控制台）
cd /opt/app/ComfyUI && <你们的启动方式>
# 逐类探测（返回非空 JSON 即加载成功）：
for t in MiniMaxH3TurboLoRA MiniMaxH3TurboSampler MiniMaxH3MemoryEfficientSageAttentionPatch EasyCache; do
  echo -n "$t: "; curl -s http://127.0.0.1:8188/object_info/$t | head -c 40; echo
done
```

四项都有输出后，在控制台再提交一次任务：页面不再出现"已自动降级为基线链路"的
⚠️ 提示即恢复 turbo（预览档 4-6 步，成片档 R2V 20 步不变）。
