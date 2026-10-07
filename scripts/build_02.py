"""Build the Chinese scenario cookbook; generated notebook is committed for readers."""
from pathlib import Path
import textwrap
import nbformat as nbf
from visualization_cases import CASES

ROOT = Path(__file__).resolve().parents[1]
cells = []

def md(s):
    cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(s).strip()))

def code(s):
    cell = nbf.v4.new_code_cell(textwrap.dedent(s).strip())
    if s.strip().startswith("# SETUP"):
        cell.metadata["tags"] = ["setup"]
    cells.append(cell)

def recipe(tag, title, scenario, question, needs, snippet, interpretation, pitfalls):
    md("<a id='{0}'></a>\n## {0} · {1}\n\n**何时使用：** {2}\n\n**想回答的问题：** {3}\n\n**输入要求：** {4}\n\n下面一格可在运行本 notebook 的 setup 后独立复制执行；其他 recipe 之间没有运行顺序依赖。".format(tag, title, scenario, question, needs))
    code(snippet)
    cells[-1].metadata["recipe_id"] = tag
    cells[-1].metadata["tags"] = ["recipe:" + tag]
    md("**如何读结果：** {0}\n\n**常见误判：** {1}".format(interpretation, pitfalls))

md("""
# 02 · 时间序列数据处理与可视化：场景化代码模板

这份 notebook 面向有限时间内的探索性研究：先确认数据的含义、质量和时间，再选择能回答具体问题的图。包含 **12 个数据处理模板 + 18 个可视化模板**，每个模板都有实际输出、中文注释、适用情形与容易误判的地方。

**使用方法：** A 部分数据处理先运行下面的 setup，再选择 D 模板。**只想画图，直接跳到 [B 部分](#visualization)**：每个 V 案例先展示输入表，再给具体任务和短代码；只需 B 部分的 import 和自己的 `df`。V 案例互不依赖，也不读取 A 部分的大型合成面板。所有示例数据均为教学构造，并非真实市场表现。

**A 部分 D 模板接入真实数据时先做三件事（V 案例直接替换自己的 `df`）：**
1. 用你的数据替换 `demo_panel`，明确一行是「一个时间 × 一个对象」还是事件记录。
2. 对齐下面的数据契约；价格、收益、数量的单位必须自己确认。`asset` 不一定是金融资产，也可以是客户、机器或产品。
3. 对每个模板重新确认数据频率与信息可用时点。本例的 `252`、工作日历和月度复利都只是本例的约定。

本材料供面试前学习及在规则允许时查询。**允许上网不自动等于允许使用个人预写代码**；能否访问或复制本仓库以面试方规定为准。面试时不要使用 AI。

### 快速导航

| 数据处理 | 可视化：描述与质量 | 可视化：时序与关系 |
|---|---|---|
| [D01 审计](#D01) · [D02 类型与单位](#D02) | [V01 日收益折线](#V01) · [V02 归一化折线](#V02) | [V07 滚动波动](#V07) · [V08 滚动相关](#V08) |
| [D03 重复与冲突](#D03) · [D04 缺失与覆盖](#D04) | [V03 缺失热图](#V03) · [V04 缺失率](#V04) | [V09 相关矩阵](#V09) · [V10 滞后散点](#V10) |
| [D05 时间与日历](#D05) · [D06 收益与极值](#D06) | [V05 收益直方图](#V05) · [V06 大幅波动](#V06) | [V11 自相关](#V11) · [V12 星期箱线图](#V12) |
| [D07 历史特征](#D07) · [D08 训练集拟合](#D08) | [V15 训练测试切分](#V15) | [V13 月度收益热图](#V13) · [V14 成交量柱图](#V14) |
| [D09 Point-in-time 连接](#D09) · [D10 重采样](#D10) | [V18 小时事件数](#V18) | [V16 分组未来收益](#V16) · [V17 回撤](#V17) |
| [D11 未来标签与 purge](#D11) · [D12 事件聚合与连接](#D12) | | |

### 数据契约与时间约定

| 字段 | 类型/单位 | 含义及限制 |
|---|---|---|
| `date` | 无时区 datetime，日频 | 本例的模拟收盘日期；无真实交易所节假日 |
| `asset` | 字符串 | Alpha / Beta / Gamma / Delta，唯一键为 `(date, asset)` |
| `price` | 正数、任意计价单位 | 合成的收益累计指数，不是真实证券价格 |
| `ret` | 小数收益 | `0.01 = 1%`；本例第一条收益未知，保留 NaN |
| `volume` | 正数、模拟数量 | 仅供演示聚合与图表；不是可成交容量 |
| `regime` | 类别 | 已知的仿真阶段，真实预测时不可直接使用 |

所有日频预测模板约定：**在日期 t 收盘后使用 t 及以前的信息，预测 t+1 起的变化**。若需要在 t 收盘前交易，必须再推迟特征或改变成交假设。
""")

code("""
# SETUP 1/2：仅使用 numpy / pandas / matplotlib；建议从这一格开始运行。
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from IPython.display import display

plt.rcParams.update({
    "figure.figsize": (10, 4), "figure.dpi": 110,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.2,
    "axes.titlesize": 12, "axes.labelsize": 10,
    "font.size": 10, "legend.frameon": False,
})
COLORS = ["#2563eb", "#e07636", "#0f8a77", "#a351a7"]
SEED = 20261007
PERIODS_PER_YEAR = 252  # 仅适用于本例近似交易日频率，不可用于任意时间序列。
print("Python:", sys.version.split()[0])
print("pandas:", pd.__version__, "numpy:", np.__version__, "matplotlib:", matplotlib.__version__)
""")

code("""
# SETUP 2/2：900 个模拟工作日 × 4 个对象；固定种子使结果可重现。
rng = np.random.RandomState(SEED)
dates = pd.bdate_range("2020-01-02", periods=900)
assets = ["Alpha", "Beta", "Gamma", "Delta"]
n = len(dates)
phase = np.where(np.arange(n) < 300, "calm", np.where(np.arange(n) < 590, "stress", "recovery"))
# 波动簇：当期波动依赖上一期冲击；阶段差异只用于构建教学数据。
market = np.zeros(n)
variance = np.zeros(n)
variance[0] = 0.008 ** 2
z = rng.standard_t(df=7, size=n) / np.sqrt(7 / 5)
for t in range(1, n):
    base_vol = 0.007 if phase[t] == "calm" else (0.018 if phase[t] == "stress" else 0.010)
    variance[t] = 0.05 * base_vol ** 2 + 0.12 * market[t-1] ** 2 + 0.83 * variance[t-1]
    drift = -0.00035 if phase[t] == "stress" else 0.00035
    market[t] = drift + np.sqrt(variance[t]) * z[t]
parts = []
for j, asset in enumerate(assets):
    idio = rng.standard_t(8, n) * (0.003 + 0.001 * j)
    season = 0.0006 * np.sin(2 * np.pi * np.arange(n) / (50 + 10 * j))
    r = (0.7 + 0.15 * j) * market + idio + season + 0.0001 * (j-1)
    r = np.clip(r, -0.25, 0.25)  # 生成过程的约束；不是对实际研究收益的裁剪建议。
    p = 100 * np.cumprod(1 + r)
    vol = rng.lognormal(12 + 0.2 * j, 0.35, n) * (1 + 12 * np.abs(r))
    parts.append(pd.DataFrame({"date": dates, "asset": asset, "price": p,
                               "ret": pd.Series(p).pct_change(fill_method=None).values,
                               "volume": np.round(vol), "regime": phase}))
demo_panel = pd.concat(parts, ignore_index=True).sort_values(["asset", "date"]).reset_index(drop=True)
assert not demo_panel.duplicated(["date", "asset"]).any()
wide_ret = demo_panel.pivot(index="date", columns="asset", values="ret").sort_index()
wide_price = demo_panel.pivot(index="date", columns="asset", values="price").sort_index()
train_cutoff = dates[630]  # 只用于示范按时间切分；不是调参选出来的日期。

# 脏数据是专用副本，任何清洗都不会改写 demo_panel。
dirty_panel = demo_panel.copy()
dirty_panel = dirty_panel.loc[~((dirty_panel["asset"] == "Delta") & dirty_panel["date"].isin(dates[80:115]))].copy()
dirty_panel.loc[(dirty_panel["asset"] == "Beta") & dirty_panel["date"].isin(dates[420:440]), "price"] = np.nan
dirty_panel.loc[dirty_panel.index[::97], "volume"] = np.nan
dirty_panel.loc[(dirty_panel["asset"] == "Gamma") & (dirty_panel["date"] == dates[222]), "price"] = -5
# 人为记录错误：把某日价格写大 12 倍；原始 ret 因此不再与 price 一致。
dirty_panel.loc[(dirty_panel["asset"] == "Alpha") & (dirty_panel["date"] == dates[350]), "price"] *= 12
exact_duplicate = dirty_panel.iloc[[20]].copy()
conflicting_duplicate = dirty_panel.iloc[[50]].copy()
conflicting_duplicate["price"] *= 1.03
dirty_panel = pd.concat([dirty_panel, exact_duplicate, conflicting_duplicate], ignore_index=True)
dirty_panel = dirty_panel.sample(frac=1, random_state=SEED).reset_index(drop=True)

# 事件级示例：不同小时不同密度；这些是模拟观测，不是固定间隔价格。
ev_rng = np.random.RandomState(SEED + 1)
ev_times = []
for day in pd.bdate_range("2023-05-01", periods=12):
    for hour in range(9, 17):
        count = ev_rng.poisson(6 if hour in (9, 16) else 2)
        secs = np.sort(ev_rng.randint(0, 3600, size=count))
        ev_times.extend(day + pd.Timedelta(hours=hour) + pd.to_timedelta(secs, unit="s"))
events = pd.DataFrame({"timestamp": pd.DatetimeIndex(ev_times)})
events["value"] = 20 + 2 * np.sin(events["timestamp"].dt.hour / 24 * 2 * np.pi) + ev_rng.normal(0, 0.4, len(events))
events["quantity"] = ev_rng.randint(1, 30, len(events))
events["asset"] = "Alpha"

display(demo_panel.head(8))
display(pd.DataFrame({"rows": [len(demo_panel), len(dirty_panel)],
                      "assets": [demo_panel["asset"].nunique(), dirty_panel["asset"].nunique()]},
                     index=["clean synthetic", "dirty exercise"]))
print("日期范围:", dates.min().date(), "至", dates.max().date(), "| 训练切分:", train_cutoff.date())
""")

md("""
### A 部分真实数据接入：替换数据上下文

**不能只替换 `demo_panel` 一行变量。** 本例的 `wide_ret`、`wide_price`、`dates`、`assets`、`dirty_panel` 都是 setup 生成的缓存。这些变量属于 A 部分的数据上下文；B 部分可视化案例使用独立的 `df`，无需修改这里。下面是集中接入代码框；它不会自动执行外部文件。完成字段映射、日历确认与重复冲突处理后，把这整个代码框复制到新格执行，再运行需要的 recipe。

```python
# 先根据实际文件路径和列名调整；不要盲目假定 price/ret/volume 的含义。
raw = pd.read_csv("your_data.csv")
raw = raw.rename(columns={"your_time_column": "date", "your_id_column": "asset"})
raw["date"] = pd.to_datetime(raw["date"], errors="raise")
dirty_panel = raw.copy()  # D01–D06 审计原始版本。

# 此处替换为你按照来源规则确认后的结果；冲突处理不应只 keep='last'。
clean = raw.copy()
assert not clean[["date", "asset"]].isna().any().any()
assert not clean.duplicated(["date", "asset"]).any(), "先按 D03 处理重复/冲突"
demo_panel = clean.sort_values(["asset", "date"]).reset_index(drop=True)
assets = sorted(demo_panel["asset"].unique())

# expected_dates 必须由真正的交易/营业/传感器日历构造，并与 date 时区一致。
# 不可默认 pd.bdate_range 等价于真实交易日历。
dates = pd.DatetimeIndex(expected_dates).sort_values().unique()
assert demo_panel["date"].isin(dates).all(), "预期日历遗漏了已观测日期"
wide_price = demo_panel.pivot(index="date", columns="asset", values="price").reindex(index=dates, columns=assets)
wide_ret = demo_panel.pivot(index="date", columns="asset", values="ret").reindex(index=dates, columns=assets)
# 如果来源只有正的复权价格、且已确认要计算相邻日历格收益，可明确选择：
# wide_ret = wide_price.pct_change(fill_method=None)
# demo_panel = demo_panel.drop(columns=["ret"], errors="ignore").merge(
#     wide_ret.rename_axis(columns="asset").stack(dropna=False).rename("ret").reset_index(),
#     on=["date", "asset"], how="left", validate="one_to_one")

train_cutoff = pd.Timestamp("YOUR_PREDEFINED_CUTOFF")  # 替换为事先确定的日期及正确时区。
PERIODS_PER_YEAR = 252  # 按真实频率与年化约定改写；不要机械保留 252。
events = None  # 清空合成事件缓存；需要事件分析时另外读入你的 timestamp/value/quantity/asset 表。
```

**数据类型不同，要选择适用的场景：**
- 只有收益而没有价格：不要伪造原始价格；可跳过价格相关模板。若构造累计指数，明确它是收益累计指数。
- 利率、价差、温度等可能为零或负数的序列：通常应考虑差分，不应套用价格收益率或回撤公式。
- 没有真实成交量：跳过 D08 中 `log_volume`；B 部分 V14 成交量图同样需要真实数量列，或换成有意义的活动指标并改名。
- 不要把合成 `regime` 当作事先可知特征。B 部分 V15 只需要数值列和预先确定的切分日期。
- 没有事件表：跳过 D12 和 V18；V12 使用日收益，不需要事件表。
- 对象不叫 Alpha/Beta：每个 recipe 顶部的对象选择要改成真实 ID。横截面对象很多时，先按明确规则选少量展示对象。

每次换数据后，重新运行所选 recipe；不要把之前数据的输出当作新数据结果。
""")

md("""
## A · 数据处理

先问「这一行是什么、这个值何时可知」，再执行清洗。下列处理不是必须全部使用的流水线：缺失、极值和日历都需要按场景决定。每个模板都保留诊断输出，便于现场解释处理前后的差异。
""")

recipe("D01", "先审计：粒度、键、类型、覆盖与可疑值",
"刚拿到任何长表，还不知道质量和覆盖情况时。",
"一行到底表示什么？主键是否唯一？哪些对象或字段存在问题？",
"dirty_panel；真实数据先将配置字段替换为实际列名。不要未经检查就认定 (时间, 对象) 必须唯一。",
"""
# 候选唯一键只适用于“一对象每天一条记录”的粒度。
d01 = dirty_panel.copy()
key = ["date", "asset"]
field_audit = pd.DataFrame({"dtype": d01.dtypes.astype(str),
                            "missing_n": d01.isna().sum(),
                            "missing_pct": d01.isna().mean().mul(100).round(2),
                            "unique_n": d01.nunique(dropna=False)})
entity_audit = d01.groupby("asset").agg(
    rows=("date", "size"), first_date=("date", "min"), last_date=("date", "max"),
    unique_dates=("date", "nunique"), missing_price=("price", lambda s: s.isna().sum()),
    nonpositive_price=("price", lambda s: s.le(0).sum()))
print("shape:", d01.shape)
print("缺失键行数:", d01[key].isna().any(axis=1).sum())
print("涉及重复键的行数:", d01.duplicated(key, keep=False).sum())
print("数值列正负无穷个数:", np.isinf(d01.select_dtypes(include=np.number)).sum().to_dict())
display(field_audit)
display(entity_audit)
display(d01.loc[d01.duplicated(key, keep=False)].sort_values(key))
""",
"`rows` 与 `unique_dates` 不同提示重复键；Gamma 的非正价格、Beta 的缺失价格和 Delta 的缺少日期是不同问题，不能统一用 fillna 解决。`missing_pct` 的分母是已出现的行，因此未出现的整行需要 D04 另外统计。",
"`describe()` 不能替代键和覆盖审计；事件记录允许同一日有很多行。重复键是否错误必须先确认数据粒度。")

recipe("D02", "统一日期、数值和单位，同时保留解析失败记录",
"CSV 读入后出现 object 类型、千位分隔符、百分数、混合日期或错误字符串。",
"哪些值成功转换，哪些需要核对？收益到底是 1% 还是 100%？",
"包含字符串日期和数值的原始表。本例 date_raw 的格式由数据说明确认；不同格式应分支解析。",
"""
d02_raw = pd.DataFrame({"date_raw": ["2023-01-03", "2023-01-04", "bad-date", "2023-01-06"],
                       "asset_raw": [" Alpha ", "alpha", "BETA", "Beta"],
                       "price_raw": ["1,234.50", "1238.10", "N/A", "oops"],
                       "return_pct_raw": ["1.2", "-0.5", "", "2.0"]})
d02 = d02_raw.copy()
d02["date"] = pd.to_datetime(d02["date_raw"], format="%Y-%m-%d", errors="coerce")
# 统一大小写只有在业务确认 ID 大小写不敏感时才适用。
d02["asset"] = d02["asset_raw"].str.strip().str.upper()
d02["price"] = pd.to_numeric(d02["price_raw"].str.replace(",", "", regex=False), errors="coerce")
# 已由数据字典确认该列是“百分数”；显式除以 100，不根据数值大小猜单位。
d02["ret"] = pd.to_numeric(d02["return_pct_raw"], errors="coerce") / 100
invalid = d02[["date", "price"]].isna().any(axis=1)
display(d02)
display(d02.loc[invalid, ["date_raw", "price_raw", "date", "price"]])
print("需要核对的行数:", invalid.sum(), "| 不自动删除原始文本。")
""",
"NaT/NaN 是解析失败或原始缺失的标志，而不是清洗成功。原始列帮助查回输入。`return_pct_raw=1.2` 对应小数收益 0.012。",
"混合日/月顺序不能靠 `dayfirst` 猜；资产 ID 前导零、大小写可能有意义；欧洲数字格式 `1.234,50` 需要不同解析规则。")

recipe("D03", "完全重复与冲突重复分开处理",
"同一个 date/asset 多次出现，需要知道是重复导入还是价格冲突。",
"可以安全去除的完全重复有多少？冲突记录需要怎样隔离？",
"dirty_panel，且已确认一天一个对象只能有一条记录。",
"""
d03 = dirty_panel.copy()
exact_n = d03.duplicated().sum()
dedup_exact = d03.drop_duplicates().copy()  # 所有列完全相同才自动去重。
key = ["date", "asset"]
conflict_mask = dedup_exact.duplicated(key, keep=False)
conflicts = dedup_exact.loc[conflict_mask].sort_values(key)
# 没有可信版本号/发布时间时，不擅自 keep='last'；先隔离供核对。
usable = dedup_exact.loc[~conflict_mask].sort_values(["asset", "date"]).copy()
assert not usable.duplicated(key).any()
print("删除完全重复:", exact_n)
print("隔离冲突行:", len(conflicts), "| 暂可用行:", len(usable))
display(conflicts)
# 如有 revision_timestamp，可先确认修订在分析时点已公开，再按明确规则取版本。
""",
"本例包含一条完全重复导入和一个价格冲突的键。隔离冲突会暂时减少数据覆盖，因此下一步要记录缺口；拿到来源解释后再选择正确值。",
"`drop_duplicates(['date','asset'], keep='last')` 只按当前行顺序选择，打乱 CSV 后结果可能改变。最终修订值还可能造成历史回看偏差。")

recipe("D04", "缺失：区分缺整行、缺字段和真实零值",
"要比较覆盖率、构造完整面板、计算变化或决定是否填补。",
"对象在某个预期时点没有记录，还是有记录但值为空？缺失影响多少后续收益？",
"dirty_panel + 经过确认的 expected_dates。此处工作日只是模拟日历。",
"""
d04 = dirty_panel.drop_duplicates().copy()
d04 = d04.loc[~d04.duplicated(["date", "asset"], keep=False)].copy()
expected_dates = dates  # 真实数据应替换成合适的交易/营业/观测日历。
expected_grid = pd.MultiIndex.from_product([expected_dates, assets], names=["date", "asset"])
observed = d04.assign(row_present=True).set_index(["date", "asset"])
aligned = observed.reindex(expected_grid)
aligned["row_present"] = aligned["row_present"].fillna(False).astype(bool)
aligned["row_absent"] = ~aligned["row_present"]
aligned["price_missing_in_present_row"] = aligned["row_present"] & aligned["price"].isna()
coverage = aligned.groupby(level="asset").agg(
    expected_n=("row_present", "size"), observed_n=("row_present", "sum"),
    absent_rows=("row_absent", "sum"), null_price_rows=("price_missing_in_present_row", "sum"))
coverage["row_coverage_pct"] = 100 * coverage["observed_n"] / coverage["expected_n"]
# 缺失后收益保留 NaN；禁止 pct_change 隐式前向填充。
p = aligned["price"].unstack("asset")
r = p.pct_change(fill_method=None)
display(coverage.round(2))
display(pd.DataFrame({"missing_price": p.isna().sum(), "missing_return": r.isna().sum()}))
""",
"缺一天价格通常会使当天和下一天的单期收益都不可算。Delta 的缺整行和 Beta 的字段缺失应分别解释。收益 NaN 不能替换成 0，否则会人为压低波动并掩盖停报。",
"对象上市前/退市后的日期不应都计作缺失。本例对象全程存在；真实分母应按对象的有效存续区间和应有日历建立。只有在意义明确时才考虑有限前向填充协变量，同时保留缺失指示器和数据年龄。")

recipe("D05", "时区、夏令时与预期日历",
"跨地区事件、UTC 时间戳、日内聚合、夏令时切换或频率不齐。",
"两个时间是否代表同一时刻？交易日和自然日有没有混用？",
"带时区的事件时间，或已知原始地区的本地时间；不明确时区不能自行猜测。",
"""
# ISO 字符串明确携带 UTC 偏移，先统一到 UTC，再转成本地展示时区。
d05 = pd.DataFrame({"timestamp_raw": ["2023-03-10T14:30:00Z", "2023-03-13T13:30:00Z", "2023-11-06T14:30:00Z"]})
d05["utc"] = pd.to_datetime(d05["timestamp_raw"], utc=True)
d05["new_york"] = d05["utc"].dt.tz_convert("America/New_York")
# 夏令时前后 UTC 开盘小时会变，本地小时仍可相同。
d05["local_hour"] = d05["new_york"].dt.hour
display(d05)

# 原始无时区字符串必须已知地区；无法判定的夏令时重复/不存在时点显式标 NaT。
local_naive = pd.DatetimeIndex(["2023-11-05 01:30", "2023-03-12 02:30", "2023-03-13 09:30"])
localized = local_naive.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
display(pd.DataFrame({"naive": local_naive, "localized": localized}))

expected = pd.bdate_range("2023-05-01", "2023-05-10")
observed = expected.delete(3)
print("相对模拟工作日历的缺口:", expected.difference(observed).strftime("%Y-%m-%d").tolist())
""",
"本地 09:30 在夏令时前后对应不同 UTC 时间。`tz_localize` 为无时区时间指定原地区；`tz_convert` 为同一时刻更换显示地区。NaT 行需要来源规则帮助消除歧义。",
"`bdate_range` 只排除周末，不认识交易所节假日、半日市和停牌；不要给所有无时区时间直接加 UTC，也不要先删除时区再合并。")

recipe("D06", "从价格计算收益，检查极值与来源一致性",
"价格表要转成收益、单位可能出错、出现跳变或原始 ret 与 price 不一致。",
"变化是单期变化还是跨缺口累计变化？极值是市场事件还是记录问题？",
"正价格的资产序列；股票通常需适当复权。对利率/价差/可负值序列，改用差分等业务合理定义。",
"""
d06 = dirty_panel.drop_duplicates().copy()
d06 = d06.loc[~d06.duplicated(["date", "asset"], keep=False)].copy()
p = d06.pivot(index="date", columns="asset", values="price").reindex(dates)
p_valid = p.where(p.gt(0))  # 非正“价格”保留为缺失，并单独报告。
simple_ret = p_valid.pct_change(fill_method=None)
log_ret = np.log(p_valid).diff()
# 差异包括本例人为价格错误；真实情况下还可能是复权口径、费用、币种不同。
provided = d06.pivot(index="date", columns="asset", values="ret").reindex(dates)
diff = (simple_ret - provided).abs()
flags = pd.concat({"price": p.stack(), "computed_ret": simple_ret.stack(),
                   "provided_ret": provided.stack(), "abs_diff": diff.stack()}, axis=1)
flags.index.names = ["date", "asset"]
flags = flags.loc[flags["abs_diff"].gt(1e-8) | flags["price"].le(0)].sort_values("abs_diff", ascending=False)
display(flags.head(10))
print("单期收益缺失数:", simple_ret.isna().sum().to_dict())
print("log1p/simple 关系最大误差:", np.nanmax(np.abs(np.log1p(simple_ret) - log_ret)))
""",
"Alpha 的错误价格会影响跳入和跳出两天的收益。Gamma 的非正价格被标为不可计算，而不是擅自改成 0。简单收益跨期用连乘；对数收益可相加，但不能把二者直接互换。",
"异常不等于错误，不应看到大变化就删。未对齐预期日历时，相邻两条记录可能跨多个日历日；`pct_change` 计算的是相邻观测变化，不自动变成一天收益。")

recipe("D07", "lag / rolling：只使用预测时点之前的信息",
"构造短期历史变化、滚动波动、基线和历史标准分数。",
"特征用了哪些日期？窗口是否跨资产？当前观测能否在决策时已知？",
"demo_panel；已按 asset/date 排序。这里明确采用 t 收盘后的预测时点。",
"""
d07 = demo_panel.sort_values(["asset", "date"]).copy()
g = d07.groupby("asset", sort=False)
d07["ret_lag1"] = g["ret"].shift(1)
# t 收盘后可用的 20 日统计包括 ret_t；shift(1) 版本用于 t 收盘前。
d07["vol20_at_close"] = g["ret"].transform(lambda s: s.rolling(20, min_periods=20).std(ddof=1))
d07["mean20_before_close"] = g["ret"].transform(lambda s: s.shift(1).rolling(20, min_periods=20).mean())
d07["momentum5_at_close"] = g["price"].pct_change(periods=5, fill_method=None)
# 不使用 center=True；窗口前方的缺失保留，不用未来数据填满。
display(d07.loc[d07["asset"].eq("Alpha"), ["date", "ret", "ret_lag1", "vol20_at_close", "mean20_before_close", "momentum5_at_close"]].iloc[18:25])
check = d07.loc[d07["asset"].eq("Alpha")].reset_index(drop=True)
assert np.isclose(check.loc[25, "mean20_before_close"], check.loc[5:24, "ret"].mean())
print("手工核对通过：第 25 行的盘前均值只使用第 5–24 行。")
""",
"窗口启动时 NaN 是历史不足的正常结果。`transform` 返回与原表对齐的一列。同一天收盘后可以知道当日收盘收益，但还不能假设以该收盘价完成响应交易。",
"`rolling(20)` 是 20 条观测，`rolling('20D')` 是 20 个自然日，含义不同。直接对拼接长表 rolling 会串对象；`center=True`、负数 shift 用作特征会引入未来。")

recipe("D08", "填补、裁剪和标准化：只在训练期学习参数",
"需要准备机器学习输入，或希望降低明显极端特征对模型的影响。",
"测试期有没有参与中位数、分位数、均值和方差的估计？",
"demo_panel 的历史特征 + train_cutoff。示范裁剪特征，不裁剪用于绩效评估的目标收益。",
"""
d08 = demo_panel.sort_values(["asset", "date"]).copy()
d08["lag1"] = d08.groupby("asset")["ret"].shift(1)
d08["vol20"] = d08.groupby("asset")["ret"].transform(lambda s: s.rolling(20, min_periods=20).std())
d08["log_volume"] = np.log1p(d08["volume"])
features = ["lag1", "vol20", "log_volume"]
X = d08[features].replace([np.inf, -np.inf], np.nan)
train_mask = d08["date"].lt(train_cutoff)
# 每项参数只用训练行估计，再原封不动应用至测试行。
train_X = X.loc[train_mask]
low, high = train_X.quantile(0.01), train_X.quantile(0.99)
clipped = X.clip(lower=low, upper=high, axis=1)
median = clipped.loc[train_mask].median()
if median.isna().any():
    raise ValueError("某个特征在训练集全缺失；先决定删除还是使用业务指定常数。")
filled = clipped.fillna(median)
mu = filled.loc[train_mask].mean()
sigma = filled.loc[train_mask].std(ddof=0).replace(0, 1)
scaled = (filled - mu) / sigma
missing_indicators = X.isna().astype(int).add_suffix("_missing")
prepared = pd.concat([d08[["date", "asset"]], scaled, missing_indicators], axis=1)
display(pd.DataFrame({"clip_low": low, "clip_high": high, "fill_median": median, "train_mean": mu, "train_std": sigma}))
display(prepared.iloc[[0, 25, 700]])
print("训练标准化均值:", scaled.loc[train_mask].mean().round(8).to_dict())
""",
"训练数据标准化后的均值接近 0；测试数据不必接近 0，因为分布可能发生变化。缺失指示器保留了填补发生的事实，便于检查缺失本身是否与目标有关。",
"窗口刚启动造成的缺失可直接排除，而不是一定填补；标准化并不能修复泄漏。每次滚动验证需要重新拟合这些参数。固定训练区间的示例不能直接当成逐日 walk-forward。")

recipe("D09", "Point-in-time asof：按发布时刻对齐外部信息",
"财务、宏观、评级或传感器汇总发布晚于其统计期间，需要用于历史预测。",
"当时究竟已公开哪一条信息？数据有没有过期？",
"决策表 decision_time 与发布表 available_at 必须在同一时区；stat_period 不是可用时刻。",
"""
d09_decisions = pd.DataFrame({"asset": ["Alpha"] * 5 + ["Beta"] * 5,
    "decision_time": list(pd.date_range("2023-04-03 16:00", periods=5, freq="D", tz="UTC")) * 2})
d09_releases = pd.DataFrame({"asset": ["Alpha", "Alpha", "Beta"],
    "stat_period": ["2023-03", "2023-03", "2023-03"],
    "available_at": pd.to_datetime(["2023-04-03 17:00Z", "2023-04-06 12:00Z", "2023-04-02 10:00Z"], utc=True),
    "published_value": [1.2, 1.3, 0.7]})
# pandas 要求连接时间键全局排序；不要只按 asset 优先排序。
d09_joined = pd.merge_asof(
    d09_decisions.sort_values("decision_time"), d09_releases.sort_values("available_at"),
    by="asset", left_on="decision_time", right_on="available_at",
    direction="backward", tolerance=pd.Timedelta("3D"), allow_exact_matches=True)
d09_joined["age_hours"] = (d09_joined["decision_time"] - d09_joined["available_at"]).dt.total_seconds() / 3600
assert (d09_joined["available_at"].dropna() <= d09_joined.loc[d09_joined["available_at"].notna(), "decision_time"]).all()
display(d09_joined.sort_values(["asset", "decision_time"]))
""",
"Alpha 在 4 月 3 日 16:00 还看不到 17:00 发布的数值；4 月 6 日发布后才可使用修订值。Beta 的旧值超过 3 天容忍期后变成缺失，显示数据年龄的意义。",
"`direction='nearest'` 可能匹配未来发布；用报告期连接也会泄漏。若发布与决策同一时间还需要处理延迟，应改为不允许精确匹配或增加可用延迟。只提供最终修订历史的来源无法还原真正 point-in-time 数据。")

recipe("D10", "重采样：收益复利、数量求和、水平取期末",
"日频变月频、事件变小时频；不同字段不能全部取平均。",
"月末标签表示哪段数据？缺失或半个月会不会被误认为完整月份？",
"wide_ret / wide_price 与明确的模拟工作日历。月频用 MonthEnd 对象兼容旧 pandas。",
"""
d10_r = wide_ret["Alpha"]
d10_p = wide_price["Alpha"]
rule = pd.offsets.MonthEnd()
monthly_return = d10_r.resample(rule, label="right", closed="right").apply(
    lambda s: (1 + s).prod(min_count=1) - 1)
observed_n = d10_r.resample(rule).count()
# 使用完整月的模拟工作日日历建立分母，能识别数据头尾的半个月。
full_calendar = pd.bdate_range(d10_r.index.min().to_period("M").start_time,
                              d10_r.index.max().to_period("M").end_time.normalize())
expected_n = pd.Series(1, index=full_calendar).resample(rule).sum()
monthly = pd.DataFrame({"raw_compound_return": monthly_return, "observed_n": observed_n,
                        "expected_n": expected_n, "last_price": d10_p.resample(rule).last()})
monthly["complete"] = monthly["observed_n"].eq(monthly["expected_n"])
monthly["complete_month_return"] = monthly["raw_compound_return"].where(monthly["complete"])
display(monthly.head(3))
display(monthly.tail(3))
print("保留的完整月:", monthly["complete"].sum(), "/", len(monthly))
""",
"头月少了首条收益，末月尚未结束，因此不能和完整月份直接比较。本例月收益表示落入该月的日收益复利。数量通常求和、水平通常取期末、利率可能取平均，必须按变量意义决定。",
"`sum(ret)` 是近似，不是简单收益的精确复利；`prod()` 默认跳过 NaN，必须同时检查有效计数。月末日期标签不表示可在整个月开始时知道该值。真实交易所日历不能用工作日替代。")

recipe("D11", "未来目标与跨边界标签：显式记录 label_end",
"预测未来 H 个观测期的变化，需要划分训练和测试。",
"一条训练样本的目标是否跨进了测试期？预测期内缺失是否破坏了目标定义？",
"wide_price / wide_ret，H=5 个模拟工作日；本模板按 t 收盘后的信息构造特征。",
"""
h = 5
p = wide_price["Alpha"]
r = wide_ret["Alpha"]
d11 = pd.DataFrame(index=p.index)
d11["momentum20"] = p.pct_change(20, fill_method=None)
d11["target_h"] = p.shift(-h) / p - 1
# 需要未来每一期收益都有观测，避免只用端点掩盖路径缺失。
future_count = r.notna().astype(int).rolling(h, min_periods=h).sum().shift(-h)
d11["target_h"] = d11["target_h"].where(future_count.eq(h))
d11["label_end"] = pd.Series(d11.index, index=d11.index).shift(-h)
valid = d11[["momentum20", "target_h"]].notna().all(axis=1)
nominal_train = (d11.index < train_cutoff) & valid
# 所有训练标签必须在测试开始之前结束；这叫边界 purge。
train = nominal_train & d11["label_end"].lt(train_cutoff)
test = (d11.index >= train_cutoff) & valid
purged = nominal_train & ~train
assert d11.loc[train, "label_end"].max() < d11.loc[test].index.min()
d11["split"] = np.where(train, "train", np.where(test, "test", np.where(purged, "purged", "unavailable")))
display(d11.loc[train_cutoff - pd.Timedelta(days=12):train_cutoff + pd.Timedelta(days=4)])
print("样本数:", d11["split"].value_counts().to_dict())
""",
"切分前最后 H 个观测的目标会跨入测试期，因而被 purge。样本末尾 H 行不可用于本样本内评估，因为未来目标尚未完整出现。",
"purge 不会让重叠的 H 期标签彼此独立；普通独立样本标准误仍可能失真。H 表示观测期而非自然日，随机切分会破坏未来预测情景。")

recipe("D12", "事件聚合与日频连接：控制行数、分母与未知零值",
"一张表是事件记录，另一张表是每天一条的主表，需要生成日频特征。",
"事件统计是否扩大了主表行数？没有事件与采集故障是否被混为零？",
"events 与 demo_panel；此例模拟时间均无时区。真实数据先统一时区并定义所属交易日。",
"""
d12_ev = events.copy()
d12_ev["date"] = d12_ev["timestamp"].dt.normalize()
# 加权均值的分子、分母必须使用同一批有效观测。
valid_pair = np.isfinite(d12_ev["value"]) & np.isfinite(d12_ev["quantity"]) & d12_ev["quantity"].gt(0)
d12_ev["weighted_value"] = (d12_ev["value"] * d12_ev["quantity"]).where(valid_pair)
d12_ev["weighted_quantity"] = d12_ev["quantity"].where(valid_pair)
d12_ev["valid_weighted_row"] = valid_pair.astype(int)
print("不参与加权均值的事件数:", (~valid_pair).sum())
daily_events = d12_ev.groupby(["date", "asset"], as_index=False).agg(
    event_count=("value", "size"), quantity=("quantity", lambda s: s.sum(min_count=1)),
    weighted_sum=("weighted_value", lambda s: s.sum(min_count=1)),
    weighted_quantity=("weighted_quantity", lambda s: s.sum(min_count=1)),
    valid_weighted_count=("valid_weighted_row", "sum"), last_event=("timestamp", "max"))
daily_events["weighted_mean"] = daily_events["weighted_sum"] / daily_events["weighted_quantity"].where(daily_events["weighted_quantity"].gt(0))
# 本例明确假定统计窗口 17:00 结束、采集处理延迟 5 分钟；实际按来源规则改写。
daily_events["available_at"] = daily_events["date"] + pd.Timedelta(hours=17, minutes=5)
assert daily_events["last_event"].lt(daily_events["available_at"]).all()
base = demo_panel.loc[demo_panel["asset"].eq("Alpha") & demo_panel["date"].between("2023-05-01", "2023-05-19"), ["date", "asset", "ret"]]
joined = base.merge(daily_events, on=["date", "asset"], how="left", validate="one_to_one", indicator=True)
assert len(joined) == len(base)
display(joined[["date", "event_count", "valid_weighted_count", "quantity", "weighted_mean", "available_at", "_merge"]])
# 只有已确认全天采集正常而确实无事件时，event_count 才可以填 0。
# 在最后一条事件出现时还不知道它是最后一条；要等窗口结束且采集/发布完成。
# 本次日连接用于审计，不能把 available_at 晚于决策时刻的统计用于预测。
""",
"连接指示器 `_merge` 帮助区分成功匹配和未匹配日期。数量加权平均的分子和分母使用相同有效行，分母必须大于 0；有效计数便于发现被排除的事件。主表行数不变是避免重复连接造成隐性加权的基本检查。",
"把尚未发生的全天事件统计接到当天开盘预测会泄漏；同一天缺少事件既可能是零次发生，也可能是采集失败，需要额外的采集状态数据。")

md("""
<a id="visualization"></a>
## B · 可视化：输入表 → 要做什么 → 代码 → 图形结果

**只想画图，可以直接从这里开始。** 本节不需要运行上面的合成数据生成器。

1. 运行下面的 import。
2. 找到一个案例，先看它完整展示的输入表 `df`，再看“要做什么”。
3. 已有自己的 `df`：对齐列名与单位，跳过“示例建表”，直接复制“绘图代码”。
4. 没有自己的数据：先运行这个案例的“示例建表”，再运行“绘图代码”。每个案例都独立建表，不需要运行前一个案例。

每个案例只画一张图，统一使用 `plt.figure()`、`plt.plot()`、`plt.title()` 等写法。表里的收益是**小数**，例如 `0.01` 表示 `1%`；图上乘以 100 后显示百分数。`NaN` 表示缺失。

这些 8–10 行小表用于看懂输入与代码，不用于判断市场规律。换成真实数据时，确认日期、单位、缺失与样本量；日期轴和图题使用英文，避免环境缺少中文字体。
""")
code("""
# SETUP：可视化只需这些导入；不依赖 A 部分的数据变量。
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

plt.rcdefaults()  # 重置前文样式，让单独运行本节也能得到相同图形。
""")
cells[-1].metadata["tags"] = ["setup", "visualization_setup"]
cells[-1]["id"] = "visualization-imports"


def simple_visualization(case):
    """The displayed table and executable fixture have a single data source."""
    tag = case["id"]
    table = ["| " + " | ".join(case["columns"]) + " |",
             "| " + " | ".join(["---"] * len(case["columns"])) + " |"]
    for row in case["rows"]:
        table.append("| " + " | ".join("NaN" if v is None else str(v) for v in row) + " |")
    md("<a id='{0}'></a>\n## {0} · {1}\n\n**输入表：`df`（展示全部 {2} 行）**\n\n{3}\n\n{4}\n\n**要做什么：** {5}\n\n**代码：** 第一个代码格只生成上面的示例表；已有自己的同列名 `df` 时跳过它，直接复制第二个绘图格。".format(
        tag, case["title"], len(case["rows"]), "\n".join(table), case["dtypes_note"], case["task"]))
    cells[-1]["id"] = tag.lower() + "-input-and-task"
    fixture = "# 示例建表：已有自己的 df 时跳过这一格。\ndf = pd.DataFrame([\n"
    fixture += "\n".join("    " + repr(row) + "," for row in case["rows"])
    fixture += "\n], columns=" + repr(case["columns"]) + ")"
    code(fixture)
    cells[-1].metadata.update({"recipe_id": tag, "tags": ["recipe:" + tag, "example_data"]})
    cells[-1]["id"] = tag.lower() + "-example-data"
    code("# 绘图代码：输入为上面格式的 df，可直接替换成你的表。\n" + case["plot"])
    cells[-1].metadata.update({"recipe_id": tag, "tags": ["recipe:" + tag, "plot"]})
    cells[-1]["id"] = tag.lower() + "-plot"
    md("**图怎么读：** " + case["reading"] + "\n\n**换数据时注意：** " + case["tip"])
    cells[-1]["id"] = tag.lower() + "-reading"


for case in CASES:
    simple_visualization(case)

md("""
### 怎么套到自己的数据

只需要把表名、列名和单位对应上。例如 V01 需要 `date` 和 `ret`：

```python
df = my_data.rename(columns={"timestamp": "date", "return": "ret"}).copy()
# 确认 ret 是小数收益，再复制 V01 的绘图格。
```

一次选择一个案例；不需要把 18 个案例连成一条流程。V03 的日期应先按预期日历补齐，V13 的输入已经是完整月收益，V16 的分组规则已经事先固定。相关的数据处理可查前面的 D 模板。

### 官方参考

- [pandas 1.5 时间序列](https://pandas.pydata.org/pandas-docs/version/1.5/user_guide/timeseries.html)
- [pandas 1.5 窗口计算](https://pandas.pydata.org/pandas-docs/version/1.5/user_guide/window.html)
- [Matplotlib 3.7 pyplot 教程](https://matplotlib.org/3.7.5/tutorials/introductory/pyplot.html)

图形用于描述数据和提出问题；不能仅凭示例图推断因果、稳定预测能力或可盈利策略。建模与回测预留在第三本 notebook。
""")

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.8.7"},
    "title": "时间序列数据处理与可视化：场景化代码模板",
}
nbf.validate(nb)
out = ROOT / "notebooks" / "02_time_series_processing_visualization.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, out)
print("Wrote", out, "cells=", len(cells))
