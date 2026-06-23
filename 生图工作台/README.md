# 生图工作台

PPT 制作指南通过 `@prompt:component-x` 引用组件 → 工作台扫描指南 → 从页面的 `prompts/component-x.md` 读取提示词 → GPT-Image2 生图。

```
京津冀平台ppt/
├── 02_完善措施量化评估/          ← 每页一个独立文件夹
│   ├── 02_完善措施量化评估_PPT制作指南.md   ← @prompt:component-a
│   ├── 02_讲稿_完善措施量化评估.md
│   ├── 02_完善措施量化评估.pptx
│   ├── build_final.cjs           ← 重建脚本
│   ├── component-*.png           ← 图片（生图输出 + 构建用）
│   └── prompts/                  ← 提示词（页面私有）
│       ├── component-a.md
│       ├── component-b.md
│       ├── component-c.md
│       └── component-d.md
│
生图工作台/
├── generate.py
├── output/                       ← 生成的图片缓存
│   └── .checkpoint.json
└── README.md
```

## 日常用法

```bash
# 查看所有页面需要哪些图
python generate.py

# 预览某页的所有提示词（不消耗 API）
python generate.py --page 02 --dry-run

# 为某页生图
python generate.py --page 02

# 扫描所有页面，全部生成
python generate.py --all
```

## 添加新页面

1. 在 `京津冀平台ppt/` 下新建 `XX_页面名/` 文件夹
2. 放入 `XX_页面名_PPT制作指南.md`（含 `@prompt:component-x` 引用）
3. 创建 `prompts/` 子目录，放入 `component-x.md`（frontmatter + 英文提示词）
4. 运行 `python generate.py --page XX` 或 `--all`
