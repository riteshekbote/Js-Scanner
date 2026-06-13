"""
Module: downloader.py
Purpose: Download JS file contents to local storage, ignoring SSL certificate errors
"""
import requests
import os
import hashlib
import urllib3

# Disable SSL warnings (since we use verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_js_files(js_urls, output_dir="downloaded_js"):
    """Download all JS files, ignoring SSL certificate errors"""
    os.makedirs(output_dir, exist_ok=True)
    local_paths = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url in js_urls:
        try:
            # Key change: add verify=False to ignore certificate validation
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code == 200:
                filename = hashlib.md5(url.encode()).hexdigest() + ".js"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                local_paths.append(filepath)
                print(f"   ✅ Downloaded: {os.path.basename(filepath)}")
            else:
                print(f"   ❌ Download failed: {url[:80]}... (HTTP {resp.status_code})")
        except Exception as e:
            print(f"   ❌ Download error: {url[:80]}... - {e}")

    return local_paths
