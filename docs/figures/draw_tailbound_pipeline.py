"""Render the symbolic-round tail-bound pipeline as SVG, PNG and PDF."""
from pathlib import Path

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

OUT = Path(__file__).resolve().parent
REGULAR = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BOLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
RED, INK, MUTED = '#AA1F3D', '#182433', '#617082'
PALE, PINK, LINE = '#F5F6F8', '#FBF3F5', '#DEE2E7'
plt.rcParams.update({'svg.fonttype': 'none', 'mathtext.fontset': 'stix', 'pdf.fonttype': 42})
fig = plt.figure(figsize=(18, 9.35), dpi=160, facecolor='white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set(xlim=(0, 1800), ylim=(1050, 115))
ax.axis('off')

def text(x, y, value, size=20, color=INK, bold=False, ha='left'):
    return ax.text(x, y, value, fontsize=size, color=color,
                   fontproperties=BOLD if bold else REGULAR,
                   ha=ha, va='center', linespacing=1.6)

def math(x, y, value, size=25, color=INK, ha='left'):
    return ax.text(x, y, '$' + value + '$', fontsize=size, color=color, ha=ha, va='center')

def rect(x, y, w, h, color=PALE, edge='none'):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=edge, linewidth=1))

def arrow(x1, y1, x2, y2, color=RED, lw=2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                mutation_scale=16, linewidth=lw, color=color))

def stage(cx, label, title):
    ax.add_patch(Circle((cx, 179), 43, facecolor=RED, edgecolor='none'))
    text(cx, 179, label, 16, 'white', True, 'center')
    text(cx, 250, title, 22, RED, True, 'center')

rect(58, 285, 282, 637)
rect(390, 285, 960, 637, '#FAFAFB')
rect(1400, 285, 342, 637, PINK)
stage(199, 'stage1', '程序输入 → CFG')
stage(870, 'stage2', '前期望 · 模板 · 约束')
stage(1571, 'stage3', '后端求解与验证')
arrow(347, 563, 381, 563)
arrow(1357, 563, 1391, 563)

# Stage 1: concise frontend overview.
text(199, 351, '程序 .pp + 验证目标', 19, bold=True, ha='center')
text(199, 390, '可附位置不变量 I', 17, MUTED, ha='center')
arrow(199, 422, 199, 468)
text(199, 505, '解析与语义检查', 20, bold=True, ha='center')
arrow(199, 542, 199, 588)
text(199, 626, '生成概率 CFG', 20, bold=True, ha='center')
text(199, 672, '守卫 · 概率 · 状态更新', 16, MUTED, ha='center')
rect(80, 765, 238, 124, 'white')
text(199, 802, '保留符号状态变量', 17, RED, True, 'center')
text(199, 848, '按守卫构造状态域', 17, MUTED, ha='center')

# Stage 2: the mathematical interface to the backend.
rect(412, 302, 916, 167, 'white', LINE)
rect(412, 302, 5, 167, RED)
text(437, 329, '① 构造未知多项式模板', 20, bold=True)
math(458, 388, r'\eta_{\mathbf{a}}(\mathbf{x})=\sum_{|\alpha|\leq D}a_{\alpha}\,\mathbf{x}^{\alpha}', 29)
text(865, 365, 'x 为符号状态；', 16, MUTED)
text(865, 400, 'D 为总次数；', 16, MUTED)
text(865, 435, r'直接合成 $\eta$，不再另取整数次幂。', 16, MUTED)
arrow(870, 472, 870, 490)

rect(412, 494, 916, 185, 'white', LINE)
rect(412, 494, 5, 185, RED)
text(437, 522, '② 验证不变量，组合一轮转移并计算前期望', 20, bold=True)
math(458, 578, r'\operatorname{Pre}_{\rm round}(\eta)(\mathbf{x})='
     r'\sum_b p_b(\mathbf{x})\,\mathbb{E}_{\mathbf{r}_b}'
     r'\!\left[\eta\!\left(F_b(\mathbf{x},\mathbf{r}_b)\right)\right]', 27)
text(458, 627, '状态更新代入 → 随机变量精确矩消元 → 概率加权求和', 18)
text(458, 660, 'b 表示概率分支；确定性守卫按覆盖域分情况生成，不分配概率。', 16, MUTED)
arrow(870, 682, 870, 700)

rect(412, 704, 916, 200, 'white', LINE)
rect(412, 704, 5, 200, RED)
text(437, 731, '③ 固定 c ∈ (0,1)，生成多项式非负约束', 20, bold=True)
math(458, 777, r'\eta(\mathbf{x})\geq 0\quad(\mathbf{x}\in I),\qquad'
     r' \eta(\mathbf{x})\geq 1\quad(\mathbf{x}\in I\cap G)', 24)
math(458, 821, r'c\eta(\mathbf{x})-\operatorname{Pre}_{\rm round}(\eta)(\mathbf{x})\geq0'
     r'\quad(\mathbf{x}\in I\cap G)', 24)
math(458, 866, r'\min_{\mathbf{a}}\ A=\mathbb{E}[\eta(X_0)]', 24)
text(1060, 777, 'G：继续循环的守卫', 16, MUTED)
text(1060, 821, 'I：循环入口不变量', 16, MUTED)

# Stage 3: proof encoding, solve, verify, bounded outer search.
text(1571, 332, '选择非负性证明策略', 18, bold=True, ha='center')
text(1571, 371, 'Putinar / Schmüdgen', 16, MUTED, ha='center')
text(1571, 404, '或 Handelman', 16, MUTED, ha='center')
arrow(1571, 427, 1571, 457)
text(1571, 487, '系数匹配 → LP / SDP', 18, bold=True, ha='center')
arrow(1571, 511, 1571, 541)
text(1571, 570, 'CVXPY 建模', 20, bold=True, ha='center')
text(1571, 608, 'MOSEK 求解', 20, bold=True, ha='center')
arrow(1571, 632, 1571, 662)
text(1571, 693, '有理重构 · 精确验证', 18, bold=True, ha='center')
rect(1421, 741, 300, 154, 'white')
text(1571, 773, '外层有预算搜索', 18, RED, True, 'center')
text(1571, 813, '二分 c；当前 D 无证书则升阶', 15, ha='center')
text(1571, 851, '将 D、c 返回 stage2 重建约束', 15, MUTED, ha='center')
text(1571, 878, '仅接受验证通过的证书', 15, MUTED, ha='center')

# Shared result bar; finite search failure is not an impossibility proof.
arrow(1571, 924, 1571, 944)
rect(58, 947, 1684, 80, PINK)
rect(58, 947, 5, 80, RED)
text(83, 986, '输出证书与统一尾界', 20, RED, True)
math(430, 986, r'\Pr(K>n)\leq\min\{1,A c^n\}=\min\{1,Ae^{-\lambda n}\},'
     r'\quad\lambda=-\ln c,\quad n=0,1,2,\ldots', 28, RED)
for extension in ('svg', 'png'):
    fig.savefig(OUT / f'tailbound_pipeline.{extension}', dpi=180, facecolor='white')
# Outline text before PDF conversion: the CFF fonts in the Noto TTC files
# otherwise produce a font-type mismatch in this Matplotlib PDF backend.
# Keep the regular SVG above editable; the PDF is font-independent vector art.
outlined_svg = OUT / 'tailbound_pipeline_outlined.svg'
with plt.rc_context({'svg.fonttype': 'path'}):
    fig.savefig(outlined_svg, facecolor='white')
with fitz.open(outlined_svg) as document:
    (OUT / 'tailbound_pipeline.pdf').write_bytes(document.convert_to_pdf())
plt.close(fig)
