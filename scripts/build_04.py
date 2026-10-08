"""Build a dataframe-first machine-learning cheat sheet with executable outputs."""
from pathlib import Path
import textwrap

import nbformat as nbf

from ml_cases_a import CASES as A
from ml_cases_b import CASES as B
from ml_cases_c import CASES as C

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
    if recipe_id == 'M10':
        cell.metadata['optional_package'] = 'xgboost'
    cells.append(cell)


markdown('''
# 04 · 机器学习与可视化 Cheat Sheet

**scikit-learn 为主，包含决策树、随机森林、梯度提升树，以及可选 XGBoost。**
沿用之前的阅读方式：**先 `display(df)` 输入样例 → 要预测什么 → 训练/验证/测试 → 指标与预测表 → `plt.*` 图 → 中文解读。**

每例数据单独生成，每例导入自己需要的 sklearn 类；只需先运行本册初始化，之后可以任选案例独立执行。
表格预览前8–9行，输出中标出总行数；机器学习需要比手算回测更多的样本，因此示例使用约140–270行合成数据。

**复制方法：** 已有自己的 `df` 时，跳过示例建表格，先 `display(df.head(8))`，对齐字段与信息时点，再复制训练和绘图格。
`features` 必须显式列出，不能用“除了目标之外全选”将未来收益、标签实现时间或事后信息混进模型。

## 按问题找案例

| 问题 | 案例 |
|---|---|
| 只有价格，怎样构造特征和未来标签？ | M01 因果特征、label_end、隔离边界 |
| 连续数值预测先做什么？ | M02 LinearRegression + DummyRegressor |
| 缺失值、量纲差异和共线性？ | M03 Pipeline + Imputer + Scaler + Ridge；附 ElasticNet 替换 |
| 数值列和类别列混合？ | M04 ColumnTransformer + OneHotEncoder |
| 预测涨跌，怎样看分类结果？ | M05 LogisticRegression + 混淆矩阵 |
| 正类很少，概率阈值怎么选？ | M06 验证集选阈值 + PR 曲线 |
| 一棵树有多深才合适？ | M07 DecisionTreeRegressor 过拟合图 |
| 想拟合非线性和特征交互？ | M08 RandomForestRegressor |
| 不额外装包的提升树？ | M09 HistGradientBoostingRegressor |
| 想用 XGBoost 和 early stopping？ | M10 可选 XGBRegressor |
| 怎样在时间序列中搜索参数？ | M11 TimeSeriesSplit + GridSearchCV |
| 多资产面板怎样滚动训练？ | M12 按日期 Walk-forward + 标签到期检查 |
| 特征是否真的帮助这个模型？ | M13 验证集置换重要性 |
| 想知道预测错在哪里？ | M14 残差 + Rank IC + 基准误差 |
| 特征太相关，想降维？ | M15 训练期拟合 PCA |
| 预测怎样接到策略与回测？ | M16 样本外预测 → 仓位 → 扣费净值 |

## 依赖与版本

基础部分需要 NumPy、pandas、Matplotlib、scikit-learn；不需要网络数据、API key 或GPU。
Python 3.8 参考版本为 **scikit-learn 1.3.2**。XGBoost 是 M10 的可选依赖；没有安装时该例会明确输出跳过提示，其余例子照常运行。

```bash
# Python 3.8：先安装仓库的基础依赖
python -m pip install -r requirements-py38.txt
# 可选：运行 M10
python -m pip install -r requirements-xgboost-py38.txt
```

较新 Python 使用 `requirements.txt`，可选 XGBoost 使用 `requirements-xgboost.txt`。
在 Jupyter 中可以用 `%pip install ...` 安装到当前 kernel 对应环境，安装后重启 kernel；代码格不会自动安装任何包。
macOS 若提示缺 `libomp.dylib`，需配置 OpenMP 运行库（例如已使用 Homebrew 的环境可 `brew install libomp`），再重启 kernel。

| 常见兼容点 | 本册写法 |
|---|---|
| 新版本 RMSE API 改动 | `np.sqrt(mean_squared_error(y, pred))` |
| OneHotEncoder 参数名 | sklearn ≥1.2 用 `sparse_output=False`；更早版本对应 `sparse=False` |
| XGBoost early stopping 参数位置 | 放在 `XGBRegressor(...)` 构造器内，验证集放在 `eval_set` 最后 |
| 随机内部验证不适合时间任务 | HistGradientBoosting 明确设置 `early_stopping=False`；需要选迭代数时另做时间验证 |

## 先确认信息时点

多数案例假定 **盘前特征 → 当天开盘至收盘收益**，所以按完整日期排序切分即可；不需要在已对齐的数据上再乱加 shift。
M01 / M11 / M12 则是 **收盘后的特征 → 随后若干期收益**，额外记录 `label_end`，训练时剔除当时尚不可知的标签。
普通随机 `train_test_split` 不适合这里的未来预测目的；多资产同日的样本应一起切分。

模型都用合成数据解释 API 和研究流程。人为设置的信号强度、测试指标和净值**不能证明真实行情可预测或策略盈利**。
日期用普通业务日生成，只代表教学采样顺序，不是实际交易所日历。
''', 'ml-introduction')

code('''
# SETUP：只需一次。每个案例的训练格再导入所需 sklearn 类。
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
import sklearn

print('scikit-learn:', sklearn.__version__)
BLUE, TEAL, RED, ORANGE = '#2563EB', '#0F766E', '#DC2626', '#D97706'
plt.rcdefaults()
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'figure.dpi': 120, 'savefig.dpi': 180,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'axes.axisbelow': True,
    'grid.color': '#E2E8F0', 'grid.alpha': 0.75,
    'axes.titlelocation': 'left', 'axes.titleweight': 'bold',
    'axes.titlesize': 13, 'axes.titlepad': 14,
    'lines.linewidth': 2, 'legend.frameon': False,
})
''', 'ml-setup', ['setup'])

for case in CASES:
    tag = case['id']
    markdown("<a id='{0}'></a>\n## {0} · {1}\n\n**先看输入 DataFrame：** 以下是实际参与此例计算的数据预览。".format(tag, case['title']), tag.lower() + '-input')
    code(case['data'], tag.lower() + '-data', ['recipe:' + tag, 'example_data'], tag)
    markdown('**场景 / 要做什么：**\n\n' + case['task'] + '\n\n**示例代码：** 明确选择特征，先切分再拟合，最后展示结果。', tag.lower() + '-task')
    code(case['train'], tag.lower() + '-train', ['recipe:' + tag, 'model'], tag)
    markdown('**可视化：** 使用刚刚计算出的指标和预测。', tag.lower() + '-visualization')
    code(case['plot'], tag.lower() + '-plot', ['recipe:' + tag, 'plot'], tag)
    markdown('**怎么看：** ' + case['reading'] + '\n\n**换数据时注意：** ' + case['caution'], tag.lower() + '-reading')

markdown('''
## 现场换数据时，优先改这几处

| 要改什么 | 操作 |
|---|---|
| 特征列 | 修改 `features` 或 `numeric / categorical`，只放预测时已知的列 |
| 目标 | 选择连续收益/金额用回归，二元事件用分类；不要把未知标签填0 |
| 日期与资产 | 日期先转 datetime 并排序；单序列日期唯一，面板 `(date, asset)` 唯一 |
| 时间切分 | 把比例边界改成研究需要的真实日期；同日资产成块，跨期标签按实际到期时间 purge |
| 预处理 | `.fit()` 只对 train；测试只能 `.transform()` 或 `.predict()`；CV 时 Pipeline 在每折里拟合 |
| 类别与常量 | 检查训练是否只有一个类；单类测试不报告ROC-AUC，常量回归目标不解释R² |
| 候选参数 | 先在训练/验证中决定；不要用最终 test 比较一堆方案再把最好者当无偏结果 |
| 样本量 | 小数据不能支持深树与大范围搜索；同时报告样本数、基准误差和分段表现 |
| 外部数据 | 检查真正发布时间、历史修订、存活偏差和当时可交易范围 |

**一眼看懂 sklearn 常用动作：** `fit(X_train, y_train)` 学习；`predict(X_test)` 输出值/类别；`predict_proba(X_test)[:, 1]` 输出二分类正类概率；`Pipeline` 把预处理和模型绑定；`GridSearchCV` 只在传入的开发数据内部比较候选。

**读图怎么选：** 回归用实际值对预测值散点、残差图；分类用混淆矩阵、PR/ROC；树复杂度用训练/验证误差曲线；模型解释用验证集置换重要性；交易效果单独看样本外净值与回撤。
不能因为两个案例的合成数据不同，却直接用它们的 RMSE 判定哪个模型更好。正式比较需要同一目标、相同切分与相同基准。

**保存图：** 在对应 `plt.show()` 前加入 `plt.savefig('ml_chart.png', dpi=180, bbox_inches='tight')`。

## API 对照资料

- [scikit-learn：避免预处理与数据泄漏错误](https://scikit-learn.org/1.3/common_pitfalls.html)
- [TimeSeriesSplit 的 gap 和时间边界](https://scikit-learn.org/1.3/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [置换重要性的解释与限制](https://scikit-learn.org/1.3/modules/permutation_importance.html)
- [HistGradientBoostingRegressor](https://scikit-learn.org/1.3/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
- [XGBoost 2.0 sklearn API 和 early stopping](https://xgboost.readthedocs.io/en/release_2.0.0/python/python_api.html)

[返回回测手册](03_modeling_and_backtesting.ipynb) · [基础可视化](02_time_series_processing_visualization.ipynb)
''', 'ml-adaptation')

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'title': '机器学习与可视化 Cheat Sheet',
}
nbf.validate(nb)
path = ROOT / 'notebooks' / '04_machine_learning_cheat_sheet.ipynb'
nbf.write(nb, str(path))
print('Wrote', path.name, 'cells=', len(cells), 'cases=', len(CASES))
