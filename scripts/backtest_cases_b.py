"""Self-contained backtest recipes B07–B12; notebook building data only."""

CASES = [
    {
        "id": "B07",
        "title": "多资产长表：上一期权重 × 当期资产收益",
        "data": '''df = pd.DataFrame({
    "date": np.repeat(pd.bdate_range("2025-01-06", periods=6), 2),
    "asset": ["A", "B"] * 6,
    "price": [100, 50, 102, 49, 101, 50, 104, 51, 103, 52, 105, 51],
    "weight": [0.6, 0.4, 0.6, 0.4, 0.3, 0.7, 0.3, 0.7, 0.5, 0.5, 0.5, 0.5],
})
display(df)''',
        "task": "输入是 date / asset / price / weight 长表，每个日期必须有所有资产的有效价格和目标权重。weight 是交易前已知、在该日收盘成交后的目标权重，只赚下一行的收盘到收盘收益。任务：先核对共同日历，再计算逐资产贡献和组合净值。本例每日再平衡、允许零权重现金、不收费用；首行没有历史持仓收益。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["date", "asset"]).reset_index(drop=True)
assert df[["date", "asset"]].notna().all().all(), "日期/资产不能为空"
assert not df.duplicated(["date", "asset"]).any(), "同一日期/资产不能有重复记录"

# pivot 会把某日缺少的资产变成 NaN：先拒绝，不能把缺报价当作 0 收益。
prices = df.pivot(index="date", columns="asset", values="price")
targets = df.pivot(index="date", columns="asset", values="weight").reindex_like(prices)
assert np.isfinite(prices.to_numpy()).all() and prices.gt(0).all().all(), "先处理缺价/无效价格"
assert np.isfinite(targets.to_numpy()).all(), "每个日期/资产都要有明确目标权重"
assert targets.ge(0).all().all() and targets.sum(axis=1).le(1 + 1e-10).all()

asset_return = prices.pct_change(fill_method=None)
held_weight = targets.shift(1, fill_value=0)  # 上日收盘后持仓，赚当日区间收益
contribution = held_weight * asset_return
contribution.iloc[0] = 0  # 只处理首行：没有此前持仓，不是填补中途缺价
portfolio_return = contribution.sum(axis=1, skipna=False)
nav = (1 + portfolio_return).cumprod()

# asset_return 首行保留 NaN，清楚表示“没有前一日价格”。
result = df.set_index(["date", "asset"])[["price", "weight"]].copy()
result["held_weight"] = held_weight.stack()
result["asset_return"] = asset_return.stack()  # 按索引对齐后，首行仍为 NaN
result["contribution"] = contribution.stack()
display(result.reset_index().round(4))
daily = pd.DataFrame({"portfolio_return": portfolio_return, "nav": nav})
display(daily.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
plt.plot(daily.index, daily["nav"], color=BLUE, marker="o", linewidth=2)
plt.axhline(1, color="grey", linestyle="--", linewidth=1)
plt.title("Multi-asset portfolio: daily rebalancing")
plt.xlabel("Date")
plt.ylabel("NAV (initial = 1)")
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "先看长表中的 held_weight：必须是同一资产上一日的目标权重。每天 contribution 加总后得到组合收益，再复合成 NAV；资产不能串行 shift，否则 A 会错用 B 的记录。",
        "caution": "本例的目标权重每天重置，所以不是买入后持有。没有手续费、利息和滑点；若加交易费，换手必须与价格变化后的真实权重比较。完整共同日历仅按输入中的日期检查：若所有资产同时缺掉一个应交易日，仍须用交易所日历另行检查。",
    },
    {
        "id": "B08",
        "title": "每周再平衡：固定股数持有，权重自然漂移",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2025-01-06", periods=10),
    "price_a": [100, 103, 101, 105, 107, 106, 108, 104, 109, 111],
    "price_b": [50, 49, 50, 49, 48, 49, 47, 50, 49, 48],
    "rebal": [True, False, False, False, False, True, False, False, False, False],
    "target_a": [0.6] * 10,
    "target_b": [0.4] * 10,
})
display(df)''',
        "task": "输入包含两只资产价格、再平衡标记 rebal 和目标权重。任务：仅在 rebal=True 的收盘按目标权重交易，其余日期固定股数、按价格估值，展示实际权重漂移和账户净值。目标权重须在成交前已知；初始资金 10,000，允许碎股，现金无利息，本例费用为 0。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and not df["date"].duplicated().any()
assert df["rebal"].isin([True, False]).all()
assert np.isfinite(df[["price_a", "price_b"]].to_numpy()).all()
assert df[["price_a", "price_b"]].gt(0).all().all()
assert np.isfinite(df[["target_a", "target_b"]].to_numpy()).all()
assert df[["target_a", "target_b"]].ge(0).all().all()
assert df[["target_a", "target_b"]].sum(axis=1).le(1 + 1e-10).all()

initial_cash = 10000.0
cash, shares_a, shares_b = initial_cash, 0.0, 0.0
history = []
for row in df.itertuples(index=False):
    equity = cash + shares_a * row.price_a + shares_b * row.price_b
    if row.rebal:
        # 先按当前价格估值，再重新配置股数。无费用，所以交易不改变权益。
        shares_a = equity * row.target_a / row.price_a
        shares_b = equity * row.target_b / row.price_b
        cash = equity - shares_a * row.price_a - shares_b * row.price_b
    history.append({"date": row.date, "rebal": row.rebal,
                    "shares_a": shares_a, "shares_b": shares_b,
                    "weight_a": shares_a * row.price_a / equity,
                    "weight_b": shares_b * row.price_b / equity,
                    "cash": cash, "equity": equity, "nav": equity / initial_cash})

result = pd.DataFrame(history)
display(result.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
plt.plot(result["date"], result["weight_a"] * 100, color=BLUE, marker="o", label="A: actual weight")
plt.plot(result["date"], result["weight_b"] * 100, color=TEAL, marker="o", label="B: actual weight")
# 虚线标记真正调仓日，其余日期的权重会随价格变化。
for day in result.loc[result["rebal"], "date"]:
    plt.axvline(day, color=ORANGE, linestyle="--", alpha=0.5)
plt.title("Weekly rebalancing and weight drift")
plt.xlabel("Date")
plt.ylabel("Actual portfolio weight (%)")
plt.legend()
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "橙色虚线当天收盘后，权重回到 60% / 40%。两次调仓之间 shares_a 和 shares_b 不变，但实际权重变化，这就是持仓漂移。收益表现可直接查看表中的 equity 或 nav。",
        "caution": "把周目标权重 ffill 到每天后再乘日收益，会实现每日恢复目标权重的另一种策略。需要真实费用时，应按新旧股数差乘成交价计费，并调整现金或可买数量；不能直接沿用本例的无费全额配置。",
    },
    {
        "id": "B09",
        "title": "每天固定金额开平仓：累计金额损益，不复合交易收益",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2025-01-06", periods=10),
    "open": [100, 102, 101, 103, 104, 103, 105, 104, 106, 107],
    "close": [102, 101, 103, 104, 103, 105, 104, 106, 107, 106],
    "amount": [1000.0] * 10,
})
display(df)''',
        "task": "每天用固定 1,000 元按 open 买入，并在当天 close 全部卖出；amount 不随盈利增长。任务：计算每日金额损益和初始 3,000 元账户的资金曲线，与简单固定投入示例对应。策略在开盘前已确定，允许碎股，忽略费用；每天收盘之后全部为现金。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and not df["date"].duplicated().any()
assert np.isfinite(df[["open", "close", "amount"]].to_numpy()).all()
assert df[["open", "close", "amount"]].gt(0).all().all()
assert df["amount"].nunique() == 1, "这个模板专门用于每日固定金额"

initial_cash = 3000.0
result = df.copy()
result["trade_return"] = result["close"] / result["open"] - 1
result["pnl"] = result["amount"] * result["trade_return"]
result["cash_before"] = initial_cash + result["pnl"].cumsum().shift(1, fill_value=0)
if (result["cash_before"] < result["amount"] - 1e-10).any():
    raise ValueError("某天开盘前现金不足，不能继续按固定金额买入")
result["equity"] = initial_cash + result["pnl"].cumsum()
# 账户收益率的分母是当日开盘前账户权益，不能误用 1,000 元交易本金。
result["account_return"] = result["pnl"] / result["cash_before"]
result["nav"] = result["equity"] / initial_cash
display(result.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
plt.plot(result["date"], result["equity"] - initial_cash,
         color=BLUE, marker="o", linewidth=2)
plt.axhline(0, color="grey", linestyle="--", linewidth=1)
plt.title("Fixed daily amount: cumulative P&L")
plt.xlabel("Date")
plt.ylabel("Cumulative P&L (currency)")
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "这条线是 pnl.cumsum()，每天投入仍是 1,000 元。trade_return 描述当天这笔交易；account_return 描述整个 3,000 元起始账户，两者分母不同。",
        "caution": "不能对 trade_return 直接 cumprod 后宣称是该固定金额账户的净值。当天开盘后才能观测到的信息不能反过来决定当天开盘成交；若信号来自开盘价本身，需要换成更晚的可成交价格。本例没有隔夜持仓、交易费用和融资。",
    },
    {
        "id": "B10",
        "title": "买入 / 持有 / 卖出指令：现金与股数账本",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2025-01-06", periods=10),
    "price": [100, 102, 101, 104, 103, 105, 103, 107, 108, 106],
    "order": ["buy", "hold", "buy", "sell", "hold", "buy", "buy", "hold", "sell", "buy"],
})
display(df)''',
        "task": "order 是成交前已经可执行的外部指令，price 是对应成交及估值价格。任务：buy 每次买入 1,000 元名义金额，重复 buy 继续加仓；sell 清空全部股数；hold 不交易。初始现金 5,000 元，买卖每边费率 10 bps，按成交金额扣费，允许碎股。输出现金、股数、手续费和账户权益。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and not df["date"].duplicated().any()
assert np.isfinite(df["price"].to_numpy()).all() and df["price"].gt(0).all()
assert df["order"].isin(["buy", "hold", "sell"]).all()

initial_cash, ticket, fee_rate = 5000.0, 1000.0, 10 / 10000
cash, shares, previous_equity = initial_cash, 0.0, initial_cash
history = []
for row in df.itertuples(index=False):
    fee, trade_notional = 0.0, 0.0
    if row.order == "buy":
        fee = ticket * fee_rate
        if cash < ticket + fee - 1e-10:
            raise ValueError("现金不足以支付买入金额和手续费")
        shares += ticket / row.price  # 再次 buy 会累加股数
        cash -= ticket + fee
        trade_notional = ticket
    elif row.order == "sell":
        trade_notional = -shares * row.price
        fee = abs(trade_notional) * fee_rate
        cash += shares * row.price - fee
        shares = 0.0
    equity = cash + shares * row.price  # 未卖出的持仓也按市场价格计入权益
    history.append({"date": row.date, "order": row.order, "price": row.price,
                    "trade_notional": trade_notional, "fee": fee,
                    "cash": cash, "shares": shares, "equity": equity,
                    "account_return": equity / previous_equity - 1})
    previous_equity = equity

result = pd.DataFrame(history)
display(result.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
plt.plot(result["date"], result["equity"], color=BLUE, linewidth=2, label="Account equity")
for order, marker, color in [("buy", "^", TEAL), ("sell", "v", RED)]:
    traded = result["order"].eq(order) & result["trade_notional"].ne(0)
    plt.scatter(result.loc[traded, "date"], result.loc[traded, "equity"],
                marker=marker, color=color, s=65, label=order)
plt.axhline(initial_cash, color="grey", linestyle="--", linewidth=1)
plt.title("Event-driven account with trading fees")
plt.xlabel("Date")
plt.ylabel("Equity (currency)")
plt.legend()
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "绿色三角表示加仓，红色三角表示清仓。第一笔买入就支付手续费，因此首日权益是 4,999 而不是 5,000；account_return 已包含这一笔成本。",
        "caution": "最后一天不自动清仓：未平仓部分按市价估值，未来卖出费用尚未计入。持有期间股数固定，因此可复用到更复杂的指令系统。若 order 从当日收盘数据生成，不能假装仍可在同一收盘价成交；应改用下一次真实可交易的价格。",
    },
    {
        "id": "B11",
        "title": "双腿配对交易：分别计算两条腿的收益贡献",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2025-01-06", periods=10),
    "price_a": [100, 102, 101, 103, 102, 104, 106, 105, 107, 108],
    "price_b": [50, 50.5, 51, 51.5, 51, 52.5, 52, 53, 53.5, 54],
    "side": [1, 1, 0, -1, -1, 0, 1, 1, -1, 0],
})
display(df)''',
        "task": "side=1 表示多 A / 空 B，side=-1 表示空 A / 多 B，side=0 空仓；非零时每条腿的绝对权重均为 0.5，总绝对敞口为账户权益的 100%。side 在该行收盘成交前已知，持仓赚下一行区间收益。任务：用真实两条腿收益算组合收益和逐腿累计金额损益，不能把价差当作可投资价格。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and not df["date"].duplicated().any()
assert np.isfinite(df[["price_a", "price_b"]].to_numpy()).all()
assert df[["price_a", "price_b"]].gt(0).all().all()
assert df["side"].isin([-1, 0, 1]).all()

initial_cash = 10000.0
returns = df[["price_a", "price_b"]].pct_change(fill_method=None)
returns.iloc[0] = 0  # 首行没有此前持仓；中途缺价格已在上方拒绝
held_side = df["side"].shift(1, fill_value=0)
contribution_a = 0.5 * held_side * returns["price_a"]
contribution_b = -0.5 * held_side * returns["price_b"]
portfolio_return = contribution_a + contribution_b
assert portfolio_return.gt(-1).all(), "权益耗尽，需另写破产/保证金规则"
equity = initial_cash * (1 + portfolio_return).cumprod()
equity_before = equity.shift(1, fill_value=initial_cash)

result = df[["date", "side"]].copy()
result["held_side"] = held_side
result["pnl_a"] = equity_before * contribution_a
result["pnl_b"] = equity_before * contribution_b
result["portfolio_return"] = portfolio_return
result["equity"] = equity
display(result.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
plt.plot(result["date"], result["pnl_a"].cumsum(), color=BLUE, label="Leg A cumulative P&L")
plt.plot(result["date"], result["pnl_b"].cumsum(), color=TEAL, label="Leg B cumulative P&L")
plt.plot(result["date"], result["equity"] - initial_cash,
         color=ORANGE, linewidth=2.5, label="Total cumulative P&L")
plt.axhline(0, color="grey", linewidth=1)
plt.title("Pair trade: additive leg P&L attribution")
plt.xlabel("Date")
plt.ylabel("Cumulative P&L (currency)")
plt.legend()
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "蓝线与绿线逐点相加必须等于橙线。先用同一份期初账户权益把逐腿收益贡献转成金额损益，然后分别 cumsum；不能把两条腿各自 cumprod 后再加总。",
        "caution": "本例每日按当前权益重置双腿权重，忽略交易费、借券费、融资和保证金限制，不是固定股数的价差仓位。price_a - price_b 可能过零，spread.pct_change() 既可能爆炸，也没有定义清楚投入资本；不能代替两条腿 P&L。若 side 来自当天收盘价，应延后至下一可交易时点执行。",
    },
    {
        "id": "B12",
        "title": "每次持有三期：三个错峰子账户处理重叠交易",
        "data": '''df = pd.DataFrame({
    "date": pd.bdate_range("2025-01-06", periods=12),
    "price": [100, 102, 101, 104, 103, 105, 107, 106, 108, 105, 109, 110],
    "signal": [1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1],
})
display(df)''',
        "task": "每天产生一个交易前已知的 0/1 信号，每笔多头从该日收盘持有到第三个后续观测的收盘。任务：初始 3,000 元平均分到三个错峰子账户，每天轮到一个子账户先结束旧持仓，再按信号开新仓；其余子账户固定股数持有。允许碎股、无手续费，未开仓资金留现金。",
        "backtest": '''df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].notna().all() and not df["date"].duplicated().any()
assert np.isfinite(df["price"].to_numpy()).all() and df["price"].gt(0).all()
assert df["signal"].isin([0, 1]).all()

initial_cash, holding_bars = 3000.0, 3
sleeve_cash = np.full(holding_bars, initial_cash / holding_bars)
sleeve_shares = np.zeros(holding_bars)
history = []
previous_equity = initial_cash
for t, row in enumerate(df.itertuples(index=False)):
    k = t % holding_bars  # 0,1,2,0,1,2...：每个子账户隔三期轮到一次
    # 仅轮到的子账户到期；其他子账户的股数保持不变。
    sleeve_cash[k] += sleeve_shares[k] * row.price
    sleeve_shares[k] = 0.0
    if row.signal == 1:
        sleeve_shares[k] = sleeve_cash[k] / row.price
        sleeve_cash[k] = 0.0
    values = sleeve_cash + sleeve_shares * row.price
    equity = values.sum()
    history.append({"date": row.date, "price": row.price, "signal": row.signal,
                    "rotating_sleeve": k + 1,
                    "value_1": values[0], "value_2": values[1], "value_3": values[2],
                    "cash": sleeve_cash.sum(), "equity": equity,
                    "account_return": equity / previous_equity - 1})
    previous_equity = equity

result = pd.DataFrame(history)
display(result.round(4))''',
        "plot": '''plt.figure(figsize=(9, 4))
for column, label, color in [("value_1", "Sleeve 1", BLUE),
                              ("value_2", "Sleeve 2", TEAL),
                              ("value_3", "Sleeve 3", ORANGE)]:
    plt.plot(result["date"], result[column] / (initial_cash / holding_bars),
             color=color, alpha=0.65, label=label)
plt.plot(result["date"], result["equity"] / initial_cash,
         color="black", linewidth=2.5, label="Total NAV")
plt.axhline(1, color="grey", linestyle="--", linewidth=1)
plt.title("Three-bar holdings with staggered sleeves")
plt.xlabel("Date")
plt.ylabel("NAV (initial = 1)")
plt.legend(ncol=2)
plt.xticks(rotation=30, ha="right")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "子账户 1 在第 0、3、6、9 行轮换；子账户 2、3 错开一行、两行。同一天可能有三笔重叠持仓，但每笔用不同的资金。总 NAV 是三个子账户 NAV 的平均，因为初始资本均等。",
        "caution": "三个子账户仅在起点各占总资本 1/3，之后各自盈利再投入，其占比会漂移，不能宣称每天维持 1/3。每笔持有三个观测区间，不一定是三个自然日。末端尚未到期的交易只按市价估值，不强行平仓；实际缺失交易日需先补齐/定义交易日历。多日 forward return 是评估标签，不能逐日 cumprod 当作可执行账户收益。",
    },
]
