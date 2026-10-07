# 时间序列研究代码模板 · 中文 Notebook

面向限时数据分析的参考手册：**按问题找模板，复制初始化单元和对应代码，修改字段，再检查输出。**
内容以时间序列与多资产面板为主，也适用于设备监测、业务指标和其他带时间戳的数据。

**70 个可独立运行的模板 · 18 张实际示例图 · 中文场景说明和代码注释。**

## 直接打开

| Notebook | 内容 | 当前状态 |
|---|---|---|
| [01 · pandas 场景模板](notebooks/01_pandas_time_series_templates.ipynb) | 读写、清洗、索引、分组、拼表、时间窗口、重采样、时区、时点连接 | 已完成 |
| [02 · 时间序列数据处理与可视化](notebooks/02_time_series_processing_visualization.ipynb) | 数据质量、缺失与异常、特征与标签，以及按研究问题选择图表 | 已完成 |
| [03 · 建模、策略应用与回测](notebooks/03_modeling_and_backtesting.ipynb) | 预留后续内容 | 尚未实现，仅说明范围 |

- **[按场景检索所有模板](docs/RECIPE_INDEX.md)**：也可在 notebook 中搜索 `P01`、`D01`、`V01` 等编号。
- **[数据接入指南](docs/DATA_ADAPTER.md)**：把陌生数据映射到模板字段，而不是硬套金融含义。
- **[运行与兼容说明](docs/COMPATIBILITY.md)**：Python 3.8 参考环境与版本差异。
- `docs/` 中的同名 HTML 是已运行的只读版本，下载后用浏览器打开。GitHub 中直接打开 `.ipynb` 可以查看代码、表格和内嵌图片。

## 图表预览

每个可视化案例按 **输入数据表 → 要做什么 → 代码 → 图形结果** 排列。输入表逐行展示，列名统一从 `df` 读取，完整预览见 [图表目录](docs/GALLERY.md)。

绘图统一采用 `plt.figure(figsize=(...))`、`plt.plot()`、`plt.title()`、`plt.xlabel()` 等写法。
每个案例只画一张简单图，最后用 `plt.tight_layout()` 和 `plt.show()` 展示；无需管理子图或坐标轴对象。

| 缺失热图：找成片缺口 | 相关矩阵：另附样本量表 |
|---|---|
| ![V03 缺失热图](docs/images/02-v03-1.png) | ![V09 收益相关矩阵](docs/images/02-v09-1.png) |
| 月度热图：输入完整月收益 | 时序诊断：收益自相关 |
| ![V13 月度收益热图](docs/images/02-v13-1.png) | ![V11 自相关](docs/images/02-v11-1.png) |

## 怎么复制最省时间

1. **P / D 模板**：先运行对应 notebook 的 setup，再选择模板。
2. **V 可视化案例**：只运行 B 部分的 import，看案例开头的输入表及任务说明。
3. 已有自己的 `df`：对齐示例列名与单位，直接运行“绘图代码”格。没有数据：先运行同一案例的“示例建表”格。
4. 每个 V 案例使用独立小表，不依赖 `demo_panel`、`wide_ret` 等全局数据，也不依赖其他案例。日期转换、排序等必要步骤留在绘图格中。
5. 示例数据很小，只用于看懂代码。真实分析要确认频率、缺失、样本量和信息时点；预测研究先保留未来测试区间。

这里的图表全部来自可复现的合成示例，**不代表真实市场规律或可盈利策略**。中文说明与注释解释用途，图内使用英文标签以避免运行环境缺少中文字体。

## 按问题选择图表

| 你想回答的问题 | 合适的图 | 同时要报告什么 |
|---|---|---|
| 每天的收益怎样变化？ | V01 收益折线 | 小数 / 百分数、日期顺序 |
| 多个资产从同一起点走势如何？ | V02 归一化折线 | 共同起点、价格为正 |
| 数据缺在哪里、哪些列缺得多？ | V03 缺失热图、V04 缺失率柱图 | 预期日历、缺整行与缺字段 |
| 收益分布如何，有哪些大波动？ | V05 直方图、V06 极值标记 | 样本量、固定阈值的含义 |
| 波动和相关性是否变化？ | V07 滚动波动、V08 滚动相关 | 窗口长度、成对有效样本 |
| 多个收益序列是否相关？ | V09 相关矩阵 | 成对样本数表 |
| 今天和明天的变化是否有关？ | V10 滞后散点、V11 自相关 | 目标对齐、lag 的单位 |
| 星期或月份是否存在差异？ | V12 星期箱线图、V13 月度热图 | 每组样本量、完整月定义 |
| 哪些日期的成交量较大？ | V14 成交量柱图 | 数量单位 |
| 哪段时间用于训练和测试？ | V15 时间切分线 | 预先确定的切分日期 |
| 不同组的未来收益有何差异？ | V16 分组均值柱图 | 事先定义的分组与样本数 |
| 历史跌幅有多大？ | V17 回撤图 | 初始净值、无缺失收益 |
| 每小时发生多少事件？ | V18 事件计数柱图 | 采集区间、零事件与采集失败 |

## 本地运行

### Python 3.8 参考环境

```bash
git clone https://github.com/EnkiDoctor/timeseries-research-notebooks.git
cd timeseries-research-notebooks
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-py38.txt
python -m jupyterlab
```

Windows 的激活命令为 `.venv\Scripts\activate`；PowerShell 可运行 `.venv\Scripts\Activate.ps1`。
`requirements-py38.txt` 是练习用的固定版本组合，不代表任何现场机器的实际依赖版本。
如使用较新的 Python，可使用 `requirements.txt`。打开两本完成的 notebook 后，选择 **Restart Kernel → Run All**。
核心示例运行时不访问网络，不需要 API key，也无需下载真实行情。

### 验证和生成阅读版

```bash
python scripts/run_notebooks.py --check-recipes --html
```

该命令从干净 kernel 执行两本 notebook，再逐个检查“初始化＋单独模板”，结果写入忽略的 `artifacts/`。
维护者加上 `--write` 可更新已提交 notebook 的输出、`docs/` 阅读版与验证报告；随后运行 `python scripts/build_index.py` 更新目录。
生成脚本在 `scripts/build_01.py`、`scripts/build_02.py`，可视化小表和短代码在 `scripts/visualization_cases.py`；日常学习无需运行它们。重新生成会覆盖 notebook，请先保存自己的修改。

本地已验证两套环境：Python 3.8.20 / pandas 1.5.3 / NumPy 1.24.4 / Matplotlib 3.7.5，以及 Python 3.12.14 / pandas 2.2.3 / NumPy 2.3.5 / Matplotlib 3.11.2。
两本合计 92 个代码格从干净 kernel 执行，70 个模板逐个独立检查通过。详细记录见 [旧版环境报告](docs/validation.json) 与 [新版环境报告](docs/validation-modern.json)。

## 关键约定

- 默认一行是一个 `date × asset` 观测；真实问题也可以把 `asset` 换成设备、客户或产品。
- `ret` 是小数简单收益：`0.01` 表示 1%。价格、收益率、计数、流量、状态变量需要不同的清洗与聚合规则。
- `shift(1)` 指前一条观测；`rolling(20)` 指 20 条观测；它们不自动表示一个交易日或 20 个自然日。
- 缺失值不等于零。聚合时要检查**部分缺失**，不能只靠 `min_count=1`；交易日历也不能用普通工作日列表替代。
- 使用按发布时间的 backward as-of 连接；观察日期、发布时间、实际可用时间可能不同。
- 可视化可用于描述，不能自动证明因果关系、预测能力或策略收益。

## 数据、许可与使用范围

仓库中的默认数据和示例为原创合成数据，可在本仓库 MIT 许可下使用。数据生成与字段说明见 [data/README.md](data/README.md)。
额外提供 [French 行业收益下载脚本](scripts/download_french.py) 作为真实数据练习入口；下载文件保存在被忽略的 `data/downloads/`，第三方数据不适用本仓库 MIT 许可，使用前应阅读提供方条款与版本说明。

这是独立学习资料，不包含任何公司官方题目、评分标准或招聘文档。联网许可不必然涵盖预先准备的代码，使用时请遵守具体场景的规则。

API 的一手资料链接已附在 notebook 中；数据源另见 [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)。
