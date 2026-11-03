# -*- coding: utf-8 -*-
"""生成《天线仿真开源软件集成与应用 核心知识点梳理》DOCX。"""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(r"C:\Users\ww\Documents\Codex\2026-10-09\ai\outputs")
OUT.mkdir(parents=True, exist_ok=True)
DOCX = OUT / "天线仿真-核心知识点梳理.docx"

BODY_FONT = "Noto Serif SC"
HEAD_FONT = "Noto Sans SC"
BLACK = RGBColor(0x00, 0x00, 0x00)
HEADER_FILL = "44546A"
ROW_FILL = "F2F2F2"
BORDER = "D9D9D9"


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


def para(doc, text="", *, size=11, font=BODY_FONT, bold=False, align=None,
         space_before=0, space_after=5, line=1.4, indent_first=None,
         keep_with_next=False, left_indent=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    pf.keep_with_next = keep_with_next
    if indent_first is not None:
        pf.first_line_indent = Pt(indent_first)
    if left_indent is not None:
        pf.left_indent = Pt(left_indent)
    if text:
        set_run(p.add_run(text), font=font, size=size, bold=bold)
    return p


def heading(doc, text, level=1):
    sizes = {1: 15, 2: 12, 3: 11}
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(13 if level == 1 else (9 if level == 2 else 7))
    pf.space_after = Pt(4)
    pf.line_spacing = 1.2
    pf.keep_with_next = True
    set_run(p.add_run(text), font=HEAD_FONT,
            size=sizes[level], bold=(level <= 2))
    return p


def _shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _borders(table):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), BORDER)
        borders.append(el)
    table._tbl.tblPr.append(borders)


def _cell_pad(table):
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", 58), ("left", 108), ("bottom", 58), ("right", 108)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    table._tbl.tblPr.append(mar)


def add_table(doc, rows, widths, *, size=9.5):
    table = doc.add_table(rows=0, cols=len(widths))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _borders(table)
    _cell_pad(table)

    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        tr_pr = table.rows[-1]._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        if r_i == 0:
            th = OxmlElement("w:tblHeader")
            th.set(qn("w:val"), "true")
            tr_pr.append(th)
        for c_i, text in enumerate(row):
            cell = cells[c_i]
            cell.width = Cm(widths[c_i])
            cell.vertical_alignment = 1
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            is_head = r_i == 0
            p.alignment = (WD_ALIGN_PARAGRAPH.CENTER if is_head
                           else (WD_ALIGN_PARAGRAPH.CENTER if len(text) <= 8
                                 else WD_ALIGN_PARAGRAPH.LEFT))
            set_run(p.add_run(text), font=HEAD_FONT if is_head else BODY_FONT,
                    size=size, bold=is_head,
                    color=RGBColor(0xFF, 0xFF, 0xFF) if is_head else BLACK)
            if is_head:
                _shade(cell, HEADER_FILL)
            elif r_i % 2 == 0:
                _shade(cell, ROW_FILL)
    for row in table.rows:
        for c_i, cell in enumerate(row.cells):
            cell.width = Cm(widths[c_i])
    return table


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.35
    set_run(p.add_run(text), size=size)
    return p


def item(doc, label, text, size=10.5):
    """带粗体小标题的条目。"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.38
    p.paragraph_format.left_indent = Pt(10)
    set_run(p.add_run(f"{label}　"), font=HEAD_FONT, size=size, bold=True)
    set_run(p.add_run(text), size=size)
    return p


# ================================================================ 文档
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.4)
sec.left_margin = sec.right_margin = Cm(2.6)

style = doc.styles["Normal"]
style.font.name = BODY_FONT
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.paragraph_format.space_before = Pt(14)
t.paragraph_format.space_after = Pt(4)
set_run(t.add_run("天线仿真开源软件集成与应用"), font=HEAD_FONT, size=19, bold=True)

st = doc.add_paragraph()
st.alignment = WD_ALIGN_PARAGRAPH.CENTER
st.paragraph_format.space_after = Pt(14)
set_run(st.add_run("核心知识点梳理"), font=HEAD_FONT, size=13)

para(doc,
     "本文件按“知识点在项目中出现在哪一步”来组织，用于准备开题、中期与答辩。"
     "每个知识点都标注了掌握程度，并说明它在本课题里的具体位置，"
     "以便优先复习真正会被问到的内容。",
     space_after=8)

add_table(doc, [
    ["标记", "含义", "要求"],
    ["★★★", "必会", "答辩大概率会问，要能用自己的话讲清楚，不能只会背名词"],
    ["★★", "理解", "知道它在做什么、为什么需要，能说个大意"],
    ["★", "了解", "听过即可，被问到能答一句" ],
], [2.0, 2.0, 11.8], size=10)

# ------------------------------------------------ 一
heading(doc, "一、天线与微波基础")

heading(doc, "1.1　天线的基本参数　★★★", 3)
para(doc,
     "方向图描述辐射能量随角度的分布，需要分清主瓣、副瓣与零点；"
     "半功率波束宽度衡量主瓣宽窄。增益 G 与方向性系数 D 的关系为 G = η·D，"
      "η 是效率。口径效率表示实际口径利用了多少理论最大增益。",
     indent_first=21)
item(doc, "在本项目里：",
     "角锥喇叭仿真给出最大方向性 16.9 dBi、口径效率 64.6%；"
     "卡塞格伦远场方向图的第一副瓣由无遮挡时的 −19.60 dB 抬高到 −16.25 dB。"
     "答辩时被问“你这个结果合理吗”，就是拿这些量级去判断。")

heading(doc, "1.2　口径场与远场的关系　★★★", 3)
para(doc,
     "这是整个射频链路的理论核心。口径面上的场分布与远场方向图之间是傅里叶变换关系：",
     indent_first=21)
para(doc, "F(θ) ∝ ∫∫ Ea(x, y) · exp( j k x sinθ ) dx dy",
     align=WD_ALIGN_PARAGRAPH.CENTER, size=11, space_after=6, keep_with_next=True)
para(doc,
     "均匀照射的圆形口径有解析解，即艾里（Airy）图案 2J₁(u)/u，"
     "其中 u = k·a·sinθ。它的第一副瓣约为 −17.6 dB。"
     "本课题用这个解析解来校核自研积分器是否写对，实测偏差 5.8×10⁻⁶。",
     indent_first=21)
item(doc, "为什么重要：",
     "答辩一定会问“你怎么知道你算的是对的”，答案就是这条——"
     "在能解析求解的简单情形上验证过。")

heading(doc, "1.3　抛物面反射面天线　★★★", 3)
para(doc,
     "抛物面的表达式为 z = r²/(4F)，F 是焦距，D 是口径直径，F/D 称为焦径比。"
     "抛物面有一条关键性质：位于焦点的点源发出的球面波，反射后变成平行于轴的平面波"
     "（反之，平行入射的平面波会汇聚到焦点）。",
     indent_first=21)
para(doc,
     "本项目取 D = 20λ、F/D = 0.4，对应矢高 3.125λ、馈源半张角 64°。"
     "张角大说明这是一个深抛物面，这一点会在后面解释副瓣差异时用到。",
     indent_first=21)

heading(doc, "1.4　卡塞格伦双反射面天线　★★★", 3)
para(doc,
     "卡塞格伦在主面焦点前加一个双曲面副反射面。双曲面的近焦点与抛物面焦点重合，"
     "馈源则放在双曲面的远焦点上。射线路径是：馈源 → 副面 → 主面 → 平行射出。",
     indent_first=21)
para(doc,
     "设计上有几个量必须一致：副面顶点位置 L、双曲面实半轴 a、半焦距 c、"
     "离心率 e = c/a = (M+1)/(M−1)，其中 M 是放大率。"
     "本项目取 M = 4，得 a = 2.400λ、c = 4.000λ、近焦点精确落在 z = 8.000λ（即 F）。",
     indent_first=21)
item(doc, "一个容易踩的坑：",
     "副面位置 L 不能简单取 F/M，那样会得到 16.4λ 的副面、约 67% 遮挡，"
     "物理上不可用。L 是自由设计参数，控制遮挡比；本项目取 L = M·F/(M+1)，"
     "得到副面口径 4.433λ、遮挡比 4.913%。")
item(doc, "优点：",
     "馈源靠近主面顶点，缩短了馈线；副面遮挡比正馈抛物面小。")

heading(doc, "1.5　馈源与照射锥削　★★", 3)
para(doc,
     "馈源方向图常用 cos^q(θ) 近似。边缘照射电平指口径边缘相对中心的电平，"
     "锥削越强，副瓣越低、但波束变宽、口径效率下降，存在折中。"
     "本项目取 −10 dB 边缘锥削。",
     indent_first=21)

# ------------------------------------------------ 二
heading(doc, "二、电磁数值计算方法")

heading(doc, "2.1　麦克斯韦方程组　★★", 3)
para(doc,
     "电磁仿真的一切出发点。需要知道四个方程的物理含义（电场如何产生、"
     "磁场如何产生、以及两个散度条件），不必背微分形式。"
     "FDTD 和有限元都是在离散化这组方程。",
     indent_first=21)

heading(doc, "2.2　时域有限差分 FDTD　★★★", 3)
para(doc,
     "FDTD 在空间上把场量交错放在 Yee 网格上，时间上用蛙跳格式交替推进电场与磁场。"
     "它直接求解时域场，一次仿真通过傅里叶变换就能得到宽频带结果。",
     indent_first=21)
para(doc,
     "两个必须知道的配套概念：空间步长要足够小（一般小于 λ/10，本项目取 λ/30）；"
     "边界要用完全匹配层（PML）吸收，否则反射波会污染结果。"
     "时间步长受 CFL 稳定性条件限制，这一点了解即可。",
     indent_first=21)
item(doc, "在本项目里：",
     "openEMS 就是 FDTD 求解器，负责馈源的全波仿真。"
     "角锥喇叭那一例用了 241 万网格、15210 个时间步。")

heading(doc, "2.3　几何光学 GO　★★★", 3)
para(doc,
     "把电磁波当作射线处理，用反射定律确定路径，用射线管能量守恒确定幅度。"
     "它不考虑波动效应，所以算不出绕射和干涉，但在电大尺寸、"
     "曲率远大于波长的地方非常好用，而且计算量极小。",
     indent_first=21)
item(doc, "在本项目里：",
     "用射线追踪把馈源发射的射线依次打到副面和主面。"
     "两条自校验判据是准直误差（出射方向应平行于视轴，实测 4.4×10⁻¹⁶）"
     "和等光程（r₁ + r₂ − z 应为常数，实测起伏 7.1×10⁻¹⁵）。")

heading(doc, "2.4　物理光学 PO　★★★", 3)
para(doc,
     "PO 在反射面上求等效面电流，再对整个面做积分得到远场。"
     "面电流的表达式是 J = 2 n × H_inc，其中 n 是反射面的单位法向、"
     "H_inc 是入射磁场。"
     "相比 GO，PO 能给出更接近真实的副瓣结构，因为它考虑了面上各点的相位贡献。",
     indent_first=21)
para(doc,
     "远场积分的基本形式是把面电流乘上相位因子 exp(jk r·r′) 后沿面求和，"
     "其中 r 是观察方向的单位矢量、r′ 是面上源点的位置矢量。"
     "本项目实现了两种：口径场法（在口径平面上积分）与面元法（在曲面上积分）。",
     indent_first=21)

heading(doc, "2.5　口径场法与面元法的区别　★★★", 3)
para(doc,
     "口径场法把反射后的场等效投影到口径平面上再做积分；面元法直接在曲面上积分，"
     "保留了斜入射的投影因子。对于本项目这种深抛物面（半张角 64°），"
     "两者算出的零点位置一致，但副瓣电平有明显差异——口径场法省略了斜度因子。",
     indent_first=21)
item(doc, "这是本课题可以写进论文的一个点：",
     "不要把这个差异藏起来，而要量化它、解释它的来源。"
     "答辩时主动说明，比被追问要好得多。")

heading(doc, "2.6　绕射理论（GTD / UTD / PTD）　★", 3)
para(doc,
     "纯 PO 在远角副瓣上会偏乐观，因为它没有描述边缘绕射。"
     "绕射理论用来补充这一块。本项目暂未引入，答辩被问到就如实说明适用范围。",
     indent_first=21)

heading(doc, "2.7　近远场变换　★★", 3)
para(doc,
     "FDTD 直接给出的是近场。要得到方向图，需要在包围天线的闭合面上记录切向场，"
     "再通过等效原理积分到远场，这个过程叫近远场变换（NF2FF）。"
     "本项目用 openEMS 的 NF2FF 盒完成。",
     indent_first=21)

# ------------------------------------------------ 三
heading(doc, "三、数学基础")

heading(doc, "3.1　傅里叶变换与方向图　★★★", 3)
para(doc,
     "口径场与远场方向图构成一对傅里叶变换：口径越大，主瓣越窄；"
     "口径上的幅度锥削越强，副瓣越低。这条对应关系能解释本项目里"
     "几乎所有方向图现象，是最值得记住的一句话。",
     indent_first=21)

heading(doc, "3.2　贝塞尔函数与艾里图案　★★", 3)
para(doc,
     "均匀圆口径的远场是 2J₁(u)/u，J₁ 是一阶贝塞尔函数。"
     "只需要记住它的形状：中心为 1，第一个零点在 u = 3.8317，"
      "也就是 k·a·sinθ = 3.8317 时；第一副瓣约 −17.6 dB。",
     indent_first=21)

heading(doc, "3.3　数值积分　★★", 3)
para(doc,
     "口径积分在极坐标下做，采样点在半径方向取中点以避免轴线奇点，"
     "面元为 ρ·dρ·dφ。曲面上的积分通常配合高斯积分以提高精度。"
     "需要意识到：数值积分的精度直接决定副瓣是否可信。",
     indent_first=21)

heading(doc, "3.4　矢量运算与坐标变换　★★", 3)
para(doc,
     "射线追踪处处用到向量反射公式 d′ = d − 2(d·n)n、叉乘求面电流、"
     "以及球坐标与直角坐标之间的转换。这些是动手改代码时的基本功。",
     indent_first=21)

# ------------------------------------------------ 四
heading(doc, "四、结构有限元")

heading(doc, "4.1　线弹性力学　★★★", 3)
para(doc,
     "应变描述变形程度，应力描述内力分布，二者通过胡克定律联系。"
     "平衡方程要求内力与外力平衡。对反射面面板来说，"
     "关心的是在自重、风载等载荷下表面位移 w(x, y) 有多大。",
     indent_first=21)

heading(doc, "4.2　有限元法与弱形式　★★★", 3)
para(doc,
     "这是 FEniCSx 的门槛，也是答辩可能问的地方。思路是："
     "把微分方程两边乘以一个试探函数再积分，通过分部积分把高阶导数转移过去，"
     "得到所谓的弱形式；然后把求解区域离散成单元，在每个单元内用形函数近似，"
     "最后装配成线性方程组求解。",
     indent_first=21)
item(doc, "一句话版本：",
     "“把微分方程换成积分的、更弱的要求，再离散成线性方程组。”"
     "能讲清这句，本科阶段的答辩就够用了。")

heading(doc, "4.3　FEniCSx 的写法　★★", 3)
para(doc,
     "典型流程是：建网格 → 建函数空间 → 用 UFL 写弱形式 a(u,v) = L(v) → "
     "加边界条件 → 求解。需要特别注意：不加 Dirichlet 边界条件时，"
     "拉普拉斯算子奇异（常数属于零空间），解会漂移到任意大的值。",
     indent_first=21)

heading(doc, "4.4　板壳与面板变形　★★", 3)
para(doc,
     "实际反射面面板多为薄板或薄壳结构，变形分析会用到板壳理论。"
     "本项目的策略是先从标准算例（如均布载荷圆板）入手，"
     "与解析解对比通过后再上真实面板几何。",
     indent_first=21)

# ------------------------------------------------ 五
heading(doc, "五、结构—电磁耦合")

heading(doc, "5.1　表面误差与相位误差　★★★", 3)
para(doc,
     "面板变形会改变电磁波走过的路径长度。位移 w 引入的光程差是 2w"
     "（一来一回），对应相位误差 Δφ = 2kw = 4πw/λ。"
     "这就是结构域与电磁域之间的桥梁，也是本课题“双域”的核心。",
     indent_first=21)

heading(doc, "5.2　Ruze 公式　★★★", 3)
para(doc,
      "表面随机误差引起的增益损失满足：",
      indent_first=21, keep_with_next=True)
para(doc, "G/G₀ = exp(−σ²)", align=WD_ALIGN_PARAGRAPH.CENTER,
     size=11, space_after=6, keep_with_next=True)
para(doc,
     "其中 σ 是相位误差的均方根（弧度）。这条公式是本项目用于验证"
     "“结构—电磁耦合算得对不对”的判据。实测 24 次随机实现后与理论值偏差 0.000 dB——"
     "也就是说耦合链路本身是对的，缺的只是真实变形数据。",
     indent_first=21)

heading(doc, "5.3　增益损失与副瓣抬升　★★", 3)
para(doc,
     "面形误差除了降低峰值增益，还会抬高副瓣、展宽主瓣。"
     "本项目已量化副面遮挡带来的影响（增益损失 −0.525 dB），"
     "后续可对结构变形做同样的量化。",
     indent_first=21)

# ------------------------------------------------ 六
heading(doc, "六、工具与工程实践")

heading(doc, "6.1　openEMS　★★", 3)
para(doc,
     "开源的 FDTD 全波求解器，配套 CSXCAD 做几何与网格建模。"
     "工作流是：建引擎 → 设激励与边界 → 建几何与网格 → 加端口 → "
     "加近远场盒 → 运行 → 后处理。本项目用它做馈源的全波仿真，"
     "官方角锥喇叭教程已验证可跑通。",
     indent_first=21)

heading(doc, "6.2　FEniCSx　★★", 3)
para(doc,
     "开源有限元库，用 Python 描述弱形式。它把“写方程”和“离散求解”分开，"
     "使用者只需要写变分形式。本项目用它做面板结构变形。",
     indent_first=21)

heading(doc, "6.3　Python 科学计算　★★", 3)
para(doc,
     "NumPy 做数组运算与向量化、SciPy 提供特殊函数与求解器、"
     "Matplotlib 出图、h5py 读写 openEMS 的结果文件。"
     "自研的 GO/PO 代码全部用 Python 实现，便于修改与验证。",
     indent_first=21)

heading(doc, "6.4　版本控制与构建　★", 3)
para(doc,
     "Git 管理代码版本，CMake 负责 C++ 项目的构建。"
     "这两项在本项目中主要是环境搭建时用到，答辩基本不会深入问。",
     indent_first=21)

# ------------------------------------------------ 七
heading(doc, "七、答辩问题预演")
para(doc, "下面这些问题覆盖了答辩最可能问到的方向，建议逐条准备答案。",
     space_after=8)

add_table(doc, [
    ["可能的问题", "回答的要点"],
    ["为什么不全波仿真，偏要用高频近似？",
     "电大尺寸下网格量按口径三次方增长，内存与时间不可承受；"
     "工程上关心的是方向图与增益，不需要完整近场细节。"],
    ["GO 和 PO 有什么区别？",
     "GO 把波当射线，只算路径与幅度，忽略波动效应；"
     "PO 在面上求等效电流再积分，能得到更真实的副瓣结构。"],
    ["你怎么证明自己算的是对的？",
     "分层验证：均匀圆口径对比解析艾里图案（偏差 5.8×10⁻⁶）；"
     "射线追踪用准直误差与等光程判据（分别 4.4×10⁻¹⁶ 与 7.1×10⁻¹⁵）；"
     "结构耦合用 Ruze 公式（偏差 0.000 dB）。"],
    ["卡塞格伦比单反射面好在哪？",
     "馈源可以放在主面顶点附近，缩短馈线；双反射面设计自由度更大，"
     "可以调节放大率与遮挡比。"],
    ["遮挡对性能有什么影响？",
     "抬高副瓣、降低峰值增益。本项目实测遮挡比 4.913%，"
     "增益损失 −0.525 dB，第一副瓣从 −19.60 dB 抬高到 −16.25 dB。"],
    ["全开源的意义是什么？",
     "不依赖商业授权，结果可复现、可迁移；"
     "这条链路本身也能用于教学与后续研究。"],
    ["你的工作量和创新点在哪？",
     "打通了全开源的双域链路并逐项验证；"
     "自研 GO/PO 积分并在解析算例上校核；"
     "把结构变形量化为口径相位误差并闭环到远场。"],
], [5.4, 10.4], size=9.5)

# ------------------------------------------------ 八
heading(doc, "八、学习顺序与时间分配")
para(doc,
     "下面按“性价比”排序。先看前面的，基本就能应对答辩；"
     "后面的是深入理解用的，时间紧可以最后看。",
     space_after=8)

add_table(doc, [
    ["顺序", "内容", "预计时间", "目的"],
    ["1", "1.1 天线参数 + 1.2 口径场与远场 + 1.3 抛物面",
     "1.5 小时", "建立整体图像，能听懂自己项目的输出"],
    ["2", "1.4 卡塞格伦几何", "1 小时", "能画出射线路径并解释为什么这么设计"],
    ["3", "2.3 GO 与 2.4 PO", "1.5 小时", "答辩核心，必须能用自己的话讲"],
    ["4", "5.1 相位误差 + 5.2 Ruze 公式", "0.5 小时", "双域耦合的桥，短小但关键"],
    ["5", "4.1 与 4.2 有限元大意", "1.5 小时", "能说清弱形式在干什么即可"],
    ["6", "2.2 FDTD 大意", "0.5 小时", "知道 openEMS 在算什么"],
    ["7", "其余章节", "按需", "被追问时能补一句"],
], [1.2, 6.0, 2.0, 6.6], size=9.5)

para(doc,
     "合计约六到七小时。建议分三次看，每次结束用自己的话把这部分讲一遍——"
     "能讲出来才算真的会了。",
     space_before=8, indent_first=21)

doc.save(str(DOCX))
print(f"saved: {DOCX}")
