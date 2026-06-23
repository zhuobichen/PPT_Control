"""Page 04: build pptx"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pathlib import Path

DIR = Path(__file__).parent
W, H = Inches(10), Inches(5.625)
R = 1.75
prs = Presentation(); prs.slide_width, prs.slide_height = W, H
s = prs.slides.add_slide(prs.slide_layouts[6])

# images
for i, (img, x) in enumerate([("component-a.png", 0.3), ("component-b.png", 5.3)]):
    ph_w, ph_h = Inches(4.4), Inches(2.5)
    iw = ph_w; ih = iw / R
    if ih > ph_h: ih = ph_h; iw = ih * R
    s.shapes.add_picture(str(DIR / img), Inches(x), Inches(0.3), iw, ih)

def add_text(x, y, w, h, txt):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    tb.text_frame.paragraphs[0].text = txt

add_text(0.3, 3.0, 4.4, 2.2,
    "【反算求解】从环境目标出发反向求解最优减排方案。以PM2.5和O3达标浓度为约束、ICET边际成本为经济约束，遗传算法自动搜索各区域、行业、污染物的最优减排组合。经50代迭代后输出Top-10方案，再通过费效比筛选最优路径。")
add_text(5.3, 3.0, 4.4, 2.2,
    "【方案比选】每条方案含达标率、治理成本、协同指数三个维度，支持多方案横向对比。最优方案以最低成本实现全面达标且减污降碳协同性最强；次优方案提供不同侧重供决策权衡。")

prs.save(str(DIR / "04_减排路径优化.pptx"))
print("Done")
