"""
Main program: JS Security Audit Agent v5.0
Supports post-audit dialog mode, can scan new URLs directly from within the dialog
"""
import sys
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from crawler import get_all_js_urls
from downloader import download_js_files
from ai_analyzer import analyze_js_file_with_context, continue_analysis_dialog
from report import generate_html_report
from config_manager import ConfigManager

REPORT_DIR = "reports"
CACHE_BASE_DIR = "js_cache"

def get_root_domain(url):
    parsed = urlparse(url)
    host = parsed.netloc
    if host.startswith('www.'):
        host = host[4:]
    parts = host.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return host

class JSSecurityAuditAgent:
    def __init__(self):
        self.history = []

    def print_header(self):
        print("\n" + "=" * 80)
        print("🛡️  JS Security Audit Agent v5.0 - Penetration Testing Assistant")
        print("=" * 80)
        print("Features: Crawl website JS files, AI analysis of sensitive info (API/keys/phone numbers/internal IPs, etc.)")
        print("     Generate HTML reports, support dialog mode, scan new URLs directly from within dialog")
        print("=" * 80)

    def print_help(self):
        print("\n📖 Instructions:")
        print("   • Enter a URL to start an audit")
        print("   • After audit completes, automatically enters dialog mode")
        print("   • In dialog, you can ask follow-up questions or paste a new URL to scan")
        print("   • Commands: exit quit, help, clear, history")
        print("\n💡 Examples:")
        print("   • https://example.com")
        print("   • audit baidu.com")

    def extract_url(self, text):
        patterns = [r'https?://[^\s<>"{}|\\^`\[\]]+', r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        return None

    def analyze_website(self, target_url):
        print(f"\n🎯 Starting audit: {target_url}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

        root_domain = get_root_domain(target_url)
        print(f"🔍 Current site root domain: {root_domain} (will auto-filter third-party APIs)")

        # Crawl JS
        print("\n📡 [1/4] Crawling all JS file links...")
        try:
            js_urls = get_all_js_urls(target_url)
            print(f"   ✅ Found {len(js_urls)} JS files")
        except Exception as e:
            print(f"   ❌ Crawl failed: {e}")
            return None
        if not js_urls:
            print("   ⚠️ No JS files found")
            return None

        # Download
        print("\n💾 [2/4] Downloading JS files locally...")
        domain = re.sub(r'[^a-zA-Z0-9]', '_', target_url)[:50]
        cache_dir = os.path.join(CACHE_BASE_DIR, domain)
        js_files = download_js_files(js_urls, output_dir=cache_dir)
        print(f"   ✅ Successfully downloaded {len(js_files)}/{len(js_urls)} files")
        if not js_files:
            return None

        # AI analysis
        print("\n🤖 [3/4] AI is analyzing each JS file...")
        all_results = []
        total_js_size = 0
        for idx, js_file in enumerate(js_files, 1):
            try:
                with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                    js_code = f.read()
                total_js_size += len(js_code)
                result = analyze_js_file_with_context(js_file, js_code, idx, len(js_files), root_domain)
                all_results.append({
                    "file": js_file,
                    "file_name": os.path.basename(js_file),
                    "size": len(js_code),
                    "line_count": js_code.count('\n'),
                    "summary": result.get("summary", ""),
                    "findings": result.get("findings", [])
                })
            except Exception as e:
                print(f"\n   ❌ Analysis failed {js_file}: {e}")
                all_results.append({"file": js_file, "file_name": os.path.basename(js_file), "size": 0, "findings": []})

        # Generate report
        print("\n📄 [4/4] Generating HTML report...")
        os.makedirs(REPORT_DIR, exist_ok=True)
        report_file = generate_html_report(all_results, target_url, output_dir=REPORT_DIR)
        print(f"   ✅ Report generated: {report_file}")

        # Stats
        total_findings = sum(len(r['findings']) for r in all_results)
        print("\n" + "=" * 80)
        print("📊 Audit Complete")
        print(f"   Files scanned: {len(js_files)}")
        print(f"   Sensitive info found: {total_findings}")
        print(f"   Report location: {report_file}")
        print("=" * 80)

        return {
            "report": report_file,
            "results": all_results,
            "js_files": js_files,
            "root_domain": root_domain,
            "target_url": target_url
        }

    def show_history(self):
        if not self.history:
            print("\n📭 No audit history")
        else:
            print("\n📋 Audit History:")
            for i, item in enumerate(self.history, 1):
                total = sum(len(r['findings']) for r in item['results'])
                print(f"   {i}. {item['url']} - {total} findings - {item['report']}")

    def run(self):
        self.print_header()
        self.print_help()
        while True:
            try:
                user_input = input("\n" + "=" * 80 + "\n💬 You: ").strip()
                if not user_input:
                    continue
                cmd = user_input.lower()
                if cmd in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                elif cmd in ['help', 'h']:
                    self.print_help()
                    continue
                elif cmd in ['clear', 'cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_header()
                    self.print_help()
                    continue
                elif cmd in ['history']:
                    self.show_history()
                    continue

                url = self.extract_url(user_input)
                if not url:
                    print("❌ No valid URL detected")
                    continue

                print(f"\n🎯 Target URL: {url}")
                confirm = input("Start audit? (y/n, default y): ").strip().lower()
                if confirm and confirm not in ['y', 'yes']:
                    print("⏸️ Cancelled")
                    continue

                result = self.analyze_website(url)
                if result:
                    self.history.append({
                        'url': url,
                        'report': result['report'],
                        'results': result['results'],
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    # Enter dialog mode with scan_callback for scanning new URLs within dialog
                    continue_analysis_dialog(result, scan_callback=self.analyze_website)
                    print("\nBack to main menu...")
            except KeyboardInterrupt:
                print("\n\n👋 User interrupt, goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Program error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    agent = JSSecurityAuditAgent()
    agent.run()
