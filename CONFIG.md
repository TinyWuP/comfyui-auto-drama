# 配置说明（CONFIG）

复制 `config.example.json` 为 `config.json`（同一目录），按下面说明填写。
**所有路径均为相对项目根目录的相对路径**，禁止写绝对路径（如 `/Users/xxx/...`）。
所有支持云端 API 的配置项，本地服务不可用时自动降级到云端。

配好后运行 `python3 scripts/check_env.py` 一键检查环境是否就绪。

---

## comfyui（远程生成服务器）

| 字段 | 说明 | 示例 |
|---|---|---|
| `server` | ComfyUI 服务器地址（局域网远程机或本机） | `http://192.168.1.23:8188` |
| `workflow_dir` | 工作流脚本目录（`build_api_graphs.py`、`*_api_template.json` 所在处） | `workflows` |
| `auth.enabled` | 认证开关：远程 ComfyUI 装了 comfyui-auth 等认证插件时设为 `true` | `false` |
| `auth.username` | 登录用户名（开启认证时必填） | `admin` |
| `auth.password` | 登录密码（**不要提交进 git**） | `xxxxxx` |
| `auth.login_path` | 登录接口路径，默认适配 `ivellioscolin/comfyui-auth`（表单登录 + 会话 cookie）；JWT 类插件（如 ComfyUI-Account-Manager）填其登录路径如 `/login` | `/comfyui-auth/login` |
| `auth.token_field` | JWT 类插件登录响应中 token 的字段名（cookie 会话类留默认即可） | `token` |

**认证说明**：`auth.enabled=true` 时，控制台首次调用 ComfyUI 接口会自动 POST 登录接口换取
会话凭证（cookie 或 Bearer token，按插件实现自适应），之后 `/prompt`、`/queue`、`/history`、
`/view`、`/upload/image`、`/object_info` 等全部自动携带；会话过期收到 401 时自动重登重试一次。
凭据错误/路径不匹配会在日志打 `[auth]` 错误，界面服务器状态提示认证失败。

**说明**：远程 ComfyUI 需要安装 MiniMax H3 节点与模型（ref2va 工作流、turbo LoRA、SageAttention、无审查 CLIP），详见 `README.md` 的"远程依赖"章节。

## storage（存储路径）

| 字段 | 说明 | 示例 |
|---|---|---|
| `output_dir` | 生成视频/图片的下载目录 | `comfyui_backup/outputs` |
| `asset_dirs` | 参考素材目录列表（角色锚点图、场景图、分镜图存放处） | `["素材", "出镜素材"]` |

## llm（语言模型：剧本生成 / 改写 / 提示词扩写）

| 字段 | 说明 | 示例 |
|---|---|---|
| `provider` | 当前使用本地还是云端：`local` 或 `cloud` | `local` |
| `provider_type` | 云端接口格式：`openai` / `claude` / `dashscope` | `openai` |
| `local.url` | 本地 OpenAI 兼容服务地址（LM Studio / Ollama） | `http://127.0.0.1:1234` |
| `local.model` | 本地模型名（需已在 LM Studio 加载） | `qwen3.6-27b-abliterated-mlx` |
| `local.token` | 本地服务鉴权 token（无鉴权留空） | `sk-lm-xxx` |
| `cloud.enabled` | 是否启用云端 API（本地不可用时自动降级） | `false` |
| `cloud.base_url` | 云端 OpenAI 兼容地址 | `https://api.openai.com/v1` |
| `cloud.api_key` | 云端 API Key（**不要提交进 git**） | `sk-xxx` |
| `cloud.model` | 云端模型名 | `gpt-4o-mini` |

**说明**：
- 只要接口兼容 OpenAI `/v1/chat/completions` 即可，DeepSeek、通义、Moonshot、OpenRouter 等都可用（填各自 base_url / api_key / model）。
- 不兼容 OpenAI 的服务用适配器：`claude`（Anthropic Messages）、`dashscope`（通义原生）；
  适配器自动转换请求/响应格式，主流程无感知。
- 云端不可用且本地离线时，控制台自动回退内置规则扩写（效果差一些，但能跑）。

## image_gen（文生图：角色锚点图 / 场景图 / 分镜图）

| 字段 | 说明 | 示例 |
|---|---|---|
| `provider` | `local` 或 `cloud` | `local` |
| `provider_type` | 云端接口格式：`openai` / `dashscope` | `openai` |
| `local.url` | 本地生图服务（Boogu-Image）地址 | `http://127.0.0.1:8081` |
| `cloud.enabled` | 是否启用云端文生图 | `false` |
| `cloud.base_url` | 云端 OpenAI 兼容图片接口 | `https://api.openai.com/v1` |
| `cloud.api_key` | 云端 Key | `sk-xxx` |
| `cloud.model` | 图片模型名 | `gpt-image-1` |
| `speed.enable_thinking` | 仅百炼端点下发：`false` 关闭思考模式，**明显提速**（默认 false） | `false` |
| `speed.prompt_extend` | 仅百炼端点下发：`false` 关闭提示词改写，省数秒（默认 false） | `false` |
| `verify` | 生图后是否调视觉模型质检（每张多一次大模型往返）；`false` 关闭省约一半耗时，但失去穿帮自动拦截 | `true` |

**说明**：
- 本地部署见 `README.md` 的"Boogu-Image 本地部署"（Apple Silicon / MLX，一键脚本 `scripts/deploy_boogu.sh`）
- 云端接口按 OpenAI `/v1/images/generations` 兼容实现（支持 `b64_json` 或 `url` 返回）；
  `provider: cloud` 时走云端，主端点失败自动降级本地
- 通义万相用 `provider_type: dashscope`（异步任务 + 自动轮询）

## vision（图片质检：检查穿帮 / 服装一致性 / 人数）

| 字段 | 说明 | 示例 |
|---|---|---|
| `base_url` | OpenAI 兼容视觉服务（本地或云端） | `http://127.0.0.1:8001/v1` |
| `api_key` | 服务鉴权（无则留空） | `sk-xxx` |
| `model` | 视觉模型名 | `qwen-vl-max` |

## console（控制台自身）

| 字段 | 说明 | 示例 |
|---|---|---|
| `port` | 控制台 Web 端口 | `8890` |
| `host` | 监听地址：`0.0.0.0` 允许局域网访问（默认），`127.0.0.1` 仅本机；也可用环境变量 `BATCH_CONSOLE_HOST` 覆盖 | `0.0.0.0` |
| `max_ref_images` | R2V 单段参考图上限（官方 Ref2VA ≤9） | `8` |

## models（R2V 出片模型，可选）

| 字段 | 说明 | 示例 |
|---|---|---|
| `r2v.unet` | Ref2VA 扩散模型（放远程 `models/diffusion_models/`） | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| `r2v.clip` | Ref2VA 文本编码器（放远程 `models/text_encoders/`） | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` |

**说明**：
- `r2v.unet` 必须是官方 Ref2VA 权重（与 T2V/I2V 的 FL2VA 是两套模型）；提交时自动检测服务器
  是否已加载，缺失则回退 FL2VA 并提示。
- `r2v.clip` 开源默认用官方 `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`；个人本地可换成
  未审查版（如 `qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors`），
  但**不要**把未审查模型名写进提交到开源仓库的 `config.example.json`。

---

## 环境变量覆盖（可选）

以下环境变量可覆盖 config.json（优先于配置文件）：

| 环境变量 | 覆盖项 |
|---|---|
| `BATCH_CONSOLE_CONFIG` | 指定 config.json 路径 |
| `COMFYUI_SERVER` | `comfyui.server` |
| `LLM_CLOUD_API_KEY` | `llm.cloud.api_key` |
| `IMAGE_CLOUD_API_KEY` | `image_gen.cloud.api_key` |
