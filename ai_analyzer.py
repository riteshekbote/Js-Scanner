import os
import json
import re
from openai import OpenAI
from config_manager import ConfigManager

def get_ai_client():
    ai_config = ConfigManager.get_ai_config()
    api_key = ai_config.get('api_key')
    api_base = ai_config.get('api_base')
    if not api_key:
        raise ValueError("请在 config.ini 中设置 api_key")
    return OpenAI(api_key=api_key, base_url=api_base)

def is_likely_placeholder(value):
    """保留有业务含义的内容，仅过滤明显的测试/占位符"""
    if not value or len(value) < 3:
        return True
    if value.isdigit() and len(value) < 5:
        return True
    placeholder_patterns = [
        r'(?i)^(test|example|demo|your-|changeme|placeholder|dummy|sample)',
        r'^[a-f0-9]{32}$',
    ]
    for pat in placeholder_patterns:
        if re.match(pat, value):
            return True
    static_ext = ('.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.ttf', '.eot', '.map', '.webp')
    if value.lower().endswith(static_ext):
        return True
    return False

def filter_high_value_findings(findings, min_confidence=0.0):
    filtered = []
    for f in findings:
        conf = f.get('confidence', 0)
        if conf < min_confidence:
            continue
        value = f.get('value', '')
        if not is_likely_placeholder(value):
            filtered.append(f)
    return filtered

def analyze_js_file(js_file_path, js_code, root_domain=None):
    if not js_code or len(js_code.strip()) == 0:
        return {"findings": [], "summary": "文件为空"}

    max_chars = 300000
    if len(js_code) > max_chars:
        js_code = js_code[:max_chars] + "\n\n... [文件过大，已截取]"

    ai_config = ConfigManager.get_ai_config()
    model = ai_config['model']
    temperature = ai_config['temperature']
    max_tokens = ai_config['max_tokens']
    min_confidence = ai_config['min_confidence']

    domain_filter_note = ""
    if root_domain:
        domain_filter_note = f"""
**API 接口过滤规则：**
- 只保留与当前站点域名 `{root_domain}` 相关的 API 接口（URL包含该域名或相对路径）
- 排除第三方域名（如 api.google.com、cdn.cloudflare.com）
"""

    prompt = f"""
你是一位专业的渗透测试专家。请仔细分析以下 JavaScript 代码，找出**对渗透测试有直接帮助的高价值敏感信息**。

{domain_filter_note}

**高价值信息包括（只输出真实可利用的）：**
1. **真实 API 端点**：例如 `/api/user/info`、`https://内网IP/api/xxx`（排除静态资源路径）
2. **硬编码凭证**：云密钥、JWT、数据库连接串、密码、Token（必须有具体值）
3. **会话凭证**：Cookie 中的 sessionid、token 真实值
4. **个人敏感信息**：真实手机号、身份证、邮箱（排除测试数据）
5. **内网地址**：10.x.x.x、172.16-31.x.x、192.168.x.x
6. **有业务含义的变量名**：如 `admin_username`、`admin_password`、`secret_key` 等（即使未直接赋值，也说明存在风险逻辑）

**不要输出以下低价值内容：**
- 版本信息（jQuery v2.1.4 等）
- 通用安全建议（如“建议设置 HttpOnly”等非具体问题）
- 测试或占位符数据（test、example、your-key-here）
- 静态资源路径（.css、.png 等）

**输出 JSON 格式，只输出 JSON：**
{{
  "summary": "简短总结",
  "findings": [
    {{
      "type": "api_endpoint",
      "value": "/api/user/login",
      "line_context": "第45行: url: '/api/user/login'",
      "confidence": 0.9,
      "risk_level": "high",
      "suggestion": "可尝试未授权访问"
    }}
  ]
}}
风险等级：critical/high/medium/low

**待分析代码：**
```javascript
{js_code}
```"""

    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是渗透测试专家，只输出 JSON，不要输出其他内容。重点关注可被利用的敏感信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        result_text = response.choices[0].message.content.strip()
        # 清理 markdown
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result = json.loads(result_text)
        if "findings" in result:
            result["findings"] = filter_high_value_findings(result["findings"], min_confidence)
        return result
    except Exception as e:
        print(f"   ⚠️ AI分析失败: {e}")
        return {"summary": "分析失败", "findings": []}

def analyze_js_file_with_context(js_file_path, js_code, file_index, total_files, root_domain=None):
    size_kb = len(js_code) / 1024
    print(f"\n📄 [{file_index}/{total_files}] 正在分析: {os.path.basename(js_file_path)} ({size_kb:.1f} KB)")
    result = analyze_js_file(js_file_path, js_code, root_domain)
    findings = result.get("findings", [])
    if findings:
        print(f"   ⚠️ 发现 {len(findings)} 处高价值信息")
        for f in findings[:3]:
            print(f"      🔴 [{f.get('risk_level', 'info')}] {f.get('type')}: {f.get('value', '')[:60]}")
    else:
        print(f"   ✅ 未发现明显敏感信息")
    return result

def continue_analysis_dialog(analysis_result, scan_callback=None):
    import re
    print("\n" + "=" * 70)
    print("💬 进入对话模式 - 你可以提问关于这些 JS 文件的任何问题")
    print("   也可以直接输入新的网址进行审计（程序会自动切换上下文）")
    print("   输入 'exit' 退出对话，返回主菜单。")
    print("=" * 70)

    current_result = analysis_result
    js_files_content = {}
    for item in current_result['results']:
        file_path = item['file']
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                js_files_content[os.path.basename(file_path)] = f.read()
        else:
            js_files_content[os.path.basename(file_path)] = "文件内容不可用"

    client = get_ai_client()
    ai_config = ConfigManager.get_ai_config()
    model = ai_config['model']
    temperature = ai_config['temperature']

    def build_summary(result):
        s = f"当前审计目标: {result['target_url']}\n根域名: {result['root_domain']}\n文件列表及发现:\n"
        for item in result['results']:
            fname = item['file_name']
            cnt = len(item['findings'])
            s += f"- {fname}: {cnt} 条发现\n"
        return s

    summary = build_summary(current_result)
    messages = [
        {"role": "system", "content": f"你是 JS 安全审计助手。用户已完成审计，以下是当前摘要：\n{summary}\n你可以基于具体文件内容回答用户的问题。如果用户提供了新网址，将由外部扫描模块处理，你无需主动扫描。"}
    ]

    while True:
        user_q = input("\n🔍 你: ").strip()
        if not user_q:
            continue
        if user_q.lower() in ('exit', 'quit', 'q'):
            print("退出对话模式。")
            break

        # 检测URL
        url_match = re.search(r'https?://[^\s]+', user_q, re.IGNORECASE)
        if url_match and scan_callback:
            new_url = url_match.group(0)
            print(f"\n🔄 检测到新网址: {new_url}，正在审计...")
            new_result = scan_callback(new_url)
            if new_result:
                current_result = new_result
                js_files_content.clear()
                for item in current_result['results']:
                    file_path = item['file']
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            js_files_content[os.path.basename(file_path)] = f.read()
                    else:
                        js_files_content[os.path.basename(file_path)] = "文件内容不可用"
                new_summary = build_summary(current_result)
                messages = [{"role": "system", "content": f"你是 JS 安全审计助手。用户已完成新审计，以下是当前摘要：\n{new_summary}\n你可以基于具体文件内容回答用户的问题。"}]
                print("✅ 新审计完成，上下文已更新。可以继续提问。")
                continue
            else:
                print("❌ 审计失败，请检查网址或网络。")
                continue

        # 普通对话
        full_context = f"用户问题: {user_q}\n\n当前所有 JS 文件内容（按需参考）：\n"
        for fname, code in js_files_content.items():
            short_code = code[:3000] + ("..." if len(code) > 3000 else "")
            full_context += f"\n### 文件 {fname}\n```javascript\n{short_code}\n```\n"
        messages.append({"role": "user", "content": full_context})
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=4096
            )
            reply = response.choices[0].message.content
            print("\n🤖 AI: " + reply)
            messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n❌ 对话出错: {e}，请重试。")