"""Independent ML recipes M06–M10; strings are copied into the notebook."""

CASES = [
    {
        "id": "M06",
        "title": "涨跌分类：处理类别不平衡，在验证集选择概率阈值",
        "data": '''rng = np.random.default_rng(606)
n = 220
momentum = rng.normal(0, 1, n)
volatility = rng.uniform(0.008, 0.025, n)
flow = rng.normal(0, 1, n)
probability = 1 / (1 + np.exp(-(-1.5 + momentum + 0.7 * flow)))
label = rng.binomial(1, probability)
return_oc = np.where(label == 1, 1, -1) * rng.uniform(0.002, 0.015, n)
df = pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=n),
                   "momentum": momentum, "volatility": volatility,
                   "flow": flow, "return_oc": return_oc, "label": label})
print("总行数：", len(df))
display(df.head(8))''',
        "task": "每行是一日，momentum、volatility、flow 均在当日开盘前可用；label 是当日开盘到收盘收益 return_oc 是否大于 0。任务：预测上涨概率。按时间取前 60% 训练、中间 20% 验证、最后 20% 测试；模型先用 class_weight='balanced'，再只在验证集选择 F1 最大的阈值。测试集只做最终评价。",
        "train": '''from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix

df["date"] = pd.to_datetime(df["date"])
assert df["date"].notna().all() and df["date"].is_unique, "日期须非空且唯一"
df = df.sort_values("date").reset_index(drop=True)
features = ["momentum", "volatility", "flow"]
cut1, cut2 = int(len(df) * 0.6), int(len(df) * 0.8)
train, valid, test = df.iloc[:cut1], df.iloc[cut1:cut2], df.iloc[cut2:]
assert train["label"].nunique() == 2, "训练集必须含两个类别"
assert valid["label"].nunique() == 2, "验证集须含两个类别才能可靠选择阈值"

# 插补和标准化均只拟合训练集；类别权重也只基于训练集。
model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                      LogisticRegression(class_weight="balanced", max_iter=1000,
                                         random_state=42))
model.fit(train[features], train["label"])
valid_probability = model.predict_proba(valid[features])[:, 1]
threshold_table = pd.DataFrame({"threshold": np.arange(0.2, 0.81, 0.1)})
threshold_table["valid_f1"] = [
    f1_score(valid["label"], valid_probability >= t, zero_division=0)
    for t in threshold_table["threshold"]]
threshold = threshold_table.loc[threshold_table["valid_f1"].idxmax(), "threshold"]
display(threshold_table.round(3))

# 阈值已经锁定，不再根据测试结果重新选阈值。
test_probability = model.predict_proba(test[features])[:, 1]
test_prediction = (test_probability >= threshold).astype(int)
y_test = test["label"]
has_two_classes = y_test.nunique() == 2
metrics = pd.DataFrame([{
    "threshold_from_valid": threshold, "test_positive_rate": y_test.mean(),
    "precision": precision_score(y_test, test_prediction, zero_division=0),
    "recall": recall_score(y_test, test_prediction, zero_division=0),
    "f1": f1_score(y_test, test_prediction, zero_division=0),
    "roc_auc": roc_auc_score(y_test, test_probability) if has_two_classes else np.nan,
    "average_precision": average_precision_score(y_test, test_probability) if has_two_classes else np.nan}])
display(metrics.round(3))
display(pd.DataFrame(confusion_matrix(y_test, test_prediction, labels=[0, 1]),
                     index=["actual_0", "actual_1"], columns=["predicted_0", "predicted_1"]))
if not has_two_classes:
    print("测试集只有一个类别：不报告 ROC-AUC / AP，也不画 PR 曲线。")''',
        "plot": '''from sklearn.metrics import precision_recall_curve

if has_two_classes:
    precision, recall, _ = precision_recall_curve(y_test, test_probability)
    plt.figure(figsize=(8, 4))
    plt.plot(recall, precision, color=BLUE, linewidth=2, label="Logistic regression")
    plt.axhline(y_test.mean(), color="grey", linestyle="--", label="Positive-rate baseline")
    plt.scatter(metrics.loc[0, "recall"], metrics.loc[0, "precision"],
                color=ORANGE, s=70, zorder=3, label="Threshold chosen on validation")
    plt.title("Test precision-recall curve")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.xlim(0, 1)
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.show()''',
        "reading": "先读混淆表：行是真实类别，列是预测类别。PR 曲线适合关注少数正类的场景，橙点是验证集选定阈值在测试集上的结果；虚线是测试集正类比例。AP 是 average precision，不应把它与任意方式计算的曲线梯形面积混为一谈。",
        "caution": "本例用 F1 选阈值是分类教学，不代表交易收益最优。class_weight 会改变拟合目标，predict_proba 未必是校准后的真实概率；如需校准，另外保留按时间分割的校准数据。不要为让曲线更好看而在测试集重选阈值，也不要仅凭 accuracy 评价不平衡分类。",
    },
    {
        "id": "M07",
        "title": "决策树回归：用验证误差选择深度，观察过拟合",
        "data": '''rng = np.random.default_rng(707)
n = 210
momentum = rng.normal(0, 1, n)
volatility = rng.uniform(0.008, 0.025, n)
flow = rng.normal(0, 1, n)
return_oc = (0.006 * np.tanh(1.5 * momentum) + 0.004 * (flow > 0)
             - 0.15 * volatility + rng.normal(0, 0.005, n))
df = pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=n),
                   "momentum": momentum, "volatility": volatility,
                   "flow": flow, "return_oc": return_oc})
print("总行数：", len(df))
display(df.head(8))''',
        "task": "用三个盘前可用特征预测当日开盘到收盘收益 return_oc。任务：比较不同 max_depth 的训练和验证 RMSE。按时间使用前 60% 训练、中间 20% 验证、最后 20% 测试；只用验证集选深度，随后在训练集与验证集合并数据上重训，最后只评价一次测试集。",
        "train": '''from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error

df["date"] = pd.to_datetime(df["date"])
assert df["date"].notna().all() and df["date"].is_unique, "日期须非空且唯一"
df = df.sort_values("date").reset_index(drop=True)
features = ["momentum", "volatility", "flow"]
cut1, cut2 = int(len(df) * 0.6), int(len(df) * 0.8)
train, valid, test = df.iloc[:cut1], df.iloc[cut1:cut2], df.iloc[cut2:]
depths = [1, 2, 3, 4, 6, None]
scores = []
for depth in depths:
    model = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=2, random_state=42)
    model.fit(train[features], train["return_oc"])
    scores.append({"depth": str(depth),
                   "train_rmse": np.sqrt(mean_squared_error(train["return_oc"], model.predict(train[features]))),
                   "valid_rmse": np.sqrt(mean_squared_error(valid["return_oc"], model.predict(valid[features])))})
depth_table = pd.DataFrame(scores)
display(depth_table.round(5))

best_depth = depths[depth_table["valid_rmse"].idxmin()]
train_valid = df.iloc[:cut2]
final_model = DecisionTreeRegressor(max_depth=best_depth, min_samples_leaf=2, random_state=42)
final_model.fit(train_valid[features], train_valid["return_oc"])
prediction = final_model.predict(test[features])
baseline = np.repeat(train_valid["return_oc"].mean(), len(test))
display(pd.DataFrame([{"selected_depth": str(best_depth),
                       "test_rmse": np.sqrt(mean_squared_error(test["return_oc"], prediction)),
                       "mean_baseline_rmse": np.sqrt(mean_squared_error(test["return_oc"], baseline))}]).round(5))
result = test[["date", "return_oc"]].assign(prediction=prediction)
display(result.head(8))''',
        "plot": '''plt.figure(figsize=(8, 4))
plt.plot(depth_table["depth"], depth_table["train_rmse"] * 100,
         color=BLUE, marker="o", linewidth=2, label="Train")
plt.plot(depth_table["depth"], depth_table["valid_rmse"] * 100,
         color=ORANGE, marker="o", linewidth=2, label="Validation")
plt.title("Tree depth: fitting vs generalization")
plt.xlabel("max_depth (None = unrestricted)")
plt.ylabel("Return RMSE (percentage points)")
plt.legend()
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "训练 RMSE 随树变深通常下降；如果验证 RMSE 开始上升，说明模型可能在拟合噪声。图中展示的是候选模型在固定训练/验证集上的表现，测试集完全不参与这张选参图。最终表格报告在训练加验证数据上重训后的测试误差。",
        "caution": "只有一次时间切分时，选出的深度可能对该段行情敏感；样本多时可改为带必要 gap 的 TimeSeriesSplit。不要查看测试误差后继续搜索深度。真实特征有缺失时，把 SimpleImputer 放进 Pipeline，并在每次候选训练时只拟合训练数据。",
    },
    {
        "id": "M08",
        "title": "随机森林：学习非线性，和训练均值基准比较",
        "data": '''rng = np.random.default_rng(808)
n = 220
momentum = rng.normal(0, 1, n)
volatility = rng.uniform(0.008, 0.025, n)
flow = rng.normal(0, 1, n)
return_oc = (0.008 * np.tanh(momentum) + 0.004 * momentum * (flow > 0)
             - 0.12 * volatility + rng.normal(0, 0.003, n))
df = pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=n),
                   "momentum": momentum, "volatility": volatility,
                   "flow": flow, "return_oc": return_oc})
print("总行数：", len(df))
display(df.head(8))''',
        "task": "三个特征在开盘前可用，目标是同日开盘到收盘收益。任务：按时间取前 80% 训练随机森林，最后 20% 作为测试；用预先固定的深度和叶节点样本数控制复杂度，并与只预测训练集均值的 DummyRegressor 比较。树模型不要求特征标准化。",
        "train": '''from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

df["date"] = pd.to_datetime(df["date"])
assert df["date"].notna().all() and df["date"].is_unique, "日期须非空且唯一"
df = df.sort_values("date").reset_index(drop=True)
features = ["momentum", "volatility", "flow"]
cut = int(len(df) * 0.8)
train, test = df.iloc[:cut], df.iloc[cut:]
# 这些参数事先指定；若要调参，须在 train 内再按时间保留验证集。
model = make_pipeline(SimpleImputer(strategy="median"),
                      RandomForestRegressor(n_estimators=150, max_depth=6,
                                            min_samples_leaf=5, max_features=1.0,
                                            random_state=42, n_jobs=1))
model.fit(train[features], train["return_oc"])
prediction = model.predict(test[features])
baseline = DummyRegressor(strategy="mean")
baseline.fit(train[features], train["return_oc"])
baseline_prediction = baseline.predict(test[features])
scores = []
for name, pred in [("Random forest", prediction), ("Training mean", baseline_prediction)]:
    scores.append({"model": name,
                   "test_rmse": np.sqrt(mean_squared_error(test["return_oc"], pred)),
                   "test_mae": mean_absolute_error(test["return_oc"], pred),
                   "test_r2": r2_score(test["return_oc"], pred) if test["return_oc"].nunique() > 1 else np.nan})
display(pd.DataFrame(scores).round(5))
result = test[["date", "return_oc"]].assign(prediction=prediction)
display(result.head(8))''',
        "plot": '''actual_pct = result["return_oc"] * 100
predicted_pct = result["prediction"] * 100
lo = min(actual_pct.min(), predicted_pct.min())
hi = max(actual_pct.max(), predicted_pct.max())
plt.figure(figsize=(6, 5))
plt.scatter(actual_pct, predicted_pct, color=BLUE, alpha=0.7,
            edgecolors="white", s=50, label="Test observations")
plt.plot([lo, hi], [lo, hi], color="grey", linestyle="--", label="Perfect prediction")
plt.title("Random forest: actual vs predicted")
plt.xlabel("Actual open-to-close return (%)")
plt.ylabel("Predicted open-to-close return (%)")
plt.legend()
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "散点越接近对角线，单次预测误差越小；若预测集中在零附近但真实收益分散，模型可能对极端值预测不足。先比较测试 RMSE 与训练均值基准，不要只看散点是否有倾斜趋势。R² 可以为负，表示相对于测试样本自身均值的平方误差基准表现更差；测试目标为常数时，本例将无法正常定义的 R² 记为 NaN。",
        "caution": "时间序列不能用随机森林 OOB 分数替代按时间验证；普通 bootstrap 训练没有保证 OOB 行只由其过去的数据预测。不要将 feature_importances_ 当作因果关系。这里的可预测模式是人为生成的，真实收益的样本外信号通常弱得多。",
    },
    {
        "id": "M09",
        "title": "HistGradientBoosting：原生处理缺失值的提升树",
        "data": '''rng = np.random.default_rng(909)
n = 220
momentum = rng.normal(0, 1, n)
volatility = rng.uniform(0.008, 0.025, n)
flow = rng.normal(0, 1, n)
return_oc = (0.006 * np.tanh(momentum) + 0.004 * (flow > 0.3)
             - 0.2 * volatility + rng.normal(0, 0.004, n))
df = pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=n),
                   "momentum": momentum, "volatility": volatility,
                   "flow": flow, "return_oc": return_oc})
# 模拟盘前部分特征缺报：目标仍完整，模型直接接收数值 NaN。
df.loc[rng.choice(n, 22, replace=False), "flow"] = np.nan
df.loc[rng.choice(n, 11, replace=False), "momentum"] = np.nan
print("总行数：", len(df))
display(df.head(8))''',
        "task": "用盘前数值特征预测同日开盘到收盘收益，输入特征存在 NaN。任务：使用 scikit-learn 自带的 HistGradientBoostingRegressor，按时间取前 80% 训练、后 20% 测试。明确关闭默认 early stopping，以避免训练过程再随机划分内部验证集；参数在看测试集前固定。",
        "train": '''from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

df["date"] = pd.to_datetime(df["date"])
assert df["date"].notna().all() and df["date"].is_unique, "日期须非空且唯一"
df = df.sort_values("date").reset_index(drop=True)
features = ["momentum", "volatility", "flow"]
cut = int(len(df) * 0.8)
train, test = df.iloc[:cut], df.iloc[cut:]
display(df[features].isna().sum().rename("missing_count").to_frame())
# 数值特征的 NaN 由模型处理；目标 y 不能缺失。
assert df["return_oc"].notna().all(), "先去掉没有可观测标签的行"
model = HistGradientBoostingRegressor(max_iter=140, learning_rate=0.06,
                                     max_leaf_nodes=7, min_samples_leaf=12,
                                     l2_regularization=0.1, early_stopping=False,
                                     random_state=42)
model.fit(train[features], train["return_oc"])
prediction = model.predict(test[features])
result = test[["date", "return_oc"]].assign(prediction=prediction)
result["residual"] = result["return_oc"] - result["prediction"]
display(result.head(8))
display(pd.DataFrame([{
    "test_rmse": np.sqrt(mean_squared_error(test["return_oc"], prediction)),
    "test_mae": mean_absolute_error(test["return_oc"], prediction),
    "mean_baseline_rmse": np.sqrt(mean_squared_error(test["return_oc"],
                                                      np.repeat(train["return_oc"].mean(), len(test))))}]).round(5))''',
        "plot": '''plt.figure(figsize=(8, 4))
plt.scatter(result["prediction"] * 100, result["residual"] * 100,
            color=TEAL, alpha=0.7, edgecolors="white", s=50)
plt.axhline(0, color="grey", linestyle="--", linewidth=1)
plt.title("Boosting model: test residuals")
plt.xlabel("Predicted return (%)")
plt.ylabel("Actual - predicted (percentage points)")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.show()''',
        "reading": "残差定义为实际值减预测值，位于零线上方表示低估。若残差随预测值出现弯曲趋势，可能遗漏了结构；若散布逐渐变宽，可能存在异方差。此图是测试集诊断，应在后续新一轮研究中处理发现的问题，不能反复用同一测试集调参。",
        "caution": "原生接受 NaN 不代表任何缺失机制都无害：先分辨缺报、停牌与数据延迟，不能把尚未发布的特征填进来。模型不会原生接受正负无穷值，也不能拟合缺失标签。固定迭代数是最短模板；需要调参时使用训练区间内的时间验证或 TimeSeriesSplit。",
    },
    {
        "id": "M10",
        "title": "XGBoost（可选依赖）：按时间验证与 early stopping",
        "data": '''rng = np.random.default_rng(1010)
n = 220
momentum = rng.normal(0, 1, n)
volatility = rng.uniform(0.008, 0.025, n)
flow = rng.normal(0, 1, n)
return_oc = (0.007 * np.tanh(momentum) + 0.004 * (flow > 0)
             - 0.1 * volatility + rng.normal(0, 0.004, n))
df = pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=n),
                   "momentum": momentum, "volatility": volatility,
                   "flow": flow, "return_oc": return_oc})
print("总行数：", len(df))
display(df.head(8))''',
        "task": "特征在盘前可用，目标 return_oc 是同日开盘到收盘收益。任务：按时间取前 60% 训练、中间 20% 验证、最后 20% 测试。用验证 RMSE 决定停止轮数，测试集不进入 eval_set。本例需要可选包 xgboost；未安装时明确跳过，不改用其他模型冒充运行结果。",
        "train": '''from sklearn.metrics import mean_squared_error, mean_absolute_error

try:
    from xgboost import XGBRegressor
    xgb_available = True
except (ImportError, OSError, ValueError) as exc:
    # XGBoostError 继承 ValueError；缺少 OpenMP 动态库时也要明确跳过。
    xgb_available = False
    print("跳过 M10：XGBoost 未安装或动态库加载失败。请按 Notebook 开头的安装说明配置后重跑。")
    print(type(exc).__name__ + ": " + str(exc).strip().splitlines()[0])

if xgb_available:
    df["date"] = pd.to_datetime(df["date"])
    assert df["date"].notna().all() and df["date"].is_unique, "日期须非空且唯一"
    df = df.sort_values("date").reset_index(drop=True)
    features = ["momentum", "volatility", "flow"]
    cut1, cut2 = int(len(df) * 0.6), int(len(df) * 0.8)
    train, valid, test = df.iloc[:cut1], df.iloc[cut1:cut2], df.iloc[cut2:]
    # early_stopping_rounds 放在构造器中，兼容 XGBoost 2.0.3 和较新版本。
    model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=2,
                         min_child_weight=5, reg_lambda=5, objective="reg:squarederror",
                         eval_metric="rmse", tree_method="hist", early_stopping_rounds=15,
                         random_state=42, n_jobs=1)
    model.fit(train[features], train["return_oc"],
              eval_set=[(train[features], train["return_oc"]),
                        (valid[features], valid["return_oc"])], verbose=False)
    # 最后一份 eval_set（验证集）用于 early stopping；predict 自动使用最佳轮数。
    history = model.evals_result()
    prediction = model.predict(test[features])
    result = test[["date", "return_oc"]].assign(prediction=prediction)
    display(result.head(8))
    display(pd.DataFrame([{
        "best_round": model.best_iteration + 1,
        "test_rmse": np.sqrt(mean_squared_error(test["return_oc"], prediction)),
        "test_mae": mean_absolute_error(test["return_oc"], prediction),
        "mean_baseline_rmse": np.sqrt(mean_squared_error(test["return_oc"],
                                                          np.repeat(train["return_oc"].mean(), len(test))))}]).round(5))''',
        "plot": '''if xgb_available:
    train_rmse = np.array(history["validation_0"]["rmse"])
    valid_rmse = np.array(history["validation_1"]["rmse"])
    rounds = np.arange(1, len(train_rmse) + 1)
    plt.figure(figsize=(8, 4))
    plt.plot(rounds, train_rmse * 100, color=BLUE, linewidth=2, label="Train")
    plt.plot(rounds, valid_rmse * 100, color=ORANGE, linewidth=2, label="Validation")
    plt.axvline(model.best_iteration + 1, color="grey", linestyle="--", label="Best validation round")
    plt.title("XGBoost: chronological validation")
    plt.xlabel("Boosting round")
    plt.ylabel("Return RMSE (percentage points)")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.show()
else:
    print("M10 图表已跳过：需要先成功加载并训练 XGBoost。")''',
        "reading": "蓝线是训练误差，橙线是后续时间段的验证误差；虚线标出验证误差最小的迭代轮数。early stopping 会继续观察若干轮，所以曲线可能延伸到虚线之后。测试集仅出现在结果表，不参与轮数选择或学习曲线。",
        "caution": "当 eval_set 有多个数据集时，最后一个用于 early stopping；不要把测试集放在最后。学习率、树深度等若继续搜索，也只能用训练区间和验证集。该模板直接保留 early stopping 得到的模型；若改为合并训练与验证集重训，须先固定最佳轮数并移除 early stopping。",
    },
]
