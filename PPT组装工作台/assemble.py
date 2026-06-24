#!/usr/bin/env python3
"""
组装工作台 -- 读 PPT 制作指南 -> GPT-5.5 -> python-pptx 代码 -> .pptx

用法:
  python assemble.py ../京津冀平台ppt/05_存在的问题/
"""

import os, sys, re, subprocess
from pathlib import Path

if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    except: pass

import requests

# ==================== config ====================
API_KEY = os.getenv("GPT_API_KEY", "__REDACTED_API_KEY__")
BASE_URL = os.getenv("GPT_BASE_URL", "https://one-hub.hycx-gd.cn/v1")
MODEL = os.getenv("PPT_ASSEMBLE_MODEL", "gpt-5.5")

# ==================== input ====================
PAGE_DIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
if not PAGE_DIR or not PAGE_DIR.is_dir():
    print("用法: python assemble.py <页面文件夹>"); sys.exit(1)

GUIDE_FILE = next(PAGE_DIR.glob("*_PPT制作指南.md"), None)
if not GUIDE_FILE:
    print(f"X 未找到 PPT制作指南.md: {PAGE_DIR}"); sys.exit(1)

IMAGES = [f.name for f in PAGE_DIR.glob("component-*.png")]
OUTPUT_NAME = f"{PAGE_DIR.name}.pptx"

print(f"\nGuide: {GUIDE_FILE.name}")
print(f"Images: {', '.join(IMAGES) if IMAGES else '(text only)'}")

# ==================== prompt ====================
guide_text = GUIDE_FILE.read_text(encoding="utf-8")

prompt = f"""你是 python-pptx 专家。根据 PPT 制作指南生成 Python 脚本。

## 指南
{guide_text}

## 可用图片
{', '.join(IMAGES) if IMAGES else '本页无图片'}
路径: str(Path(__file__).parent / "component-x.png")

## 硬约束
- slide: Inches(10), Inches(5.625) (16:9)
- 配色: 标题栏 #1C2833, 背景 #F4F6F6, 正文 #2C3E50, 强调 #2E86AB
- 字体: 中文微软雅黑, 数字/英文 Arial
- 字号: 标题 18-20pt, 正文 8.5-10pt, 脚注 7-8pt
- 图片等比缩放: 宽高比 1.75, 居中不畸变
- 演讲备注: slide.notes_slide.notes_text_frame.text = ...
- 输出文件名: prs.save(str(Path(__file__).parent / (Path(__file__).parent.name + ".pptx")))
- 开头: from pptx import Presentation; from pptx.util import Inches, Pt; from pptx.dml.color import RGBColor; from pathlib import Path

只输出 ```python ``` 代码块，不要解释。
"""

print(f"\nSending to {MODEL}...")

# ==================== call GPT ====================
def call_gpt(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [
        {"role": "system", "content": "你是 python-pptx 专家。只输出代码。"},
        {"role": "user", "content": prompt},
    ], "temperature": 0.2, "max_tokens": 4000}

    for attempt in range(3):
        try:
            resp = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"  {e}")
        if attempt < 2: print(f"  retry {attempt + 2}/3...")
    raise RuntimeError("GPT call failed")

raw = call_gpt(prompt)

# ==================== extract code ====================
code_match = re.search(r"```python\s*\n(.*?)```", raw, re.DOTALL)
if not code_match: code_match = re.search(r"```\s*\n(.*?)```", raw, re.DOTALL)
code = code_match.group(1).strip() if code_match else raw

print("\n" + "=" * 60)
print("GPT generated build.py:")
print("=" * 60)
print(code)
print("=" * 60)

answer = input(f"\nSave & run -> {OUTPUT_NAME}? [Y/n] ").strip().lower()
if answer and answer != "y":
    print("Cancelled"); sys.exit(0)

# ==================== save & run ====================
(PAGE_DIR / "build.py").write_text(code, encoding="utf-8")
print(f"Saved: build.py")

os.chdir(str(PAGE_DIR))
result = subprocess.run([sys.executable, "build.py"], capture_output=True, text=True)
if result.returncode == 0:
    pptx_path = PAGE_DIR / OUTPUT_NAME
    if not pptx_path.exists():
        others = list(PAGE_DIR.glob("*.pptx"))
        if others:
            max(others, key=lambda p: p.stat().st_mtime).rename(pptx_path)
    size = pptx_path.stat().st_size / 1024 if pptx_path.exists() else 0
    print(f"Done: {OUTPUT_NAME} ({size:.0f}KB)")
else:
    print(f"FAIL: {result.stderr}")
    print(f"  code kept at build.py for manual debug")
