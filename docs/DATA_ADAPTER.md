# 把自己的数据接到模板

不要因为模板使用 `price`、`ret` 就把所有时间序列强行转成金融收益。一行可能是日汇总、一次成交或一次传感器采样，先确认业务含义。

## 1. 最小数据合同

| 字段 | 含义 | 必须确认 |
|---|---|---|
| `date` | 观测时间或区间结束时间 | 格式、时区、频率、区间标签 |
| `asset` | 资产/设备/产品/其他实体 | 唯一键通常是 `date, asset` |
| `price` / `value` | 数值水平 | 单位、是否应为正、是否有重置/拆股 |
| `ret` | 相邻有效会话的简单收益 | 已是小数还是百分数，是否跨缺失区间 |
| `volume` | 区间内流量/交易量 | 求和还是末值，负值有无含义 |
| `available_at` | 实际可用时间 | 不能直接用报表所属期代替发布时间 |

第一本模板通常使用局部微型例子，直接替换对应 `DataFrame` 即可。第二本初始化单元给出 `demo_panel`、`dirty_panel`、`wide_ret`、`wide_price`、`dates`、`assets`、`train_cutoff` 和独立事件表 `events`。
替换数据时必须同步这些变量，不能只改 `demo_panel` 而让部分图继续读取合成数据的宽表缓存。第二本 setup 后的“集中替换数据入口”给出完整接入代码。

## 2. 长表入口示例

```python
from pathlib import Path
import numpy as np
import pandas as pd

# 只修改路径、列名映射与日期格式；这不是无需检查的自动清洗器。
path = Path('data/local/my_data.csv')
raw = pd.read_csv(path)
x = raw.rename(columns={'timestamp': 'date', 'ticker': 'asset', 'close': 'price'}).copy()
x['date'] = pd.to_datetime(x['date'], format='%Y-%m-%d', errors='coerce')
x['price'] = pd.to_numeric(x['price'], errors='coerce')
assert x[['date', 'asset']].notna().all().all(), '无效键应先隔离调查'
assert not x.duplicated(['date', 'asset']).any(), '重复键应先确认修订或多事件语义'
x = x.sort_values(['asset', 'date']).reset_index(drop=True)

# 只有已确认相邻行表示所需收益区间时，这才是相应区间的收益。
x['ret'] = x.groupby('asset', observed=True)['price'].pct_change(fill_method=None)
```

如果输入已经是收益率，直接保留并统一单位，不再调用 `pct_change()`。若只有单序列，可显式添加 `asset='series_1'`。若数据是计数/负数可出现的业务指标，优先用差分、增长率或保留水平，并说明分母为零的处理。

对于具有相应字段的日频面板，同步缓存的基本形式为：

```python
demo_panel = x.copy()
dirty_panel = x.copy()  # 仅用于审计自己的数据，不重新注入合成错误。
assets = sorted(demo_panel['asset'].dropna().unique())
wide_ret = demo_panel.pivot(index='date', columns='asset', values='ret').sort_index()
wide_price = demo_panel.pivot(index='date', columns='asset', values='price').sort_index()
# dates 必须来自已确认的预期会话/采样日历；不能从观测的并集推断所有缺整行。
dates = pd.DatetimeIndex(expected_dates)
train_cutoff = pd.Timestamp('2024-01-01')  # 按任务设定，不复制合成数据的边界。
events = pd.DataFrame(columns=['timestamp', 'asset', 'value', 'quantity'])
```

没有事件数据时跳过事件模板，不能继续使用 setup 的模拟事件。没有价格、成交量或阶段标签时，跳过相应图表；不要为了匹配示例而伪造字段。

## 3. 宽表入口示例

```python
# wide.index 是日期，wide.columns 是实体。
long = (wide.rename_axis('date').reset_index()
        .melt(id_vars='date', var_name='asset', value_name='value'))
```

缺失宽表单元与长表缺行不是同一件事。先建立真正的预期会话/采样时间，再区分上市前、休市、停牌、故障与字段缺失。

## 4. 选择开发区间

如果后续目的是预测，先按实际任务冻结未来区间，例如：

```python
development = x.loc[x['date'] < '2024-01-01'].copy()
holdout = x.loc[x['date'] >= '2024-01-01'].copy()
```

先将 EDA 模板接到 `development`。涉及未来标签时，还需检查标签实现日期是否跨越边界；仅按特征日期切分不够。
模板内的合成 `regime` 或已知异常标记用于说明生成过程，不是从历史数据提前可知的预测特征。

## 5. 保存结论

每个图表至少附上：使用的区间、实体数、有效样本数、单位、处理规则，以及一句观察和一个替代解释。
不要仅因模板图形好看就复制结论；真实数据的观察可能与合成示例完全相反。
