"""Risk sizing, evaluation and visual reporting cases for the backtest cheat sheet."""

CASES = [
    {
        'id': 'B13',
        'title': '波动率目标仓位：只使用交易前已经知道的风险',
        'data': '''
df = pd.DataFrame({
    'open':  [100, 101, 99, 102, 101, 104, 103, 106, 104, 102, 105, 107],
    'close': [101, 99, 102, 101, 104, 103, 106, 104, 102, 105, 107, 106],
}, index=pd.bdate_range('2024-01-08', periods=12))
display(df)
''',
        'task': '''**场景：** 希望波动大时少持仓、波动小时多持仓。输入为日频 `open / close`，每行代表一场交易会话。

**要做什么：** 用截至 t 日收盘的历史收益估计波动，决定 t+1 日开盘的仓位；持有至下一开盘。表中的 `asset_return[t]` 结束于 t 日开盘，所以乘的是 t−2 日收盘计算的权重。例中窗口 3 天便于手算，真实研究可事先选择更长窗口。''',
        'backtest': '''
result = df.sort_index().copy()
assert result.index.is_unique
assert np.isfinite(result[['open', 'close']]).all().all()
assert (result[['open', 'close']] > 0).all().all()
window, periods_per_year = 3, 252
target_vol, max_weight = 0.10, 1.0
close_return = result['close'].pct_change(fill_method=None)
result['estimated_vol'] = close_return.rolling(window).std(ddof=1) * np.sqrt(periods_per_year)
# 0 波动/预热不足时不下单；目标仅是风险估计，并不保证未来实现波动。
valid_vol = result['estimated_vol'].where(result['estimated_vol'] > 0)
result['weight_at_close'] = (target_vol / valid_vol).clip(upper=max_weight).fillna(0)
result['holding'] = result['weight_at_close'].shift(2, fill_value=0)
result['asset_return'] = result['open'].pct_change(fill_method=None)
result.iloc[0, result.columns.get_loc('asset_return')] = 0
result['strategy_return'] = result['holding'] * result['asset_return']
result['nav'] = (1 + result['strategy_return']).cumprod()
# 比较基准也从最早能够使用同一历史窗口的开盘开始。
eligible = result['estimated_vol'].notna().shift(2, fill_value=False)
result['fixed_nav'] = (1 + eligible * result['asset_return']).cumprod()
display(result.round(4))
''',
        'plot': '''
plt.figure(figsize=(10, 4))
plt.plot(result.index, result['nav'], color=BLUE, marker='o', label='Volatility target')
plt.plot(result.index, result['fixed_nav'], color=TEAL, linestyle='--', label='100% weight, same start')
plt.axhline(1, color='grey', linewidth=0.8)
plt.title('Risk sizing: compare the same trading period')
plt.xlabel('Valuation at open')
plt.ylabel('NAV (initial capital = 1)')
plt.legend()
plt.tight_layout()
plt.show()
''',
        'reading': '先在结果表核对 estimated_vol → weight_at_close → holding 的两行延迟，再看风险控制是否改变净值路径。收益不一定提高。',
        'caution': '这是无成本、每日开盘再平衡的 long-only 演示；现金收益为 0。252 只适用于已核对的交易日日频。最后两行收盘权重没有完整的后续开盘到开盘收益，不把它们补成盈利或亏损。',
    },
    {
        'id': 'B14',
        'title': '样本外回测：训练集定候选、验证集选阈值、测试集只评一次',
        'data': '''
df = pd.DataFrame({
    'open': [100.0] * 18,
    'close': [101, 99, 102, 98, 101, 100, 102, 99, 101,
              98, 103, 101, 99, 102, 98, 101, 100, 103],
    'score_before_open': [0.2, -0.5, 0.8, -0.9, 0.4, -0.1,
                          0.7, -0.2, 0.6, -0.8, 0.9, 0.3,
                          0.8, 0.4, -0.7, -0.3, 0.1, 0.9],
    'split': ['train'] * 6 + ['validation'] * 6 + ['test'] * 6,
}, index=pd.bdate_range('2024-01-08', periods=18))
display(df)
''',
        'task': '''**场景：** 已有盘前可用的预测分数，想测试“分数大于阈值做多、小于负阈值做空，否则空仓”。`split` 是事先划好的连续时间区间。

**要做什么：** 用训练分数生成 3 个候选阈值，只在验证集比较；锁定阈值后算测试集净收益。每天开盘建仓、收盘全部平仓，因此本例没有跨边界持仓，也没有重叠多日标签。输入分数为手工演示；真实模型必须在生成每个分数之前完成训练，标准化也只能拟合历史训练数据。''',
        'backtest': '''
result = df.sort_index().copy()
assert result.index.is_unique
assert np.isfinite(result[['open', 'close', 'score_before_open']]).all().all()
assert (result[['open', 'close']] > 0).all().all()
assert set(result['split']) == {'train', 'validation', 'test'}
train = result['split'].eq('train')
valid = result['split'].eq('validation')
test = result['split'].eq('test')
assert result.index[train].max() < result.index[valid].min()
assert result.index[valid].max() < result.index[test].min()
result['asset_return'] = result['close'] / result['open'] - 1
fee_rate, gross_weight = 5 / 10000, 0.8
candidates = np.unique(result.loc[train, 'score_before_open'].abs().quantile([0.25, 0.5, 0.75]))
rows = []
for threshold in candidates:
    score = result.loc[valid, 'score_before_open']
    weight = np.sign(score) * score.abs().gt(threshold) * gross_weight
    r = result.loc[valid, 'asset_return']
    # 每天都开平仓：入场名义金额 |w|，出场名义金额 |w|*(1+r)。
    net = weight * r - fee_rate * weight.abs() * (2 + r)
    assert (net > -1).all()
    rows.append([threshold, (1 + net).prod() - 1])
selection = pd.DataFrame(rows, columns=['threshold', 'validation_net_return'])
best_threshold = selection.loc[selection['validation_net_return'].idxmax(), 'threshold']
# 到这里才使用 test 的实际收益；同分时使用候选列表中较小的阈值。
oos = result.loc[test].copy()
score = oos['score_before_open']
oos['weight'] = np.sign(score) * score.abs().gt(best_threshold) * gross_weight
oos['cost'] = fee_rate * oos['weight'].abs() * (2 + oos['asset_return'])
oos['strategy_return'] = oos['weight'] * oos['asset_return'] - oos['cost']
assert (oos['strategy_return'] > -1).all()
oos['nav'] = (1 + oos['strategy_return']).cumprod()
display(selection.round(4))
print('Locked threshold:', round(best_threshold, 4))
display(oos.round(4))
''',
        'plot': '''
# 用第0期本金作起点，避免把测试首日亏损藏掉。
x = np.arange(len(oos) + 1)
plt.figure(figsize=(10, 4))
plt.plot(x, np.r_[1, oos['nav'].to_numpy()], color=BLUE, marker='o')
plt.axhline(1, color='grey', linewidth=0.8)
plt.title('Held-out test: threshold locked before this period')
plt.xlabel('Test trading day (0 = initial capital)')
plt.ylabel('Net NAV')
plt.tight_layout()
plt.show()
''',
        'reading': '验证集表用于选参数，图只画锁定参数后的测试净值。即使测试表现不好，也先报告结果，再把新想法留给新的未见样本。',
        'caution': '本例允许做空，忽略借券费、保证金、滑点与成交容量；fee_rate 为单边费率。训练/验证/测试各 6 行只展示流程，不能说明泛化能力。若改成 h 日标签，应按标签结束/可用时间 purge 跨边界样本；不能只按特征日期切分。',
    },
    {
        'id': 'B15',
        'title': '绩效表与回撤：从每日净收益计算，不漏掉首日亏损',
        'data': '''
df = pd.DataFrame({
    'strategy_return': [-0.02, 0.01, 0.015, -0.03, 0.01, -0.01,
                         0.025, 0.015, -0.005, 0.01, 0.005, -0.01],
}, index=pd.bdate_range('2024-01-08', periods=12))
display(df)
''',
        'task': '''**场景：** 已经得到每个交易日的账户净收益 `strategy_return`（已扣本策略应计成本；空仓日也有一行）。

**要做什么：** 给出累计收益、按 252 期口径的几何年化收益、波动、Sharpe、最大回撤、最长水下期数和上涨日比例，再画回撤。首日亏损必须相对于初始净值 1 计算。''',
        'backtest': '''
result = df.sort_index().copy()
assert result.index.is_unique
r = result['strategy_return']
assert len(r) >= 2 and np.isfinite(r).all() and (r > -1).all()
periods_per_year, risk_free_annual = 252, 0.0
rf_per_day = (1 + risk_free_annual) ** (1 / periods_per_year) - 1
result['nav'] = (1 + r).cumprod()
result['high_watermark'] = result['nav'].cummax().clip(lower=1)
result['drawdown'] = result['nav'] / result['high_watermark'] - 1
underwater = result['drawdown'].lt(-1e-12)
# 连续水下“观测期数”，并非自然日；尚未恢复的最后一段也计入。
result['underwater_periods'] = underwater.groupby((~underwater).cumsum()).cumsum()
annual_return = result['nav'].iloc[-1] ** (periods_per_year / len(r)) - 1
annual_vol = r.std(ddof=1) * np.sqrt(periods_per_year)
sharpe = (r - rf_per_day).mean() / r.std(ddof=1) * np.sqrt(periods_per_year) if r.std(ddof=1) > 0 else np.nan
max_drawdown = result['drawdown'].min()
summary = pd.DataFrame({
    'value': [len(r), result['nav'].iloc[-1] - 1, annual_return, annual_vol,
              sharpe, max_drawdown, result['underwater_periods'].max(), (r > 0).mean()],
    'unit': ['periods', 'decimal return', 'decimal / year', 'decimal / sqrt(year)',
             'ratio', 'decimal', 'periods', 'fraction of ALL days'],
}, index=['observations', 'total_return', 'annualized_return', 'annualized_volatility',
          'Sharpe', 'max_drawdown', 'longest_underwater', 'positive_day_fraction'])
display(summary.round(4))
display(result.round(4))
''',
        'plot': '''
x = np.arange(len(result) + 1)
drawdown_pct = np.r_[0, result['drawdown'].to_numpy() * 100]
plt.figure(figsize=(10, 4))
plt.fill_between(x, drawdown_pct, 0, color=RED, alpha=0.20)
plt.plot(x, drawdown_pct, color=RED)
plt.axhline(0, color='grey', linewidth=0.8)
plt.title('Drawdown includes the initial capital baseline')
plt.xlabel('Trading day (0 = initial capital)')
plt.ylabel('Drawdown (%)')
plt.tight_layout()
plt.show()
''',
        'reading': '先看样本长度、总收益和最大回撤。第一天跌 2%，回撤就是 −2%，不能因为第一天成了 cummax 的起点而显示 0。上涨日比例是按天统计，不能称为每笔交易胜率。',
        'caution': '12 个合成日只用来演示计算，年化数字极不稳定。这里的年化收益按 252 个观测期缩放，不是自然日 CAGR；若观测不规则，先建立完整每日权益序列。sqrt(252) 是常见尺度换算，有自相关时 Sharpe 的这种年化可能失真；不能视为显著性检验。',
    },
    {
        'id': 'B16',
        'title': '月度收益热图：空白月份与未结束月份分开处理',
        'data': '''
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-30', '2024-01-31', '2024-02-01', '2024-02-29',
                            '2024-03-01', '2024-03-28', '2024-04-01', '2024-04-12']),
    'strategy_return': [0.01, -0.005, 0.015, 0.003, -0.02, 0.005, 0.012, -0.003],
    'month_complete': [False, False, True, True, True, True, False, False],
})
display(df)
''',
        'task': '''**场景：** 把已经得到的每日净收益做月度汇报。`month_complete` 必须根据外部交易日历和采集覆盖范围事先确定，同一个月应一致；不能从“该月恰好有一条数据”推断完整。

**要做什么：** 月内用 `(1 + r).prod() - 1`，同时报告输入行数和完整性。热图用 `*` 标记部分月份，用灰格表示没有数据。本小表假设未列出的日子已验证为零收益，只为缩短展示；实际使用应提供完整逐日净收益表，不能擅自省略未知日。''',
        'backtest': '''
result = df.copy()
result['date'] = pd.to_datetime(result['date'])
result = result.sort_values('date').set_index('date')
assert result.index.is_unique
assert np.isfinite(result['strategy_return']).all()
assert (result['strategy_return'] > -1).all()
assert result['month_complete'].notna().all()
assert result['month_complete'].isin([True, False]).all()
month_key = result.index.to_period('M')
assert result.groupby(month_key)['month_complete'].nunique().eq(1).all()
monthly = result.groupby(month_key).agg(
    monthly_return=('strategy_return', lambda r: (1 + r).prod() - 1),
    shown_rows=('strategy_return', 'size'),
    complete=('month_complete', 'first'),
)
monthly['year'] = monthly.index.year
monthly['month'] = monthly.index.month
heat = monthly.pivot(index='year', columns='month', values='monthly_return').reindex(columns=range(1, 13))
complete = monthly.pivot(index='year', columns='month', values='complete').reindex(columns=range(1, 13))
display(monthly.round(4))
''',
        'plot': '''
values = heat.to_numpy(dtype=float) * 100
limit = max(np.nanmax(np.abs(values)), 0.01)
cmap = plt.get_cmap('RdBu').copy()
cmap.set_bad('#E2E8F0')
plt.figure(figsize=(11, 3))
plt.imshow(values, cmap=cmap, vmin=-limit, vmax=limit, aspect='auto')
plt.grid(False)
plt.xticks(range(12), range(1, 13))
plt.yticks(range(len(heat)), heat.index)
for row in range(len(heat)):
    for col in range(12):
        value = values[row, col]
        label = '-' if np.isnan(value) else '{:.1f}%{}'.format(value, '' if complete.iloc[row, col] else '*')
        color = 'white' if np.isfinite(value) and abs(value) > 0.6 * limit else '#1E293B'
        plt.text(col, row, label, ha='center', va='center', color=color)
plt.colorbar(label='Return (%)')
plt.title('Monthly return (* partial month; grey = no data)')
plt.xlabel('Month')
plt.tight_layout()
plt.show()
''',
        'reading': '完整月份和部分月份不能直接比较；没有数据的月份显示灰格，不显示为零收益。shown_rows 是本输入表的行数，不是经过日历确认的实际交易日总数。',
        'caution': '本案例用小表说明聚合与画图。实际缺失一整天时，groupby 不会自动报错；必须先按真实会话日历检查覆盖，不能用普通 bdate_range 冒充交易所日历。',
    },
    {
        'id': 'B17',
        'title': '策略与基准：净值比较、主动收益与滚动风险',
        'data': '''
df = pd.DataFrame({
    'strategy_return': [0.01, -0.005, 0.012, 0, -0.01, 0.02, -0.004, 0.008, 0.003, -0.007],
    'benchmark_return': [0.008, -0.01, 0.015, 0.004, -0.012, 0.016, -0.006, 0.006, 0.007, -0.003],
}, index=pd.bdate_range('2024-01-08', periods=10))
display(df)
''',
        'task': '''**场景：** 比较同一时间区间、同一估值时点的策略净收益与基准总收益。两列需要是相同单位、相同日历，不能一个是日收益、另一个是累计收益。

**要做什么：** 计算两条净值、相对财富 `strategy_nav / benchmark_nav`、每日主动收益和滚动跟踪误差。图画同一起点的净值，表中补充滚动风险；窗口 3 天只用于展示。''',
        'backtest': '''
result = df.sort_index().copy()
columns = ['strategy_return', 'benchmark_return']
assert result.index.is_unique
assert np.isfinite(result[columns]).all().all()
assert (result[columns] > -1).all().all()
window, periods_per_year = 3, 252
result['strategy_nav'] = (1 + result['strategy_return']).cumprod()
result['benchmark_nav'] = (1 + result['benchmark_return']).cumprod()
result['relative_wealth'] = result['strategy_nav'] / result['benchmark_nav']
result['active_return'] = result['strategy_return'] - result['benchmark_return']
result['rolling_vol'] = result['strategy_return'].rolling(window).std(ddof=1) * np.sqrt(periods_per_year)
result['rolling_tracking_error'] = result['active_return'].rolling(window).std(ddof=1) * np.sqrt(periods_per_year)
active_std = result['active_return'].std(ddof=1)
information_ratio = result['active_return'].mean() / active_std * np.sqrt(periods_per_year) if active_std > 0 else np.nan
display(result.round(4))
display(pd.DataFrame({'value': [result['relative_wealth'].iloc[-1] - 1, information_ratio]},
                     index=['relative_wealth_gain', 'annualized_information_ratio']).round(4))
''',
        'plot': '''
x = np.arange(len(result) + 1)
plt.figure(figsize=(10, 4))
plt.plot(x, np.r_[1, result['strategy_nav'].to_numpy()], color=BLUE, marker='o', label='Strategy (net)')
plt.plot(x, np.r_[1, result['benchmark_nav'].to_numpy()], color=TEAL, linestyle='--', label='Benchmark')
plt.title('Strategy and benchmark: aligned dates, same starting capital')
plt.xlabel('Trading day (0 = initial capital)')
plt.ylabel('NAV')
plt.legend()
plt.tight_layout()
plt.show()
''',
        'reading': '策略净值更高说明这段样本累计财富更高；rolling_tracking_error 衡量主动收益的波动。relative_wealth 准确表示两条累计财富之比，不能用 (1 + active_return).cumprod() 代替它。',
        'caution': '基准收益应与策略的币种、分红、估值时点匹配；例中基准为无额外交易成本的参考指数。图不能证明 alpha，10 天也不足以支持稳定性判断。不要用 inner join 静默删去策略亏损日或基准缺失日。',
    },
    {
        'id': 'B18',
        'title': '费用敏感性：同一交易计划在不同单边费率下重算账户',
        'data': '''
df = pd.DataFrame({
    'price': [100, 102, 101, 103, 99, 101, 102, 100],
    'trade_shares': [5, 0, -5, 4, 0, -4, 3, -3],
}, index=pd.bdate_range('2024-01-08', periods=8))
display(df)
''',
        'task': '''**场景：** 已经有成交股数计划：`trade_shares > 0` 买入、`< 0` 卖出、`0` 不交易，指令在对应成交价可交易之前已知。本例先把交易计划固定，单独观察费用影响。

**要做什么：** 对 0、5、10、20 bps 单边费用重算现金/股票账户，画最终累计收益对费率的敏感性。每笔费用等于 `abs(成交股数 × 成交价) × 单边费率`，卖出同样扣费。''',
        'backtest': '''
result = df.sort_index().copy()
assert result.index.is_unique
assert np.isfinite(result[['price', 'trade_shares']]).all().all()
assert (result['price'] > 0).all()
initial_cash = 1000.0
fee_grid_bps = [0, 5, 10, 20]
equity_paths, rows = {}, []
for bps in fee_grid_bps:
    cash, shares, total_fees = initial_cash, 0.0, 0.0
    history = []
    for row in result.itertuples():
        trade_value = row.trade_shares * row.price
        fee = abs(trade_value) * bps / 10000
        cash -= trade_value + fee
        shares += row.trade_shares
        if cash < -1e-8 or shares < -1e-8:
            raise ValueError('该费用下计划不可执行：现金不足或出现卖空')
        equity = cash + shares * row.price
        total_fees += fee
        history.append(equity)
    equity_paths[str(bps) + ' bps'] = history
    rows.append([bps, total_fees, equity / initial_cash - 1])
equity_paths = pd.DataFrame(equity_paths, index=result.index)
sensitivity = pd.DataFrame(rows, columns=['fee_bps_one_way', 'total_fees', 'total_return'])
display(sensitivity.round(4))
display(equity_paths.round(2))
''',
        'plot': '''
values = sensitivity['total_return'] * 100
plt.figure(figsize=(9, 4))
plt.bar(sensitivity['fee_bps_one_way'].astype(str), values, color=BLUE, width=0.6)
for i, value in enumerate(values):
    plt.text(i, value, '{:.2f}%'.format(value), ha='center', va='bottom' if value >= 0 else 'top')
plt.axhline(0, color='grey', linewidth=0.8)
plt.margins(y=0.2)
plt.title('Cost sensitivity for the same share-trading plan')
plt.xlabel('One-way fee (bps)')
plt.ylabel('Total net return (%)')
plt.tight_layout()
plt.show()
''',
        'reading': '交易计划固定时，费用越高，最终资金越少。首笔买入和最后卖出都在费用中；最后一行确实把持仓清零，所以这里没有尚未计提的平仓费。',
        'caution': '这是固定成交股数计划的反事实成本比较。若策略按账户权益重新计算仓位，费用会改变之后的下单数量，应该对每种费率重新运行完整策略。它也不包含价格冲击、无法成交和融资费用。',
    },
]
