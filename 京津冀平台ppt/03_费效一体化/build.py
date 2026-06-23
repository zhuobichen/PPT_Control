"""第(3)页 费效一体化+协同评估 — 上图上文字，具体布局自调"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pathlib import Path

DIR = Path(__file__).parent
W, H = Inches(10), Inches(5.625)
R = 1.75

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
s = prs.slides.add_slide(prs.slide_layouts[6])

# ── 左图 ──
ph_w, ph_h = Inches(4.4), Inches(2.5)
iw = ph_w; ih = iw / R
if ih > ph_h: ih = ph_h; iw = ih * R
s.shapes.add_picture(str(DIR / "component-a.png"), Inches(0.3), Inches(0.3), iw, ih)

# ── 右图 ──
ph_w2, ph_h2 = Inches(4.4), Inches(2.5)
iw2 = ph_w2; ih2 = iw2 / R
if ih2 > ph_h2: ih2 = ph_h2; iw2 = ih2 * R
s.shapes.add_picture(str(DIR / "component-b.png"), Inches(5.3), Inches(0.3), iw2, ih2)

# ── 文字 ──
def add_text(x, y, w, h, txt):
    tb = s.shapes.add_textbox(x, y, w, h)
    tb.text_frame.word_wrap = True
    tb.text_frame.paragraphs[0].text = txt

add_text(Inches(0.3), Inches(3.0), Inches(4.4), Inches(2.2),
    "【全流程管线】措施量化结果串联六大模块：成本评估（ICET边际成本曲线）、RSM浓度响应（响应面模拟）、SMAT数据融合（模型-监测空间插值校正）、健康效益（BenMAP货币化）、协同分析（AQB+CRB→SI）。")
add_text(Inches(5.3), Inches(3.0), Inches(4.4), Inches(2.2),
    "【协同评估】从大气健康收益（AQB）与碳社会成本（CRB）两维综合——AQB 衡量污染物减排的健康收益，CRB 衡量 CO2 的碳社会成本；归一化后计算协同指数 SI（0~1），SI 越高 = 减污降碳协同性越强。")

prs.save(str(DIR / "03_费效一体化.pptx"))
print("Done")
