"""
主程序：JS安全审计Agent v5.0
支持审计后对话模式，对话中可输入新网址继续扫描
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
        print("🛡️  JS安全审计Agent v5.0 - 渗透测试辅助工具")
        print("=" * 80)
        print("功能：抓取网站JS文件，AI分析敏感信息（API/密钥/手机号/内网IP等）")
        print("     生成HTML报告，支持对话模式，可在对话中直接输入新网址续扫")
        print("=" * 80)

    def print_help(self):
        print("\n📖 使用说明:")
        print("   • 直接输入网址开始审计")
        print("   • 审计完成后自动进入对话模式")
        print("   • 对话中可继续提问，也可直接输入新网址进行扫描")
        print("   • 命令: exit退出, help帮助, clear清屏, history历史")
        print("\n💡 示例:")
        print("   • https://example.com")
        print("   • 帮我审计一下 baidu.com")

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
        print(f"\n🎯 开始审计: {target_url}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

        root_domain = get_root_domain(target_url)
        print(f"🔍 当前站点根域名: {root_domain} (将自动过滤第三方API)")

        # 抓取JS
        print("\n📡 [1/4] 抓取所有JS文件链接...")
        try:
            js_urls = get_all_js_urls(target_url)
            print(f"   ✅ 发现 {len(js_urls)} 个JS文件")
        except Exception as e:
            print(f"   ❌ 抓取失败: {e}")
            return None
        if not js_urls:
            print("   ⚠️ 未发现任何JS文件")
            return None

        # 下载
        print("\n💾 [2/4] 下载JS文件到本地...")
        domain = re.sub(r'[^a-zA-Z0-9]', '_', target_url)[:50]
        cache_dir = os.path.join(CACHE_BASE_DIR, domain)
        js_files = download_js_files(js_urls, output_dir=cache_dir)
        print(f"   ✅ 成功下载 {len(js_files)}/{len(js_urls)} 个文件")
        if not js_files:
            return None

        # AI分析
        print("\n🤖 [3/4] AI正在分析每个JS文件...")
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
                print(f"\n   ❌ 分析失败 {js_file}: {e}")
                all_results.append({"file": js_file, "file_name": os.path.basename(js_file), "size": 0, "findings": []})

        # 生成报告
        print("\n📄 [4/4] 生成HTML报告...")
        os.makedirs(REPORT_DIR, exist_ok=True)
        report_file = generate_html_report(all_results, target_url, output_dir=REPORT_DIR)
        print(f"   ✅ 报告已生成: {report_file}")

        # 统计
        total_findings = sum(len(r['findings']) for r in all_results)
        print("\n" + "=" * 80)
        print("📊 审计完成")
        print(f"   扫描文件数: {len(js_files)}")
        print(f"   发现敏感信息: {total_findings} 处")
        print(f"   报告位置: {report_file}")
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
            print("\n📭 暂无分析历史")
        else:
            print("\n📋 分析历史:")
            for i, item in enumerate(self.history, 1):
                total = sum(len(r['findings']) for r in item['results'])
                print(f"   {i}. {item['url']} - {total} 处发现 - {item['report']}")

    def run(self):
        self.print_header()
        self.print_help()
        while True:
            try:
                user_input = input("\n" + "=" * 80 + "\n💬 你: ").strip()
                if not user_input:
                    continue
                cmd = user_input.lower()
                if cmd in ['exit', '退出', 'quit', 'q']:
                    print("\n👋 再见！")
                    break
                elif cmd in ['help', '帮助', 'h']:
                    self.print_help()
                    continue
                elif cmd in ['clear', '清空', 'cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_header()
                    self.print_help()
                    continue
                elif cmd in ['history', '历史']:
                    self.show_history()
                    continue

                url = self.extract_url(user_input)
                if not url:
                    print("❌ 未识别到有效的URL地址")
                    continue

                print(f"\n🎯 目标网址: {url}")
                confirm = input("确认开始审计？(y/n，直接回车默认y): ").strip().lower()
                if confirm and confirm not in ['y', 'yes', '是']:
                    print("⏸️ 已取消")
                    continue

                result = self.analyze_website(url)
                if result:
                    self.history.append({
                        'url': url,
                        'report': result['report'],
                        'results': result['results'],
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    # 进入对话模式，并传递 scan_callback 以便对话中扫描新网址
                    continue_analysis_dialog(result, scan_callback=self.analyze_website)
                    print("\n回到主菜单...")
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，再见！")
                break
            except Exception as e:
                print(f"\n❌ 程序异常: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    agent = JSSecurityAuditAgent()
    agent.run()