#!/usr/bin/env python3
"""
生图工作台 - 扫描 PPT 制作指南，从 prompts/ 目录提取提示词，调用 GPT-Image2 生图。

工作流:
  PPT制作指南(@prompt:id) ──→ prompts/component-x.md ──→ GPT-Image2 API ──→ output/*.png

用法:
  python generate.py                        # 扫描所有指南，列出每页需要哪些组件
  python generate.py --page 02              # 为第（2）页生图
  python generate.py --page 02 --dry-run    # 预览第（2）页所有提示词
  python generate.py --all                  # 扫描所有页面，批量生图
  python generate.py --component component-a  # 按组件ID直接生成

提示词目录:
  ../京津冀平台ppt/prompts/*.md
PPT指南:
  ../京津冀平台ppt/*_PPT制作指南.md
"""

import os
import sys
import json
import time
import base64
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Windows GBK 兼容
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests

# ======================== 路径配置 ========================

WORKBENCH_DIR = Path(__file__).parent
OUTPUT_DIR = WORKBENCH_DIR / "output"
CHECKPOINT_FILE = OUTPUT_DIR / ".checkpoint.json"

# PPT 制作指南目录（每页一个子文件夹，其中包含指南 md + prompts/）
GUIDES_DIR = WORKBENCH_DIR.parent / "京津冀平台ppt"

# API 配置
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "__REDACTED_API_KEY__")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://one-hub.hycx-gd.cn/v1")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-2-ca")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1792x1024")
IMAGE_QUALITY = os.getenv("IMAGE_QUALITY", "high")
MAX_RETRIES = 3
RETRY_DELAY = 10
API_TIMEOUT = 300


# ======================== 提示词文件解析 ========================

def parse_prompts_dir(prompts_dir: str) -> Dict[str, Dict]:
    """
    扫描 prompts/ 目录，每个 .md 文件一个组件。
    文件格式：
        ---
        id: component-x
        title: 组件名称
        usage: ...
        size: ...
        ---
        (英文提示词正文)
    返回 {component_id: {id, title, prompt, ...}}
    """
    if not Path(prompts_dir).exists():
        print(f"❌ 提示词目录不存在: {prompts_dir}")
        sys.exit(1)

    components = {}

    for f in sorted(Path(prompts_dir).glob("*.md")):
        content = f.read_text(encoding="utf-8")

        # 解析 frontmatter（--- ... ---）
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not fm_match:
            print(f"⚠️ {f.name}: 缺少 frontmatter，跳过")
            continue

        yaml_text = fm_match.group(1)
        prompt_text = fm_match.group(2).strip()

        # 提取 id 和 title
        id_match = re.search(r'id:\s*(.*)', yaml_text)
        title_match = re.search(r'title:\s*(.*)', yaml_text)
        comp_id = id_match.group(1).strip() if id_match else f.stem
        title = title_match.group(1).strip() if title_match else comp_id

        components[comp_id] = {
            "id": comp_id,
            "title": title,
            "file": f.name,
            "prompt": prompt_text,
            "prompt_length": len(prompt_text),
        }

    return components


# ======================== PPT 指南扫描 ========================

def scan_guides(guides_dir: str) -> List[Dict]:
    """
    递归扫描 PPT 制作指南目录，每页一个子文件夹，
    提取子文件夹内 *_PPT制作指南.md 的 @prompt:<id> 引用。
    返回 [{page, folder, file, title, components: [component_id, ...], prompts_dir}]
    """
    guides = []
    guide_pattern = re.compile(r'@prompt:(component-\w+)')

    for f in sorted(Path(guides_dir).glob("**/*_PPT制作指南.md")):
        content = f.read_text(encoding="utf-8")

        # 提取页面标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        page_title = title_match.group(1) if title_match else f.stem

        # 提取页面编号（如 02）
        page_match = re.match(r'(\d+)', f.name)
        page_num = page_match.group(1) if page_match else "??"

        # 提取 @prompt:id 引用（去重、保序）
        refs = list(dict.fromkeys(guide_pattern.findall(content)))

        # 该页面的 prompts 目录
        prompts_dir = f.parent / "prompts"

        if refs:
            guides.append({
                "page": page_num,
                "folder": str(f.parent),
                "file": f.name,
                "title": page_title,
                "components": refs,
                "prompts_dir": str(prompts_dir),
            })

    return guides


# ======================== 断点管理 ========================

def load_checkpoint() -> Dict:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    return {}


def save_checkpoint(comp_id: str, image_path: str):
    cp = load_checkpoint()
    cp[comp_id] = {
        "image_path": image_path,
        "generated_at": datetime.now().isoformat(),
    }
    CHECKPOINT_FILE.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")


# ======================== 图片生成 ========================

def generate_image(prompt: str, output_name: str) -> Optional[str]:
    """调用 GPT-Image2 API 生成图片（线程安全），返回保存路径"""
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": IMAGE_SIZE,
        "quality": IMAGE_QUALITY,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                f"{IMAGE_BASE_URL}/images/generations",
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()["data"][0]
                return _save_image(data, output_name)
            else:
                error_text = resp.text[:200]
                if resp.status_code == 400 and "content_filter" in error_text.lower():
                    return None
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    return None


def _save_image(data: dict, name: str) -> Optional[str]:
    """保存图片到 output 目录（线程安全）"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if "b64_json" in data and data["b64_json"]:
        img_bytes = base64.b64decode(data["b64_json"])
    elif "url" in data and data["url"]:
        r = requests.get(data["url"], timeout=60)
        img_bytes = r.content
    else:
        return None

    out_path = OUTPUT_DIR / f"{name}.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    return str(out_path)


# ======================== 命令实现 ========================

def cmd_list(guides: List[Dict]):
    """按页面展示：每页需要哪些组件"""
    print("\n📋 PPT 页面 → 组件清单\n")

    all_ids = set()
    for g in guides:
        # 加载该页面的提示词
        lib = parse_prompts_dir(g["prompts_dir"])
        count = len(g["components"])
        print(f"  第({g['page']})页: {g['title']}")
        print(f"    指南: {g['file']}  (在 {Path(g['folder']).name}/)")
        print(f"    需要组件 ({count}个):")
        for cid in g["components"]:
            info = lib.get(cid, {})
            title = info.get("title", "⚠️ prompts/ 中未找到!")
            prompt_len = info.get("prompt_length", 0)
            print(f"      {cid}  →  {title}  ({prompt_len}字符)")
        print()
        all_ids.update(g["components"])

    print(f"{'─'*60}")
    print(f"共 {len(guides)} 个页面, 涉及 {len(all_ids)} 个组件")
    print(f"根目录: {GUIDES_DIR}")

    print(f"\n用法:")
    print(f"  python generate.py --page 02         # 为指定页面生图")
    print(f"  python generate.py --all              # 扫描所有页面，批量生图")


def cmd_dry_run_page(page_num: str, guides: List[Dict]):
    """预览指定页面的所有提示词"""
    guide = next((g for g in guides if g["page"] == page_num), None)
    if not guide:
        page_ids = [g["page"] for g in guides]
        print(f"❌ 未找到第({page_num})页，可用: {', '.join(page_ids)}")
        sys.exit(1)

    lib = parse_prompts_dir(guide["prompts_dir"])

    print(f"\n📝 第({guide['page']})页: {guide['title']}")
    print(f"   来源: {Path(guide['folder']).name}/{guide['file']}\n")

    for cid in guide["components"]:
        comp = lib.get(cid)
        if not comp:
            print(f"\n⚠️ {cid}: prompts/ 中未找到!\n")
            continue
        print(f"{'─'*60}")
        print(f"组件: {comp['title']} ({cid})")
        print(f"提示词长度: {comp['prompt_length']} 字符")
        print(f"{'─'*60}")
        print(comp["prompt"])
        print()


def cmd_dry_run_component(cid: str, guides: List[Dict]):
    """预览单个组件提示词（从所有页面的 prompts 中查找）"""
    comp = None
    for g in guides:
        lib = parse_prompts_dir(g["prompts_dir"])
        if cid in lib:
            comp = lib[cid]
            break
    if not comp:
        print(f"❌ 未知组件: {cid}")
        print(f"   可用: 扫描所有页面的 prompts/ 目录")
        sys.exit(1)

    print(f"\n📝 组件: {comp['title']} ({comp['id']})")
    print(f"提示词长度: {comp['prompt_length']} 字符")
    print("-" * 60)
    print(comp["prompt"])
    print("-" * 60)


def _generate_components(comp_ids: List[str], library: Dict[str, Dict], force: bool, parallel: bool = True):
    """并行调用 GPT-Image2 API，一个组件一个请求，同时发起"""
    checkpoint = load_checkpoint()
    pending = []

    for cid in comp_ids:
        if cid not in library:
            print(f"  ⚠️ {cid}: prompts/ 中未找到，跳过")
            continue
        if cid in checkpoint and not force:
            prev = checkpoint[cid]
            print(f"  ⏭️  {library[cid]['title']} ({cid}) → 已生成 {Path(prev['image_path']).name}")
        else:
            pending.append(library[cid])

    if not pending:
        print("\n✅ 全部已生成！加 --force 强制重新生成")
        return

    print(f"\n🚀 {len(pending)} 张图并行生成中...\n")

    if len(pending) == 1 or not parallel:
        # 单图：顺序
        comp = pending[0]
        img_path = generate_image(comp["prompt"], comp["id"])
        if img_path:
            save_checkpoint(comp["id"], img_path)
            size_kb = Path(img_path).stat().st_size / 1024
            print(f"  ✅ {comp['title']} ({comp['id']}) → {Path(img_path).name} ({size_kb:.0f}KB)")
        else:
            print(f"  ❌ {comp['title']} ({comp['id']}) 失败")
    else:
        # 并行：ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(pending)) as ex:
            futures = {
                ex.submit(generate_image, comp["prompt"], comp["id"]): comp
                for comp in pending
            }
            success = 0
            for f in as_completed(futures):
                comp = futures[f]
                try:
                    img_path = f.result()
                except Exception as e:
                    print(f"  ❌ {comp['title']} ({comp['id']}) 异常: {e}")
                    continue
                if img_path:
                    save_checkpoint(comp["id"], img_path)
                    size_kb = Path(img_path).stat().st_size / 1024
                    print(f"  ✅ {comp['title']} ({comp['id']}) → {Path(img_path).name} ({size_kb:.0f}KB)")
                    success += 1
                else:
                    print(f"  ❌ {comp['title']} ({comp['id']}) 失败")

    print(f"\n{'='*60}")
    path_count = len([p for p in OUTPUT_DIR.glob("*.png")])
    print(f"📊 output/ 共 {path_count} 张图")


def cmd_page(page_num: str, guides: List[Dict], force: bool):
    """为指定页面生成所有组件图"""
    guide = next((g for g in guides if g["page"] == page_num), None)
    if not guide:
        page_ids = [g["page"] for g in guides]
        print(f"❌ 未找到第({page_num})页，可用: {', '.join(page_ids)}")
        sys.exit(1)

    lib = parse_prompts_dir(guide["prompts_dir"])

    print(f"\n🎯 第({guide['page']})页: {guide['title']}")
    print(f"   来源: {Path(guide['folder']).name}/{guide['file']}")
    print(f"   需要 {len(guide['components'])} 个组件: {', '.join(guide['components'])}")

    _generate_components(guide["components"], lib, force)


def cmd_all(guides: List[Dict], force: bool):
    """扫描所有页面，为所有组件生图"""
    print("\n🔍 扫描 PPT 制作指南...")
    all_components = []  # [(cid, lib), ...]

    for g in guides:
        lib = parse_prompts_dir(g["prompts_dir"])
        comps = [(cid, lib.get(cid)) for cid in g["components"] if lib.get(cid)]
        unknown = [cid for cid in g["components"] if not lib.get(cid)]
        print(f"   第({g['page']})页 → {len(comps)}个组件: {', '.join(g['components'])}")
        if unknown:
            print(f"     ⚠️ prompts/ 中未找到: {', '.join(unknown)}")
        all_components.extend(comps)

    # 去重保序（按 component id）
    seen = set()
    unique = []
    all_lib = {}
    for cid, comp in all_components:
        if cid not in seen:
            seen.add(cid)
            unique.append(cid)
            all_lib[cid] = comp

    print(f"\n📊 汇总: {len(guides)} 页面, {len(unique)} 个独立组件")

    _generate_components(unique, all_lib, force)


# ======================== 主入口 ========================

def main():
    parser = argparse.ArgumentParser(
        description="生图工作台 — 扫描 PPT 制作指南 → 提取提示词 → GPT-Image2 生图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate.py                      扫描所有指南，展示页面→组件清单
  python generate.py --page 02            为第（2）页生图
  python generate.py --page 02 --dry-run  预览第（2）页所有提示词
  python generate.py --component component-a  单独生成指定组件
  python generate.py --component component-a --dry-run  预览指定组件
  python generate.py --all                扫描所有页面，批量生图
  python generate.py --all --force        强制重新生成全部
        """,
    )
    parser.add_argument("--page", type=str, help="为指定页面生图（如 02）")
    parser.add_argument("--component", type=str, help="按组件ID生成（如 component-a）")
    parser.add_argument("--all", action="store_true", help="扫描所有页面，批量生图")
    parser.add_argument("--dry-run", action="store_true", help="仅预览提示词，不调API（配合 --page 或 --component）")
    parser.add_argument("--force", action="store_true", help="强制重新生成（跳过断点）")
    args = parser.parse_args()

    # 扫描所有页面的制作指南
    guides = scan_guides(str(GUIDES_DIR))
    if not guides:
        print("❌ 未找到任何 PPT 制作指南")
        sys.exit(1)

    # 路由
    if args.page and args.dry_run:
        cmd_dry_run_page(args.page, guides)
    elif args.page:
        cmd_page(args.page, guides, args.force)
    elif args.component and args.dry_run:
        cmd_dry_run_component(args.component, guides)
    elif args.component:
        # 从所有页面的 prompts 中查找
        for g in guides:
            lib = parse_prompts_dir(g["prompts_dir"])
            if args.component in lib:
                _generate_components([args.component], lib, args.force)
                sys.exit(0)
        print(f"❌ 未知组件: {args.component}")
        sys.exit(1)
    elif args.all:
        cmd_all(guides, args.force)
    else:
        cmd_list(guides)


if __name__ == "__main__":
    main()
