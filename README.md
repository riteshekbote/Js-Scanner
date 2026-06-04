API Agent — AI 驱动的 JS 安全审计工具

API Agent 是一款面向渗透测试的 JavaScript 代码审计工具。它自动抓取目标网站的所有 JS 文件，通过 AI（DeepSeek / OpenAI / 本地模型）深度分析，精准识别高价值敏感信息（API 接口、硬编码密钥、JWT、手机号、身份证、内网 IP 等），并生成交互式 HTML 报告。支持审计后对话模式，可在对话中继续提问或直接输入新网址无缝扫描，大幅提升渗透测试效率。


## 配置

在项目根目录创建 `config.ini` 文件：

```ini
[AI]
api_base = https://api.deepseek.com
api_key = sk-你的真实密钥
model = deepseek-chat
temperature = 0.1
max_tokens = 8192
min_confidence = 0.0

[App]
report_dir = reports
cache_dir = js_cache
auto_open_report = false
```

| 配置项 | 说明 |
|--------|------|
| `api_base` | 兼容 OpenAI API 的服务地址 |
| `api_key`  | 你的 API 密钥 |
| `model` | 模型名称（如 `deepseek-chat`、`gpt-4o-mini`、`llama3`） |
| `temperature` | 0–1，越低输出越确定（审计推荐 0.1） |
| `max_tokens` | 每次分析最大输出 token 数 |
| `min_confidence` | 0.0–1.0，低于此置信度的发现将被过滤（0.0 保留全部） |
| `report_dir` | HTML 报告输出目录 |
| `cache_dir` | 下载的 JS 文件缓存目录 |
| `auto_open_report` | 是否自动打开报告（Windows） |

### 切换 AI 提供商示例

| 提供商 | `api_base` | `api_key` | `model` |
|--------|-----------|-----------|---------|
| DeepSeek | `https://api.deepseek.com` | 你的 DeepSeek 密钥 | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | 你的 OpenAI 密钥 | `gpt-4o-mini` |
| 本地 Ollama | `http://localhost:11434/v1` | 任意字符串（如 `ollama`） | 你拉取的模型名（如 `llama3`） |

## 使用方法

### 交互模式（推荐）

```bash
python src/main.py
```

- 输入网址（如 `https://example.com`）开始审计
- 审计完成后自动进入 **对话模式**
- 在对话模式中：
  - 提问追问：例如“解释一下 `config.js` 中那个密钥的用途”
  - 粘贴新网址：直接输入 `https://另一个站点.com`，AI 会自动扫描新站点并更新上下文
  - 输入 `exit` 退出对话，返回主菜单
- 内置命令：`help`、`clear`、`history`

### 单次扫描模式

```bash
python src/main.py https://example.com
```


执行完整审计流程（爬取 → 下载 → 分析 → 生成报告）后退出。<img width="1005" height="1173" alt="c6f2cd83a1c8b353b7e66433e1650424" src="https://github.com/user-attachments/assets/50f77a03-3dff-4a04-b8f8-e31a59c8b790" />


<img width="951" height="1155" alt="d3b1dc5da22e54e20afbd10b509e35a2" src="https://github.com/user-attachments/assets/07913ed4-367a-40ae-8e0b-5afa9a199c6f" />

<img width="1788" height="396" alt="c7858762e4317ac30be0d0848a0d42bb" src="https://github.com/user-attachments/assets/ca892ab4-cfb6-46ec-9a04-cbc3f7f8d9c3" />



### 打包为 Windows EXE

```bash
python build_exe.py
```

生成 `dist/API_Agent.exe`，为单文件可执行程序，无需 Python 环境即可运行（需确保目标机器已安装 Playwright 浏览器，或通过 `playwright install chromium` 安装）。

## 报告示例

生成的 HTML 报告包含：

- **统计卡片**：扫描文件数、发现总数、严重/高危风险数
- **泄露类型分布**：按 API 端点、硬编码密钥、个人信息等分类
- **每个文件的详细发现**：
  - 类型（`api_endpoint`、`hardcoded_secret`、`phone_number` 等）
  - 泄露内容（**完整原始值**，便于直接复制利用）
  - 代码上下文（行号及附近代码）
  - 风险等级（`critical` / `high` / `medium` / `low`）
  - 修复建议
  - 置信度百分比
- **一键复制**：复制所有发现（制表符分隔，可粘贴到 Excel）或仅复制 API 接口列表（每行一个 URL）

<img width="1614" height="1389" alt="55eb0608e502ace9f8189120ee372fa3" src="https://github.com/user-attachments/assets/3c7a93a8-b3e1-45a6-b859-f751a4807f85" />

<img width="1433" height="741" alt="7cf9d09c2357cfec2ba4f5a2f0cdc342" src="https://github.com/user-attachments/assets/dd25e004-1bc6-4157-87a4-e3b711ea9e50" />

## 常见问题

**1. 遇到 SSL 证书错误？**  
工具已自动忽略证书错误（Playwright 和 requests 均配置 `verify=False`）。如仍报错，请检查目标网站是否可访问。

**2. AI 分析无结果或报告为空？**  
- 检查 `config.ini` 中的 `api_key` 是否正确
- 尝试将 `min_confidence` 设为 `0.0`
- 确认 AI 模型支持 OpenAI 兼容的聊天补全接口

**3. 如何降低误报率？**  
调高 `config.ini` 中的 `min_confidence`（如 `0.7`）。也可修改 `ai_analyzer.py` 中的 `is_likely_placeholder()` 函数，增加过滤规则。

**4. 对话模式中如何扫描新网站？**  
直接在对话输入中粘贴新网址（以 `https://` 开头），Agent 会自动爬取新站点并更新上下文，无需退出。

**5. 可以分析需要登录的网站吗？**  
目前未内置登录态，可自行修改 `crawler.py`，在创建页面后添加 `page.context.add_cookies([...])` 注入 Cookie。

**6. 能否分析本地 JS 文件？**  
工具设计为分析在线网站。如需分析本地文件，可将文件路径作为 URL 输入（不推荐），或自行扩展代码。

## 高级定制

- **自定义敏感信息规则**：编辑 `ai_analyzer.py` 中的 `prompt` 和 `is_likely_placeholder()` 函数
- **调整代码截断长度**：修改 `ai_analyzer.py` 中的 `max_chars`（默认 300000 字符）
- **批量扫描**：编写 shell 脚本循环调用 `python src/main.py <URL>`

## 免责声明

本工具仅用于**授权的安全测试**和**代码自查**。请勿用于未经授权的系统。AI 分析结果可能存在误报或漏报，关键发现请务必人工复核。

## 许可证

MIT

---

**项目地址**: [https://github.com/tax3056/API-Agent_JSbot](https://github.com/tax3056/API-Agent_JSbot)  
**让 AI 帮你挖掘 JS 中的宝藏，安静又高效。**
```
