"""Page 05: issues — client-friendly"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pathlib import Path

DIR = Path(__file__).parent
W, H = Inches(10), Inches(5.625)
NAVY = RGBColor(0x1C,0x28,0x33); ACCENT = RGBColor(0x2E,0x86,0xAB)
WHITE = RGBColor(0xFF,0xFF,0xFF); BG = RGBColor(0xF4,0xF6,0xF6)
DARK = RGBColor(0x2C,0x3E,0x50); RED = RGBColor(0xC0,0x39,0x2B)
AMBER = RGBColor(0xE6,0x7E,0x22); GREEN = RGBColor(0x4C,0xAF,0x50)

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
s = prs.slides.add_slide(prs.slide_layouts[6])

bg = s.shapes.add_shape(1,0,0,W,H); bg.fill.solid(); bg.fill.fore_color.rgb = BG; bg.line.fill.background()

# title bar
s.shapes.add_shape(1,0,0,W,Inches(0.62)).fill.solid(); s.shapes[-1].fill.fore_color.rgb = NAVY; s.shapes[-1].line.fill.background()
t1 = s.shapes.add_textbox(Inches(0.42),Inches(0.12),Inches(9.2),Inches(0.32))
t1.text_frame.paragraphs[0].text = "存在的问题与后续改进方向"
t1.text_frame.paragraphs[0].font.size = Pt(20); t1.text_frame.paragraphs[0].font.color.rgb = WHITE; t1.text_frame.paragraphs[0].font.bold = True

# summary bar
sm = s.shapes.add_shape(1,Inches(0.42),Inches(0.82),Inches(9.16),Inches(0.44))
sm.fill.solid(); sm.fill.fore_color.rgb = RGBColor(0xE8,0xF1,0xF5); sm.line.fill.background()
smp = sm.text_frame.paragraphs[0]; smp.font.size = Pt(9.5); smp.font.color.rgb = DARK
smp.text = "平台已完成措施量化、费效评估、路径优化三项核心能力，部署推广阶段仍有以下短板需补齐："

# four cards in 2x2 grid
cards = [
    (0.42, 1.45, 4.34, RED,   "子平台尚未交付",
     ["京津冀、长三角前端页面未上线",
      "部分早期模块仅覆盖少数行业",
      "需尽快完成前端部署与模块升级"]),
    (5.24, 1.45, 4.34, AMBER, "运维保障待加强",
     ["缺少统一监控和自动告警机制",
      "系统运行状态不可见",
      "大计算量任务缺乏队列调度"]),
    (0.42, 3.08, 4.34, AMBER, "模块间对接效率待提升",
     ["服务间数据格式尚未完全统一",
      "存在较多格式转换环节",
      "API 路由新旧两套尚在切换"]),
    (5.24, 3.08, 4.34, GREEN, "历史版本待整合",
     ["部分模块存在新旧两套实现",
      "功能尚未完全对齐",
      "须统一以降低维护成本"]),
]

for x, y, width, color, title, items in cards:
    # card
    card = s.shapes.add_shape(1,Inches(x),Inches(y),Inches(width),Inches(1.42))
    card.fill.solid(); card.fill.fore_color.rgb = WHITE; card.line.fill.background()
    # left accent bar
    bar = s.shapes.add_shape(1,Inches(x),Inches(y),Inches(0.06),Inches(1.42))
    bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.fill.background()
    # title
    tb = s.shapes.add_textbox(Inches(x+0.18),Inches(y+0.12),Inches(width-0.3),Inches(0.24))
    tb.text_frame.paragraphs[0].text = title
    tb.text_frame.paragraphs[0].font.size = Pt(11); tb.text_frame.paragraphs[0].font.color.rgb = NAVY
    tb.text_frame.paragraphs[0].font.bold = True
    # items
    for i, item in enumerate(items):
        tb2 = s.shapes.add_textbox(Inches(x+0.18),Inches(y+0.45+i*0.3),Inches(width-0.3),Inches(0.26))
        tb2.text_frame.paragraphs[0].text = item
        tb2.text_frame.paragraphs[0].font.size = Pt(9); tb2.text_frame.paragraphs[0].font.color.rgb = DARK

# footer
fn = s.shapes.add_textbox(Inches(0.42),Inches(4.78),Inches(9.16),Inches(0.2))
fn.text_frame.paragraphs[0].text = "上述问题不影响已上线功能使用，后续迭代中将逐步补齐，为大规模推广和长期运维奠定基础"
fn.text_frame.paragraphs[0].font.size = Pt(7.5); fn.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x7F,0x8C,0x8D)
fn.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

s.notes_slide.notes_text_frame.text = "本页说明当前平台存在的问题。已交付三大核心能力，但子平台前端未上线、缺少运维监控、模块对接效率待提升、历史版本需整合。这些问题不影响已上线功能，后续迭代逐步补齐。"

prs.save(str(DIR / "05_存在的问题.pptx"))
print("Done")
