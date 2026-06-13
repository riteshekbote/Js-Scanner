API Agent — AI-Powered JS Security Audit Tool

API Agent is a JavaScript code audit tool designed for penetration testing. It automatically crawls all JS files from a target website, performs deep analysis using AI (DeepSeek / OpenAI / local models), accurately identifies high-value sensitive information (API endpoints, hardcoded secrets, JWT, phone numbers, ID numbers, internal IPs, etc.), and generates an interactive HTML report. It supports a post-audit dialog mode where you can continue asking questions or directly enter new URLs for seamless scanning, greatly improving penetration testing efficiency.

## Configuration

Create a `config.ini` file in the project root directory:

```ini
[AI]
api_base = https://api.deepseek.com
api_key = sk-your-actual-key
model = deepseek-chat
temperature = 0.1
max_tokens = 8192
min_confidence = 0.0

[App]
report_dir = reports
cache_dir = js_cache
auto_open_report = false
```

| Config | Description |
|--------|-------------|
| `api_base` | OpenAI-compatible API service URL |
| `api_key` | Your API key |
| `model` | Model name (e.g. `deepseek-chat`, `gpt-4o-mini`, `llama3`) |
| `temperature` | 0–1, lower = more deterministic (recommended 0.1 for audit) |
| `max_tokens` | Max output tokens per analysis |
| `min_confidence` | 0.0–1.0, findings below this threshold are filtered (0.0 keeps all) |
| `report_dir` | HTML report output directory |
| `cache_dir` | Downloaded JS file cache directory |
| `auto_open_report` | Whether to auto-open the report (Windows) |

### Switching AI Providers

| Provider | `api_base` | `api_key` | `model` |
|----------|-----------|-----------|---------|
| DeepSeek | `https://api.deepseek.com` | Your DeepSeek key | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | Your OpenAI key | `gpt-4o-mini` |
| Local Ollama | `http://localhost:11434/v1` | Any string (e.g. `ollama`) | Your pulled model (e.g. `llama3`) |

## Usage

### Interactive Mode (Recommended)

```bash
python src/main.py
```

- Enter a URL (e.g. `https://example.com`) to start the audit
- After the audit completes, automatically enters **Dialog Mode**
- In dialog mode:
  - Ask follow-up questions: e.g. "Explain what that key in `config.js` is used for"
  - Paste a new URL: directly enter `https://another-site.com`, and the AI will automatically scan the new site and update the context
  - Enter `exit` to leave dialog mode and return to the main menu
- Built-in commands: `help`, `clear`, `history`

### Single Scan Mode

```bash
python src/main.py https://example.com
```

Runs the full audit pipeline (crawl → download → analyze → generate report) and exits.<img width="1005" height="1173" alt="c6f2cd83a1c8b353b7e66433e1650424" src="https://github.com/user-attachments/assets/50f77a03-3dff-4a04-b8f8-e31a59c8b790" />

<img width="951" height="1155" alt="d3b1dc5da22e54e20afbd10b509e35a2" src="https://github.com/user-attachments/assets/07913ed4-367a-40ae-8e0b-5afa9a199c6f" />

<img width="1788" height="396" alt="c7858762e4317ac30be0d0848a0d42bb" src="https://github.com/user-attachments/assets/ca892ab4-cfb6-46ec-9a04-cbc3f7f8d9c3" />

### Package as Windows EXE

```bash
python build_exe.py
```

Generates `dist/API_Agent.exe`, a single-file executable that runs without a Python environment (the target machine must have Playwright browsers installed, or install via `playwright install chromium`).

## Report Features

The generated HTML report includes:

- **Stats Cards**: scanned file count, total findings, critical/high risk counts
- **Leak Type Distribution**: categorized by API endpoints, hardcoded secrets, personal info, etc.
- **Per-File Detailed Findings**:
  - Type (`api_endpoint`, `hardcoded_secret`, `phone_number`, etc.)
  - Leaked content (**full original value** for easy copy-paste)
  - Code context (line number and surrounding code)
  - Risk level (`critical` / `high` / `medium` / `low`)
  - Remediation suggestions
  - Confidence percentage
- **One-Click Copy**: copy all findings (tab-separated, pasteable into Excel) or just the API endpoint list (one URL per line)

<img width="1614" height="1389" alt="55eb0608e502ace9f8189120ee372fa3" src="https://github.com/user-attachments/assets/3c7a93a8-b3e1-45a6-b859-f751a4807f85" />

<img width="1433" height="741" alt="7cf9d09c2357cfec2ba4f5a2f0cdc342" src="https://github.com/user-attachments/assets/dd25e004-1bc6-4157-87a4-e3b711ea9e50" />

## FAQ

**1. SSL certificate errors?**  
The tool already ignores certificate errors (Playwright and requests are both configured with `verify=False`). If errors persist, check that the target website is accessible.

**2. AI analysis returns no results or the report is empty?**  
- Check that `api_key` in `config.ini` is correct
- Try setting `min_confidence` to `0.0`
- Confirm the AI model supports OpenAI-compatible chat completion endpoints

**3. How to reduce false positives?**  
Increase `min_confidence` in `config.ini` (e.g. `0.7`). You can also modify the `is_likely_placeholder()` function in `ai_analyzer.py` to add more filtering rules.

**4. How to scan a new website in dialog mode?**  
Simply paste a new URL (starting with `https://`) directly in the dialog input. The Agent will automatically crawl the new site and update the context without needing to exit.

**5. Can it analyze websites that require login?**  
Currently no built-in login state. You can modify `crawler.py` to add `page.context.add_cookies([...])` after creating the page to inject cookies.

**6. Can it analyze local JS files?**  
The tool is designed for online websites. To analyze local files, you can enter the file path as a URL (not recommended), or extend the code yourself.

## Advanced Customization

- **Custom sensitive info rules**: Edit the `prompt` and `is_likely_placeholder()` function in `ai_analyzer.py`
- **Adjust code truncation length**: Modify `max_chars` in `ai_analyzer.py` (default 300000 chars)
- **Batch scanning**: Write a shell script to loop through `python src/main.py <URL>`

## Disclaimer

This tool is intended for **authorized security testing** and **self-code review only**. Do not use it on unauthorized systems. AI analysis results may contain false positives or false negatives; always manually verify critical findings.

## License

MIT

---

**Project URL**: [https://github.com/tax3056/API-Agent_JSbot](https://github.com/tax3056/API-Agent_JSbot)  
**Let AI uncover the gold in your JS files — quietly and efficiently.**
