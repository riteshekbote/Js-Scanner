"""
Module: report.py
Purpose: Generate a detailed HTML audit report with code context, one-click copy, expand/collapse all
"""
from jinja2 import Template
from datetime import datetime
import re
import os

def sanitize_filename(url):
    """Generate a valid filename from a URL"""
    name = re.sub(r'^https?://', '', url)
    name = re.sub(r'[^\w\-_\.]', '_', name)
    if len(name) > 100:
        name = name[:100]
    return name

def generate_html_report(all_results, target_url, output_dir="reports"):
    """Generate HTML report with full details and interactive features"""
    os.makedirs(output_dir, exist_ok=True)

    total_files = len(all_results)
    total_findings = sum(len(r['findings']) for r in all_results)

    risk_stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for result in all_results:
        for finding in result['findings']:
            risk = finding.get('risk_level', 'low')
            if risk in risk_stats:
                risk_stats[risk] += 1

    type_stats = {}
    for result in all_results:
        for finding in result['findings']:
            ftype = finding.get('type', 'other')
            type_stats[ftype] = type_stats.get(ftype, 0) + 1

    template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JS Security Audit Report - {{ target_url }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .url { font-size: 16px; opacity: 0.9; word-break: break-all; }
        .header .time { font-size: 14px; opacity: 0.8; margin-top: 10px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #667eea; }
        .stat-card .label { color: #666; margin-top: 5px; }
        .stat-card .button-group { margin-top: 15px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
        
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: bold;
            transition: background 0.2s;
        }
        .copy-btn:hover { background: #218838; }
        .copy-api-btn { background: #17a2b8; }
        .copy-api-btn:hover { background: #138496; }
        .expand-btn { background: #6c757d; }
        .expand-btn:hover { background: #5a6268; }
        
        .risk-critical { background: #dc2626; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        .risk-high { background: #f97316; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        .risk-medium { background: #eab308; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        .risk-low { background: #22c55e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; }
        
        .file-card { background: white; border-radius: 12px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .file-header { background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e9ecef; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .file-header:hover { background: #e9ecef; }
        .file-name { font-weight: 600; font-family: monospace; font-size: 14px; color: #333; word-break: break-all; }
        .file-badge { background: #667eea; color: white; padding: 2px 10px; border-radius: 20px; font-size: 12px; }
        .file-content { padding: 20px; display: none; }
        .file-content.open { display: block; }
        
        .findings-table { width: 100%; border-collapse: collapse; }
        .findings-table th, .findings-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e9ecef; vertical-align: top; }
        .findings-table th { background: #f8f9fa; font-weight: 600; color: #495057; }
        .findings-table tr:hover { background: #f8f9fa; }
        
        .finding-value { 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            background: #f1f3f4; 
            padding: 4px 8px; 
            border-radius: 4px; 
            word-break: break-all; 
            white-space: pre-wrap;
            max-width: 350px;
            display: inline-block;
            user-select: text;
            cursor: text;
        }
        .line-context {
            font-family: monospace;
            font-size: 12px;
            background: #fff3cd;
            padding: 4px 8px;
            border-radius: 4px;
            word-break: break-all;
            white-space: pre-wrap;
            max-width: 400px;
        }
        .suggestion { font-size: 13px; color: #6c757d; max-width: 300px; }
        
        .no-findings { text-align: center; padding: 40px; color: #6c757d; }
        .no-findings:before { content: "✅ "; font-size: 20px; }
        
        .footer { text-align: center; padding: 20px; color: #6c757d; font-size: 12px; margin-top: 20px; }
        
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
            pointer-events: none;
        }
        .toast.show { opacity: 1; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔒 JS Security Audit Report</h1>
        <div class="url">Target: {{ target_url }}</div>
        <div class="time">Generated: {{ now }}</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card"><div class="number">{{ total_files }}</div><div class="label">Files Scanned</div></div>
        <div class="stat-card">
            <div class="number">{{ total_findings }}</div>
            <div class="label">Findings</div>
            {% if total_findings > 0 %}
            <div class="button-group">
                <button class="copy-btn" id="copyAllBtn">📋 Copy All Findings</button>
                <button class="copy-btn copy-api-btn" id="copyApiBtn">🌐 Copy API Endpoints</button>
            </div>
            {% endif %}
        </div>
        <div class="stat-card"><div class="number">{{ risk_stats.critical }}</div><div class="label">Critical Risk</div></div>
        <div class="stat-card"><div class="number">{{ risk_stats.high }}</div><div class="label">High Risk</div></div>
    </div>
    
    {% if type_stats %}
    <div class="stat-card" style="margin-bottom: 20px;">
        <div class="label">Leak Type Distribution</div>
        <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 10px;">
            {% for type, count in type_stats.items() %}
            <span style="background: #e9ecef; padding: 4px 12px; border-radius: 20px; font-size: 13px;">{{ type }}: {{ count }}</span>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0;">📁 Detailed Analysis Results</h3>
        <div>
            <button class="copy-btn expand-btn" id="expandAllBtn">📂 Expand All</button>
            <button class="copy-btn expand-btn" id="collapseAllBtn">📁 Collapse All</button>
        </div>
    </div>
    
    {% for item in all_results %}
    <div class="file-card">
        <div class="file-header" onclick="toggleFile(this)">
            <span class="file-name">📄 {{ item.file_name }}</span>
            <span class="file-badge">{{ item.findings|length }} findings</span>
        </div>
        <div class="file-content">
            {% if item.findings %}
            <table class="findings-table">
                <thead>
                    <tr><th>Type</th><th>Leaked Content</th><th>Code Context</th><th>Risk Level</th><th>Remediation</th><th>Confidence</th></tr>
                </thead>
                <tbody>
                    {% for finding in item.findings %}
                    <tr data-type="{{ finding.type }}" data-value="{{ finding.value }}" data-risk="{{ finding.risk_level }}">
                        <td><strong>{{ finding.type }}</strong></td>
                        <td><code class="finding-value">{{ finding.value }}</code></td>
                        <td class="line-context">{{ finding.line_context|default('Unknown position') }}</td>
                        <td><span class="risk-{{ finding.risk_level }}">{{ finding.risk_level | upper }}</span></td>
                        <td class="suggestion">{{ finding.suggestion }}</td>
                        <td>{{ (finding.confidence * 100)|int }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="no-findings">No sensitive information leaked</div>
            {% endif %}
        </div>
    </div>
    {% endfor %}
    
    <div class="footer">
        <p>Report generated by JS Security Audit Agent | AI analysis may contain false positives, please manually verify</p>
        <p style="margin-top: 5px;">⚠️ It is recommended to address any discovered sensitive information leaks promptly</p>
    </div>
</div>

<div id="toast" class="toast">Copied to clipboard</div>

<script>
function toggleFile(header) {
    var content = header.nextElementSibling;
    content.classList.toggle('open');
}

function expandAll() {
    var contents = document.querySelectorAll('.file-content');
    contents.forEach(function(content) {
        content.classList.add('open');
    });
}

function collapseAll() {
    var contents = document.querySelectorAll('.file-content');
    contents.forEach(function(content) {
        content.classList.remove('open');
    });
}

function copyToClipboard(text, successMsg) {
    navigator.clipboard.writeText(text).then(function() {
        var toast = document.getElementById('toast');
        toast.textContent = successMsg || 'Copied to clipboard';
        toast.classList.add('show');
        setTimeout(function() {
            toast.classList.remove('show');
        }, 2000);
    }).catch(function(err) {
        console.error('Copy failed: ', err);
        alert('Copy failed, please manually select and copy');
    });
}

function copyAllFindings() {
    var rows = document.querySelectorAll('.findings-table tbody tr');
    var findings = [];
    rows.forEach(function(row) {
        var type = row.cells[0]?.innerText.trim() || '';
        var value = row.cells[1]?.innerText.trim() || '';
        var risk = row.cells[3]?.innerText.trim() || '';
        if (value && value !== 'No sensitive information leaked') {
            findings.push(`${type}\t${value}\t${risk}`);
        }
    });
    if (findings.length === 0) {
        alert('Nothing to copy');
        return;
    }
    copyToClipboard(findings.join('\\n'), 'Copied ' + findings.length + ' findings');
}

function copyApiEndpoints() {
    var rows = document.querySelectorAll('.findings-table tbody tr');
    var apiList = [];
    rows.forEach(function(row) {
        var type = row.cells[0]?.innerText.trim() || '';
        var value = row.cells[1]?.innerText.trim() || '';
        if (value && (type.includes('api_endpoint') || type.includes('api_') || type === 'api_endpoint')) {
            apiList.push(value);
        }
    });
    if (apiList.length === 0) {
        alert('No API endpoints found');
        return;
    }
    copyToClipboard(apiList.join('\\n'), 'Copied ' + apiList.length + ' API endpoints');
}

document.addEventListener('DOMContentLoaded', function() {
    var allBtn = document.getElementById('copyAllBtn');
    if (allBtn) allBtn.addEventListener('click', copyAllFindings);
    var apiBtn = document.getElementById('copyApiBtn');
    if (apiBtn) apiBtn.addEventListener('click', copyApiEndpoints);
    var expandBtn = document.getElementById('expandAllBtn');
    if (expandBtn) expandBtn.addEventListener('click', expandAll);
    var collapseBtn = document.getElementById('collapseAllBtn');
    if (collapseBtn) collapseBtn.addEventListener('click', collapseAll);
});
</script>
</body>
</html>
    """

    template = Template(template_str)
    filename = sanitize_filename(target_url)
    output_file = os.path.join(output_dir, f"{filename}.html")

    report_data = []
    for r in all_results:
        report_data.append({
            "file_name": os.path.basename(r["file"]),
            "findings": r.get("findings", [])
        })

    html = template.render(
        target_url=target_url,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_files=total_files,
        total_findings=total_findings,
        risk_stats=risk_stats,
        type_stats=type_stats,
        all_results=report_data
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file
