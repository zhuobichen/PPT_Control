"""第(2)页 完善措施量化评估"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pathlib import Path

DIR = Path(__file__).parent
W, H = Inches(10), Inches(5.625); R = 1.75
prs = Presentation(); prs.slide_width, prs.slide_height = W, H
s = prs.slides.add_slide(prs.slide_layouts[6])

for img, x in [("component-a.png", 0.3), ("component-b.png", 5.3)]:
    ph_w, ph_h = Inches(4.4), Inches(2.5)
    iw = ph_w; ih = iw / R
    if ih > ph_h: ih = ph_h; iw = ih * R
    s.shapes.add_picture(str(DIR / img), Inches(x), Inches(0.3), iw, ih)

def T(x, y, w, h, txt):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    tb.text_frame.paragraphs[0].text = txt

T(0.3, 3.0, 4.4, 2.2,
    "【演进路径】平台最初仅覆盖电力、工业水泥、交通 3 个行业。经四次迭代——先新增 7 个工业部门扩至 10 个，再补齐农业、溶剂、开放燃烧、民用（14 个），最后接入油气储运——目前覆盖 15 个部门、73 个子行业。")
T(5.3, 3.0, 4.4, 2.2,
    "【计算流程】各行业按统一的三步框架计算减排：1) 技改技术（末端治理与能效提升）；2) 活动水平（产业规模变化调整排放基线）；3) 工艺革新（按行业选用适配公式）。交通和新增部门走子部门级逐项计算，精度更高。")

prs.save(str(DIR / "02_完善措施量化评估.pptx"))
print("Done")
