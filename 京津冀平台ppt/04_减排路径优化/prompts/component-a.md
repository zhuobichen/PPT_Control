---
id: component-a
title: 减排路径优化——反算求解流程
---
A clean horizontal 3-stage pipeline diagram showing the inverse optimization workflow. Canvas: 1792x1024 pixels (16:9).

Three rounded-rectangle stage cards arranged left to right in one horizontal row, evenly spaced, connected by thick right-pointing arrows (→). Each card is ~30% canvas width, centered vertically.

Stage 1 (left, blue #3B7DD8, white text):
- Top: target/bullseye icon
- Title: "目标设定"
- Subtitle: "PM2.5/O3 浓度目标"
- Bottom small text: "基准年差距分析"

Stage 2 (center, orange #E8913A, white text):
- Top: DNA helix icon
- Title: "GA 迭代寻优"
- Subtitle: "种群20·迭代50代"
- Middle detail box (lightened bg #F5A623):
  "全部达标 → fitness=成本(越低越好)"
  "未达标 → fitness=1+超标量/达标率²"
  in small white text
- Bottom: "达标优先 + 达标后选成本最低" in tiny white

Stage 3 (right, green #4CAF50, white text):
- Top: podium/trophy icon
- Title: "Top 方案输出"
- Subtitle: "按成本升序排列"
- Bottom small text: "成本最低 = 最优路径"

Arrows between cards: thick light-gray #BDC3C7, simple triangle arrowhead.

Below all three cards, a full-width annotation line in dark text: "未达标方案 fitness>1，天然排在所有达标方案之后 → 先保证空气质量合格，再挑成本最低的"

Style: Clean flat vector. Solid color fills. White background #FFFFFF. No 3D, no gradients, no shadows. Chinese text. Rounded corners ~8px.

Quality: Professional infographic, crisp edges, perfect alignment.
