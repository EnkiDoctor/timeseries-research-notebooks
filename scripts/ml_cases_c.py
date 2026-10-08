"""Independent time-aware model selection, diagnostics and application recipes."""

CASES = [
    {
        'id': 'M11', 'title': 'TimeSeriesSplit + GridSearchCV：带间隔的时间调参',
        'data': '''
rng = np.random.RandomState(111)
df = pd.DataFrame({
    'date': pd.bdate_range('2023-01-02', periods=190),
    'close': 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, 190))),
})
print('输入共', len(df), '行；先看前8行')
display(df.head(8))
''',
        'task': '''**场景：** 用截至当天收盘的历史收益与波动，预测未来 3 个观测期的收益。`date` 是会话日期，`close` 为一致口径的正价格。

**要做什么：** 先保留时间最晚的 20% 作为最终测试集；开发集内部使用 `TimeSeriesSplit(gap=3)` 搜索 Ridge 的 alpha。用 Pipeline 确保每个 fold 单独拟合填充器和标准化。每行同时记录 16:05 的预测时间及标签在未来 16:00 的实现时间；训练标签必须先于预测可用。''',
        'train': '''
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date').reset_index(drop=True)
assert data['date'].notna().all() and data['date'].is_unique
assert np.isfinite(data['close']).all() and data['close'].gt(0).all()
horizon = 3
ret = data['close'].pct_change(fill_method=None)
data['momentum'] = data['close'].pct_change(3, fill_method=None)
data['volatility'] = ret.rolling(5).std()
data['target'] = data['close'].shift(-horizon) / data['close'] - 1
data['prediction_time'] = data['date'] + pd.Timedelta(hours=16, minutes=5)
data['label_end'] = data['date'].shift(-horizon) + pd.Timedelta(hours=16)
features = ['momentum', 'volatility']
samples = data.dropna(subset=features + ['target', 'label_end']).reset_index(drop=True)
test_start = samples.loc[int(len(samples) * 0.8), 'prediction_time']
dev = samples.loc[(samples['prediction_time'] < test_start) & (samples['label_end'] < test_start)]
test = samples.loc[samples['prediction_time'] >= test_start]
cv = TimeSeriesSplit(n_splits=3, test_size=20, gap=horizon)
for train_i, valid_i in cv.split(dev):
    assert dev.iloc[train_i]['label_end'].max() < dev.iloc[valid_i]['prediction_time'].min()
pipeline = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge())
search = GridSearchCV(pipeline, {'ridge__alpha': [0.1, 1, 10, 100]}, cv=cv,
                      scoring='neg_mean_squared_error', n_jobs=1, refit=True)
search.fit(dev[features], dev['target'])
cv_table = pd.DataFrame({
    'alpha': [p['ridge__alpha'] for p in search.cv_results_['params']],
    'CV_RMSE': np.sqrt(-search.cv_results_['mean_test_score']),
})
test_prediction = search.predict(test[features])  # 参数已锁定，这时才评估最终test。
display(cv_table.round(6))
display(pd.DataFrame({'best_alpha': [search.best_params_['ridge__alpha']],
                      'test_RMSE': [np.sqrt(mean_squared_error(test['target'], test_prediction))]}))
''',
        'plot': '''
plt.figure(figsize=(9, 4))
plt.plot(cv_table['alpha'], cv_table['CV_RMSE'] * 100, color=BLUE, marker='o')
plt.xscale('log')
plt.title('Ridge: chronological CV inside the development period')
plt.xlabel('Regularization alpha (log scale)')
plt.ylabel('CV RMSE (percentage points)')
plt.tight_layout()
plt.show()
''',
        'reading': '横轴是惩罚强度，纵轴是开发集内部各验证 fold 的平均 MSE 再开方；越低越好。最终测试误差单独在表中报告，不参与选 alpha。',
        'caution': 'gap 是样本行数，不自动代表自然日；本例每会话只有一行、标签固定3期，因此可按此设置。面板、缺行或标签延迟不齐时应按实际 label_end 清除不可用样本，见 M12。多期标签有重叠，CV 分数不是独立样本显著性证明。',
    },
    {
        'id': 'M12', 'title': '多资产面板 Walk-forward：按日期成块滚动训练',
        'data': '''
rng = np.random.RandomState(112)
dates = pd.bdate_range('2023-01-02', periods=90)
parts = []
for asset in ['A', 'B', 'C']:
    parts.append(pd.DataFrame({
        'date': dates, 'asset': asset,
        'close': 100 * np.exp(np.cumsum(rng.normal(0, 0.012, len(dates)))),
        'flow': rng.normal(size=len(dates)),
    }))
df = pd.concat(parts, ignore_index=True).sort_values(['date', 'asset']).reset_index(drop=True)
print('输入共', len(df), '行；先看前9行')
display(df.head(9))
''',
        'task': '''**场景：** 每个日期有多只资产，预测各资产随后2期收益。`flow` 假定在该日收盘前已发布；`close` 在收盘后可用。

**要做什么：** 从有历史特征的第41个日期开始，每10个日期重新训练一次；同一天全部资产共同进入预测块，不能把同日 A 放训练、B 放测试。每次拟合只使用标签已在该预测块起点之前实现的行，输出逐行样本外预测及每块误差。''',
        'train': '''
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values(['asset', 'date']).reset_index(drop=True)
assert data[['date', 'asset']].notna().all().all()
assert not data.duplicated(['date', 'asset']).any()
assert np.isfinite(data[['close', 'flow']]).all().all() and data['close'].gt(0).all()
assert data.pivot(index='date', columns='asset', values='close').notna().all().all()
g = data.groupby('asset', sort=False)
data['momentum'] = g['close'].pct_change(2, fill_method=None)
data['target'] = g['close'].shift(-2) / data['close'] - 1
data['prediction_time'] = data['date'] + pd.Timedelta(hours=16, minutes=5)
data['label_end'] = g['date'].shift(-2) + pd.Timedelta(hours=16)
features = ['momentum', 'flow']
samples = data.dropna(subset=features + ['target', 'label_end']).copy()
all_dates = np.sort(samples['date'].unique())
predictions, audit = [], []
for start in range(40, len(all_dates), 10):
    block_dates = all_dates[start:start + 10]
    fit_time = pd.Timestamp(block_dates[0]) + pd.Timedelta(hours=16, minutes=5)
    train = samples.loc[(samples['prediction_time'] < fit_time) & (samples['label_end'] < fit_time)]
    test = samples.loc[samples['date'].isin(block_dates)].copy()
    assert train['label_end'].max() < test['prediction_time'].min()
    model = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge(alpha=10))
    model.fit(train[features], train['target'])
    test['prediction'] = model.predict(test[features])
    test['fit_time'] = fit_time
    predictions.append(test[['date', 'asset', 'target', 'prediction', 'fit_time']])
    audit.append([fit_time, train['label_end'].max(), len(train), len(test),
                  np.sqrt(mean_squared_error(test['target'], test['prediction']))])
oos = pd.concat(predictions).sort_values(['date', 'asset'])
folds = pd.DataFrame(audit, columns=['fit_time', 'last_train_label_end', 'n_train', 'n_test', 'RMSE'])
assert not oos.duplicated(['date', 'asset']).any()
display(folds)
display(oos.head(9).round(5))
''',
        'plot': '''
plt.figure(figsize=(10, 4))
plt.bar(np.arange(len(folds)), folds['RMSE'] * 100, color=BLUE, width=0.6)
plt.xticks(np.arange(len(folds)), folds['fit_time'].dt.strftime('%Y-%m-%d'), rotation=25)
plt.title('Panel walk-forward: all assets share the same date blocks')
plt.xlabel('Model fit date')
plt.ylabel('Out-of-sample block RMSE (percentage points)')
plt.tight_layout()
plt.show()
''',
        'reading': '审计表先核对 last_train_label_end 早于 fit_time。各块预测来自当时可训练的模型；下一块可以加入此时已经实现的旧标签，这与真实在线更新一致。',
        'caution': '滚动过程是预先固定的评估方案；看完整段结果后再改模型，整段就成为开发集，需要另留新的测试期。标签是2期重叠收益，不能把预测表中的 target 逐行复合成交易净值；交易执行另按03册建账。',
    },
    {
        'id': 'M13', 'title': '验证集 Permutation Importance：哪些特征影响预测误差',
        'data': '''
rng = np.random.RandomState(113)
n = 200
momentum = rng.normal(size=n)
flow = rng.normal(size=n)
df = pd.DataFrame({
    'date': pd.bdate_range('2023-01-02', periods=n),
    'momentum': momentum, 'flow': flow, 'noise_feature': rng.normal(size=n),
    'return_oc': 0.006 * momentum + 0.004 * np.tanh(flow) + rng.normal(0, 0.006, n),
})
print('输入共', len(df), '行；先看前8行')
display(df.head(8))
''',
        'task': '''**场景：** 想解释模型在未参与拟合的数据上依赖哪些特征。三列数值特征假定盘前可用；`return_oc` 是当天收盘后才能知道的开盘至收盘收益。

**要做什么：** 先用前60%训练随机森林，随后20%验证；在验证集打乱每个特征，计算 MAE 增加多少。最后20%暂不读取收益，保留给后续真正最终评估。''',
        'train': '''
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date').reset_index(drop=True)
features = ['momentum', 'flow', 'noise_feature']
assert data['date'].is_unique and data['date'].notna().all()
cut1, cut2 = int(len(data) * 0.6), int(len(data) * 0.8)
train, valid = data.iloc[:cut1], data.iloc[cut1:cut2]
reserved_test = data.iloc[cut2:]
assert np.isfinite(data.iloc[:cut2][features + ['return_oc']]).all().all()
model = RandomForestRegressor(n_estimators=100, max_depth=4, min_samples_leaf=8,
                              random_state=13, n_jobs=1)
model.fit(train[features], train['return_oc'])
validation_mae = mean_absolute_error(valid['return_oc'], model.predict(valid[features]))
permuted = permutation_importance(model, valid[features], valid['return_oc'],
                                 scoring='neg_mean_absolute_error', n_repeats=15,
                                 random_state=13, n_jobs=1)
importance = pd.DataFrame({
    'feature': features, 'MAE_increase': permuted.importances_mean,
    'repeat_std': permuted.importances_std,
}).sort_values('MAE_increase')
display(pd.DataFrame({'validation_MAE': [validation_mae], 'untouched_test_rows': [len(reserved_test)]}))
display(importance.round(6))
''',
        'plot': '''
plt.figure(figsize=(9, 4))
plt.barh(importance['feature'], importance['MAE_increase'] * 100,
         xerr=importance['repeat_std'] * 100, color=BLUE, alpha=0.85, capsize=3)
plt.axvline(0, color='grey', linewidth=0.8)
plt.title('Permutation importance on chronological validation data')
plt.xlabel('Increase in MAE (percentage points; bars = repeat std)')
plt.tight_layout()
plt.show()
''',
        'reading': '条形越靠右，打乱这个特征后验证误差增幅越大。误差棒是重复打乱之间的标准差，不是统计置信区间。负值表示该次打乱反而改善误差，不能解释成稳定负因果作用。',
        'caution': '只说明这个模型、这段验证数据中的预测依赖，不证明因果或交易价值。相关特征会相互替代；逐行打乱也会破坏时间结构，强自相关数据可改用保持块内结构的置换。按此结果选特征后，仍要用保留测试集做最终评估。',
    },
    {
        'id': 'M14', 'title': '回归诊断：残差、Rank IC 与基准误差',
        'data': '''
rng = np.random.RandomState(114)
n = 180
momentum, flow = rng.normal(size=n), rng.normal(size=n)
df = pd.DataFrame({
    'date': pd.bdate_range('2023-01-02', periods=n), 'momentum': momentum, 'flow': flow,
    'return_oc': 0.006 * momentum + 0.004 * flow ** 2 + rng.normal(0, 0.008, n),
})
print('输入共', len(df), '行；先看前8行')
display(df.head(8))
''',
        'task': '''**场景：** 模型已经生成最终时间测试集的预测，要检查预测误差是否偏向一侧、预测与实际是否有排序关系。输入特征盘前可用，目标是同日开盘至收盘收益。

**要做什么：** 使用预先指定的 Ridge 模型，输出 MAE、RMSE、R²、平均残差及整个单资产测试期间的 Rank IC，并与训练均值预测对比。残差定义为实际减预测。''',
        'train': '''
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date').reset_index(drop=True)
features = ['momentum', 'flow']
assert data['date'].notna().all() and data['date'].is_unique
assert np.isfinite(data[features + ['return_oc']]).all().all()
cut = int(len(data) * 0.7)
train, test = data.iloc[:cut], data.iloc[cut:].copy()
model = make_pipeline(StandardScaler(), Ridge(alpha=10))
model.fit(train[features], train['return_oc'])
test['prediction'] = model.predict(test[features])
test['residual'] = test['return_oc'] - test['prediction']
baseline = np.full(len(test), train['return_oc'].mean())
rank_ic = test['prediction'].corr(test['return_oc'], method='spearman') if test['prediction'].nunique() > 1 and test['return_oc'].nunique() > 1 else np.nan
metrics = pd.DataFrame({
    'MAE': [mean_absolute_error(test['return_oc'], test['prediction']), mean_absolute_error(test['return_oc'], baseline)],
    'RMSE': [np.sqrt(mean_squared_error(test['return_oc'], test['prediction'])), np.sqrt(mean_squared_error(test['return_oc'], baseline))],
    'R2': [r2_score(test['return_oc'], pred) if test['return_oc'].nunique() > 1 else np.nan
           for pred in [test['prediction'], baseline]],
}, index=['Ridge', 'Training mean'])
display(metrics.round(5))
display(pd.DataFrame({'mean_residual': [test['residual'].mean()], 'time_series_rank_IC': [rank_ic]}))
display(test[['date', 'return_oc', 'prediction', 'residual']].head(8).round(5))
''',
        'plot': '''
plt.figure(figsize=(9, 4))
plt.scatter(test['prediction'] * 100, test['residual'] * 100, color=BLUE, alpha=0.65, edgecolors='white')
plt.axhline(0, color=RED, linestyle='--', linewidth=1)
plt.title('Held-out residuals: actual return minus prediction')
plt.xlabel('Predicted return (%)')
plt.ylabel('Residual (percentage points)')
plt.tight_layout()
plt.show()
''',
        'reading': '残差系统偏正/负可能反映偏差；散点呈曲线可能是遗漏非线性。Rank IC 是本例单资产跨时间的 Spearman 相关，不是每天多资产的横截面 IC。',
        'caution': '相关性不等于可交易收益，R²也可能为负；这里没有显著性检验。若看这张最终测试图后再修改特征或模型，该区间就成为开发资料，需新的未见区间重新验证。',
    },
    {
        'id': 'M15', 'title': 'PCA 降维：只用训练期拟合，再投影未来数据',
        'data': '''
rng = np.random.RandomState(115)
n = 160
factor_1, factor_2 = rng.normal(size=n), rng.normal(size=n)
df = pd.DataFrame({
    'date': pd.bdate_range('2023-01-02', periods=n),
    'feature_a': factor_1 + rng.normal(0, 0.2, n),
    'feature_b': 2 * factor_1 + rng.normal(0, 0.3, n),
    'feature_c': factor_2 + rng.normal(0, 0.2, n),
    'feature_d': factor_1 - factor_2 + rng.normal(0, 0.3, n),
})
print('输入共', len(df), '行；先看前8行')
display(df.head(8))
''',
        'task': '''**场景：** 多个数值特征高度相关，先想看主要变化方向或给后续模型提供低维输入。这里没有监督学习标签。

**要做什么：** 前75%日期拟合填充、标准化和两维 PCA，再把后25%投影到同一个坐标系，报告训练期解释方差比例和载荷。不能把未来数据一起拿去拟合 StandardScaler / PCA。''',
        'train': '''
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date').reset_index(drop=True)
features = ['feature_a', 'feature_b', 'feature_c', 'feature_d']
assert data['date'].notna().all() and data['date'].is_unique
assert not np.isinf(data[features].to_numpy()).any()
cut = int(len(data) * 0.75)
train = data.iloc[:cut]
assert train[features].notna().any().all(), '训练期不能有整列缺失的特征'
pipeline = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), PCA(n_components=2))
pipeline.fit(train[features])
coordinates = pipeline.transform(data[features])  # transform不重新学习均值、尺度和方向。
projection = data[['date']].copy()
projection[['PC1', 'PC2']] = coordinates
projection['split'] = np.where(np.arange(len(data)) < cut, 'train', 'future')
pca = pipeline.named_steps['pca']
variance = pd.DataFrame({'explained_ratio': pca.explained_variance_ratio_}, index=['PC1', 'PC2'])
loadings = pd.DataFrame(pca.components_.T, index=features, columns=['PC1', 'PC2'])
display(variance.round(4))
display(loadings.round(4))
display(projection.head(8).round(4))
''',
        'plot': '''
plt.figure(figsize=(8, 5))
for group, color, marker in [('train', BLUE, 'o'), ('future', ORANGE, '^')]:
    points = projection.loc[projection['split'].eq(group)]
    plt.scatter(points['PC1'], points['PC2'], color=color, marker=marker, alpha=0.6, label=group)
plt.title('PCA coordinates learned from training data only')
plt.xlabel('PC1')
plt.ylabel('PC2')
plt.legend()
plt.tight_layout()
plt.show()
''',
        'reading': '投影用于观察训练期与未来期的分布是否相似。载荷表示标准化特征如何组成主成分，方差比例来自训练数据。',
        'caution': 'PCA 保留的是特征方差，不是预测收益的能力；解释方差高也不保证模型效果好。若将 PCA 用于监督模型，应该放进同一 Pipeline，每个时间 fold 内重新拟合；主成分整体符号可以翻转。',
    },
    {
        'id': 'M16', 'title': '模型预测 → 仓位 → 样本外日内回测',
        'data': '''
rng = np.random.RandomState(116)
n = 210
momentum, flow = rng.normal(size=n), rng.normal(size=n)
open_price = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
day_return = 0.003 * momentum + 0.002 * flow + rng.normal(0, 0.01, n)
df = pd.DataFrame({
    'date': pd.bdate_range('2023-01-02', periods=n),
    'momentum': momentum, 'flow': flow,
    'open': open_price, 'close': open_price * (1 + day_return),
})
print('输入共', len(df), '行；先看前8行')
display(df.head(8))
''',
        'task': '''**场景：** 将监督模型预测接到03册的回测。`momentum / flow` 假定在当天开盘前已经可用，`open / close` 是当天可成交与估值价格；模型预测开盘至收盘收益。

**要做什么：** 按时间60%训练、20%验证、20%测试。训练 Ridge，验证集选择不交易区间的阈值；模型和阈值均锁定后，每天开盘按预测决定 +50% / −50% / 0 仓位，收盘全部平仓，扣两边实际名义成交金额的费用。''',
        'train': '''
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data = data.sort_values('date').reset_index(drop=True)
features = ['momentum', 'flow']
assert data['date'].notna().all() and data['date'].is_unique
assert np.isfinite(data[features + ['open', 'close']]).all().all()
assert (data[['open', 'close']] > 0).all().all()
data['return_oc'] = data['close'] / data['open'] - 1
cut1, cut2 = int(len(data) * 0.6), int(len(data) * 0.8)
train, valid, test = data.iloc[:cut1], data.iloc[cut1:cut2], data.iloc[cut2:].copy()
model = make_pipeline(StandardScaler(), Ridge(alpha=10))
model.fit(train[features], train['return_oc'])
validation_prediction = model.predict(valid[features])
fee_rate, max_weight = 2 / 10000, 0.5
thresholds = [0.0, 0.001, 0.002, 0.003]
rows = []
for threshold in thresholds:
    weight = np.sign(validation_prediction) * (np.abs(validation_prediction) > threshold) * max_weight
    cost = fee_rate * np.abs(weight) * (2 + valid['return_oc'])
    net = weight * valid['return_oc'] - cost
    assert (net > -1).all()
    rows.append([threshold, (1 + net).prod() - 1])
selection = pd.DataFrame(rows, columns=['threshold', 'validation_net_return'])
best_threshold = selection.loc[selection['validation_net_return'].idxmax(), 'threshold']
test['prediction'] = model.predict(test[features])  # 不在test重新训练或重新挑阈值。
test['position'] = np.sign(test['prediction']) * test['prediction'].abs().gt(best_threshold) * max_weight
test['cost'] = fee_rate * test['position'].abs() * (2 + test['return_oc'])
test['strategy_return'] = test['position'] * test['return_oc'] - test['cost']
assert test['strategy_return'].gt(-1).all()
test['nav'] = (1 + test['strategy_return']).cumprod()
test['drawdown'] = test['nav'] / test['nav'].cummax().clip(lower=1) - 1
display(selection.round(5))
display(test[['date', 'prediction', 'position', 'return_oc', 'cost', 'strategy_return', 'nav']].head(8).round(5))
display(pd.DataFrame({'test_RMSE': [np.sqrt(mean_squared_error(test['return_oc'], test['prediction']))],
                      'net_return': [test['nav'].iloc[-1] - 1], 'max_drawdown': [test['drawdown'].min()],
                      'active_days': [test['position'].ne(0).sum()], 'locked_threshold': [best_threshold]}))
''',
        'plot': '''
plt.figure(figsize=(10, 4))
plt.plot(np.arange(len(test) + 1), np.r_[1, test['nav'].to_numpy()], color=BLUE, label='Model strategy, net')
plt.axhline(1, color='grey', linewidth=0.8, label='Cash (zero interest)')
plt.title('Held-out trading: model and threshold locked in advance')
plt.xlabel('Test trading day (0 = initial capital)')
plt.ylabel('Net NAV')
plt.legend()
plt.tight_layout()
plt.show()
''',
        'reading': '预测误差与净收益分别报告。当天盘前预测决定当天开仓，因此直接乘同日 return_oc，不再 shift；若特征只能收盘后知道，就必须改变成交时点与标签，不能只照抄此公式。',
        'caution': '这是合成可预测关系演示，不是发现了真实 alpha；忽略滑点、借券、容量与保证金。fee_rate是单边，cost包括入场和按收盘市值退出。模型只用训练集拟合，验证后未重新拟合，阈值与所用模型保持配套。测试收益可命名为 strategy_return 后接03册 B15–B17。',
    },
]
