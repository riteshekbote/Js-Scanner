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
        raise ValueError("Please set api_key in config.ini")
    return OpenAI(api_key=api_key, base_url=api_base)

def is_likely_placeholder(value):
    """Keep content with business meaning, only filter obvious test/placeholder values"""
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
        return {"findings": [], "summary": "File is empty"}

    max_chars = 300000
    if len(js_code) > max_chars:
        js_code = js_code[:max_chars] + "\n\n... [File too large, truncated]"

    ai_config = ConfigManager.get_ai_config()
    model = ai_config['model']
    temperature = ai_config['temperature']
    max_tokens = ai_config['max_tokens']
    min_confidence = ai_config['min_confidence']

    domain_filter_note = ""
    if root_domain:
        domain_filter_note = f"""
**API Endpoint Filtering Rules:**
- Only keep API endpoints related to the current site domain `{root_domain}` (URLs containing this domain or relative paths)
- Exclude third-party domains (e.g. api.google.com, cdn.cloudflare.com)
"""

    prompt = f"""
You are a professional penetration testing expert. Carefully analyze the following JavaScript code and identify **high-value sensitive information that is directly useful for penetration testing**.

{domain_filter_note}

**High-value information includes (only output what is actually exploitable):**
1. **Real API Endpoints**: e.g. `/api/user/info`, `https://internal-ip/api/xxx` (exclude static resource paths)
2. **Hardcoded Credentials**: cloud keys, JWT, database connection strings, passwords, tokens (must have concrete values)
3. **Session Credentials**: real sessionid, token values from cookies
4. **Personal Sensitive Information**: real phone numbers, ID numbers, emails (exclude test data)
5. **Internal Addresses**: 10.x.x.x, 172.16-31.x.x, 192.168.x.x
6. **Business-relevant Variable Names**: e.g. `admin_username`, `admin_password`, `secret_key`, etc. (even if not directly assigned, they indicate risky logic)

**Do NOT output the following low-value content:**
- Version information (jQuery v2.1.4, etc.)
- Generic security advice (e.g. "consider setting HttpOnly" - non-specific)
- Test or placeholder data (test, example, your-key-here)
- Static resource paths (.css, .png, etc.)

**Output JSON only, nothing else:**
{{
  "summary": "Brief summary",
  "findings": [
    {{
      "type": "api_endpoint",
      "value": "/api/user/login",
      "line_context": "Line 45: url: '/api/user/login'",
      "confidence": 0.9,
      "risk_level": "high",
      "suggestion": "Try unauthorized access"
    }}
  ]
}}
Risk levels: critical/high/medium/low

**Code to analyze:**
```javascript
{js_code}
```"""

    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a penetration testing expert. Output only JSON, nothing else. Focus on exploitable sensitive information."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        result_text = response.choices[0].message.content.strip()
        # Clean markdown
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
        print(f"   ⚠️ AI analysis failed: {e}")
        return {"summary": "Analysis failed", "findings": []}

def analyze_js_file_with_context(js_file_path, js_code, file_index, total_files, root_domain=None):
    size_kb = len(js_code) / 1024
    print(f"\n📄 [{file_index}/{total_files}] Analyzing: {os.path.basename(js_file_path)} ({size_kb:.1f} KB)")
    result = analyze_js_file(js_file_path, js_code, root_domain)
    findings = result.get("findings", [])
    if findings:
        print(f"   ⚠️ Found {len(findings)} high-value items")
        for f in findings[:3]:
            print(f"      🔴 [{f.get('risk_level', 'info')}] {f.get('type')}: {f.get('value', '')[:60]}")
    else:
        print(f"   ✅ No obvious sensitive information found")
    return result

def continue_analysis_dialog(analysis_result, scan_callback=None):
    import re
    print("\n" + "=" * 70)
    print("💬 Dialog mode activated - ask anything about these JS files")
    print("   You can also paste a new URL for audit (context will switch automatically)")
    print("   Type 'exit' to leave dialog mode and return to main menu.")
    print("=" * 70)

    current_result = analysis_result
    js_files_content = {}
    for item in current_result['results']:
        file_path = item['file']
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                js_files_content[os.path.basename(file_path)] = f.read()
        else:
            js_files_content[os.path.basename(file_path)] = "File content not available"

    client = get_ai_client()
    ai_config = ConfigManager.get_ai_config()
    model = ai_config['model']
    temperature = ai_config['temperature']

    def build_summary(result):
        s = f"Current audit target: {result['target_url']}\nRoot domain: {result['root_domain']}\nFiles and findings:\n"
        for item in result['results']:
            fname = item['file_name']
            cnt = len(item['findings'])
            s += f"- {fname}: {cnt} findings\n"
        return s

    summary = build_summary(current_result)
    messages = [
        {"role": "system", "content": f"You are a JS security audit assistant. The user has completed an audit. Here is the current summary:\n{summary}\nYou can answer user questions based on specific file content. If the user provides a new URL, the external scan module will handle it; you do not need to scan proactively."}
    ]

    while True:
        user_q = input("\n🔍 You: ").strip()
        if not user_q:
            continue
        if user_q.lower() in ('exit', 'quit', 'q'):
            print("Exiting dialog mode.")
            break

        # Detect URL
        url_match = re.search(r'https?://[^\s]+', user_q, re.IGNORECASE)
        if url_match and scan_callback:
            new_url = url_match.group(0)
            print(f"\n🔄 New URL detected: {new_url}, starting audit...")
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
                        js_files_content[os.path.basename(file_path)] = "File content not available"
                new_summary = build_summary(current_result)
                messages = [{"role": "system", "content": f"You are a JS security audit assistant. The user has completed a new audit. Here is the current summary:\n{new_summary}\nYou can answer user questions based on specific file content."}]
                print("✅ New audit complete, context updated. Feel free to continue asking.")
                continue
            else:
                print("❌ Audit failed, please check the URL or network.")
                continue

        # Normal conversation
        full_context = f"User question: {user_q}\n\nCurrent JS file contents (for reference):\n"
        for fname, code in js_files_content.items():
            short_code = code[:3000] + ("..." if len(code) > 3000 else "")
            full_context += f"\n### File {fname}\n```javascript\n{short_code}\n```\n"
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
            print(f"\n❌ Dialog error: {e}, please try again.")
