# 环境兼容与排错

目标是让模板使用 Python 3.8 可用语法和 pandas 1.5 常见 API。仓库的验证报告记录实际运行版本，**Python 3.8.20 的验证不等于已经在 3.8.7 或某个未知现场镜像中验证**。

拿到环境先运行：

```python
import sys
import numpy as np
import pandas as pd
import matplotlib
print(sys.version)
print('numpy:', np.__version__)
print('pandas:', pd.__version__)
print('matplotlib:', matplotlib.__version__)
```

| 常见差异 | 本仓库的做法 |
|---|---|
| 新版月末别名 `ME` 在旧 pandas 中不可用 | 使用 `pd.offsets.MonthEnd()` |
| `pct_change` 的缺失填充默认行为可能变动 | 显式指定 `fill_method=None`，先确认观测日历 |
| 分类型分组 `observed` 默认值可能变化 | 关键分组显式设置 `observed=True` |
| 日期混合格式在不同版本的推断不同 | 尽量写具体 `format`，多格式分别解析，不依赖 `format='mixed'` |
| Python 3.8 不支持较新的类型标注语法 | 模板不依赖 `list[str]`、`X | None` 或 `match` |
| `DataFrame.append` 在新 pandas 已删除 | 使用 `pd.concat` |
| 链式赋值和 Copy-on-Write 的差异 | 使用 `.loc[mask, column] = value` 与 `.copy()` |
| `merge_asof` 报 `keys must be sorted` | 优先按连接时间全局升序，再加分组列；两边分别检查 |
| 中文字体缺失 | 图内用英文标签，中文说明在 Markdown 与代码注释中 |

01–03 使用 NumPy、pandas、Matplotlib、IPython；部分相关性计算需要 SciPy。04 增加 scikit-learn，M10 可选使用 XGBoost。Excel/Parquet 是可选读写示例，不是默认运行依赖。
不依赖 seaborn、statsmodels、行情 API、在线 notebook 服务、GPU 或深度学习框架。

## 机器学习版本

| 环境 | scikit-learn | 可选 XGBoost |
|---|---|---|
| Python 3.8.20 | 1.3.2 | 2.0.3 |
| Python 3.12.14 | 1.7.2 | 3.1.3 |

XGBoost 单独安装：旧版用 `requirements-xgboost-py38.txt`，现代版用 `requirements-xgboost.txt`，先装基础 requirements。
macOS 新版 XGBoost 可能不带 OpenMP 动态库；若出现 `libomp.dylib` 加载错误，需要安装/配置该运行库，例如在已使用 Homebrew 的环境中执行 `brew install libomp`。本次现代环境验证进程使用已有 scikit-learn 包内的 OpenMP 库，未修改系统库。普通 notebook 加载失败时会明确跳过 M10；`--require-optional` 模式要求它实际训练，CI 使用此模式。

本册用 `np.sqrt(mean_squared_error(...))` 避免 RMSE 参数版本差异。`OneHotEncoder(sparse_output=False)` 需要 sklearn≥1.2，更老版本可改用 `sparse=False`。XGBoost 的 `early_stopping_rounds` 放在构造器，而不是传入 `fit`。

如果出现报错，先查看 traceback 的最后一行、输入 `shape/dtypes/head`、索引与字段名称，再查当前版本文档。不建议在限时环境中首先升级整个环境。

本地固定依赖：`requirements-py38.txt`。较新 Python：`requirements.txt`。
实际验证：[`validation.json`](validation.json)。CI 从干净环境执行，并同时检验模板能否独立复制运行。

另有 [Python 3.12 / pandas 2.2 验证记录](validation-modern.json)。旧版和新版均执行了全部 122 个独立模板及变体（含 18 个回测和16个机器学习案例），M10 在两套环境均实际训练；实际现场版本仍需当场确认。

来源：[pandas 1.5 文档](https://pandas.pydata.org/pandas-docs/version/1.5/)、[Matplotlib 3.7.5 依赖](https://matplotlib.org/3.7.5/devel/dependencies.html)。
