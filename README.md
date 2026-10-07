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

每张图都附有“何时用、输入是什么、如何读、容易误判什么”，完整预览见 [图表目录](docs/GALLERY.md)。

| 缺失热图：找成片缺口 | 相关矩阵：同时检查样本量 |
|---|---|
| ![V03 缺失热图](docs/images/02-v03-1.png) | ![V09 相关系数与有效样本数](docs/images/02-v09-1.png) |
| 月度热图：屏蔽不完整月份 | 时序诊断：变化与绝对变化的自相关 |
| ![V13 月度收益热图](docs/images/02-v13-1.png) | ![V11 自相关](docs/images/02-v11-1.png) |

## 怎么复制最省时间

1. 找到符合问题的模板，先读它的**使用场景、输入要求和常见误判**。
2. 复制 notebook 开头标记为 `setup` 的初始化代码，再复制该模板的完整代码格。每个模板经过独立执行检查，不依赖之前的其他模板结果。
3. 第一本多数模板自带微型例子；将示例表替换成自己的数据。第二本共享一份合成面板，按接入指南替换入口与列名。
4. 检查日期、唯一键、单位、可用时间和样本量，再解读结果。保留模板里的断言，按真实数据合同调整，不能仅为消除报错而删除。
5. 对于预测研究，先保留未来测试区间；EDA、参数和阈值选择应在开发区间内完成。

这里的图表全部来自可复现的合成示例，**不代表真实市场规律或可盈利策略**。中文说明与注释解释用途，图内使用英文标签以避免运行环境缺少中文字体。

## 按问题选择图表

| 你想回答的问题 | 合适的图 | 同时要报告什么 |
|---|---|---|
| 哪段时间或哪个资产缺数据？ | 缺失热图、覆盖率曲线 | 预期日历、缺整行还是缺字段 |
| 不同量纲的序列走势是否类似？ | 小多图、共同起点归一化曲线 | 起始日期、原始单位、归一化方法 |
| 尾部有多重，极端值在哪？ | 直方图、ECDF、分位数表、异常时间标记 | 样本量、分位数、异常保留/剔除理由 |
| 波动或关系是否随时间改变？ | 滚动波动、滚动相关、分段图 | 窗口与最小观测数、时间段 |
| 哪些序列共同变化？ | 收益相关矩阵＋有效样本数 | 成对缺失、共同市场暴露 |
| 是否有滞后或周期结构？ | lag scatter、ACF、星期/小时箱线图 | 等间隔假设、时区、样本依赖 |
| 信号与未来结果是否相关？ | 共同样本散点、hexbin、训练集分箱图 | 标签实现时点、每箱样本量、样本外区分 |
| 历史损失路径如何？ | 净值和回撤图 | 初始净值、缺失收益、真实可交易性 |

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
生成脚本在 `scripts/build_01.py`、`scripts/build_02.py`，日常学习无需运行它们。重新生成会覆盖 notebook，请先保存自己的修改。

本地已验证两套环境：Python 3.8.20 / pandas 1.5.3 / NumPy 1.24.4 / Matplotlib 3.7.5，以及 Python 3.12.14 / pandas 2.2.3 / NumPy 2.3.5 / Matplotlib 3.11.2。
两本合计 73 个代码格从干净 kernel 执行，70 个模板逐个独立检查通过。详细记录见 [旧版环境报告](docs/validation.json) 与 [新版环境报告](docs/validation-modern.json)。

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
