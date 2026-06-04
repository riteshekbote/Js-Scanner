"""
模块：downloader.py
功能：下载JS文件内容到本地，忽略SSL证书错误
"""
import requests
import os
import hashlib
import urllib3

# 禁用SSL警告（因为使用了 verify=False）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_js_files(js_urls, output_dir="downloaded_js"):
    """下载所有JS文件，忽略SSL证书错误"""
    os.makedirs(output_dir, exist_ok=True)
    local_paths = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url in js_urls:
        try:
            # 关键修改：添加 verify=False 忽略证书验证
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code == 200:
                filename = hashlib.md5(url.encode()).hexdigest() + ".js"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                local_paths.append(filepath)
                print(f"   ✅ 下载成功: {os.path.basename(filepath)}")
            else:
                print(f"   ❌ 下载失败: {url[:80]}... (HTTP {resp.status_code})")
        except Exception as e:
            print(f"   ❌ 下载异常: {url[:80]}... - {e}")

    return local_paths