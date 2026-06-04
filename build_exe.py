import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'src/main.py',
    '--name=JSAuditAgent',
    '--onefile',
    '--noconsole',
    '--add-data=config.ini;.',
    '--add-data=src/crawler.py;src',
    '--add-data=src/downloader.py;src',
    '--add-data=src/ai_analyzer.py;src',
    '--add-data=src/report.py;src',
    '--add-data=src/config_manager.py;src',
    '--collect-all=playwright',
    '--collect-all=jinja2'
])