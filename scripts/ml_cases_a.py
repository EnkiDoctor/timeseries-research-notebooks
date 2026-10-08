"""Independent sklearn examples M01-M05; generated notebooks need no repo imports."""

CASES = [
    {
        "id": "M01",
        "title": "价格表 → 因果特征、未来标签与隔离边界",
        "data": '''rng = np.random.RandomState(101)
n = 140
df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=n),
    "close": 100 * np.cumprod(1 + rng.normal(0.0002, 0.012, n)),
})
print("输入行数：", len(df))
display(df.head(8).round(4))''',
        "task": "场景：只有每日收盘价，要预测下一段 close-to-close 收益。date 是交易日，close 是收盘价。假定每天 16:00 收盘信息齐备后生成特征：当天收益、过去5期均值、过去10期波动率。feature_time 记录预测时点，label_end 记录标签全部实现的时点。先构造标签，再按时间切分；训练标签必须严格早于测试首次预测时点，因此边界处至少有一条样本被隔离。最后用训练收益均值建立最简单的基线。",
        "train": '''from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].is_unique and (df["close"] > 0).all()
df["feature_time"] = df["date"] + pd.Timedelta(hours=16)
df["ret_1"] = df["close"].pct_change(fill_method=None)
# 收盘后预测，允许使用今天已经实现的收益；rolling 不使用未来行。
df["mean_5"] = df["ret_1"].rolling(5, min_periods=5).mean()
df["vol_10"] = df["ret_1"].rolling(10, min_periods=10).std()
df["target"] = df["close"].shift(-1) / df["close"] - 1
df["label_end"] = df["feature_time"].shift(-1)
features = ["ret_1", "mean_5", "vol_10"]
# 前10行窗口不足；最后1行没有未来标签。只删除，不能把标签填成0。
data = df.dropna(subset=features + ["target", "label_end"]).copy()
display(data[["feature_time"] + features + ["target", "label_end"]].head(8))

test_start = data["feature_time"].iloc[int(len(data) * 0.7)]
train = data.loc[data["label_end"] < test_start].copy()
test = data.loc[data["feature_time"] >= test_start].copy()
purged = data.loc[(data["feature_time"] < test_start) & (data["label_end"] >= test_start)]
assert train["label_end"].max() < test["feature_time"].min()
baseline = DummyRegressor(strategy="mean")
baseline.fit(train[features], train["target"])
test["prediction"] = baseline.predict(test[features])
display(pd.DataFrame({
    "split": ["train", "purged", "test"],
    "rows": [len(train), len(purged), len(test)],
    "first_prediction": [x["feature_time"].min() for x in [train, purged, test]],
    "last_label_end": [x["label_end"].max() for x in [train, purged, test]],
}))
display(test[["feature_time", "target", "prediction"]].head(8))
display(pd.DataFrame({"MAE": [mean_absolute_error(test["target"], test["prediction"])],
                      "RMSE": [np.sqrt(mean_squared_error(test["target"], test["prediction"]))]}))''',
        "plot": '''plt.figure(figsize=(10, 3.5))
plt.scatter(train["feature_time"], np.zeros(len(train)), color=BLUE, s=16)
plt.scatter(purged["feature_time"], np.ones(len(purged)), color=ORANGE, s=65, marker="x")
plt.scatter(test["feature_time"], np.full(len(test), 2), color=TEAL, s=16)
plt.axvline(test_start, color=ORANGE, linestyle="--", label="First test prediction")
plt.yticks([0, 1, 2], ["Train", "Purged", "Test"])
plt.ylim(-0.5, 2.6)
plt.title("Split by prediction time, purge by label availability")
plt.xlabel("Feature / prediction time")
plt.legend(loc="upper left")
plt.tight_layout()
plt.show()''',
        "reading": "先看加工后的表：每一行特征都只用截至 feature_time 的价格，而 target 会用到 label_end 的价格。橙色叉号表示训练标签在测试开始时尚未严格落在过去；本例将其隔离。基线的预测值是训练集 target 的均值，不会从测试期更新。",
        "caution": "本例是预测任务，不是可成交回测。收盘后得到信号，通常不能再按同一收盘价成交；接回测时应改成下一开盘执行并重新对齐收益。这里采用 label_end < test_start 的保守边界；若多期标签跨越更多交易日，应继续按真实 label_end 隔离，不能只固定删1行。140行合成数据只用于展示流程。",
    },
    {
        "id": "M02",
        "title": "线性回归：对比训练集均值基线",
        "data": '''rng = np.random.RandomState(102)
n = 150
flow_z = rng.normal(size=n)
overnight_ret = rng.normal(0, 0.008, n)
prev_ret = rng.normal(0, 0.01, n)
df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=n),
    "flow_z": flow_z,
    "overnight_ret": overnight_ret,
    "prev_ret": prev_ret,
    "intraday_ret": 0.0025 * flow_z + 0.18 * overnight_ret - 0.08 * prev_ret + rng.normal(0, 0.006, n),
})
print("输入行数：", len(df))
display(df.head(8).round(5))''',
        "task": "场景：使用盘前信息预测当天开盘到收盘收益。flow_z 是事先定义的盘前订单流分数，overnight_ret 是昨收至09:25盘前报价的收益，prev_ret 是上一交易日已实现收益；三者在当天09:25已知。intraday_ret 是当天开盘到收盘收益，直到收盘才完整已知。按日期前70%训练、后30%测试；比较 LinearRegression 与只预测训练均值的 DummyRegressor，展示 MAE、RMSE、R²。",
        "train": '''from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
assert df["date"].is_unique
features = ["flow_z", "overnight_ret", "prev_ret"]
split = int(len(df) * 0.7)
train, test = df.iloc[:split].copy(), df.iloc[split:].copy()
assert train["date"].max() < test["date"].min()
X_train, y_train = train[features], train["intraday_ret"]
X_test, y_test = test[features], test["intraday_ret"]
model = LinearRegression()
baseline = DummyRegressor(strategy="mean")
model.fit(X_train, y_train)
baseline.fit(X_train, y_train)
test["prediction"] = model.predict(X_test)
test["baseline"] = baseline.predict(X_test)
metrics = []
for name in ["prediction", "baseline"]:
    metrics.append({"model": name,
                    "MAE": mean_absolute_error(y_test, test[name]),
                    "RMSE": np.sqrt(mean_squared_error(y_test, test[name])),
                    "R2": r2_score(y_test, test[name]) if y_test.nunique() > 1 else np.nan})
display(pd.DataFrame(metrics).set_index("model").round(5))
display(test[["date", "intraday_ret", "prediction", "baseline"]].head(8).round(5))''',
        "plot": '''actual_pct = test["intraday_ret"] * 100
pred_pct = test["prediction"] * 100
lower = min(actual_pct.min(), pred_pct.min()) - 0.1
upper = max(actual_pct.max(), pred_pct.max()) + 0.1
plt.figure(figsize=(6, 5))
plt.scatter(actual_pct, pred_pct, color=BLUE, alpha=0.65, edgecolors="white", s=45)
plt.plot([lower, upper], [lower, upper], color=ORANGE, linestyle="--", label="Perfect prediction")
plt.xlim(lower, upper)
plt.ylim(lower, upper)
plt.axhline(0, color="grey", linewidth=0.7)
plt.axvline(0, color="grey", linewidth=0.7)
plt.title("Linear regression: held-out predictions")
plt.xlabel("Actual intraday return (%)")
plt.ylabel("Predicted intraday return (%)")
plt.legend()
plt.tight_layout()
plt.show()''',
        "reading": "散点越接近对角线，预测误差越小；集中在水平线附近说明模型给出的预测变化有限。先检查模型的 MAE/RMSE 是否比训练均值基线更低，再看 R²。R²可以为负；其参照的分母使用测试目标相对测试均值的平方差，并不等同于表里的训练均值基线。",
        "caution": "收益使用小数存储，绘图乘100后是百分比。这里模拟了微弱线性关系，不能据此推断真实可预测性。不要预测价格水平后用高R²宣称策略有效，也不要根据测试结果反复选特征。若同一天有多资产，应按完整日期切分，不能在同一天中间切行。",
    },
    {
        "id": "M03",
        "title": "缺失值与量纲不同：Imputer → Scaler → Ridge",
        "data": '''rng = np.random.RandomState(103)
n = 150
order_flow = rng.normal(0, 1000, n)
prev_ret = rng.normal(0, 0.012, n)
past_vol = rng.uniform(0.008, 0.03, n)
df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=n),
    "order_flow": order_flow,
    "prev_ret": prev_ret,
    "past_vol": past_vol,
    "intraday_ret": 0.000002 * order_flow - 0.12 * prev_ret + 0.08 * (past_vol - 0.02) + rng.normal(0, 0.006, n),
})
# 模拟特征缺失；标签仍完整，不填充或伪造标签。
df.loc[rng.choice(n, 15, replace=False), "order_flow"] = np.nan
df.loc[rng.choice(n, 12, replace=False), "past_vol"] = np.nan
print("输入行数：", len(df))
display(df.head(8).round(5))''',
        "task": "场景：数值特征有缺失、单位不同，希望建立稳定的线性基线。order_flow 是盘前流量，prev_ret 是昨日收益，past_vol 是截至昨日的波动率，全部在当天开盘前可用；intraday_ret 是当天开盘至收盘收益。前70%训练、后30%测试。在 Pipeline 内用训练数据拟合中位数填充、标准化与 Ridge，避免先对全量数据做预处理。alpha=1.0 事先固定。",
        "train": '''from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
features = ["order_flow", "prev_ret", "past_vol"]
split = int(len(df) * 0.7)
train, test = df.iloc[:split].copy(), df.iloc[split:].copy()
assert train["date"].max() < test["date"].min()
assert train[features].notna().any().all(), "训练期整列为空时应删除或另行定义该特征"
assert df["intraday_ret"].notna().all()
model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("ridge", Ridge(alpha=1.0)),
])
model.fit(train[features], train["intraday_ret"])
test["prediction"] = model.predict(test[features])
baseline = DummyRegressor(strategy="mean").fit(train[features], train["intraday_ret"])
test["baseline"] = baseline.predict(test[features])
display(pd.DataFrame({"train_missing": train[features].isna().sum(),
                      "test_missing": test[features].isna().sum(),
                      "train_median": model.named_steps["imputer"].statistics_}, index=features))
display(pd.DataFrame([
    {"model": c, "MAE": mean_absolute_error(test["intraday_ret"], test[c]),
     "RMSE": np.sqrt(mean_squared_error(test["intraday_ret"], test[c]))}
    for c in ["prediction", "baseline"]
]).set_index("model").round(5))
display(test[["date", "intraday_ret", "prediction"]].head(8).round(5))
coef = pd.Series(model.named_steps["ridge"].coef_, index=features).sort_values()
display(coef.to_frame("coefficient_per_training_std"))''',
        "plot": '''plt.figure(figsize=(8, 4))
plt.barh(coef.index, coef * 10000, color=np.where(coef >= 0, BLUE, RED), height=0.55)
plt.axvline(0, color="grey", linewidth=0.8)
plt.title("Ridge coefficients after training-only scaling")
plt.xlabel("Predicted return change per one training standard deviation (bp)")
plt.ylabel("Feature")
plt.tight_layout()
plt.show()''',
        "reading": "中位数表可以直接核对填充值是否只来自训练段。系数图表示其他特征不变时，填充后的某特征提高一个训练期标准差，预测收益变化多少bp；1bp=0.0001。若要换成 ElasticNet，可导入 ElasticNet 后将最后一步替换为 ('ridge', ElasticNet(alpha=0.0001, l1_ratio=0.5, max_iter=10000))；保留步骤名是为了沿用下方取系数代码。参数只是演示，正式调参应在训练期内部做时间验证。",
        "caution": "不能在切分前执行 fit_transform，也不能对测试期重新 fit。标准化系数不等于因果效应，相关特征会分摊系数。示例只有150行；真实数据中缺失本身可能有信息，可另设缺失指示列。若标签缺失，应排除无法评估的行，不能用中位数填充收益标签。",
    },
    {
        "id": "M04",
        "title": "数值＋类别列：ColumnTransformer 与未知类别",
        "data": '''rng = np.random.RandomState(104)
n = 150
event_type = rng.choice(["normal", "earnings", "macro"], size=n).astype(object)
event_type[120::3] = "special"  # 只在测试期出现的新品类。
flow_z = rng.normal(size=n)
prev_ret = rng.normal(0, 0.012, n)
event_effect = pd.Series(event_type).map({"normal": 0, "earnings": 0.002, "macro": -0.001, "special": 0.003}).to_numpy()
df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=n),
    "flow_z": flow_z,
    "prev_ret": prev_ret,
    "event_type": event_type,
    "intraday_ret": 0.002 * flow_z - 0.08 * prev_ret + event_effect + rng.normal(0, 0.005, n),
})
df.loc[[4, 30, 70, 110], "flow_z"] = np.nan
df.loc[[7, 35, 80, 115], "event_type"] = np.nan
print("输入行数：", len(df))
display(df.head(8).round(5))''',
        "task": "场景：盘前数值特征与已预告事件类别混在同一个表中，测试期还出现新品类。flow_z、prev_ret 和 event_type 均在当天开盘前已知；event_type 只能使用当时已知的日程，不能事后按收益贴标签。intraday_ret 是当天开盘至收盘收益。数值列做中位数填充和标准化，类别列做众数填充和 one-hot；日期和目标明确不进入模型。",
        "train": '''from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
numeric = ["flow_z", "prev_ret"]
categorical = ["event_type"]
features = numeric + categorical
split = int(len(df) * 0.7)
train, test = df.iloc[:split].copy(), df.iloc[split:].copy()
assert train["date"].max() < test["date"].min()
numeric_steps = Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scaler", StandardScaler())])
category_steps = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                           ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
# sparse_output=False 需要 sklearn >= 1.2；老版本对应参数名 sparse=False。
preprocess = ColumnTransformer([("num", numeric_steps, numeric),
                                ("cat", category_steps, categorical)], remainder="drop")
model = Pipeline([("preprocess", preprocess), ("ridge", Ridge(alpha=1.0))])
model.fit(train[features], train["intraday_ret"])
test["prediction"] = model.predict(test[features])
baseline = DummyRegressor(strategy="mean").fit(train[numeric], train["intraday_ret"])
test["baseline"] = baseline.predict(test[numeric])
seen = set(train["event_type"].dropna().unique())
unseen = set(test["event_type"].dropna().unique()) - seen
print("训练期出现的类别：", sorted(seen))
print("测试期新增的类别：", sorted(unseen))
display(pd.DataFrame({"model": ["Ridge", "Train mean"],
                      "RMSE": [np.sqrt(mean_squared_error(test["intraday_ret"], test[c]))
                               for c in ["prediction", "baseline"]]}))
display(test[["date", "event_type", "intraday_ret", "prediction"]].head(8).round(5))
display(test.loc[test["event_type"].isin(unseen), ["date", "event_type", "prediction"]].head(4))''',
        "plot": '''plt.figure(figsize=(10, 4))
plt.plot(test["date"], test["intraday_ret"] * 100, color="grey", alpha=0.6, linewidth=1, label="Actual")
plt.plot(test["date"], test["prediction"] * 100, color=BLUE, linewidth=1.7, label="Prediction")
plt.axhline(0, color="grey", linewidth=0.7)
plt.title("Mixed columns: held-out actual and predicted returns")
plt.xlabel("Test date")
plt.ylabel("Intraday return (%)")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()''',
        "reading": "图只展示测试段。新增 special 类别可以正常预测，因为 handle_unknown='ignore' 将这个类别在该 one-hot 特征块中编码为全0；它没有学到 special 的独有效应。下方小表特意打印了未知类别的预测，便于验证整个流程。",
        "caution": "不要将类别直接编码成1、2、3后交给线性回归，除非类别真的有数值顺序。one-hot 的类别集合和填充值只能从训练期学习。本例每行是一个交易日；多资产面板应按日期整体切分。正式训练前还应处理训练期整列缺失的情况；这不是用全量数据补齐类别词典的理由。",
    },
    {
        "id": "M05",
        "title": "涨跌分类：LogisticRegression 与混淆矩阵",
        "data": '''rng = np.random.RandomState(105)
n = 160
flow_z = rng.normal(size=n)
overnight_ret = rng.normal(0, 0.008, n)
vol_z = rng.normal(size=n)
latent_return = 0.9 * flow_z + 50 * overnight_ret - 0.4 * vol_z + rng.logistic(size=n)
df = pd.DataFrame({
    "date": pd.bdate_range("2024-01-02", periods=n),
    "flow_z": flow_z,
    "overnight_ret": overnight_ret,
    "vol_z": vol_z,
    "intraday_ret": 0.006 * np.tanh(latent_return),
})
df["target_up"] = (df["intraday_ret"] > 0).astype(int)
print("输入行数：", len(df))
display(df.head(8).round(5))''',
        "task": "场景：预测当日收盘是否高于开盘。flow_z、overnight_ret、vol_z 是当天开盘前已知的特征；intraday_ret 是当日开盘至收盘收益，仅用来生成 target_up，不能放入 X。target_up=1 代表上涨，0代表不涨。按日期前70%训练、后30%测试；用固定0.5概率阈值，比较 LogisticRegression 与永远预测训练期多数类的 DummyClassifier。",
        "train": '''from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
features = ["flow_z", "overnight_ret", "vol_z"]
split = int(len(df) * 0.7)
train, test = df.iloc[:split].copy(), df.iloc[split:].copy()
assert train["date"].max() < test["date"].min()
assert train["target_up"].nunique() == 2, "训练段需要同时含有上涨和不涨两类"
assert test["target_up"].nunique() == 2, "本例要求测试段含两类以比较 balanced accuracy"
model = Pipeline([("imputer", SimpleImputer(strategy="median")),
                  ("scaler", StandardScaler()),
                  ("logit", LogisticRegression(C=1.0, max_iter=1000, random_state=105))])
model.fit(train[features], train["target_up"])
test["prob_up"] = model.predict_proba(test[features])[:, 1]
test["prediction"] = (test["prob_up"] >= 0.5).astype(int)
baseline = DummyClassifier(strategy="most_frequent")
baseline.fit(train[features], train["target_up"])
test["baseline"] = baseline.predict(test[features])
display(pd.DataFrame({"train_count": train["target_up"].value_counts(),
                      "test_count": test["target_up"].value_counts()}).sort_index())
display(pd.DataFrame([
    {"model": c, "accuracy": accuracy_score(test["target_up"], test[c]),
     "balanced_accuracy": balanced_accuracy_score(test["target_up"], test[c])}
    for c in ["prediction", "baseline"]
]).set_index("model").round(4))
display(test[["date", "target_up", "prob_up", "prediction", "baseline"]].head(8).round(4))
cm = confusion_matrix(test["target_up"], test["prediction"], labels=[0, 1])
display(pd.DataFrame(cm, index=["Actual 0", "Actual 1"], columns=["Pred 0", "Pred 1"]))''',
        "plot": '''plt.figure(figsize=(5.5, 4.5))
plt.imshow(cm, cmap="Blues", vmin=0)
plt.colorbar(label="Number of observations")
for row in range(2):
    for col in range(2):
        plt.text(col, row, str(cm[row, col]), ha="center", va="center", fontsize=16,
                 color="white" if cm[row, col] > cm.max() / 2 else "black")
plt.xticks([0, 1], ["Not up (0)", "Up (1)"])
plt.yticks([0, 1], ["Not up (0)", "Up (1)"])
plt.grid(False)
plt.title("Logistic regression: test confusion matrix")
plt.xlabel("Predicted class at threshold 0.5")
plt.ylabel("Actual class")
plt.tight_layout()
plt.show()''',
        "reading": "混淆矩阵纵轴是真实类别、横轴是预测类别；左上和右下是正确预测，右上是假阳性，左下是假阴性。accuracy 是整体正确率；balanced accuracy 是两类召回率的平均，能减少类别比例差异造成的误导。先与多数类基线比较，再判断分类器是否有增益。",
        "caution": "阈值0.5预先固定，不根据这张测试混淆矩阵反复调整。概率质量、阈值选择和类别不平衡还需要单独验证；提高分类准确率不保证赚钱，因为涨跌幅和交易成本并不相同。本例的标准化分数是合成输入，实际构造时也必须避免用全样本均值或标准差。",
    },
]
