"""Page 04: 减排路径优化（反算）"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pathlib import Path

DIR = Path(__file__).parent
W, H = Inches(10), Inches(5.625); R = 1.75
NAVY = RGBColor(0x1C,0x28,0x33); ACCENT = RGBColor(0x2E,0x86,0xAB)
WHITE = RGBColor(0xFF,0xFF,0xFF); BG = RGBColor(0xF4,0xF6,0xF6)
DARK = RGBColor(0x2C,0x3E,0x50); MUTED = RGBColor(0x7F,0x8C,0x8D)

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
s = prs.slides.add_slide(prs.slide_layouts[6])

# background
bg = s.shapes.add_shape(1,0,0,W,H); bg.fill.solid(); bg.fill.fore_color.rgb = BG; bg.line.fill.background()

# title bar
s.shapes.add_shape(1,0,0,W,Inches(0.62)).fill.solid(); s.shapes[-1].fill.fore_color.rgb = NAVY; s.shapes[-1].line.fill.background()
t1 = s.shapes.add_textbox(Inches(0.42),Inches(0.12),Inches(6.8),Inches(0.32))
t1.text_frame.paragraphs[0].text = "减排路径优化（反算）——目标倒推最优方案"
t1.text_frame.paragraphs[0].font.size = Pt(19); t1.text_frame.paragraphs[0].font.color.rgb = WHITE; t1.text_frame.paragraphs[0].font.bold = True

# tag pill
tag = s.shapes.add_shape(1,Inches(7.55),Inches(0.16),Inches(1.95),Inches(0.32))
tag.fill.solid(); tag.fill.fore_color.rgb = ACCENT; tag.line.fill.background()
tag.text_frame.paragraphs[0].text = "ABaCAS-OE · GA"
tag.text_frame.paragraphs[0].font.size = Pt(9); tag.text_frame.paragraphs[0].font.color.rgb = WHITE; tag.text_frame.paragraphs[0].font.bold = True
tag.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# metrics row
m = s.shapes.add_shape(1,Inches(0.52),Inches(0.88),Inches(8.96),Inches(0.44))
m.fill.solid(); m.fill.fore_color.rgb = WHITE; m.line.fill.background()
mp = m.text_frame.paragraphs[0]; mp.alignment = PP_ALIGN.CENTER
mp.text = "种群 20 · 迭代 50 代  ｜  两层适应度（达标 → 成本）  ｜  Top-10 方案"
mp.font.size = Pt(10); mp.font.color.rgb = DARK

# section title
st = s.shapes.add_textbox(Inches(3.28),Inches(1.5),Inches(3.44),Inches(0.32))
st.text_frame.paragraphs[0].text = "反算求解流程"
st.text_frame.paragraphs[0].font.size = Pt(15); st.text_frame.paragraphs[0].font.color.rgb = ACCENT; st.text_frame.paragraphs[0].font.bold = True
st.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# image
ph_w, ph_h = Inches(8.0), Inches(2.4)
iw = ph_w; ih = iw / R
if ih > ph_h: ih = ph_h; iw = ih * R
s.shapes.add_picture(str(DIR / "component-a.png"), Inches(1.0), Inches(1.9), iw, ih)

# description box
desc = s.shapes.add_shape(1,Inches(0.6),Inches(4.55),Inches(8.8),Inches(0.7))
desc.fill.solid(); desc.fill.fore_color.rgb = WHITE; desc.line.fill.background()
dt = desc.text_frame; dt.word_wrap = True
dt.paragraphs[0].text = "GA 两层适应度：未达标 → fitness=1+超标量÷达标率²（fitness>1 天然排后）；全部城市达标 → fitness=治理成本。达标方案按成本升序排列，成本最低即最优路径。"
dt.paragraphs[0].font.size = Pt(9); dt.paragraphs[0].font.color.rgb = DARK
dt.paragraphs[0].line_spacing = Pt(14)

# footnote
fn = s.shapes.add_textbox(Inches(0.6),Inches(5.25),Inches(8.8),Inches(0.18))
fn.text_frame.paragraphs[0].text = "后端引擎：ABaCAS-OE（GeneticAlgorithm.py / GeneticAlgorithm.cs）"
fn.text_frame.paragraphs[0].font.size = Pt(7.5); fn.text_frame.paragraphs[0].font.color.rgb = MUTED
fn.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

s.notes_slide.notes_text_frame.text = "反算逻辑：从PM2.5/O3环境目标出发，GA进行20种群50代迭代。两层适应度——达标优先，未达标fitness>1自动后排；达标方案内部按成本排序，成本最低即最优。"

prs.save(str(DIR / "04_减排路径优化.pptx"))
print("Done")
