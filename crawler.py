"""
模块：crawler.py
功能：使用无头浏览器访问目标网站，收集所有加载的JS文件URL（忽略证书错误）
"""
from playwright.sync_api import sync_playwright
import urllib.parse

def get_all_js_urls(url, timeout=30000):
    """返回该URL下所有JS文件的完整URL列表，忽略HTTPS证书错误"""
    js_urls = set()

    with sync_playwright() as p:
        # 步骤1：启动浏览器（这里不再设置 ignore_https_errors）
        # 推荐使用 chromium（WebKit 对证书策略更严格，ignore_https_errors 支持可能不稳定）[reference:1][reference:2]
        browser = p.chromium.launch(headless=True, proxy=None)

        # 步骤2：创建 Browser Context，在这里正确设置参数
        # 注意：ignore_https_errors=True 将绕过 SSL 证书验证，允许访问证书无效的 HTTPS 站点[reference:3][reference:4]
        context = browser.new_context(ignore_https_errors=True)

        # 步骤3：通过 Context 创建新页面
        page = context.new_page()

        # 监听网络请求，捕获JS文件
        def on_request(request):
            if request.resource_type == "script":
                js_urls.add(request.url)

        page.on("request", on_request)

        # 访问页面，设置更宽松的超时和等待策略
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout)
        except Exception as e:
            # 如果 networkidle 超时，尝试使用 domcontentloaded 继续
            print(f"   ⚠️ 等待 networkidle 超时，尝试继续: {e}")
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)

        # 获取页面中所有 script 标签的 src
        script_srcs = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
        }''')
        js_urls.update(script_srcs)

        browser.close()

    # 补全相对路径为绝对URL
    base_domain = urllib.parse.urljoin(url, '/')
    full_urls = set()
    for js in js_urls:
        if js.startswith(('http://', 'https://')):
            full_urls.add(js)
        else:
            full_urls.add(urllib.parse.urljoin(base_domain, js))

    return list(full_urls)