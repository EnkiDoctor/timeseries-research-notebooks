"""Small input tables and direct pyplot recipes for Notebook 02."""

CASES = [
    {
        "id": "V01",
        "title": "日收益：看收益随时间怎样变化",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", 0.010], ["2024-01-03", -0.015],
            ["2024-01-04", 0.006], ["2024-01-05", 0.022],
            ["2024-01-08", -0.008], ["2024-01-09", 0.004],
            ["2024-01-10", -0.025], ["2024-01-11", 0.012],
        ],
        "dtypes_note": "date 是交易日期；ret 是当天收益率，用小数表示，0.01 就是 1%。每个日期一行。",
        "task": "画出日收益折线，并画一条 0% 水平线，观察正负收益与大幅波动出现在哪天。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")  # 折线必须按时间连接

plt.figure(figsize=(10, 4))
plt.plot(df["date"], df["ret"] * 100, marker="o")  # 小数转百分数
plt.axhline(0, color="grey", linewidth=0.8)
plt.title("Daily return")
plt.xlabel("Date")
plt.ylabel("Return (%)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "1 月 5 日收益为 +2.2%，1 月 10 日为 -2.5%；水平线帮助区分上涨和下跌。",
        "tip": "收益已有百分数数值（例如 1 表示 1%）时，不要再乘以 100。",
    },
    {
        "id": "V02",
        "title": "两只资产：从相同起点比较价格变化",
        "columns": ["date", "asset_a", "asset_b"],
        "rows": [
            ["2024-01-02", 100, 50], ["2024-01-03", 102, 49],
            ["2024-01-04", 101, 51], ["2024-01-05", 104, 52],
            ["2024-01-08", 103, 53], ["2024-01-09", 106, 52],
            ["2024-01-10", 108, 54], ["2024-01-11", 110, 53],
        ],
        "dtypes_note": "date 是共同交易日期；asset_a、asset_b 是两只资产的正价格；这个模板要求两列日期对齐且没有缺失值。",
        "task": "把两只资产第一天的价格都设为 100，放在同一张折线图里比较区间表现。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
prices = df.set_index("date")[["asset_a", "asset_b"]]
rebased = prices / prices.iloc[0] * 100  # 用同一个起始日期

plt.figure(figsize=(10, 4))
plt.plot(rebased.index, rebased["asset_a"], label="Asset A")
plt.plot(rebased.index, rebased["asset_b"], label="Asset B")
plt.title("Prices rebased to 100")
plt.xlabel("Date")
plt.ylabel("Rebased price")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "最后一天 A 为 110、B 为 106，表示相对共同起点，价格分别上涨 10% 和 6%。",
        "tip": "比较投资表现时优先使用口径一致的复权价格；本例价格变化不包含手续费。",
    },
    {
        "id": "V03",
        "title": "缺失热图：看哪些日期、哪些列缺数据",
        "columns": ["date", "A", "B", "C"],
        "rows": [
            ["2024-01-02", 100, 50, 80], ["2024-01-03", 101, None, 81],
            ["2024-01-04", 102, None, 82], ["2024-01-05", None, 52, 83],
            ["2024-01-08", 104, 53, None], ["2024-01-09", 105, 54, None],
            ["2024-01-10", 106, 55, None], ["2024-01-11", 107, 56, 87],
        ],
        "dtypes_note": "date 按预期交易日每天一行；A、B、C 是待检查的数值列；空白表示缺失。整日缺数据也必须保留那一行。",
        "task": "用热图标出缺失位置：每一行是一个日期，每一列是一个字段，黄色代表缺失。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
values = df.set_index("date")[["A", "B", "C"]]

plt.figure(figsize=(7, 5))
plt.imshow(values.isna(), aspect="auto", cmap="viridis", vmin=0, vmax=1)
plt.xticks(range(len(values.columns)), values.columns)
plt.yticks(range(len(values)), values.index.strftime("%Y-%m-%d"))
plt.colorbar(ticks=[0, 1], label="Missing: 0 = no, 1 = yes")
plt.title("Missing data by date and column")
plt.xlabel("Column")
plt.ylabel("Date")
plt.tight_layout()
plt.show()''',
        "reading": "B 在 1 月 3–4 日连续缺失，C 在 1 月 8–10 日连续缺失，A 只有 1 月 5 日缺失。",
        "tip": "如果某个日期整行不存在，isna() 看不到它；先按正确的交易日历补齐日期。",
    },
    {
        "id": "V04",
        "title": "缺失率：快速比较哪些字段最不完整",
        "columns": ["date", "A", "B", "C"],
        "rows": [
            ["2024-01-02", 100, 50, 80], ["2024-01-03", 101, None, 81],
            ["2024-01-04", 102, None, 82], ["2024-01-05", None, 52, 83],
            ["2024-01-08", 104, 53, None], ["2024-01-09", 105, 54, None],
            ["2024-01-10", 106, 55, None], ["2024-01-11", 107, 56, 87],
        ],
        "dtypes_note": "每行对应一个预期交易日；A、B、C 是数值字段；缺失率的分母为这张表的全部行数。",
        "task": "计算 A、B、C 三列各自的缺失比例，按从高到低画柱状图。",
        "plot": '''missing_pct = df[["A", "B", "C"]].isna().mean().sort_values(ascending=False) * 100

plt.figure(figsize=(7, 4))
plt.bar(missing_pct.index, missing_pct.values)
plt.title("Missing rate by column")
plt.xlabel("Column")
plt.ylabel("Missing (%)")
plt.ylim(0, 100)
plt.tight_layout()
plt.show()''',
        "reading": "C 缺失 3/8 = 37.5%，B 缺失 25%，A 缺失 12.5%；可先检查 C 的来源与覆盖范围。",
        "tip": "缺失率高不代表必须删列；先分清尚未上市、休市、无成交和采集失败。",
    },
    {
        "id": "V05",
        "title": "收益分布：看收益主要落在哪个范围",
        "columns": ["ret"],
        "rows": [[-0.025], [-0.015], [-0.008], [0.004], [0.006], [0.010], [0.012], [0.022]],
        "dtypes_note": "ret 是每个观测期的收益率，小数单位；所有行应采用相同的收益周期，例如全部为日收益。",
        "task": "把日收益画成直方图，横轴用百分数，纵轴表示落入该区间的观测数量。",
        "plot": '''returns_pct = df["ret"].dropna() * 100  # 绘图时忽略缺失，不把它当作 0

plt.figure(figsize=(8, 4))
plt.hist(returns_pct, bins=5, edgecolor="white")
plt.axvline(0, color="grey", linewidth=0.8)
plt.title("Daily return distribution")
plt.xlabel("Return (%)")
plt.ylabel("Count")
plt.tight_layout()
plt.show()''',
        "reading": "柱子的高度表示样本在各收益区间的数量；这个小例子同时包含正收益和负收益。",
        "tip": "8 行只用于演示语法；真实分布分析需要更多样本，分箱数量也会影响外观。",
    },
    {
        "id": "V06",
        "title": "大幅波动：标出绝对收益超过 2% 的日期",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", 0.010], ["2024-01-03", -0.015],
            ["2024-01-04", 0.006], ["2024-01-05", 0.022],
            ["2024-01-08", -0.008], ["2024-01-09", 0.004],
            ["2024-01-10", -0.025], ["2024-01-11", 0.012],
        ],
        "dtypes_note": "date 是日期，ret 是小数单位的日收益；阈值 0.02 表示 2%。",
        "task": "画日收益折线，并用红点突出绝对收益大于 2% 的观测，方便回查原始数据。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
large_move = df["ret"].abs() > 0.02  # 固定阈值，可按任务调整

plt.figure(figsize=(10, 4))
plt.plot(df["date"], df["ret"] * 100, label="Daily return")
plt.scatter(df.loc[large_move, "date"], df.loc[large_move, "ret"] * 100, color="red", label="Absolute return > 2%", zorder=3)
plt.axhline(2, color="grey", linestyle="--")
plt.axhline(-2, color="grey", linestyle="--")
plt.title("Large daily moves")
plt.xlabel("Date")
plt.ylabel("Return (%)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "红点对应 1 月 5 日的 +2.2% 和 1 月 10 日的 -2.5%，是优先回查的日期。",
        "tip": "大幅波动可能是真实行情，不能仅凭超过阈值就认定错误或删除。",
    },
    {
        "id": "V07",
        "title": "滚动波动：看近期收益是否越来越不稳定",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", 0.002], ["2024-01-03", -0.003],
            ["2024-01-04", 0.004], ["2024-01-05", -0.002],
            ["2024-01-08", 0.020], ["2024-01-09", -0.025],
            ["2024-01-10", 0.030], ["2024-01-11", -0.018],
        ],
        "dtypes_note": "date 是交易日期；ret 是小数单位的日收益；每个交易日只有一行。",
        "task": "计算过去 3 个观测的日收益样本标准差，画折线观察波动水平的变化，不做年化。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
rolling_std = df["ret"].rolling(3, min_periods=3).std()  # 包含当前行，默认 ddof=1

plt.figure(figsize=(10, 4))
plt.plot(df["date"], rolling_std * 100, marker="o")
plt.title("Rolling 3-observation daily return standard deviation")
plt.xlabel("Date")
plt.ylabel("Daily return standard deviation (%)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "前两行因观测不足没有结果；后半段收益振幅增大，滚动标准差明显上升。",
        "tip": "窗口 3 仅供小表演示，实际常改为 20 或 60；它数的是观测行，不是日历天。",
    },
    {
        "id": "V08",
        "title": "滚动相关：看两只资产的联动是否变化",
        "columns": ["date", "ret_a", "ret_b"],
        "rows": [
            ["2024-01-02", 0.010, 0.008], ["2024-01-03", -0.010, -0.009],
            ["2024-01-04", 0.020, 0.017], ["2024-01-05", -0.020, -0.016],
            ["2024-01-08", 0.015, -0.014], ["2024-01-09", -0.015, 0.016],
            ["2024-01-10", 0.025, -0.020], ["2024-01-11", -0.025, 0.022],
        ],
        "dtypes_note": "date 是双方共同交易日期；ret_a、ret_b 是同期日收益率，小数单位，按日期一一对应。",
        "task": "计算两只资产最近 3 个观测的相关系数，画出联动从同向到反向的变化。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
rolling_corr = df["ret_a"].rolling(3, min_periods=3).corr(df["ret_b"])

plt.figure(figsize=(10, 4))
plt.plot(df["date"], rolling_corr, marker="o")
plt.axhline(0, color="grey", linewidth=0.8)
plt.ylim(-1.05, 1.05)
plt.title("Rolling 3-observation return correlation")
plt.xlabel("Date")
plt.ylabel("Correlation")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "前半段相关系数接近 +1，后半段接近 -1；这组演示数据刻意展示联动方向变化。",
        "tip": "3 对观测的相关性非常不稳定；实际应扩大窗口，窗口内不足 3 对或某列恒定时结果为缺失。",
    },
    {
        "id": "V09",
        "title": "相关矩阵：比较多只资产的同期收益关系",
        "columns": ["A", "B", "C"],
        "rows": [
            [0.010, 0.008, -0.009], [-0.010, -0.007, 0.008],
            [0.020, 0.016, -0.012], [-0.020, -0.015, 0.019],
            [0.015, None, -0.010], [-0.015, -0.009, None],
            [0.025, 0.019, -0.021], [-0.025, -0.018, 0.024],
        ],
        "dtypes_note": "每一行代表同一个交易日，A、B、C 是三只资产的小数日收益；列间已按日期对齐，空白为缺失。",
        "task": "先列出每两列共同非空的样本数，再画收益相关系数热图，比较正相关与负相关。",
        "plot": '''returns = df[["A", "B", "C"]]
valid = returns.notna().astype(int)
pair_counts = valid.T.dot(valid)  # 每对资产共同非空的观测数
display(pair_counts)
corr = returns.corr(min_periods=3)

plt.figure(figsize=(6, 5))
plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
plt.xticks(range(len(corr)), corr.columns)
plt.yticks(range(len(corr)), corr.index)
plt.colorbar(label="Correlation")
plt.title("Pairwise return correlation")
plt.tight_layout()
plt.show()''',
        "reading": "A 与 B 正相关，C 与它们负相关；A–B 和 A–C 各有 7 对观测，B–C 只有 6 对。",
        "tip": "相关性不表示因果；缺失模式不同会让各格子使用不同日期，必须一起检查样本数。",
    },
]

CASES += [
    {
        "id": "V10",
        "title": "今日收益与下一交易日收益散点图",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", 0.012], ["2024-01-03", -0.008],
            ["2024-01-04", 0.006], ["2024-01-05", -0.015],
            ["2024-01-08", 0.004], ["2024-01-09", 0.011],
            ["2024-01-10", -0.003], ["2024-01-11", 0.007],
        ],
        "dtypes_note": "date 是同一资产不重复、无缺交易日的日期；ret 是日收益的小数，例如 0.012 表示 1.2%。",
        "task": "把今日收益放在横轴，下一交易日收益放在纵轴，观察两者是否存在明显关系。",
        "plot": '''# 先按日期排序，再把下一行收益移到今天这一行。
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").copy()
df["next_ret"] = df["ret"].shift(-1)
pairs = df[["ret", "next_ret"]].dropna()  # 两列必须成对删除缺失值

plt.figure(figsize=(7, 4))
plt.scatter(pairs["ret"] * 100, pairs["next_ret"] * 100)
plt.axhline(0, color="grey", linewidth=0.8)
plt.axvline(0, color="grey", linewidth=0.8)
plt.title("Today vs next trading day")
plt.xlabel("Today's return (%)")
plt.ylabel("Next trading day's return (%)")
plt.tight_layout()
plt.show()''',
        "reading": "每个点是一对相邻交易日的收益；点云形状可以提示后续要检验的关系。",
        "tip": "这里只有 7 对观测，不能据此判断预测能力；若日期有缺口，下一行不一定是下一交易日。",
    },
    {
        "id": "V11",
        "title": "收益自相关柱状图",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", 0.012], ["2024-01-03", -0.008],
            ["2024-01-04", 0.006], ["2024-01-05", -0.015],
            ["2024-01-08", 0.004], ["2024-01-09", 0.011],
            ["2024-01-10", -0.003], ["2024-01-11", 0.007],
            ["2024-01-12", -0.006], ["2024-01-15", 0.002],
        ],
        "dtypes_note": "date 是同一资产完整的交易日序列；ret 是收益小数，此例以交易日观测数作为滞后单位。",
        "task": "计算收益与前 1、2、3 个交易日收益的相关系数，并画成柱状图。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
ret = df.sort_values("date")["ret"]
lags = [1, 2, 3]
correlations = [ret.autocorr(lag=k) for k in lags]

plt.figure(figsize=(7, 4))
plt.bar(lags, correlations)
plt.axhline(0, color="grey", linewidth=0.8)
plt.xticks(lags)
plt.ylim(-1, 1)
plt.title("Return autocorrelation")
plt.xlabel("Lag (trading observations)")
plt.ylabel("Correlation")
plt.tight_layout()
plt.show()''',
        "reading": "每根柱子显示一个滞后的相关系数，正负号分别表示同向和反向关系。",
        "tip": "10 条数据仅用于演示代码，没有置信区间；柱子较高也不能说明存在稳定规律。",
    },
    {
        "id": "V12",
        "title": "不同星期的收益箱线图",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-08", 0.012], ["2024-01-09", -0.006],
            ["2024-01-10", 0.003], ["2024-01-11", -0.009],
            ["2024-01-12", 0.007], ["2024-01-15", -0.005],
            ["2024-01-16", 0.004], ["2024-01-17", -0.002],
            ["2024-01-18", 0.006], ["2024-01-19", 0.001],
        ],
        "dtypes_note": "date 是日收益所属的交易日期，ret 是收益小数；本例每个星期类别恰有两条记录。",
        "task": "按星期一到星期五分组，用箱线图比较各组收益的分布。",
        "plot": '''weekday = pd.to_datetime(df["date"]).dt.dayofweek  # 周一=0，周五=4
groups = [df.loc[weekday == k, "ret"].dropna() * 100 for k in range(5)]

plt.figure(figsize=(7, 4))
plt.boxplot(groups)
plt.xticks([1, 2, 3, 4, 5], ["Mon", "Tue", "Wed", "Thu", "Fri"])
plt.axhline(0, color="grey", linewidth=0.8)
plt.title("Daily returns by weekday")
plt.xlabel("Weekday")
plt.ylabel("Daily return (%)")
plt.tight_layout()
plt.show()''',
        "reading": "箱体和中位线用于比较各组分布；本例每组只有两个点，形状只是绘图示意。",
        "tip": "真实分析需要更多样本和分期检验；不要从这 10 条数据推断星期效应。",
    },
    {
        "id": "V13",
        "title": "月度收益热力图",
        "columns": ["month", "monthly_ret"],
        "rows": [
            ["2023-01-01", 0.025], ["2023-02-01", -0.018],
            ["2023-03-01", 0.010], ["2023-04-01", 0.036],
            ["2024-03-01", -0.028], ["2024-04-01", 0.014],
            ["2024-05-01", -0.007], ["2024-06-01", 0.022],
        ],
        "dtypes_note": "每行已是一个完整月份的复合收益，monthly_ret 为小数；每月只有一行，未提供的月份保留缺失。",
        "task": "把年份放在行、月份放在列，用颜色展示每个月的收益。",
        "plot": '''month = pd.to_datetime(df["month"])
table = df.assign(year=month.dt.year, month_number=month.dt.month).pivot(
    index="year", columns="month_number", values="monthly_ret")
table = table.reindex(columns=range(1, 13))  # 缺月保持 NaN，不填零
limit = table.abs().max().max() * 100

plt.figure(figsize=(10, 3))
plt.imshow(table * 100, aspect="auto", cmap="RdBu", vmin=-limit, vmax=limit)
plt.colorbar(label="Monthly return (%)")
plt.xticks(range(12), range(1, 13))
plt.yticks(range(len(table)), table.index)
plt.title("Monthly returns; blank = missing")
plt.xlabel("Month")
plt.ylabel("Year")
plt.tight_layout()
plt.show()''',
        "reading": "颜色深浅表示收益幅度；空白格表示没有该月数据，不表示收益为零。",
        "tip": "先确认日数据覆盖完整月份再计算月收益；此模板只负责绘制已经验证的月收益。",
    },
    {
        "id": "V14",
        "title": "每日成交量柱状图",
        "columns": ["date", "volume"],
        "rows": [
            ["2024-01-02", 1250000], ["2024-01-03", 1180000],
            ["2024-01-04", 1420000], ["2024-01-05", 3200000],
            ["2024-01-08", 1670000], ["2024-01-09", 1360000],
            ["2024-01-10", 1210000], ["2024-01-11", 1490000],
        ],
        "dtypes_note": "date 是同一资产的日期，volume 是当日成交股数；如果原数据是手数或成交额，需要相应修改纵轴单位。",
        "task": "画每日成交量，找出明显放量的日期。",
        "plot": '''dates = pd.to_datetime(df["date"])

plt.figure(figsize=(8, 4))
plt.bar(dates, df["volume"] / 1000000)
plt.title("Daily trading volume")
plt.xlabel("Date")
plt.ylabel("Volume (million shares)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()''',
        "reading": "示例中 1 月 5 日的柱子明显更高，可以回到原始记录检查当天发生了什么。",
        "tip": "周末留白属于日期轴的正常间隔；成交量增加本身不说明未来价格会上涨。",
    },
    {
        "id": "V15",
        "title": "在时间序列上标出训练与测试边界",
        "columns": ["date", "value"],
        "rows": [
            ["2024-01-02", 100], ["2024-01-03", 102],
            ["2024-01-04", 101], ["2024-01-05", 104],
            ["2024-01-08", 103], ["2024-01-09", 106],
            ["2024-01-10", 105], ["2024-01-11", 108],
        ],
        "dtypes_note": "date 是观测日期，value 是要检查的数值；本例约定 2024-01-08 起的数据属于测试区间。",
        "task": "画出时间序列，并在测试集开始的日期画一条竖线。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
test_start = pd.Timestamp("2024-01-08")  # 替换成你预先确定的测试起点

plt.figure(figsize=(8, 4))
plt.plot(pd.to_datetime(df["date"]), df["value"], marker="o")
plt.axvline(test_start, color="red", linestyle="--", label="Test starts")
plt.title("Time series and train/test boundary")
plt.xlabel("Date")
plt.ylabel("Value")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()''',
        "reading": "红线之前为训练区间，红线当天及之后为测试区间，便于检查两段数据覆盖范围。",
        "tip": "画边界不等于已消除泄漏；预处理参数仍须只从训练集估计，跨边界的预测标签也须处理。",
    },
    {
        "id": "V16",
        "title": "不同特征分组的下一期平均收益",
        "columns": ["bucket", "next_ret"],
        "rows": [
            ["Low", -0.010], ["Low", 0.004], ["Low", -0.003],
            ["Mid", 0.002], ["Mid", -0.004], ["Mid", 0.005],
            ["High", 0.008], ["High", -0.002], ["High", 0.006],
        ],
        "dtypes_note": "bucket 是使用当时可知特征和事先固定规则得到的组别；next_ret 为下一期收益小数，仅用于事后评估。",
        "task": "比较 Low、Mid、High 三组的下一期平均收益，同时列出每组有效样本数。",
        "plot": '''summary = df.groupby("bucket")["next_ret"].agg(["mean", "count"])
summary = summary.reindex(["Low", "Mid", "High"])
display(summary.rename(columns={"mean": "平均收益（小数）", "count": "有效样本数"}))

plt.figure(figsize=(7, 4))
plt.bar(summary.index, summary["mean"] * 100)
plt.axhline(0, color="grey", linewidth=0.8)
plt.title("Mean next-period return by feature bucket")
plt.xlabel("Feature bucket")
plt.ylabel("Mean next-period return (%)")
plt.tight_layout()
plt.show()''',
        "reading": "柱子比较各组的下一期平均收益；同时看表中样本数，避免把少量观测的均值当作稳定效果。",
        "tip": "分组规则不能根据这些未来收益反向选择；图中关系尚未检验显著性、交易成本或样本外表现。",
    },
    {
        "id": "V17",
        "title": "从日收益计算并画回撤",
        "columns": ["date", "ret"],
        "rows": [
            ["2024-01-02", -0.020], ["2024-01-03", 0.010],
            ["2024-01-04", 0.030], ["2024-01-05", -0.040],
            ["2024-01-08", -0.015], ["2024-01-09", 0.020],
            ["2024-01-10", 0.010], ["2024-01-11", 0.035],
        ],
        "dtypes_note": "date 是唯一且完整的日期序列；ret 是不含缺失、均大于 -1 的日收益小数，初始净值设为 1。",
        "task": "把日收益复合成净值，计算相对历史最高净值的跌幅，并画回撤曲线。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
wealth = (1 + df["ret"]).cumprod()  # 初始净值为 1
peak = wealth.cummax().clip(lower=1)  # 把初始净值纳入历史最高值
drawdown = wealth / peak - 1
dates = pd.to_datetime(df["date"])

plt.figure(figsize=(8, 4))
plt.fill_between(dates, drawdown * 100, 0, alpha=0.3)
plt.plot(dates, drawdown * 100)
plt.title("Drawdown from previous peak")
plt.xlabel("Date")
plt.ylabel("Drawdown (%)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()''',
        "reading": "曲线越低，距离此前最高净值越远；本例第一天亏损也会正确显示为负回撤。",
        "tip": "缺失收益不能默认填零；若输入为策略收益，还须明确是否已扣除交易成本。",
    },
    {
        "id": "V18",
        "title": "每小时事件数量柱状图",
        "columns": ["timestamp"],
        "rows": [
            ["2024-01-08 09:10:00"], ["2024-01-08 09:42:00"],
            ["2024-01-08 10:15:00"], ["2024-01-08 12:05:00"],
            ["2024-01-08 12:20:00"], ["2024-01-08 12:51:00"],
            ["2024-01-08 13:08:00"], ["2024-01-08 14:25:00"],
        ],
        "dtypes_note": "每行是一条事件；timestamp 使用同一时区，本例确认当天 09:00 至 15:00 的采集持续完整。",
        "task": "按小时统计事件条数，并显示完全没有事件的小时。",
        "plot": '''events = df.assign(timestamp=pd.to_datetime(df["timestamp"]))
counts = events.set_index("timestamp").resample("1h").size()
# 替换成实际已确认完整采集的起止小时；本例最后一格覆盖 14:00–15:00。
hours = pd.date_range("2024-01-08 09:00", "2024-01-08 14:00", freq="1h")
counts = counts.reindex(hours, fill_value=0)  # 使用已确认完整的采集区间

plt.figure(figsize=(8, 4))
plt.bar(counts.index.strftime("%H:%M"), counts.values)
plt.title("Events per hour")
plt.xlabel("Hour starting")
plt.ylabel("Number of events")
plt.yticks(range(int(counts.max()) + 1))
plt.tight_layout()
plt.show()''',
        "reading": "12 点这一小时有三条事件，11 点这一小时为零，方便观察事件到达是否均匀。",
        "tip": "只有确认采集完整时，空小时才可记为零；采集故障导致的缺失必须另行标记。",
    },
]
