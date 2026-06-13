"""
Module: crawler.py
Purpose: Use a headless browser to visit the target website and collect all loaded JS file URLs (ignoring certificate errors)
"""
from playwright.sync_api import sync_playwright
import urllib.parse

def get_all_js_urls(url, timeout=30000):
    """Return a list of full URLs for all JS files under the given URL, ignoring HTTPS certificate errors"""
    js_urls = set()

    with sync_playwright() as p:
        # Step 1: Launch browser (ignore_https_errors is no longer set here)
        # Recommendation: use chromium (WebKit has stricter cert policy, ignore_https_errors support may be unstable)
        browser = p.chromium.launch(headless=True, proxy=None)

        # Step 2: Create Browser Context, configure parameters properly here
        # Note: ignore_https_errors=True bypasses SSL certificate validation for sites with invalid certs
        context = browser.new_context(ignore_https_errors=True)

        # Step 3: Create a new page via Context
        page = context.new_page()

        # Monitor network requests, capture JS files
        def on_request(request):
            if request.resource_type == "script":
                js_urls.add(request.url)

        page.on("request", on_request)

        # Visit the page with relaxed timeout and wait strategy
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout)
        except Exception as e:
            # If networkidle times out, fall back to domcontentloaded
            print(f"   ⚠️ networkidle timeout, continuing: {e}")
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)

        # Get all script tag src attributes from the page
        script_srcs = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
        }''')
        js_urls.update(script_srcs)

        browser.close()

    # Resolve relative paths to absolute URLs
    base_domain = urllib.parse.urljoin(url, '/')
    full_urls = set()
    for js in js_urls:
        if js.startswith(('http://', 'https://')):
            full_urls.add(js)
        else:
            full_urls.add(urllib.parse.urljoin(base_domain, js))

    return list(full_urls)
