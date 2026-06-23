---
id: component-a
title: 最优减排路径求解流程
---
A high-quality diagram showing the genetic algorithm optimization workflow for emission reduction pathway search. Canvas: 1792x1024 pixels (16:9).

Layout: Three panels in a loop/cycle arrangement. Left panel (inputs), center panel (optimization engine), right panel (outputs), with a feedback arrow from right back to center showing iterative GA evolution.

Left panel — "优化目标与约束" (dark gray #2C3E50, white text):
- Top: target icon, label "减排目标" with subtext "PM2.5 / O3 达标浓度"
- Middle: yuan coin icon, label "经济约束" with subtext "ICET 边际成本曲线"
- Bottom: grid icon, label "控制因子" with subtext "多区域·多行业·多污染物"

Center panel — "遗传算法寻优" (blue #3B7DD8, white text, largest panel):
- Top: DNA helix / evolution icon
- Title: "遗传算法迭代求解"
- Four sub-items arranged as a cycle:
  - "种群初始化" (拉丁超立方采样)
  - "适应度评估" (RSM浓度响应 + 减排成本)
  - "交叉变异" (选择最优个体)
  - "精英保留" (Top方案进入下一代)
- Each iteration labeled with GA parameters in small text: "种群20 · 迭代50代 · 交叉0.8 · 变异0.05"

Right panel — "最优路径输出" (green #4CAF50, white text):
- Top: trophy icon, label "Top-X 最优方案"
- Sub-items in a ranked list:
  - "#1 最优方案" with fitness score + cost + attainment
  - "#2 次优方案"
  - "…更多备选路径"
- Bottom annotation: "每条路径 = 各区域/行业/污染物的最优减排比例组合"

Connecting arrows: thick directional arrows between panels. Feedback arrow from right to center labeled "下一代迭代".

Style: Clean flat vector, white background #FFFFFF. No 3D. No photo. No gradients. All Chinese labels. Professional government infographic.
