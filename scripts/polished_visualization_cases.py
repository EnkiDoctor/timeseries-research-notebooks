"""Readable style variants for the basic visualization input tables."""

STYLED = {
    "V01": {
        "beauty": "蓝色折线搭配淡色面积，以红色标注绝对收益最大的日期，先看整体路径，再找到重点。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
returns_pct = df["ret"] * 100  # 保持缺失值；单位改为百分数

plt.figure(figsize=(10, 4.5))
plt.plot(df["date"], returns_pct, color=BLUE, marker="o", markersize=5, linewidth=2)
plt.fill_between(df["date"].to_numpy(), returns_pct.to_numpy(), 0, color=BLUE, alpha=0.08)
plt.axhline(0, color=MUTED, linewidth=1)
if returns_pct.notna().any():  # 只标出一个重点，避免文字挤满图
    peak = returns_pct.abs().idxmax()
    plt.scatter(df.loc[peak, "date"], returns_pct.loc[peak], color=RED, s=55, zorder=3)
    plt.annotate("Largest move: {:+.1f}%".format(returns_pct.loc[peak]),
                 xy=(df.loc[peak, "date"], returns_pct.loc[peak]),
                 xytext=(0, 14 if returns_pct.loc[peak] > 0 else -22),
                 textcoords="offset points", ha="center", color=RED)
plt.title("Daily return")
plt.xlabel("Date")
plt.ylabel("Return (%)")
plt.xticks(rotation=30, ha="right")
plt.margins(x=0.10, y=0.22)
plt.tight_layout()
plt.show()''',
    },
    "V02": {
        "beauty": "用蓝绿两色区分资产，保留共同起点参考线，在曲线末端直接显示资产名称与最终数值。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
prices = df.set_index("date")[["asset_a", "asset_b"]]
rebased = prices / prices.iloc[0] * 100  # 输入要求价格为正且无缺失，共同起点为 100

plt.figure(figsize=(10, 4.5))
plt.axhline(100, color=MUTED, linewidth=1, linestyle="--")
for column, label, color in [("asset_a", "A", BLUE), ("asset_b", "B", TEAL)]:
    plt.plot(rebased.index, rebased[column], color=color, linewidth=2.5)
    last_value = rebased[column].iloc[-1]
    plt.scatter(rebased.index[-1], last_value, color=color, s=35, zorder=3)
    plt.annotate("{}  {:.1f}".format(label, last_value),
                 xy=(rebased.index[-1], last_value), xytext=(8, 0),
                 textcoords="offset points", va="center", color=color, fontweight="bold")
plt.title("Two assets, one starting point")
plt.xlabel("Date")
plt.ylabel("Rebased price (start = 100)")
plt.xticks(rotation=30, ha="right")
plt.margins(x=0.12, y=0.15)  # 为末端文字留空间
plt.tight_layout()
plt.show()''',
    },
    "V03": {
        "beauty": "用浅灰与黄色两个离散颜色区分完整与缺失，只在缺失格子写 ×，避免把有无缺失误读为连续数值。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
values = df.set_index("date")[["A", "B", "C"]]
missing = values.isna()

plt.figure(figsize=(7, 5.2))
plt.grid(False)  # 热图不叠加默认的水平网格线
plt.imshow(missing, aspect="auto", cmap=ListedColormap(["#F1F5F9", "#FBBF24"]),
           vmin=-0.5, vmax=1.5, interpolation="nearest")
plt.xticks(range(len(values.columns)), values.columns)
plt.yticks(range(len(values)), values.index.strftime("%m-%d"))
for row, column in zip(*np.where(missing.to_numpy())):
    plt.text(column, row, "×", ha="center", va="center", color=INK, fontsize=16)
plt.colorbar(ticks=[0, 1], label="0 = observed   |   1 = missing", shrink=0.75, pad=0.04)
plt.title("Where is data missing?")
plt.xlabel("Column")
plt.ylabel("Date")
plt.tight_layout()
plt.show()''',
    },
    "V04": {
        "beauty": "改为从高到低的横向条形图，统一 0–100% 刻度，并在条形末端直接写出缺失比例。",
        "plot": '''missing_pct = df[["A", "B", "C"]].isna().mean().sort_values(ascending=False) * 100

plt.figure(figsize=(8, 4))
plt.barh(missing_pct.index, missing_pct.values, color=ORANGE, height=0.55)
plt.ylim(len(missing_pct) - 0.5, -0.5)  # 将最高缺失率放在最上方
for row, value in enumerate(missing_pct):
    plt.text(min(value + 2, 98), row, "{:.1f}%".format(value), va="center",
             ha="right" if value > 94 else "left", color=INK, fontweight="bold")
plt.title("Which columns need attention?")
plt.xlabel("Missing observations (%)")
plt.ylabel("Column")
plt.xlim(0, 100)  # 缺失率使用完整的百分数范围
plt.xticks([0, 25, 50, 75, 100])
plt.grid(False, axis="y")
plt.grid(True, axis="x", color=LIGHT, linewidth=0.7)
plt.tight_layout()
plt.show()''',
    },
    "V05": {
        "beauty": "以低饱和蓝色直方图展示分布，增加橙色中位数线，参考线与图例帮助定位中心。",
        "plot": '''returns_pct = df["ret"].dropna() * 100  # 不将缺失收益替换成 0
median_pct = returns_pct.median()

plt.figure(figsize=(8, 4.5))
plt.hist(returns_pct, bins=5, color=BLUE, alpha=0.75,
         edgecolor="white", linewidth=1.5, label="Daily returns")
plt.axvline(0, color=MUTED, linewidth=1, linestyle=":", label="Zero return")
if pd.notna(median_pct):
    plt.axvline(median_pct, color=ORANGE, linewidth=2, linestyle="--",
                label="Median: {:+.2f}%".format(median_pct))
plt.title("Where do daily returns concentrate?")
plt.xlabel("Return (%)")
plt.ylabel("Observation count")
plt.legend(loc="upper left", fontsize=9)
plt.margins(y=0.30)  # 给图例留出空间
plt.tight_layout()
plt.show()''',
    },
    "V06": {
        "beauty": "用浅灰折线作为背景，只将越过 ±2% 阈值的点和数值标为红色，把注意力集中到需要检查的日期。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
large_move = df["ret"].abs() > 0.02  # 固定阈值：2%

plt.figure(figsize=(10, 4.5))
plt.plot(df["date"], df["ret"] * 100, color=MUTED, linewidth=1.5, marker="o", markersize=4)
plt.axhspan(-2, 2, color=BLUE, alpha=0.05)  # 淡色背景表示阈值以内
plt.axhline(2, color=ORANGE, linewidth=1, linestyle="--", label="±2% threshold")
plt.axhline(-2, color=ORANGE, linewidth=1, linestyle="--")
plt.scatter(df.loc[large_move, "date"], df.loc[large_move, "ret"] * 100,
            color=RED, s=65, edgecolors="white", zorder=3, label="Large move")
for date, ret in df.loc[large_move, ["date", "ret"]].itertuples(index=False, name=None):
    plt.annotate("{:+.1f}%".format(ret * 100), xy=(date, ret * 100),
                 xytext=(0, 12 if ret > 0 else -18), textcoords="offset points",
                 ha="center", color=RED, fontweight="bold")
plt.title("Flag large moves for inspection")
plt.xlabel("Date")
plt.ylabel("Return (%)")
plt.xticks(rotation=30, ha="right")
plt.legend(loc="upper left", fontsize=9)
plt.margins(x=0.05, y=0.35)
plt.tight_layout()
plt.show()''',
    },
    "V07": {
        "beauty": "用蓝色曲线与浅色面积突出波动水平，纵轴从 0 开始，并在最后一个有效观测旁标出数值。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
rolling_std_pct = df["ret"].rolling(3, min_periods=3).std() * 100  # ddof=1，未年化

plt.figure(figsize=(10, 4.5))
plt.plot(df["date"], rolling_std_pct, color=BLUE, linewidth=2.5, marker="o", markersize=5)
plt.fill_between(df["date"].to_numpy(), rolling_std_pct.to_numpy(), 0, color=BLUE, alpha=0.10)
last = rolling_std_pct.last_valid_index()  # 前两行仍保持缺失，不补成 0
if last is not None:
    plt.scatter(df.loc[last, "date"], rolling_std_pct.loc[last], color=BLUE, s=50, zorder=3)
    plt.annotate("{:.2f}%".format(rolling_std_pct.loc[last]),
                 xy=(df.loc[last, "date"], rolling_std_pct.loc[last]),
                 xytext=(8, 0), textcoords="offset points", va="center", color=BLUE)
plt.title("Is recent volatility rising?")
plt.xlabel("Date")
plt.ylabel("3-observation daily return std. (%)")
plt.ylim(bottom=0)
plt.xticks(rotation=30, ha="right")
plt.margins(x=0.14, y=0.20)
plt.tight_layout()
plt.show()''',
    },
    "V08": {
        "beauty": "以蓝色相关曲线展示变化，用绿、红淡色面积区分正相关和负相关，并固定相关系数的刻度范围。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
rolling_corr = df["ret_a"].rolling(3, min_periods=3).corr(df["ret_b"])
x = df["date"].to_numpy()
y = rolling_corr.to_numpy()  # NaN 保持缺失，不补成 0

plt.figure(figsize=(10, 4.5))
plt.fill_between(x, y, 0, where=y >= 0, color=TEAL, alpha=0.12, interpolate=True)
plt.fill_between(x, y, 0, where=y < 0, color=RED, alpha=0.10, interpolate=True)
plt.plot(x, y, color=BLUE, linewidth=2.5, marker="o", markersize=5)
plt.axhline(0, color=MUTED, linewidth=1)
plt.ylim(-1.08, 1.08)  # 略留空间防止 ±1 处的标记被裁切
plt.yticks([-1, -0.5, 0, 0.5, 1])
plt.title("Does the relationship change over time?")
plt.xlabel("Date")
plt.ylabel("3-observation return correlation")
plt.xticks(rotation=30, ha="right")
plt.margins(x=0.06)
plt.tight_layout()
plt.show()''',
    },
    "V09": {
        "beauty": "相关热图固定 −1 到 +1 的色标，每格显示两位小数，文字颜色随底色深浅变化；共同样本数继续单独展示。",
        "plot": '''returns = df[["A", "B", "C"]]
valid = returns.notna().astype(int)
pair_counts = valid.T.dot(valid)  # 每格相关性使用的共同非空样本数
print("Pairwise valid observation counts")
display(pair_counts)
corr = returns.corr(min_periods=3)

plt.figure(figsize=(6.5, 5.2))
plt.grid(False)
plt.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, interpolation="nearest")
plt.xticks(range(len(corr)), corr.columns)
plt.yticks(range(len(corr)), corr.index)
for row in range(len(corr)):
    for column in range(len(corr)):
        value = corr.iloc[row, column]
        label = "NA" if pd.isna(value) else "{:.2f}".format(value)
        color = "white" if pd.notna(value) and abs(value) > 0.55 else INK
        plt.text(column, row, label, ha="center", va="center",
                 color=color, fontsize=13, fontweight="bold")
plt.colorbar(ticks=[-1, -0.5, 0, 0.5, 1], label="Correlation", shrink=0.80, pad=0.04)
plt.title("Pairwise return relationships")
plt.tight_layout()
plt.show()''',
    },
}

STYLED.update({
    "V10": {
        "beauty": "用半透明蓝点、白色描边和浅灰零线突出点云，同时在标题注明有效配对数。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").copy()
df["next_ret"] = df["ret"].shift(-1)  # 下一交易日收益，只用于事后观察
pairs = df[["ret", "next_ret"]].dropna()  # 成对删除缺失，不分别删两列

plt.figure(figsize=(8, 4.8))
plt.scatter(pairs["ret"] * 100, pairs["next_ret"] * 100,
            s=95, color=BLUE, alpha=0.8, edgecolors="white", linewidths=1.2, zorder=3)
plt.axhline(0, color=MUTED, linewidth=0.9, linestyle="--")
plt.axvline(0, color=MUTED, linewidth=0.9, linestyle="--")
plt.title("Today vs next trading day  |  n = {}".format(len(pairs)))
plt.xlabel("Today's return (%)")
plt.ylabel("Next trading day's return (%)")
plt.margins(0.18)
plt.tight_layout()
plt.show()''',
    },
    "V11": {
        "beauty": "正负相关分色，直接标注系数，并保留固定相关系数刻度方便比较。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
ret = df.sort_values("date")["ret"]
lags = [1, 2, 3]
correlations = [ret.autocorr(lag=k) for k in lags]
colors = [TEAL if value >= 0 else RED for value in correlations]

plt.figure(figsize=(8, 4.8))
plt.bar(lags, correlations, color=colors, width=0.55, alpha=0.9, zorder=3)
plt.axhline(0, color=MUTED, linewidth=0.9)
for lag, value in zip(lags, correlations):
    if pd.notna(value):  # 常数列等情况可能得不到相关系数
        plt.annotate("{:+.2f}".format(value), (lag, value),
                     xytext=(0, 7 if value >= 0 else -7), textcoords="offset points",
                     ha="center", va="bottom" if value >= 0 else "top", color=INK)
plt.xticks(lags, ["Lag {}".format(k) for k in lags])
plt.yticks([-1, -0.5, 0, 0.5, 1])
plt.ylim(-1.12, 1.12)
plt.title("Return autocorrelation")
plt.xlabel("Lag (trading observations)")
plt.ylabel("Correlation")
plt.tight_layout()
plt.show()''',
    },
    "V12": {
        "beauty": "用浅蓝箱体、深色中位线和原始观测点呈现分布，星期标签同时显示真实样本数。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
weekday = df["date"].dt.dayofweek  # 周一=0，周五=4
groups = [df.loc[weekday == k, "ret"].dropna() * 100 for k in range(5)]
names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
labels = ["{}\\nn = {}".format(name, len(group)) for name, group in zip(names, groups)]

plt.figure(figsize=(8, 4.8))
plt.boxplot(groups, widths=0.45, patch_artist=True, showfliers=False,
            boxprops={"facecolor": "#DBEAFE", "edgecolor": BLUE},
            medianprops={"color": INK, "linewidth": 2},
            whiskerprops={"color": MUTED}, capprops={"color": MUTED})
for position, group in enumerate(groups, start=1):
    plt.scatter([position] * len(group), group, s=35, color=BLUE,
                alpha=0.65, edgecolors="white", zorder=3)  # 原始点包括离群值
plt.xticks(range(1, 6), labels)
plt.axhline(0, color=MUTED, linewidth=0.9, linestyle="--")
plt.title("Daily returns by weekday")
plt.xlabel("Weekday")
plt.ylabel("Daily return (%)")
plt.tight_layout()
plt.show()''',
    },
    "V13": {
        "beauty": "使用以零为中心的对称色阶、格内百分数和灰色缺失格，明确区分零收益与未提供数据。",
        "plot": '''df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")
table = df.assign(year=df["month"].dt.year, month_number=df["month"].dt.month).pivot(
    index="year", columns="month_number", values="monthly_ret")
table = table.reindex(columns=range(1, 13)) * 100  # 缺月保持 NaN，收益转百分数
limit = table.abs().max().max()
limit = limit if pd.notna(limit) and limit > 0 else 1  # 全零或全缺失时仍能画图
cmap = plt.get_cmap("RdBu").copy()
cmap.set_bad(LIGHT)  # 灰色代表缺失，不能填成零收益

plt.figure(figsize=(11, max(3.5, len(table) * 0.6 + 1.8)))
plt.imshow(table, aspect="auto", cmap=cmap, vmin=-limit, vmax=limit)
for row in range(len(table)):
    for col in range(12):
        value = table.iloc[row, col]
        label = "—" if pd.isna(value) else "{:+.1f}%".format(value)
        color = "white" if pd.notna(value) and abs(value) > limit * 0.6 else INK
        plt.text(col, row, label, ha="center", va="center", color=color, fontsize=9)
plt.colorbar(label="Monthly return (%)", shrink=0.8, pad=0.02)
plt.xticks(range(12), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
plt.yticks(range(len(table)), table.index)
plt.grid(False)
plt.title("Monthly returns  |  grey = missing")
plt.xlabel("Month")
plt.ylabel("Year")
plt.tight_layout()
plt.show()''',
    },
    "V14": {
        "beauty": "普通日期用浅蓝色，最大成交量用深蓝突出，并在柱顶直接显示百万股数值。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
volume_m = df["volume"] / 1000000  # 单位由股转换为百万股
colors = [BLUE if value == volume_m.max() else "#BFDBFE" for value in volume_m]

plt.figure(figsize=(10, 4.8))
plt.bar(df["date"], volume_m, color=colors, width=0.65, zorder=3)
for date, value in zip(df["date"], volume_m):
    if pd.notna(value):
        plt.annotate("{:.2f}".format(value), (date, value),
                     xytext=(0, 6), textcoords="offset points", ha="center", color=INK)
max_volume = volume_m.max()
upper = max(max_volume * 1.2, 1) if pd.notna(max_volume) else 1
plt.ylim(0, upper)  # 全缺失时保留空图，不把缺失成交量改成 0
plt.title("Daily trading volume")
plt.xlabel("Date")
plt.ylabel("Volume (million shares)")
plt.xticks(df["date"], df["date"].dt.strftime("%m-%d"), rotation=30)
plt.tight_layout()
plt.show()''',
    },
    "V15": {
        "beauty": "用两块浅色背景区分训练与测试，边界用虚线标出，时间序列保持同一条清晰折线。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
test_start = pd.Timestamp("2024-01-08")  # 改成预先确定的测试起点，当天属于测试集

plt.figure(figsize=(10, 4.8))
plt.axvspan(df["date"].min(), test_start, color=BLUE, alpha=0.07, label="Train")
plt.axvspan(test_start, df["date"].max(), color=ORANGE, alpha=0.10, label="Test")
plt.plot(df["date"], df["value"], color=BLUE, linewidth=2.2,
         marker="o", markersize=6, markeredgecolor="white", zorder=3)
plt.axvline(test_start, color=ORANGE, linestyle="--", linewidth=1.5, label="Test starts")
plt.title("Time series and train/test boundary")
plt.xlabel("Date")
plt.ylabel("Value")
plt.legend(loc="upper left", ncol=3)
plt.margins(y=0.2)
plt.xticks(df["date"], df["date"].dt.strftime("%m-%d"), rotation=30)
plt.tight_layout()
plt.show()''',
    },
    "V16": {
        "beauty": "均值柱按正负分色，直接标出百分数与每组有效样本数，减少来回查表。",
        "plot": '''summary = df.groupby("bucket")["next_ret"].agg(["mean", "count"])
summary = summary.reindex(["Low", "Mid", "High"])
display(summary.rename(columns={"mean": "平均收益（小数）", "count": "有效样本数"}))
mean_pct = summary["mean"] * 100
colors = [TEAL if value >= 0 else RED for value in mean_pct]
labels = ["{}\\nn = {}".format(group, int(count)) for group, count in summary["count"].fillna(0).items()]

plt.figure(figsize=(8, 4.8))
plt.bar(range(len(summary)), mean_pct, color=colors, width=0.55, alpha=0.9, zorder=3)
plt.axhline(0, color=MUTED, linewidth=0.9)
for position, value in enumerate(mean_pct):
    if pd.notna(value):
        plt.annotate("{:+.2f}%".format(value), (position, value),
                     xytext=(0, 7 if value >= 0 else -7), textcoords="offset points",
                     ha="center", va="bottom" if value >= 0 else "top", color=INK)
plt.xticks(range(len(summary)), labels)
plt.margins(y=0.3)
plt.title("Mean next-period return by feature bucket")
plt.xlabel("Feature bucket")
plt.ylabel("Mean next-period return (%)")
plt.tight_layout()
plt.show()''',
    },
    "V17": {
        "beauty": "柔和红色面积呈现回撤深度，用深红曲线和箭头标签指出区间最深回撤。",
        "plot": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
wealth = (1 + df["ret"]).cumprod()
peak = wealth.cummax().clip(lower=1)  # 初始净值为 1，首日亏损也应计入回撤
drawdown_pct = (wealth / peak - 1) * 100
worst = drawdown_pct.idxmin()

plt.figure(figsize=(10, 4.8))
plt.fill_between(df["date"], drawdown_pct, 0, color=RED, alpha=0.12)
plt.plot(df["date"], drawdown_pct, color=RED, linewidth=2.2)
plt.axhline(0, color=MUTED, linewidth=0.9)
plt.scatter(df.loc[worst, "date"], drawdown_pct.loc[worst], color=RED,
            s=75, edgecolors="white", zorder=3)
plt.annotate("Worst: {:.2f}%".format(drawdown_pct.loc[worst]),
             (df.loc[worst, "date"], drawdown_pct.loc[worst]),
             xytext=(0, 28), textcoords="offset points", ha="center", color=INK,
             arrowprops={"arrowstyle": "->", "color": RED})
plt.title("Drawdown from previous peak")
plt.xlabel("Date")
plt.ylabel("Drawdown (%)")
plt.margins(y=0.15)
plt.xticks(df["date"], df["date"].dt.strftime("%m-%d"), rotation=30)
plt.tight_layout()
plt.show()''',
    },
    "V18": {
        "beauty": "用青色突出事件最多的小时，柱顶标出计数，零事件小时保留标签和整数纵轴。",
        "plot": '''events = df.assign(timestamp=pd.to_datetime(df["timestamp"]))
events = events.sort_values("timestamp")
counts = events.set_index("timestamp").resample("1h").size()
# 替换成实际已确认完整采集的起止小时；本例最后一格覆盖 14:00–15:00。
hours = pd.date_range("2024-01-08 09:00", "2024-01-08 14:00", freq="1h")
counts = counts.reindex(hours, fill_value=0)  # 只有采集完整时，空小时才能记为零
colors = [TEAL if value == counts.max() else "#99D5CD" for value in counts]

plt.figure(figsize=(9, 4.8))
plt.bar(range(len(counts)), counts.values, color=colors, width=0.6, zorder=3)
for position, value in enumerate(counts):
    plt.annotate(str(value), (position, value), xytext=(0, 6),
                 textcoords="offset points", ha="center", color=INK)
plt.xticks(range(len(counts)), counts.index.strftime("%H:%M"))
plt.yticks(range(int(counts.max()) + 1))
plt.ylim(0, max(counts.max() * 1.2, 1))
plt.title("Events per hour")
plt.xlabel("Hour starting")
plt.ylabel("Number of events")
plt.tight_layout()
plt.show()''',
    },
})

STYLED["V13"]["reading"] = "蓝色表示正收益，红色表示负收益；灰色横杠表示未提供该月数据，不表示收益为零。"
STYLED["V15"]["reading"] = "橙色切分线之前为训练区间，切分线当天及之后为测试区间；浅色背景帮助辨认范围。"
