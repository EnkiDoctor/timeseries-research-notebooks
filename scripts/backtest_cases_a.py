"""Independent, transparent backtest recipes B01-B06 (Python 3.8 compatible)."""

CASES = [
    {
        "id": "B01",
        "title": "单资产：收盘成交，赚取下一段收盘到收盘收益",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=8),
    "close": [100, 102, 101, 104, 103, 105, 102, 104],
    "position": [1.0, 1.0, 0.5, 0.0, 1.0, 0.5, 0.0, 0.0],
})
display(df)''',
        "task": "close 是每日收盘价；position 是当天收盘成交后希望持有的目标资金权重，1=满仓、0=空仓。这里假定 position 在该收盘成交前已经确定，且能按收盘价成交。每天收盘按目标权重再平衡；截至当天收盘的收益由上一行 position 决定，所以 shift(1)。首行开始前为空仓。若信号只能等当天收盘后才能算出，请用 B02。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and df["date"].is_unique
assert np.isfinite(df[["close", "position"]].to_numpy()).all()
assert (df["close"] > 0).all() and df["position"].between(0, 1).all()

# 当天的资产收益，来自上一收盘到当前收盘；首行没有前值。
df["asset_ret"] = df["close"].pct_change(fill_method=None)
df["held_weight"] = df["position"].shift(1, fill_value=0)
df["strategy_ret"] = df["held_weight"] * df["asset_ret"]
df.loc[0, "strategy_ret"] = 0.0  # 首行前没有持仓，不是补齐缺失行情。
df["nav"] = (1 + df["strategy_ret"]).cumprod()
display(df[["date", "close", "position", "held_weight", "asset_ret", "strategy_ret", "nav"]].round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.plot(df["date"], df["nav"], color=BLUE, marker="o", label="Strategy")
plt.plot(df["date"], df["close"] / df["close"].iloc[0], color=TEAL, linestyle="--", label="Buy and hold")
plt.axhline(1, color="grey", linewidth=0.8)
plt.title("Close-to-close strategy")
plt.xlabel("Date")
plt.ylabel("Wealth / initial wealth")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "先在结果表中对照 position 和 held_weight：今天把 position 改为0，不会取消已经持仓经过的上一段收益。图中的两条线从相同资金起点比较。",
        "caution": "本例忽略费用、滑点和现金利息；position 是每天重新设置的目标权重，不是固定股数。价格应包含一致的分红/拆股处理；最后一行的新持仓尚无下一段收益。示例权重只是演示记账，不能解释为有效策略。",
    },
    {
        "id": "B02",
        "title": "收盘后生成信号：下一期开盘成交，按开盘到开盘结算",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=8),
    "open": [100, 102, 101, 104, 102, 105, 103, 106],
    "close_signal": [1.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0, 1.0],
})
display(df)''',
        "task": "open 是当天开盘价；close_signal 是当天收盘后才能知道的目标权重。t日收盘的信号在t+1日开盘成交，从t+1开盘持有到t+2开盘，因此归属t+2行的开盘到开盘收益要乘 close_signal.shift(2)。这里统一在开盘时点观察账户，不混用收盘估值。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and df["date"].is_unique
assert np.isfinite(df[["open", "close_signal"]].to_numpy()).all()
assert (df["open"] > 0).all() and df["close_signal"].between(0, 1).all()

# execute_weight 是此刻开盘成交后仓位；held_weight 是刚结束区间的仓位。
df["execute_weight"] = df["close_signal"].shift(1, fill_value=0)
df["held_weight"] = df["close_signal"].shift(2, fill_value=0)
df["open_to_open_ret"] = df["open"].pct_change(fill_method=None)
df["strategy_ret"] = df["held_weight"] * df["open_to_open_ret"]
df.loc[0, "strategy_ret"] = 0.0  # 数据开始前为空仓。
df["nav"] = (1 + df["strategy_ret"]).cumprod()
display(df[["date", "open", "close_signal", "execute_weight", "held_weight", "open_to_open_ret", "strategy_ret", "nav"]].round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.plot(df["date"], df["nav"], color=BLUE, marker="o", label="Strategy marked at open")
plt.axhline(1, color="grey", linewidth=0.8)
plt.title("Close signal, next-open execution")
plt.xlabel("Date (valuation at market open)")
plt.ylabel("Wealth / initial wealth")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "第1行收盘信号为1，在第2行开盘执行，到第3行开盘才记录它赚取的完整区间收益。因此开头两行策略收益都是0。结果中的执行权重与收益归属权重相差一行。",
        "caution": "shift(2) 只适用于本例的信号时间和收益标签定义，不能机械套用。最后一行信号还没有下一开盘，无法执行；倒数第2行信号虽在最后开盘执行，也没有后续开盘估值。本例忽略费用，并假设信号在下一开盘前已可交易。",
    },
    {
        "id": "B03",
        "title": "日内交易：开盘建仓、收盘平仓，隔夜空仓",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=8),
    "open": [100, 102, 101, 104, 102, 105, 103, 106],
    "close": [101, 101, 103, 103, 104, 104, 106, 105],
    "position": [1.0, 0.5, -0.5, 0.0, 1.0, -1.0, 0.5, 0.0],
})
display(df)''',
        "task": "open/close 是同一天的开/收盘价；position 是当天开盘前已知的资金权重，正数做多、负数做空。每天按开盘价建仓，按当天收盘价全部平仓，隔夜没有持仓。因为position已与要交易的当天对齐，直接乘当天open-to-close收益，不再shift。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and df["date"].is_unique
assert np.isfinite(df[["open", "close", "position"]].to_numpy()).all()
assert (df[["open", "close"]] > 0).all().all()
assert df["position"].between(-1, 1).all()

# 每日开盘使用当前账户资金确定交易名义金额，收盘后全回现金。
df["intraday_ret"] = df["close"] / df["open"] - 1
df["strategy_ret"] = df["position"] * df["intraday_ret"]
assert (1 + df["strategy_ret"] > 0).all(), "账户耗尽时应停止回测并处理清算"
df["nav"] = (1 + df["strategy_ret"]).cumprod()
display(df[["date", "open", "close", "position", "intraday_ret", "strategy_ret", "nav"]].round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.bar(df["date"], df["strategy_ret"] * 100,
        color=np.where(df["strategy_ret"] >= 0, TEAL, RED), width=0.7)
plt.axhline(0, color="grey", linewidth=0.8)
plt.title("Intraday P&L: flat overnight")
plt.xlabel("Date")
plt.ylabel("Daily strategy return (%)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "看负的position遇到价格下跌时是否产生正收益。柱图每根柱子对应一次日内交易日的资金收益；position=0时不参与当天价格变化。",
        "caution": "必须确认position真的在开盘前可知，不能根据当天close反推。本例忽略每天开仓和平仓的两边费用、滑点、借券费和做空约束；隔夜跳空不属于本策略收益。",
    },
    {
        "id": "B04",
        "title": "不规则日内bar：先逐段记账，再复合为每日收益",
        "data": '''df = pd.DataFrame({
    "timestamp": ["2024-01-02 09:30", "2024-01-02 10:40", "2024-01-02 16:00",
                  "2024-01-03 09:30", "2024-01-03 11:15", "2024-01-03 16:00",
                  "2024-01-04 09:30", "2024-01-04 13:10", "2024-01-04 16:00"],
    "price": [100, 101, 102, 99, 100, 103, 104, 102, 105],
    "position": [1.0, 0.5, 0.5, 1.0, 0.0, 1.0, 0.5, 1.0, 0.0],
})
display(df)''',
        "task": "timestamp 是同一个市场的本地时刻，price是该时点成交/估值价格；position在该时点成交前已知。bar的间隔可以不同；用上一时点仓位乘相邻价格收益。本例允许跨夜持仓，所以前一天16:00到次日09:30的变化也计入次日收益。最后按本地自然日复合，不把bar收益直接相加。",
        "backtest": '''df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize("Asia/Hong_Kong")
df = df.sort_values("timestamp").reset_index(drop=True)
assert df["timestamp"].notna().all() and df["timestamp"].is_unique
assert np.isfinite(df[["price", "position"]].to_numpy()).all()
assert (df["price"] > 0).all() and df["position"].between(0, 1).all()

df["bar_ret"] = df["price"].pct_change(fill_method=None)
df["held_weight"] = df["position"].shift(1, fill_value=0)
df["strategy_ret"] = df["held_weight"] * df["bar_ret"]
df.loc[0, "strategy_ret"] = 0.0
df["date"] = df["timestamp"].dt.normalize()
daily = (1 + df["strategy_ret"]).groupby(df["date"]).prod().sub(1).to_frame("daily_ret")
daily["nav"] = (1 + daily["daily_ret"]).cumprod()
display(df[["timestamp", "price", "held_weight", "bar_ret", "strategy_ret"]].round(4))
display(daily.round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.bar(daily.index, daily["daily_ret"] * 100,
        color=np.where(daily["daily_ret"] >= 0, TEAL, RED), width=0.6)
plt.axhline(0, color="grey", linewidth=0.8)
plt.title("Irregular bars aggregated to daily returns")
plt.xlabel("Local calendar date")
plt.ylabel("Compounded daily return (%)")
plt.xticks(daily.index, daily.index.strftime("%Y-%m-%d"))
plt.tight_layout()
plt.show()''',
        "reading": "逐bar表展示收益具体来自哪个区间；每日表把属于同一天的这些区间按(1+r)连乘。隔夜跳空被计入区间终点所在日，因此早盘那根bar不只是开盘后的收益。",
        "caution": "不按bar数直接套sqrt(252)或假设每bar等时长。这里自然日正好对应示例交易日；期货夜盘应使用交易所session标签分组。缺失行情先查原因，不能任意补0；本例默认相邻记录间持续持仓、首日从09:30开始，不含更早区间，且每个记录时点再平衡。",
    },
    {
        "id": "B05",
        "title": "真实成交费用：用现金和股数记账，精确调整目标权重",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=8),
    "close": [100, 102, 101, 104, 103, 105, 102, 104],
    "target_weight": [0.8, 0.8, 0.4, 0.4, 0.9, 0.9, 0.4, 0.0],
})
display(df)''',
        "task": "close是执行和估值价格；target_weight是当日收盘成交前已知的、费后账户权益中股票应占比例，范围0到1。每个时点先按现价估值，再交易到目标；手续费=实际买入或卖出名义金额×fee_rate。本例允许小数股，初始资金10000、单边费率10bp，最后目标为0表示平仓。用cash/shares可正确处理价格引起的权重漂移：目标不变时也可能有交易。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and df["date"].is_unique
assert np.isfinite(df[["close", "target_weight"]].to_numpy()).all()
assert (df["close"] > 0).all() and df["target_weight"].between(0, 1).all()
initial_cash, fee_rate = 10000.0, 0.001
cash, shares = initial_cash, 0.0
records = []

for row in df.itertuples(index=False):
    old_stock_value = shares * row.close
    equity_before = cash + old_stock_value  # 交易前按当前价格估值
    w = row.target_weight
    gap = w * equity_before - old_stock_value
    # 解 trade = w * (equity_before - fee_rate * abs(trade)) - old_stock_value。
    # trade>0买入，trade<0卖出；保证最终股票权重等于w，而非费用前近似。
    trade = gap / (1 + w * fee_rate) if gap >= 0 else gap / (1 - w * fee_rate)
    cost = abs(trade) * fee_rate
    shares += trade / row.close
    cash -= trade + cost
    equity = cash + shares * row.close
    assert equity > 0 and cash >= -1e-8
    records.append([cash, shares, trade, cost, abs(trade) / equity_before, equity])

result = pd.DataFrame(records, columns=["cash", "shares", "trade_value", "cost", "turnover", "equity"])
result = pd.concat([df, result], axis=1)
# 第一行费用不能丢：分母用初始资金，而不是第一行交易后的equity。
result["period_ret"] = result["equity"] / result["equity"].shift(1, fill_value=initial_cash) - 1
result["nav"] = result["equity"] / initial_cash
result["drawdown"] = result["equity"] / result["equity"].cummax().clip(lower=initial_cash) - 1
result["actual_weight"] = result["shares"] * result["close"] / result["equity"]
assert np.allclose(result["actual_weight"], result["target_weight"])
display(result[["date", "target_weight", "actual_weight", "trade_value", "cost", "turnover", "equity", "nav", "drawdown"]].round(4))
display(pd.DataFrame({"total_cost": [result["cost"].sum()], "net_return": [result["nav"].iloc[-1] - 1], "max_drawdown": [result["drawdown"].min()]}).round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.plot(result["date"], result["nav"], color=BLUE, marker="o", label="After trading fees")
plt.axhline(1, color="grey", linewidth=0.8, label="Initial capital")
plt.title("Cash-and-shares account with transaction fees")
plt.xlabel("Date")
plt.ylabel("Wealth / initial capital")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "看前两行：目标权重同为0.8，但价格上涨后原股票占比变大，仍需卖出一小部分，因此有真实费用。首行净值略低于1是首次建仓费；末行费用包含全部平仓。",
        "caution": "此模板限单资产、只做多、现金收益0、小数股、每次收盘再平衡；手续费按买卖成交绝对金额计，不除以2。turnover=当次成交名义金额/交易前权益；不是target_weight.diff()。本例不处理冲击成本、最低手续费、整数股、税费或拆股分红现金流；若close是原始价格，需另记这些企业行动。",
    },
    {
        "id": "B06",
        "title": "多资产宽表：先合并每日持仓收益，再复合组合净值",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=8),
    "price_A": [100, 102, 101, 104, 103, 105, 102, 104],
    "price_B": [50, 49, 50, 51, 50, 49, 50, 51],
    "weight_A": [0.6, 0.6, 0.5, 0.5, 0.0, 0.5, 0.0, 0.0],
    "weight_B": [0.4, 0.4, -0.5, -0.5, 0.0, -0.5, 0.0, 0.0],
})
display(df)''',
        "task": "每个日期一行，price_A/B为两资产同一收盘时点的价格；weight_A/B为该收盘成交前已知的组合资金目标权重。0.6/0.4表示60%/40%多头；0.5/-0.5表示50%做多A、50%做空B。每天再平衡，以前一天权重乘当天各资产收益，并逐行求和得到组合收益；最后只对组合收益做cumprod。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and df["date"].is_unique
assert np.isfinite(df[["price_A", "price_B", "weight_A", "weight_B"]].to_numpy()).all()
assert (df[["price_A", "price_B"]] > 0).all().all()
assert (df[["weight_A", "weight_B"]].abs().sum(axis=1) <= 1 + 1e-12).all()

returns = df[["price_A", "price_B"]].pct_change(fill_method=None)
returns.columns = ["A", "B"]
weights = df[["weight_A", "weight_B"]].copy()
weights.columns = ["A", "B"]  # 标签对齐后相乘，避免列名不同产生NaN。
held = weights.shift(1, fill_value=0)
contribution = held * returns
contribution.iloc[0] = 0.0  # 首行之前明确没有持仓。
df["contribution_A"] = contribution["A"]
df["contribution_B"] = contribution["B"]
df["strategy_ret"] = contribution.sum(axis=1, min_count=2)
assert df["strategy_ret"].notna().all() and (1 + df["strategy_ret"] > 0).all()
df["gross_exposure"] = held.abs().sum(axis=1)
df["net_exposure"] = held.sum(axis=1)
df["nav"] = (1 + df["strategy_ret"]).cumprod()
display(df[["date", "weight_A", "weight_B", "contribution_A", "contribution_B", "strategy_ret", "gross_exposure", "net_exposure", "nav"]].round(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.plot(df["date"], df["nav"], color=BLUE, marker="o", label="Portfolio")
plt.axhline(1, color="grey", linewidth=0.8)
plt.title("Portfolio wealth after combining asset returns")
plt.xlabel("Date")
plt.ylabel("Wealth / initial wealth")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()''',
        "reading": "结果中contribution_A和contribution_B相加恰好是strategy_ret。50%多A、50%空B时net_exposure为0，但gross_exposure为1，仍然承担价格风险；空仓区间净值不变。",
        "caution": "假定日频再平衡、收益价格口径一致且包含相应分红拆股调整，现金利息与融资成本为0，忽略费用及借券约束。首行没有历史持仓；表中gross/net为刚结束区间的持仓敞口。不能先把各资产独立复合，再相加当作动态再平衡组合；缺失资产收益也不能默认当0。",
    },
]
