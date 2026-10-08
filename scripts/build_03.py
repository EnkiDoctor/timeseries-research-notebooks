"""Build an executable, case-first backtesting and reporting cheat sheet."""
from pathlib import Path
import textwrap

import nbformat as nbf

from backtest_cases_a import CASES as A
from backtest_cases_b import CASES as B
from backtest_cases_c import CASES as C

ROOT = Path(__file__).resolve().parents[1]
CASES = A + B + C
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


markdown('''
# 03 · 回测与可视化 Cheat Sheet

从最简单的 `仓位 × 收益` 开始，按成交时点、账户记账方法和数据形状选择模板。

每个案例都按 **`display(df)` 输入表 → 场景与任务 → 回测代码与结果表 → `plt.*` 图 → 解读** 排列。
先读小表，确定自己的列表示什么，再复制代码。所有案例都能独立运行，不需要先执行前面的案例。

1. 运行一次下面的初始化格。
2. 找到 B01–B18 中适合的案例；练习时运行它的示例建表格。
3. 已有数据时跳过示例建表，先 `display(df.head())` 检查字段，再运行该例的回测格和绘图格。
4. 先用小表核对一两笔金额，再换完整数据；示例的 `assert` 帮你发现错位或不符合假设的输入。

这里把已有的 position / score 当作输入；**不把构造策略、调参和回测收益混为一件事**。
B14 展示时间划分与阈值选择，完整机器学习建模不属于本册。
数据均为合成教学小表，没有策略盈利证据。图内用英文避免字体缺失，解释与注释使用中文。

## 先决定用哪一种记账

| 你拿到什么 / 想做什么 | 对应案例 |
|---|---|
| 一列价格、一列目标仓位，成交前已知仓位 | B01 收盘→收盘 |
| 收盘后才有信号，下一开盘执行 | B02 开盘→开盘 |
| 当天开盘前已知信号、收盘全部退出 | B03 当日开→收 |
| 不规则日内时间戳，允许跨夜 | B04 逐bar→逐日复合 |
| 要认真算换手和交易费 | B05 现金/股数/费后目标权重 |
| 多资产价格和权重，宽表或长表 | B06 / B07 |
| 每周等指定日期再平衡，其余时间不交易 | B08 固定股数与权重漂移 |
| 每次固定投入金额，不按账户权益复投 | B09 固定本金PnL |
| 已有 buy/hold/sell 指令 | B10 事件驱动账户 |
| 两条腿的配对策略 | B11 双腿贡献 |
| 每天新开一笔、每笔持有3期 | B12 独立分批账户 |
| 按历史波动调整仓位 | B13 风险目标 |
| 选参数并报告真正未见的测试结果 | B14 时间切分 |
| 已有每日净收益，需要指标与回撤图 | B15 |
| 月度汇报、对照基准与滚动风险、费用敏感性 | B16 / B17 / B18 |

## 三种时序，别机械地加 shift

| 已知信息与成交约定 | 本行收益区间 | 对应仓位 |
|---|---|---|
| t−1 收盘成交前确定权重，按该收盘成交 | `close[t] / close[t-1] - 1` | `position.shift(1)` |
| t−2 收盘后产生信号，t−1 开盘成交 | `open[t] / open[t-1] - 1` | `close_signal.shift(2)` |
| t 开盘前确定仓位，当天开仓并平仓 | `close[t] / open[t] - 1` | 当行 `position` |

`shift` 移动的是观测行，不能自动保证可交易，也不自动代表自然日。你需要先写出“信号可用 → 成交 → 估值”的时间线。

**共同单位：** 收益 0.01 = 1%；仓位是相对于账户权益的资金比例；单边 1 bp = 0.0001。
`pnl` 是货币金额，`return` 是收益率；账户净值是 `equity / initial_cash`。
无费用向量化案例假定在每个指定时点再平衡，现金利息为 0；它们不是固定股数持有。
''', 'backtest-introduction')

code('''
# SETUP：只运行一次；每个case仍然有自己的输入df。
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

BLUE, TEAL, RED, ORANGE = '#2563EB', '#0F766E', '#DC2626', '#D97706'
plt.rcdefaults()
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'figure.dpi': 120, 'savefig.dpi': 180,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'axes.axisbelow': True,
    'grid.color': '#E2E8F0', 'grid.alpha': 0.8,
    'axes.titlelocation': 'left', 'axes.titleweight': 'bold',
    'axes.titlesize': 13, 'axes.titlepad': 14,
    'lines.linewidth': 2, 'legend.frameon': False,
})
''', 'backtest-setup', ['setup'])

for case in CASES:
    tag = case['id']
    markdown("<a id='{0}'></a>\n## {0} · {1}\n\n**先看输入 DataFrame。** 下面的建表代码仅用来演示；替换成自己的同结构 `df` 后，先 display 再做回测。".format(tag, case['title']), tag.lower() + '-input')
    code(case['data'], tag.lower() + '-data', ['recipe:' + tag, 'example_data'], tag)
    markdown('**场景 / 要做什么：**\n\n' + case['task'] + '\n\n**回测代码：** 同时展示中间列或账户结果，方便逐行核对。', tag.lower() + '-task')
    code(case['backtest'], tag.lower() + '-backtest', ['recipe:' + tag, 'backtest'], tag)
    markdown('**可视化：** 直接使用刚刚算出的结果。', tag.lower() + '-visualization')
    code(case['plot'], tag.lower() + '-plot', ['recipe:' + tag, 'plot'], tag)
    markdown('**怎么看：** ' + case['reading'] + '\n\n**换数据时注意：** ' + case['caution'], tag.lower() + '-reading')

markdown('''
## 复制前的快速对照

| 检查点 | 怎么判断 |
|---|---|
| 信号是不是未来信息？ | 找到生成信号所需的最后一个时间戳，必须早于成交；收盘后算出的信号不能在同一收盘无延迟成交。 |
| 第一笔与最后一笔记了什么？ | 初始持仓是否为0；建仓费是否计入；最后是按市值估值还是已经平仓；未结束区间不虚构收益。 |
| 缺失行情怎么办？ | 先查日历、停牌、退市、数据断档；不能用填0收益让问题消失。 |
| 长表是否对齐？ | 检查 `(date, asset)` 唯一性、共同估值时点和完整持仓资产，分组shift不能跨资产。 |
| 权重还是股数？ | 权重保持不变通常需要交易；股数保持不变时权重会随价格漂移。 |
| 费用按什么计算？ | 按买卖绝对成交金额，含首次建仓和实际平仓；不得把目标权重差当通用实际换手。 |
| 净值、PnL、收益率单位是否混淆？ | 固定投入用货币PnL累计；权益比例策略用实际账户收益复合。 |
| 能否年化？ | 先确认完整、规则的收益频率和足够样本；先把不规则记录变成按会话估值的权益序列。 |
| 是投资组合还是价格差？ | 双腿分别计算资金贡献；零附近的价差不能直接pct_change。 |
| 调参是否污染测试？ | 事先确定切分；候选和阈值选择不用测试收益；多期标签按可用时间清除跨界样本。 |

本册不模拟限价订单队列、停牌无法成交、借券供给、保证金强平或动态价格冲击。遇到这些数据，先给出执行假设再扩展账户记账，不能把不存在的成交当作已实现交易。

## 汇报时最少展示什么

1. 一张输入/对齐样例表：解释信号、成交价、实际持仓和收益各在哪个时点。
2. 策略与基准净值、回撤、成本和样本长度；将样本内与样本外分开标记。
3. 交易次数/金额、敞口和费用定义；按日上涨比例与按笔胜率分开说。
4. 一个稳定性检查：分时期、成本敏感性或参数邻域；描述限制和下一步验证。

**保存当前图：** 在对应 `plt.show()` 前加 `plt.savefig('backtest_chart.png', dpi=180, bbox_inches='tight')`。

API 对照：[pandas pct_change](https://pandas.pydata.org/pandas-docs/version/1.5/reference/api/pandas.Series.pct_change.html) · [pandas shift](https://pandas.pydata.org/pandas-docs/version/1.5/reference/api/pandas.DataFrame.shift.html) · [Matplotlib pyplot](https://matplotlib.org/3.7.5/tutorials/introductory/pyplot.html)

本文件沿用仓库中的既有文件名，内容已从预留页更新为回测与可视化手册。
''', 'backtest-checklist')

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'title': '回测与可视化 Cheat Sheet',
}
nbf.validate(nb)
path = ROOT / 'notebooks' / '03_modeling_and_backtesting.ipynb'
nbf.write(nb, str(path))
print('Wrote', path.name, 'cells=', len(cells), 'cases=', len(CASES))
