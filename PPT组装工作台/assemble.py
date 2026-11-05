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
API_KEY = os.getenv("GPT_API_KEY")
BASE_URL = os.getenv("GPT_BASE_URL")
MODEL = os.getenv("PPT_ASSEMBLE_MODEL", "gpt-5.5")

if not API_KEY or not BASE_URL:
    print("X 请先设置环境变量 GPT_API_KEY 和 GPT_BASE_URL"); sys.exit(1)

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

# ==================== 静态审查 + 隔离执行 ====================
# 审计项：原实现把模型生成的代码直接 subprocess.run 到宿主机。
# 交互确认只能防手滑，不能限制权限。这里做三件事：
#   1) 执行前静态扫描危险模式（外部进程 / 网络 / 动态执行 / 越界文件操作）
#   2) 子进程里注入守卫：禁网、禁起进程（socket/subprocess/ctypes 一律拒绝导入）
#   3) 限时 300s + 最小环境变量 + 只在专题目录内运行
DANGEROUS_PATTERNS = [
    (r"\b(subprocess|os\.system|os\.popen|pty|socket|ctypes|multiprocessing)\b", "外部进程 / 底层调用"),
    (r"\b(requests|urllib|httpx|aiohttp|websockets|http\.client)\b", "网络访问"),
    (r"\b(eval|exec|compile)\s*\(", "动态执行代码"),
    (r"\b(shutil\.rmtree|os\.remove|os\.unlink|os\.rmdir)\b", "删除文件"),
    (r"\bopen\s*\(\s*[rbfu]*['\"](?:[A-Za-z]:[\\/]|/|\.\.)", "访问绝对路径 / 上级目录"),
]

SANDBOX_BOOTSTRAP = r'''
import builtins, os, runpy, sys

BLOCKED = {"socket", "subprocess", "ctypes", "multiprocessing", "pty",
           "requests", "urllib", "http", "httpx", "aiohttp", "websockets"}
_orig_import = builtins.__import__

def _guard_import(name, *a, **k):
    if name.split(".")[0] in BLOCKED:
        raise RuntimeError("[sandbox] 禁止导入模块: " + name)
    return _orig_import(name, *a, **k)

builtins.__import__ = _guard_import

def _denied(*a, **k):
    raise RuntimeError("[sandbox] 禁止执行该操作")

for _n in ("system", "popen", "spawnv", "spawnl", "execv", "execve", "execvp"):
    if hasattr(os, _n):
        setattr(os, _n, _denied)

sys.argv = ["build.py"]
runpy.run_path("build.py", run_name="__main__")
'''


def scan_generated(code: str) -> list[tuple[str, str]]:
    """返回 [(命中的模式说明, 命中的片段)]，空列表表示没发现问题。"""
    hits = []
    for pattern, label in DANGEROUS_PATTERNS:
        m = re.search(pattern, code)
        if m:
            hits.append((label, m.group(0)))
    return hits


def run_sandboxed(code: str, page_dir: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    """在受限解释器里执行 build.py：禁网、禁起子进程、最小环境、限时。"""
    (page_dir / "build.py").write_text(code, encoding="utf-8")
    safe_env = {
        k: v for k, v in os.environ.items()
        if k.upper() in {"SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA"}
    }
    safe_env["PYTHONNOUSERSITE"] = "1"
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", SANDBOX_BOOTSTRAP],
        cwd=str(page_dir), capture_output=True, text=True, timeout=timeout, env=safe_env,
    )


print("\n" + "=" * 60)
print("静态审查")
print("=" * 60)
findings = scan_generated(code)
if findings:
    for label, snippet in findings:
        print(f"  ⚠ {label}: {snippet[:60]}")
    if not os.getenv("PPT_ASSEMBLE_FORCE"):
        print("\n发现可疑模式，已拒绝执行。确认无误后用 PPT_ASSEMBLE_FORCE=1 重跑。")
        print("生成代码已保留在 build.py 供人工审查。")
        (PAGE_DIR / "build.py").write_text(code, encoding="utf-8")
        sys.exit(2)
    print("  （已设置 PPT_ASSEMBLE_FORCE=1，继续）")
else:
    print("  未发现外部进程 / 网络 / 动态执行模式")

answer = input(f"\nSave & run -> {OUTPUT_NAME}? [Y/n] ").strip().lower()
if answer and answer != "y":
    print("Cancelled"); sys.exit(0)

# ==================== save & run ====================
os.chdir(str(PAGE_DIR))
print("运行中（禁网 / 禁子进程 / 300s 上限）...")
try:
    result = run_sandboxed(code, PAGE_DIR)
except subprocess.TimeoutExpired:
    print("FAIL: 生成脚本超过 300s 未结束，已终止")
    sys.exit(1)

if result.returncode == 0:
    pptx_path = PAGE_DIR / OUTPUT_NAME
    if not pptx_path.exists():
        others = list(PAGE_DIR.glob("*.pptx"))
        if others:
            max(others, key=lambda p: p.stat().st_mtime).rename(pptx_path)
    size = pptx_path.stat().st_size / 1024 if pptx_path.exists() else 0
    print(f"Done: {OUTPUT_NAME} ({size:.0f}KB)")
else:
    print(f"FAIL: {result.stderr[:1500]}")
    print(f"  code kept at build.py for manual debug")
