# -*- coding: utf-8 -*-
"""生成《天线仿真开源软件集成与应用 毕业设计规划书》DOCX。"""

import os
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(r"C:\Users\ww\Documents\Codex\2026-10-09\ai\outputs")
OUT.mkdir(parents=True, exist_ok=True)
DOCX = OUT / "天线仿真开源软件集成与应用-毕业设计规划书.docx"

BODY_FONT = "Noto Serif SC"
HEAD_FONT = "Noto Sans SC"
BLACK = RGBColor(0x00, 0x00, 0x00)
HEADER_FILL = "44546A"      # 深灰蓝
ROW_FILL = "F2F2F2"         # 浅灰
BORDER = "D9D9D9"


# ----------------------------------------------------------------- 基础工具
def set_run(run, *, font=BODY_FONT, size=11, bold=False, color=BLACK):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font)


def para(doc, text="", *, style=None, size=11, font=BODY_FONT, bold=False,
         align=None, space_before=0, space_after=5, line=1.4, indent_first=None,
         keep_with_next=False):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    pf.keep_with_next = keep_with_next
    if indent_first is not None:
        pf.first_line_indent = Pt(indent_first)
    if text:
        set_run(p.add_run(text), font=font, size=size, bold=bold)
    return p


def heading(doc, text, level=1):
    sizes = {1: 15, 2: 12.5}
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(13 if level == 1 else 10)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.2
    pf.keep_with_next = True          # 标题不能孤在页底
    set_run(p.add_run(text), font=HEAD_FONT, size=sizes[level], bold=True)
    return p


def _shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), BORDER)
        borders.append(el)
    tbl_pr.append(borders)


def _cell_pad(table, top=58, bottom=58, left=108, right=108):
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.append(mar)


def add_table(doc, rows, widths, *, header=True, size=10, first_col_bold=False):
    n_cols = len(widths)
    table = doc.add_table(rows=0, cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _borders(table)
    _cell_pad(table)

    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        # 行内容不跨页断开
        tr_pr = table.rows[-1]._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr_pr.append(cant)
        if header and r_i == 0:
            # 表格跨页时重复表头
            th = OxmlElement("w:tblHeader")
            th.set(qn("w:val"), "true")
            tr_pr.append(th)
        for c_i, text in enumerate(row):
            cell = cells[c_i]
            cell.width = Cm(widths[c_i])
            cell.vertical_alignment = 1  # center
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            is_head = header and r_i == 0
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_head else (
                WD_ALIGN_PARAGRAPH.CENTER if len(text) <= 12 and c_i == 0
                else WD_ALIGN_PARAGRAPH.LEFT)
            set_run(
                p.add_run(text),
                font=HEAD_FONT if is_head else BODY_FONT,
                size=size,
                bold=is_head or (first_col_bold and c_i == 0),
                color=RGBColor(0xFF, 0xFF, 0xFF) if is_head else BLACK,
            )
            if is_head:
                _shade(cell, HEADER_FILL)
            elif r_i % 2 == 0:
                _shade(cell, ROW_FILL)

    # 固定列宽
    for row in table.rows:
        for c_i, cell in enumerate(row.cells):
            cell.width = Cm(widths[c_i])
    return table


# ----------------------------------------------------------------- 文档
doc = Document()

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)
sec.left_margin = Cm(2.8)
sec.right_margin = Cm(2.8)

style = doc.styles["Normal"]
style.font.name = BODY_FONT
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)

# ---------------- 标题 ----------------
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.paragraph_format.space_before = Pt(18)
t.paragraph_format.space_after = Pt(4)
set_run(t.add_run("天线仿真开源软件集成与应用"), font=HEAD_FONT, size=20, bold=True)

st = doc.add_paragraph()
st.alignment = WD_ALIGN_PARAGRAPH.CENTER
st.paragraph_format.space_after = Pt(20)
set_run(st.add_run("毕业设计规划书"), font=HEAD_FONT, size=13, bold=False)

para(doc,
     "本规划说明“天线仿真开源软件集成与应用”课题的目标、技术路线、已完成的前期工作、"
     "进度安排与预期成果，供指导教师审阅。课题要求打通一条全开源的电磁—结构双域仿真链路，"
     "并以 20λ 卡塞格伦天线作为统一算例完成建模与验证。",
     size=11, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=10)

# ---------------- 1 课题概况 ----------------
heading(doc, "一、课题概况")
add_table(doc, [
    ["项目", "内容"],
    ["课题名称", "天线仿真开源软件集成与应用"],
    ["课题类型", "工程设计类"],
    ["完成方式", "在实验、实习、工程实践和社会调查等社会实践中完成"],
    ["统一算例", "20λ 卡塞格伦天线（D = 20λ，F/D = 0.4）"],
    ["能力要求", "一定的编程能力；已修微波与天线技术课程"],
], [3.0, 12.4], size=10)

# ---------------- 2 背景与意义 ----------------
heading(doc, "二、选题背景与意义")
para(doc,
     "大型反射面天线的电尺寸很大。若直接用全波方法求解，网格尺寸受波长限制，"
     "三维网格量大致按口径的三次方增长，内存与计算时间都难以承受。"
     "而工程上真正关心的指标是方向图、增益、副瓣电平与口径效率，"
     "这些并不需要完整的近场细节。",
     indent_first=22)
para(doc,
     "本课题因此把问题拆成两个尺度：尺寸小、结构复杂的馈源用全波方法精确求解；"
     "电大尺寸的反射面改用几何光学与物理光学的高频近似，不做体网格。"
     "在此基础上，再把反射面面板的结构变形量化为口径上的相位误差并回代电磁链路，"
     "形成电磁与结构两个域之间的闭环。",
     indent_first=22)
para(doc,
     "全部环节只使用开源软件，成果可复现、可迁移，不依赖商业授权；"
     "链路本身也可以用于教学与后续研究。",
     indent_first=22)

# ---------------- 3 研究内容与目标 ----------------
heading(doc, "三、研究内容与目标")
para(doc, "课题工作分为三个部分。", space_after=8)

for label, text in [
    ("射频域",
     "用 openEMS 对角锥喇叭馈源做 FDTD 全波仿真，导出馈源方向图；"
     "再用自研的几何光学/物理光学积分完成主、副反射面的射线追踪与远场计算。"),
    ("结构域",
     "用 FEniCSx 完成反射面面板在自重、风载等载荷下的线弹性变形求解，"
     "输出位移场。"),
    ("双域耦合",
     "把面板变形转换为主面口径上的相位扰动，回代到电磁链路，"
     "量化增益损失与副瓣电平的变化。"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Pt(12)
    set_run(p.add_run(f"{label}　"), font=HEAD_FONT, size=11, bold=True)
    set_run(p.add_run(text), size=11)

para(doc,
     "目标是在 20λ 卡塞格伦算例上完成端到端验证，并把关键环节与解析结果或"
     "理论公式比对：口径积分用均匀圆口径的 Airy 图案校核，"
     "结构相位误差引起的增益损失用 Ruze 公式校核。",
     indent_first=22, space_before=6)

# ---------------- 4 技术路线 ----------------
heading(doc, "四、技术路线")
para(doc, "整条链路的信号流如下。", space_after=8, keep_with_next=True)

add_table(doc, [
    ["环节", "工具", "输入", "输出"],
    ["馈源全波仿真", "openEMS（FDTD）", "喇叭几何、激励", "馈源方向图 g(θ)"],
    ["射线追踪", "自研 GO", "g(θ)、反射面几何", "口径场幅度与相位"],
    ["远场计算", "自研 PO 积分", "口径场分布", "远场方向图 E(θ, φ)"],
    ["结构变形", "FEniCSx（线弹性有限元）", "面板几何、载荷", "位移场 w(x, y)"],
    ["双域耦合", "自研脚本", "w(x, y)", "口径相位扰动 Δφ = 2kw"],
], [3.3, 4.0, 4.0, 4.1], size=9.5)

para(doc,
     "其中射线路径为：馈源位于双曲面的远焦点，射线先打到副面，反射后打到主面，"
     "再平行于视轴射出。副面是旋转双曲面，其近焦点与抛物面主面的焦点重合，"
     "这是卡塞格伦能把馈源球面波准直为平面波的原因。",
     indent_first=22, space_before=10)

# ---------------- 5 前期工作 ----------------
heading(doc, "五、前期工作进展")
para(doc,
     "截至本规划提交时，环境搭建与射频侧的主要链路已经完成并逐项验证，"
     "结果如下。",
     space_after=8, keep_with_next=True)

add_table(doc, [
    ["环节", "已完成内容", "验证结果"],
    ["仿真环境",
     "Windows 与 WSL 双层环境；openEMS v0.37.0、FEniCSx dolfinx 0.11.0 全部就绪",
     "环境自检 20 项通过"],
    ["口径积分器",
     "口径场法 PO 积分、面元 PO 积分，以及用于校核的解析对照",
     "均匀圆口径数值解与解析 Airy 图案偏差 5.8×10⁻⁶"],
    ["卡塞格伦几何",
     "共焦设计方程、副面口径与遮挡比计算，并带几何自检",
     "近焦点精确落在主面焦点；副面遮挡比 4.913%"],
    ["双反射面链路",
     "馈源→副面→主面的全链路射线追踪",
     "出射准直误差 4.4×10⁻¹⁶，等光程起伏 7.1×10⁻¹⁵"],
    ["远场与遮挡",
     "含副面遮挡的 PO 远场积分，以及遮挡比对增益的影响扫描",
     "遮挡增益损失 −0.525 dB；第一副瓣由 −19.60 dB 抬高到 −16.25 dB"],
    ["结构—电磁判据",
     "把相位误差映射为增益损失的 Ruze 关系，作为耦合正确性的判据",
     "24 次随机实现后与理论值偏差 0.000 dB"],
    ["全波工具链",
     "openEMS 官方角锥喇叭教程端到端跑通，确认馈源建模路径可用",
     "15 GHz 喇叭最大方向性 16.9 dBi，口径效率 64.6%"],
], [2.6, 7.2, 5.6], size=9)

para(doc,
     "上述结果说明射频侧链路与验证判据已经成立，"
     "余下的工作集中在馈源接入、结构域求解与双域耦合三处。",
     indent_first=22, space_before=10)

# ---------------- 6 难点与对策 ----------------
heading(doc, "六、关键技术难点与对策")
add_table(doc, [
    ["难点", "说明", "对策"],
    ["共形面积分精度",
     "反射面是曲面，积分精度直接决定方向图副瓣是否可信",
     "参数化曲面配合高斯积分；用解析 Airy 图案作为积分器的硬性校核"],
    ["遮挡与绕射",
     "副面遮挡会抬高副瓣；边缘绕射影响远角副瓣",
     "先做射线遮挡判决；在结果分析中说明纯 PO 的适用范围，必要时补充绕射项"],
    ["口径幅度模型",
     "目前采用一阶模型，未跟踪射线管截面积",
     "跟踪射线管 Jacobian，得到严格的几何光学幅度分布"],
    ["计算规模",
     "全波仿真网格量大，单次运行时间较长",
     "先用粗网格试算确定参数，再逐步加密；利用结构对称性降低计算量"],
    ["双域数据接口",
     "结构位移与电磁相位量纲和采样方式不同",
     "统一以波长为单位归一化，固定数据格式，并在接口处做量级检查"],
], [2.8, 6.4, 6.2], size=9)

# ---------------- 7 进度计划 ----------------
heading(doc, "七、进度计划")
add_table(doc, [
    ["阶段", "时间", "主要工作", "阶段成果"],
    ["开题准备", "2026.10 - 2026.11", "文献调研、方案论证、环境与前期链路搭建", "开题报告、任务书"],
    ["馈源建模", "2026.11 - 2026.12", "openEMS 角锥喇叭建模与馈源方向图导出", "馈源模型与 g(θ) 数据"],
    ["结构域求解", "2026.12 - 2027.01", "FEniCSx 面板变形建模，并用基准算例对解析解", "位移场 w(x, y)"],
    ["双域耦合", "2027.01 - 2027.02", "变形转换为口径相位扰动并回代电磁链路", "耦合结果与 Ruze 判据复核"],
    ["综合算例", "2027.02 - 2027.03", "20λ 卡塞格伦完整链路运行与参数扫描", "完整数据集与图表"],
    ["论文撰写", "2027.03 - 2027.04", "中期检查、论文初稿", "中期报告、论文初稿"],
    ["修改定稿", "2027.04 - 2027.05", "查重、修改、定稿", "论文定稿"],
    ["答辩", "2027.05 - 2027.06", "答辩材料准备、预答辩与正式答辩", "答辩材料"],
], [2.4, 3.4, 5.6, 4.0], size=9)

para(doc,
     "上表按常规时间节点编排，实际执行需与学院公布的正式日程对齐。",
     indent_first=22, space_before=8)

# ---------------- 8 预期成果 ----------------
heading(doc, "八、预期成果")
for text in [
    "一条可运行的全开源电磁—结构双域仿真链路，包含馈源建模、射线追踪、"
    "物理光学远场计算、结构有限元求解与耦合脚本。",
    "20λ 卡塞格伦天线的完整仿真结果，包括方向图、增益、副面遮挡影响"
    "与结构变形引起的增益损失，并附与解析结果的比对。",
    "毕业设计论文一篇，以及答辩演示材料。",
]:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.35
    for r in p.runs:
        r.text = ""
    set_run(p.add_run(text), size=11)

doc.save(str(DOCX))
print(f"saved: {DOCX}")
