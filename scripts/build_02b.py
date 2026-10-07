"""Build the separate polished visualization notebook without changing the basic edition."""
from pathlib import Path
import textwrap

import nbformat as nbf

from visualization_cases import CASES
from polished_visualization_cases import STYLED

ROOT = Path(__file__).resolve().parents[1]
cells = []


def markdown(source, cell_id):
    cell = nbf.v4.new_markdown_cell(textwrap.dedent(source).strip())
    cell.id = cell_id
    cells.append(cell)


def code(source, cell_id, tags, recipe_id=None):
    cell = nbf.v4.new_code_cell(textwrap.dedent(source).strip())
    cell.id = cell_id
    cell.metadata['tags'] = tags
    if recipe_id:
        cell.metadata['recipe_id'] = recipe_id
    cells.append(cell)


markdown("""
# 02b · 时间序列可视化：美观版

适合把探索结果放进研究汇报。与基础版的 V01–V18 使用**相同的小表和分析任务**，这里编号为 S01–S18，便于对照绘图写法。

仍然按 **输入表 → 要做什么 → 代码 → 图形结果** 阅读，每例只画一张图，使用 `plt.figure()`、`plt.plot()`、`plt.title()` 等写法。

**怎么用：**
1. 先运行下面的主题初始化格，统一导入库、配色、字体和网格。
2. 找到案例，检查自己的 `df` 是否具有表中列名和单位。
3. 已有 `df` 时跳过示例建表，直接复制绘图格；练习时先运行该例的示例建表格。

这里的配色和标注用于突出信息：数值写单位、关键点带标签、同类图保持一致。代码没有自定义绘图函数，每个样式都能在代码中直接修改。

全部小表均为人工构造的教学数据，并非真实市场行情。示例表只有 8–10 行，用于理解代码，不能据此判断市场规律。收益 `0.01` 表示 `1%`；缺失仍是缺失。图内使用英文和环境自带字体，中文解释保留在表格与代码旁。

| 想做什么 | 案例 |
|---|---|
| 展示收益、比较两条走势 | S01–S02 |
| 缺失位置、缺失率、收益分布、极端值 | S03–S06 |
| 滚动波动、滚动相关、相关矩阵 | S07–S09 |
| 滞后关系、自相关、星期与月度比较 | S10–S13 |
| 成交量、训练测试边界、分组收益 | S14–S16 |
| 回撤、每小时事件数 | S17–S18 |
""", 'polished-introduction')

code("""
# SETUP：只需运行一次。之后每个案例使用自己的 df。
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from IPython.display import display

BLUE = "#2563EB"
TEAL = "#0F766E"
ORANGE = "#D97706"
RED = "#DC2626"
INK = "#1E293B"
MUTED = "#64748B"
LIGHT = "#E2E8F0"

plt.rcdefaults()
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "figure.dpi": 120, "savefig.dpi": 200,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": LIGHT, "axes.linewidth": 0.8,
    "axes.titlelocation": "left", "axes.titlesize": 15,
    "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlepad": 16,
    "axes.labelcolor": MUTED, "axes.labelpad": 8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
    "grid.color": LIGHT, "grid.linewidth": 0.7, "grid.alpha": 0.7,
    "lines.linewidth": 2.2, "legend.frameon": False,
})
""", 'polished-setup', ['setup'])


for case in CASES:
    tag = 'S' + case['id'][1:]
    style = STYLED[case['id']]
    table = ['| ' + ' | '.join(case['columns']) + ' |',
             '| ' + ' | '.join(['---'] * len(case['columns'])) + ' |']
    for row in case['rows']:
        table.append('| ' + ' | '.join('NaN' if x is None else str(x) for x in row) + ' |')
    task = style.get('task', case['task'])
    markdown("<a id='{0}'></a>\n## {0} · {1}\n\n**输入表：`df`（全部 {2} 行）**\n\n{3}\n\n{4}\n\n**要做什么：** {5}\n\n**代码：** 已有同列名的 `df` 时，跳过第一个示例建表格，复制第二个绘图格。".format(
        tag, case['title'], len(case['rows']), '\n'.join(table), case['dtypes_note'], task), tag.lower() + '-input-and-task')
    fixture = '# 示例建表：已有自己的 df 时跳过。\ndf = pd.DataFrame([\n'
    fixture += '\n'.join('    ' + repr(row) + ',' for row in case['rows'])
    fixture += '\n], columns=' + repr(case['columns']) + ')'
    code(fixture, tag.lower() + '-example-data', ['recipe:' + tag, 'example_data'], tag)
    code('# 绘图代码：先运行本册主题初始化格。\n' + style['plot'],
         tag.lower() + '-plot', ['recipe:' + tag, 'plot'], tag)
    markdown('**美化了哪里：** ' + style['beauty'] + '\n\n**图怎么读：** ' +
             style.get('reading', case['reading']) + '\n\n**换数据时注意：** ' +
             style.get('tip', case['tip']), tag.lower() + '-reading')

markdown("""
## 改成自己的样式

常用的几处修改：`figsize` 调整大小；`color` 改颜色；`alpha` 调整透明度；`marker` 控制数据点；`plt.title()` 和轴标签说明单位。主题格的字号和网格设置会作用于之后新建的图。

小表适合逐点标注；换成几千行数据时只保留末值、极值或少量重点标签，必要时去掉 `marker`。类别过多时选择有依据的展示子集，不把所有文字挤进一张图。需要恢复 Matplotlib 默认外观时，运行 `plt.rcdefaults()`。

**保存图片：** 在所选案例的 `plt.show()` 前加入下面这一行。文件名自行改写，重复使用同名文件会覆盖旧图。

```python
plt.savefig("my_chart.png", dpi=200, bbox_inches="tight", facecolor="white")
```

[返回基础版](02_time_series_processing_visualization.ipynb) · [Matplotlib pyplot 文档](https://matplotlib.org/3.7.5/tutorials/introductory/pyplot.html)
""", 'polished-customization')

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'title': '时间序列可视化：美观版',
}
nbf.validate(nb)
path = ROOT / 'notebooks' / '02b_time_series_visualization_polished.ipynb'
nbf.write(nb, str(path))
print('Wrote', path, 'cells=', len(cells))
