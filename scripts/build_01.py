"""Build the self-contained, Chinese pandas time-series recipe notebook.

This generator itself uses Python 3.8-compatible syntax. Executable recipes require
numpy and pandas only, except for an optional, explicitly marked Excel branch.
"""
from pathlib import Path
from textwrap import dedent
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
recipes = []


def recipe(code_id, title, scenario, inputs, change, output, pitfall, code, extra=""):
    recipes.append({
        "id": code_id, "title": title, "scenario": scenario, "inputs": inputs,
        "change": change, "output": output, "pitfall": pitfall,
        "code": dedent(code).strip(), "extra": dedent(extra).strip(),
    })


recipe("P01", "从表结构开始：Series、DataFrame、类型和形状",
       "刚拿到未知数据，先确定一行代表什么；区分一列 Series 与一列表 DataFrame。",
       "date：观测日期；asset：资产；price：价格；volume：数量。",
       "把样例 df 换成你的表；先检查字段名与单位，再选择列。",
       "原表 4×4；df['price'] 是长度 4 的 Series；df[['price']] 是 4×1 的表。",
       "shape 是行列数，size 是元素数；数字字符串不等于数值；索引不自动代表业务主键。",
       r'''
       df = pd.DataFrame({
           "date": pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"]),
           "asset": ["A", "B", "A", "B"],
           "price": [100.0, 50.0, 101.0, 49.0],
           "volume": [1000, 2000, 1200, 2200],
       })
       display(df)
       display(pd.DataFrame({"dtype": df.dtypes.astype(str), "non_null": df.notna().sum()}))
       print("行、列：", df.shape, "| 价格列形状：", df["price"].shape, df[["price"]].shape)
       assert df.shape == (4, 4) and df["date"].dtype.kind == "M"
       assert not df.duplicated(["date", "asset"]).any()
       ''')

recipe("P02", "读 CSV：保留代码前导零、指定缺失值与数值单位",
       "读入包含证券代码、日期、逗号分隔数量或供应商缺失标记的 CSV。",
       "date：YYYY-MM-DD；asset：需要保留前导零的标识；price / volume：数值文本。",
       "将 StringIO(csv_text) 换成文件路径；按数据字典修改 usecols、dtype、na_values。",
       "清洗后的 3×4 表，以及无法解析为数值的非空原始字段。",
       "不要把所有列强转 float；'NA' 可能是合法标识。保留原值，审计解析失败，百分数必须明确是否除以 100。",
       r'''
       from io import StringIO
       csv_text = 'date,asset,price,volume\n2024-01-02,000001,10.5,"1,000"\n2024-01-03,000001,MISSING,1200\n2024-01-04,000001,10.7,unknown\n'
       df = pd.read_csv(StringIO(csv_text), usecols=["date", "asset", "price", "volume"],
                        dtype={"asset": "string", "price": "string", "volume": "string"},
                        keep_default_na=False, na_values=["", "MISSING"])
       df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="raise")
       for col in ["price", "volume"]:
           raw = df[col].copy()
           cleaned = raw.str.replace(",", "", regex=False)
           df[col] = pd.to_numeric(cleaned, errors="coerce")
           failed = raw.notna() & df[col].isna()
           if failed.any():
               display(pd.DataFrame({"field": col, "raw_value": raw[failed]}))
       display(df)
       assert df.loc[0, "asset"] == "000001" and df.loc[0, "volume"] == 1000
       assert df["price"].isna().sum() == 1 and df["volume"].isna().sum() == 1
       ''')

recipe("P03", "多种日期格式：按规则解析并保留坏记录",
       "同一日期列混有 YYYY-MM-DD 与 YYYY/MM/DD，需要兼容旧版 pandas。",
       "raw_date：原始字符串，可能包含空格、空值或错误日期。",
       "按已知格式增减正则掩码与 format；对日/月顺序不明的数据先确认口径。",
       "原字符串、解析后日期、parse_failed 三列；错误记录可独立检查。",
       "不要依赖新版本 format='mixed'；不要猜 01/02/2024 是 1 月 2 日还是 2 月 1 日；errors='coerce' 后必须审计。",
       r'''
       df = pd.DataFrame({"raw_date": ["2024-01-02", "2024/01/03", " 2024-01-04 ", "bad", None]})
       text = df["raw_date"].astype("string").str.strip()
       parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
       for pattern, fmt in [(r"^\d{4}-\d{2}-\d{2}$", "%Y-%m-%d"),
                            (r"^\d{4}/\d{2}/\d{2}$", "%Y/%m/%d")]:
           mask = text.str.match(pattern, na=False)
           parsed.loc[mask] = pd.to_datetime(text.loc[mask], format=fmt, errors="coerce")
       df["date"] = parsed
       df["parse_failed"] = text.notna() & parsed.isna()
       display(df)
       display(df.loc[df["parse_failed"]])
       assert df["date"].notna().sum() == 3 and df["parse_failed"].sum() == 1
       ''')

recipe("P04", "Excel 可选入口：选 sheet、字段和代码类型",
       "题目给 Excel 工作簿时读取指定工作表；没有文件时，本单元运行内置示例。",
       "可选文件 data/interview.xlsx，工作表 observations，列 date / asset / price。",
       "设置 excel_path 和 sheet_name；先用 pd.ExcelFile 查看 sheet_names。",
       "三列标准表；无文件时明确显示“内置样例”，不会伪称读取真实文件。",
       "Excel 引擎通常需要额外 openpyxl。不要面试现场为本示例安装依赖；已有 CSV 时优先直接读 CSV。",
       r'''
       excel_path = ROOT / "data" / "interview.xlsx"
       if excel_path.exists():
           # 仅在确实提供 Excel 文件时执行；环境需已有相应 Excel 引擎。
           book = pd.ExcelFile(excel_path)
           print("工作表：", book.sheet_names)
           df = pd.read_excel(book, sheet_name="observations", usecols=["date", "asset", "price"],
                              dtype={"asset": "string"})
           source = "Excel 文件"
       else:
           df = pd.DataFrame({"date": ["2024-01-02", "2024-01-03"],
                              "asset": ["000001", "000001"], "price": [10.5, 10.6]})
           source = "内置样例（未读取 Excel）"
       df["date"] = pd.to_datetime(df["date"], errors="raise")
       df["price"] = pd.to_numeric(df["price"], errors="raise")
       print("数据来源：", source)
       display(df)
       assert set(df.columns) == {"date", "asset", "price"}
       ''')

recipe("P05", "第一轮审计：类型、缺失、主键、覆盖范围",
       "拿到数据后的前 5 分钟，检查样本单位、主键和日期覆盖；输出可放入汇报。",
       "date + asset 暂定为主键；price 为观测值。",
       "修改 key_cols；确认重复表示错误、修订版本还是本来就有更细粒度。",
       "按字段审计表、疑似重复记录、各资产覆盖和有效价格数量。",
       "重复日期不一定错误；时间序列面板允许同一天不同资产。不能仅凭 date 重复就去重。",
       r'''
       df = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04"]),
                          "asset": ["A", "A", "A", "B"], "price": [100.0, None, 102.0, 50.0]})
       key_cols = ["date", "asset"]
       audit = pd.DataFrame({"dtype": df.dtypes.astype(str), "n_missing": df.isna().sum(),
                             "missing_rate": df.isna().mean(), "n_unique": df.nunique(dropna=False)})
       duplicates = df.loc[df.duplicated(key_cols, keep=False)].sort_values(key_cols)
       coverage = df.groupby("asset").agg(start=("date", "min"), end=("date", "max"),
                                          rows=("date", "size"), valid_prices=("price", "count"))
       display(audit)
       display(duplicates)
       display(coverage)
       assert len(duplicates) == 2 and audit.loc["price", "n_missing"] == 1
       ''')

recipe("P06", "筛选：loc / iloc / 布尔掩码 / query",
       "按标签、位置或业务条件抽取行列；切片结果随后还要修改。",
       "asset、price、volume 三列；这里索引标签是 10 / 20 / 30 / 40。",
       "修改 thresholds、selected_assets 与选择的列；需要修改时用 .copy()。",
       "loc 条件筛选表、iloc 位置筛选表，以及等价 query 结果。",
       "loc 的整数是标签，iloc 的整数是位置；& / | 两侧条件要加括号；字符串列可含缺失。",
       r'''
       df = pd.DataFrame({"asset": ["A", "B", "A", "C"], "price": [100.0, 50.0, 103.0, 80.0],
                          "volume": [1000, 800, 1200, 900]}, index=[10, 20, 30, 40])
       threshold = 100.0
       mask = df["asset"].isin(["A", "B"]) & (df["price"] >= threshold)
       selected = df.loc[mask, ["asset", "price"]].copy()
       by_position = df.iloc[:2, :2]
       by_query = df.query("asset in ['A', 'B'] and price >= @threshold")[["asset", "price"]]
       display(selected)
       display(by_position)
       assert selected.equals(by_query) and selected.index.tolist() == [10, 30]
       ''')

recipe("P07", "索引自动对齐：先决定按标签还是按位置运算",
       "两列相加、赋值或拼接后出现意外 NaN，通常要检查 index。",
       "两个带资产标签的 Series，资产集合并不相同。",
       "修改期望的标签集合；只有证明行序一致时才考虑 .to_numpy()。",
       "默认按标签相加的结果，以及显式 inner / outer 对齐的对照。",
       "不要为了消除 NaN 直接 reset_index(drop=True)；这可能把不同日期、不同资产硬配成一行。",
       r'''
       left = pd.Series([1.0, 2.0], index=["A", "B"], name="left")
       right = pd.Series([20.0, 30.0], index=["B", "C"], name="right")
       report = pd.concat([left, right, (left + right).rename("sum_by_label")], axis=1)
       aligned_left, aligned_right = left.align(right, join="inner")
       inner_sum = aligned_left + aligned_right
       display(report)
       display(inner_sum.to_frame("matched_only"))
       assert inner_sum.to_dict() == {"B": 22.0}
       assert report["sum_by_label"].isna().sum() == 2
       ''')

recipe("P08", "安全赋值：copy、loc、assign 与 where / mask",
       "清洗局部数据或新增特征，避免链式赋值和修改原表的歧义。",
       "asset、price、volume；负成交量在本例中是非法值。",
       "修改业务条件与新列公式；保留原始列以便追踪。",
       "原始表和清洗后的副本；新增非法值标记及名义成交额。",
       "不要写 df[mask]['col'] = value；不要用 inplace=True 解决所有问题。where 保留条件为真的值，mask 替换条件为真的值。",
       r'''
       raw = pd.DataFrame({"asset": ["A", "B", "C"], "price": [100.0, 50.0, 20.0],
                           "volume": [1000.0, -1.0, 300.0]})
       clean = raw.copy()
       clean["bad_volume"] = clean["volume"] < 0
       clean.loc[clean["bad_volume"], "volume"] = np.nan
       clean = clean.assign(notional=lambda x: x["price"] * x["volume"])
       clean["positive_price"] = clean["price"].where(clean["price"] > 0)
       display(raw)
       display(clean)
       assert raw.loc[1, "volume"] == -1.0 and pd.isna(clean.loc[1, "volume"])
       ''')

recipe("P09", "缺失值一：按资产前向填充，并限制陈旧程度",
       "允许上一笔已知报价短时延用，但不同资产不能互填，过旧报价不能无限使用。",
       "date、asset、quote；缺失表示此日未获得新报价。",
       "修改 max_age；实际应按日历时间或已知交易会话计算。",
       "保留原 quote，新增 last_observed_at、quote_age、quote_filled。",
       "ffill(limit=2) 限的是行数而非两天；不能用 bfill 给历史预测填入未来值；价格、成交量和标签不应使用同一规则。",
       r'''
       df = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-08", "2024-01-02", "2024-01-03"]),
                          "asset": ["A", "A", "A", "B", "B"], "quote": [100.0, None, None, None, 50.0]})
       df = df.sort_values(["asset", "date"]).reset_index(drop=True)
       max_age = pd.Timedelta("2D")
       df["last_observed_at"] = df["date"].where(df["quote"].notna())
       df["last_observed_at"] = df.groupby("asset")["last_observed_at"].ffill()
       df["quote_age"] = df["date"] - df["last_observed_at"]
       candidate = df.groupby("asset")["quote"].ffill()
       df["quote_filled"] = candidate.where(df["quote_age"] <= max_age)
       display(df)
       assert df.loc[1, "quote_filled"] == 100.0
       assert pd.isna(df.loc[2, "quote_filled"]) and pd.isna(df.loc[3, "quote_filled"])
       ''')

recipe("P10", "缺失值二：训练集统计量填补与缺失指示变量",
       "非时间报价类特征需要为模型填补；使用训练段中位数，同时保留缺失信息。",
       "date、feature；cutoff 之前属于训练段。",
       "修改 cutoff 和 feature_cols；这里演示单特征，实际建模可使用 sklearn Pipeline。",
       "原特征、缺失标记和填补后的特征；打印只在训练段估计的中位数。",
       "全样本 median 含测试分布信息；目标标签通常不能填补后当作真实标签评估；训练列全缺失应明确报错。",
       r'''
       df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=6),
                          "feature": [1.0, np.nan, 3.0, 100.0, np.nan, 200.0]})
       cutoff = pd.Timestamp("2024-01-04")
       train = df["date"] < cutoff
       train_median = df.loc[train, "feature"].median()
       assert pd.notna(train_median), "训练段无有效特征，先处理数据覆盖问题"
       df["feature_missing"] = df["feature"].isna().astype("int8")
       df["feature_filled"] = df["feature"].fillna(train_median)
       print("训练段中位数：", train_median)
       display(df)
       assert train_median == 2.0 and df.loc[4, "feature_filled"] == 2.0
       ''')

recipe("P11", "重复记录：区分完全重复、冲突值与数据修订",
       "同一业务主键有多行，需要解释是重复导出、不同版本还是不同事件。",
       "date + asset 为主键；updated_at 为版本时间；price 为字段值。",
       "修改 key_cols 和版本规则；只在业务确认使用最新修订的离线分析中保留最后版本。",
       "冲突表与按版本选择后的唯一主键表。",
       "drop_duplicates(keep='last') 取决于当前行序；最新版可能在历史预测时尚不可知，预测特征需用 P18 按 available_at 匹配。",
       r'''
       raw = pd.DataFrame({"date": pd.to_datetime(["2024-01-02"] * 3 + ["2024-01-03"]),
                           "asset": ["A"] * 4, "price": [100.0, 100.0, 101.0, 102.0],
                           "updated_at": pd.to_datetime(["2024-01-02 16:00", "2024-01-02 16:00", "2024-01-04 09:00", "2024-01-03 16:00"])})
       key_cols = ["date", "asset"]
       exact_removed = raw.drop_duplicates().copy()
       conflicts = exact_removed.loc[exact_removed.duplicated(key_cols, keep=False)].sort_values(key_cols + ["updated_at"])
       latest_snapshot = exact_removed.sort_values(key_cols + ["updated_at"]).drop_duplicates(key_cols, keep="last")
       display(conflicts)
       display(latest_snapshot)
       print("本例 latest_snapshot 仅供按最新版描述；不得直接用于历史可交易特征。")
       assert len(exact_removed) == 3 and not latest_snapshot.duplicated(key_cols).any()
       ''')

recipe("P12", "无穷值、占位值、单位与合法范围",
       "供应商用 -999 表示缺失，百分比以 1.5 表示 1.5%，或计算后出现 inf。",
       "raw_return_pct：百分数；volume：非负数量；sentinel -999 是本例约定。",
       "根据数据字典修改 sentinel、单位和合法范围；不要套用到任意连续特征。",
       "原值、十进制收益、非法收益标记和清洗结果。",
       "真实大涨大跌不能仅因为极端就删除；简单收益理论下限为 -1，上限不设统一阈值；复权价格错误需回源检查。",
       r'''
       df = pd.DataFrame({"raw_return_pct": [1.5, -2.0, -999.0, np.inf, -120.0],
                          "volume": [1000.0, 2000.0, 0.0, -1.0, 100.0]})
       value = df["raw_return_pct"].replace(-999.0, np.nan) / 100.0
       value = value.replace([np.inf, -np.inf], np.nan)
       df["invalid_simple_return"] = value < -1.0
       df["return_decimal"] = value.mask(df["invalid_simple_return"])
       df["volume_clean"] = df["volume"].where(df["volume"] >= 0)
       display(df)
       assert df.loc[0, "return_decimal"] == 0.015
       assert df["return_decimal"].notna().sum() == 2 and df.loc[2, "volume_clean"] == 0.0
       ''')

recipe("P13", "groupby：agg 压缩成每组一行，transform 保持原行数",
       "做各资产描述统计，或把组均值、组样本量广播回原始表。",
       "asset、value；value 可以是收益或非金融测量值。",
       "修改分组键与聚合函数；使用命名聚合让输出列名清晰。",
       "agg 输出资产×统计量；transform 输出与原表同长度的列。",
       "size 计入缺失行，count 只计非缺失值；本例全样本组均值用于描述，不可直接当预测标准化参数。",
       r'''
       df = pd.DataFrame({"asset": ["A", "A", "A", "B", "B"], "value": [1.0, 2.0, None, 10.0, 12.0]})
       summary = df.groupby("asset").agg(n_rows=("value", "size"), n_valid=("value", "count"),
                                         mean=("value", "mean"), std=("value", "std"))
       df["group_mean_descriptive"] = df.groupby("asset")["value"].transform("mean")
       df["group_n_valid"] = df.groupby("asset")["value"].transform("count")
       display(summary)
       display(df)
       assert summary.loc["A", "n_rows"] == 3 and summary.loc["A", "n_valid"] == 2
       assert len(df["group_mean_descriptive"]) == len(df)
       ''')

recipe("P14", "横截面排名、并列名次与固定阈值分箱",
       "每天比较不同资产的相对得分，生成 percentile rank 或便于汇报的分组。",
       "date、asset、score；每个日期内资产唯一，且分数在同一决策时点可知。",
       "修改 rank 的 method / ascending；根据目标选择固定阈值或分位数桶。",
       "保留全部行，新增百分位排名与 low / middle / high 桶。",
       "并列值多时 qcut 可能无法形成足够桶；method='first' 会让行序决定名次。固定排名阈值不保证每桶人数相同。",
       r'''
       df = pd.DataFrame({"date": pd.to_datetime(["2024-01-02"] * 5),
                          "asset": list("ABCDE"), "score": [1.0, 1.0, 2.0, 3.0, np.nan]})
       df["rank_pct"] = df.groupby("date")["score"].rank(method="average", pct=True)
       df["bucket"] = pd.cut(df["rank_pct"], bins=[0.0, 0.4, 0.8, 1.0],
                              labels=["low", "middle", "high"], include_lowest=True)
       display(df)
       display(df.groupby("bucket", observed=True)["asset"].count().rename("n_assets").to_frame())
       assert df.loc[0, "rank_pct"] == df.loc[1, "rank_pct"] == 0.375
       assert pd.isna(df.loc[4, "bucket"])
       ''')

recipe("P15", "组覆盖筛选：计数、最小样本量和保留缺失组",
       "只分析样本足够的对象，或审计缺失分类标签对应的记录。",
       "asset 为分组标识，value 可以缺失；这里对缺失 asset 显式保留独立组。",
       "修改 min_observations；明确筛的是总行数还是有效观测数。",
       "每行附有效观测数的原表、组汇总与通过筛选后的表。",
       "groupby 默认忽略 NA 分组键；有效样本不足时估计很不稳定。真实预测场景的样本量筛选必须只用当时已知历史。",
       r'''
       df = pd.DataFrame({"asset": ["A", "A", "A", "B", "B", None],
                          "value": [1.0, 2.0, None, 5.0, None, 9.0]})
       df["asset_group"] = df["asset"].fillna("__MISSING_ASSET__")
       df["n_valid_descriptive"] = df.groupby("asset_group")["value"].transform("count")
       min_observations = 2
       kept = df.loc[df["n_valid_descriptive"] >= min_observations].copy()
       display(df.groupby("asset_group").agg(rows=("value", "size"), valid=("value", "count")))
       display(kept)
       assert len(kept) == 3 and set(kept["asset"]) == {"A"}
       ''')

recipe("P16", "concat：合并多个批次，并记录来源与边界重复",
       "按月份、文件或供应商分批读入的数据，需要纵向拼接。",
       "每批包含 date、asset、value；source_file 记录文件来源。",
       "修改批次列表和主键；真实多文件可用 sorted(Path(...).glob('*.csv'))。",
       "拼接后的表以及跨文件重复记录；不自动删除冲突。",
       "循环中不断 concat 会反复复制；先放 list 再一次 concat。列缺失会产生 NaN，不能误以为所有文件模式一致。",
       r'''
       batch_a = pd.DataFrame({"date": ["2024-01-02", "2024-01-03"], "asset": ["A", "A"], "value": [1.0, 2.0]})
       batch_b = pd.DataFrame({"date": ["2024-01-03", "2024-01-04"], "asset": ["A", "A"], "value": [2.0, 3.0]})
       parts = []
       for source_name, part in [("batch_a.csv", batch_a), ("batch_b.csv", batch_b)]:
           assert set(part.columns) == {"date", "asset", "value"}
           parts.append(part.assign(source_file=source_name))
       combined = pd.concat(parts, ignore_index=True)
       combined["date"] = pd.to_datetime(combined["date"], format="%Y-%m-%d")
       duplicates = combined.loc[combined.duplicated(["date", "asset"], keep=False)]
       display(combined)
       display(duplicates)
       assert len(combined) == 4 and len(duplicates) == 2
       ''')

recipe("P17", "merge：限制连接基数、检查未匹配和空键",
       "把资产元数据连接到逐日观测表，防止多对多连接意外放大样本。",
       "observations：asset、value；metadata：asset、sector，asset 应唯一。",
       "修改 on、how 和 validate；多条观测连接一条元数据用 many_to_one。",
       "保留左表行数的连接结果，含 _merge 标记；独立显示未匹配键。",
       "pandas 会让两边空键彼此匹配，与常见 SQL 语义不同；先拒绝或隔离空键。多对多需业务理由，不能为运行成功删除 validate。",
       r'''
       observations = pd.DataFrame({"asset": ["A", "A", "B", "C", None], "value": [1, 2, 3, 4, 5]})
       metadata = pd.DataFrame({"asset": ["A", "B"], "sector": ["Tech", "Energy"]})
       assert metadata["asset"].notna().all() and metadata["asset"].is_unique
       null_keys = observations.loc[observations["asset"].isna()].copy()
       usable = observations.loc[observations["asset"].notna()].copy()
       joined = usable.merge(metadata, on="asset", how="left", validate="many_to_one", indicator=True)
       unmatched = joined.loc[joined["_merge"] == "left_only", ["asset"]].drop_duplicates()
       display(joined)
       display(unmatched)
       display(null_keys)
       assert len(joined) == len(usable) and unmatched["asset"].tolist() == ["C"]
       ''')

recipe("P18", "merge_asof：按信息可用时间做 point-in-time 连接",
       "在每个决策时点取该资产当时已发布的最近特征，限制数据陈旧程度。",
       "decisions：asset、decision_at；releases：asset、available_at、feature。available_at 是可获知时间，不是报告所属期。",
       "修改 tolerance、时间字段与 exact-match 规则；右表同资产同发布时间必须先明确消歧。",
       "每条决策最多匹配一条过去发布记录，含 age；未匹配保留 NaN。",
       "两侧必须按各自时间键全局递增排序，不能只 sort_values(['asset','time'])。backward 才是向过去匹配；严格发布延迟可设 allow_exact_matches=False。",
       r'''
       decisions = pd.DataFrame({"asset": ["A", "B", "A", "B"],
                                 "decision_at": pd.to_datetime(["2024-01-03 10:00", "2024-01-03 10:00", "2024-01-06 10:00", "2024-01-06 10:00"])})
       decisions["row_id"] = np.arange(len(decisions))
       releases = pd.DataFrame({"asset": ["A", "B", "A"],
                                "available_at": pd.to_datetime(["2024-01-02 09:00", "2024-01-03 11:00", "2024-01-05 09:00"]),
                                "feature": [10.0, 20.0, 11.0]})
       assert not releases.duplicated(["asset", "available_at"]).any()
       left = decisions.sort_values(["decision_at", "asset"])
       right = releases.sort_values(["available_at", "asset"])
       joined = pd.merge_asof(left, right, left_on="decision_at", right_on="available_at", by="asset",
                              direction="backward", tolerance=pd.Timedelta("2D"), allow_exact_matches=True)
       joined["age"] = joined["decision_at"] - joined["available_at"]
       joined = joined.sort_values("row_id").drop(columns="row_id").reset_index(drop=True)
       display(joined)
       matched = joined["available_at"].notna()
       assert (joined.loc[matched, "age"] >= pd.Timedelta(0)).all()
       assert (joined.loc[matched, "age"] <= pd.Timedelta("2D")).all()
       assert joined["feature"].notna().sum() == 2  # B 的第一条是未来发布，第二条已太陈旧。
       ''')

recipe("P19", "长表转宽表：pivot 与有明确业务聚合的 pivot_table",
       "把 date × asset 的长表变成相关矩阵、收益矩阵常用的宽表。",
       "date、asset、return；期望 date + asset 唯一。",
       "修改 index / columns / values；有重复时先检查，不要默认取均值掩盖冲突。",
       "宽收益表，行是日期、列是资产；新增的空单元仍为 NaN。",
       "pivot 要求主键唯一；pivot_table 会聚合。收益是否能平均、成交量是否应求和，必须由样本含义决定。",
       r'''
       long = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03"]),
                            "asset": ["A", "B", "A"], "return": [0.01, -0.02, 0.03]})
       assert not long.duplicated(["date", "asset"]).any(), "先检查重复，不要静默取均值"
       wide = long.pivot(index="date", columns="asset", values="return").sort_index()
       # 另一个业务：多笔交易的成交数量允许在同日同资产求和。
       trades = pd.DataFrame({"date": pd.to_datetime(["2024-01-02"] * 3),
                              "asset": ["A", "A", "B"], "quantity": [100, 200, 50]})
       volume_wide = trades.pivot_table(index="date", columns="asset", values="quantity", aggfunc="sum")
       display(wide)
       display(volume_wide)
       assert wide.shape == (2, 2) and pd.isna(wide.loc[pd.Timestamp("2024-01-03"), "B"])
       assert volume_wide.loc[pd.Timestamp("2024-01-02"), "A"] == 300
       ''')

recipe("P20", "宽表转长表：melt、stack 和缺失值保留",
       "把每个资产占一列的数据转为可 groupby、连接或作图的长格式。",
       "date 列 + 多个资产数值列。",
       "修改 id_vars、value_vars、var_name 和 value_name；显式决定是否丢弃缺失观测。",
       "原宽表 2×3，长表 4×3；保留 B 在第二天的缺失值。",
       "melt 会保留 NaN；传统 stack 默认丢弃 NaN。写清楚这一差异，避免样本覆盖悄悄改变。",
       r'''
       wide = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                            "A": [0.01, 0.02], "B": [-0.01, np.nan]})
       long = wide.melt(id_vars=["date"], value_vars=["A", "B"], var_name="asset", value_name="return")
       long = long.sort_values(["date", "asset"]).reset_index(drop=True)
       roundtrip = long.pivot(index="date", columns="asset", values="return")
       display(long)
       display(roundtrip)
       assert len(long) == 4 and long["return"].isna().sum() == 1
       assert np.allclose(roundtrip.values, wide.set_index("date").values, equal_nan=True)
       ''')

recipe("P21", "MultiIndex：用资产与时间定位，并安全回到普通列",
       "数据已有两层索引，需要按资产取时间序列、按日期取横截面或接外部表。",
       "asset、date、value；asset + date 唯一。",
       "修改索引层名称；使用 xs(level=...) 避免混淆层顺序。",
       "两层索引表、A 的时间序列、某日横截面和 reset_index 后的普通表。",
       "切片前 sort_index；索引层不是普通列；groupby / rolling 常新增索引层，不能盲目赋回。",
       r'''
       df = pd.DataFrame({"asset": ["B", "A", "A", "B"],
                          "date": pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-03", "2024-01-02"]),
                          "value": [20.0, 1.0, 2.0, 10.0]})
       panel = df.set_index(["asset", "date"]).sort_index()
       assert panel.index.is_unique
       one_asset = panel.xs("A", level="asset")
       one_date = panel.xs(pd.Timestamp("2024-01-03"), level="date")
       flat = panel.reset_index()
       display(panel)
       display(one_asset)
       display(one_date)
       assert one_asset["value"].tolist() == [1.0, 2.0]
       assert flat.shape == df.shape
       ''')

recipe("P22", "按资产计算 shift、diff 与收益：禁止跨资产串行",
       "给每个资产计算上一条价格、价格变化和相邻观测的简单收益。",
       "date、asset、price；价格必须为正，主键必须唯一。",
       "修改价格字段；收益口径是相邻已存在的观测行，是否等于一天需另外核实。",
       "新增 prev_price、price_diff、return_1row；各资产首行收益为 NaN。",
       "整体 df['price'].pct_change() 会跨资产计算；先排序再分组；pct_change(fill_method=None) 防止旧版默认填充缺失价格。",
       r'''
       df = pd.DataFrame({"asset": ["B", "A", "B", "A", "A"],
                          "date": pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]),
                          "price": [51.0, 100.0, 50.0, np.nan, 102.0]})
       assert not df.duplicated(["asset", "date"]).any()
       assert (df["price"].dropna() > 0).all()
       df = df.sort_values(["asset", "date"]).reset_index(drop=True)
       group = df.groupby("asset")["price"]
       df["prev_price"] = group.shift(1)
       df["price_diff"] = group.diff(1)
       df["return_1row"] = group.pct_change(periods=1, fill_method=None)
       display(df)
       assert df.groupby("asset").head(1)["return_1row"].isna().all()
       assert df.loc[df["asset"] == "A", "return_1row"].isna().all()
       assert np.isclose(df.loc[4, "return_1row"], 0.02)
       ''')

recipe("P23", "未来收益标签：明确预测起点、终点和缺失尾部",
       "构造从时点 t 到该资产第 h 条未来观测的收益标签，用于预测评估。",
       "date、asset、price；假设价格经过适当复权，并且每个资产时间顺序清楚。",
       "修改 horizon；真实执行若要下一开盘进场，应改分母、终点及交易成本口径。",
       "feature_at、label_end、future_return 三个核心字段，末尾 h 行无标签。",
       "shift(-h) 只能用于标签，不能进入当时特征；h 条观测不是 h 个自然日；以收盘价作分母不自动说明能在该价成交。",
       r'''
       df = pd.DataFrame({"asset": ["A"] * 5 + ["B"] * 5,
                          "date": list(pd.date_range("2024-01-02", periods=5)) * 2,
                          "price": [100., 101., 102., 103., 104., 50., 49., 51., 52., 53.]})
       df = df.sort_values(["asset", "date"]).reset_index(drop=True)
       horizon = 2
       group = df.groupby("asset")
       df["feature_at"] = df["date"]
       df["label_end"] = group["date"].shift(-horizon)
       df["future_return"] = group["price"].shift(-horizon) / df["price"] - 1.0
       display(df)
       known_labels = df["future_return"].notna()
       assert (df.loc[known_labels, "label_end"] > df.loc[known_labels, "feature_at"]).all()
       assert df["future_return"].isna().sum() == 2 * horizon
       assert np.isclose(df.loc[0, "future_return"], 0.02)
       ''')

recipe("P24", "rolling：最近 N 行与最近 N 天不是同一窗口",
       "观测频率不规则，要区分固定条数与真实时间跨度；决定是否排除当前观测。",
       "唯一递增 DatetimeIndex 的单资产 Series，含隔周末或停牌造成的间隔。",
       "修改 window、min_periods 和 closed；本例时间窗口采用 [t−3 天, t)，不含当前值。",
       "原序列、过去 2 行均值、过去 3 自然日均值的对照表。",
       "rolling(3) 是 3 条观测；rolling('3D') 是 3×24 小时。是否使用当前值取决于决策时点；UTC 跨 DST 的小时窗与当地自然日也不同。",
       r'''
       s = pd.Series([10.0, 20.0, 30.0, 40.0],
                     index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-08", "2024-01-09"]), name="value")
       assert s.index.is_monotonic_increasing and s.index.is_unique
       result = s.to_frame()
       result["past_2_rows"] = s.shift(1).rolling(window=2, min_periods=2).mean()
       result["past_3_days"] = s.rolling(window="3D", closed="left", min_periods=1).mean()
       display(result)
       assert result.loc["2024-01-08", "past_2_rows"] == 15.0
       assert pd.isna(result.loc["2024-01-08", "past_3_days"])
       assert result.loc["2024-01-09", "past_3_days"] == 30.0
       ''')

recipe("P25", "分组 rolling 对齐：transform 或移除明确的组索引层",
       "在面板数据中计算各资产过去窗口统计量，并可靠地赋回原行。",
       "asset、date、value；排序后重新建立唯一整数行索引。",
       "修改窗口与统计量；在每个组内 shift，不能 rolling 后对整列 shift。",
       "用两种写法得到一致的 past_mean；显示 grouped rolling 返回的 MultiIndex。",
       "groupby().rolling() 的结果带组键索引，直接赋值可能报错或错位；reset_index(drop=True) 会抹掉可用于对齐的原行号。",
       r'''
       df = pd.DataFrame({"asset": ["B", "A", "B", "A", "B", "A"],
                          "date": pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04", "2024-01-04"]),
                          "value": [10., 1., 20., 2., 30., 3.]})
       df = df.sort_values(["asset", "date"]).reset_index(drop=True)
       df["past_mean"] = df.groupby("asset")["value"].transform(lambda s: s.shift(1).rolling(2, min_periods=2).mean())
       # 等价写法：先在资产内部滞后，再 rolling；保留原行号以便赋回。
       df["lagged"] = df.groupby("asset")["value"].shift(1)
       grouped_result = df.groupby("asset")["lagged"].rolling(2, min_periods=2).mean()
       aligned = grouped_result.reset_index(level=0, drop=True).reindex(df.index)
       df["past_mean_equivalent"] = aligned
       display(grouped_result.rename("rolling_with_group_index").to_frame())
       display(df)
       assert np.allclose(df["past_mean"], df["past_mean_equivalent"], equal_nan=True)
       assert df.groupby("asset").head(2)["past_mean"].isna().all()
       ''')

recipe("P26", "expanding 与 ewm：历史累计均值和指数加权均值",
       "用所有过去观测或更重视近期观测的方式构造平滑特征。",
       "asset、date、value；按资产时间排序。",
       "修改 min_periods、span 或 alpha，以及 adjust；本例均排除当前观测。",
       "与原表同形状，新增 past_expanding_mean、past_ewm。",
       "ewm(span=...) 基于观测条数，不自动等于日历半衰期；adjust=False 是递推权重；缺失值处理和初始化影响结果。",
       r'''
       df = pd.DataFrame({"asset": ["A"] * 4 + ["B"] * 4,
                          "date": list(pd.date_range("2024-01-02", periods=4)) * 2,
                          "value": [1., 2., 6., 4., 10., 20., 60., 40.]})
       df = df.sort_values(["asset", "date"]).reset_index(drop=True)
       df["past_expanding_mean"] = df.groupby("asset")["value"].transform(lambda s: s.shift(1).expanding(min_periods=2).mean())
       df["past_ewm"] = df.groupby("asset")["value"].transform(lambda s: s.shift(1).ewm(span=3, adjust=False, min_periods=2).mean())
       display(df)
       assert df.loc[2, "past_expanding_mean"] == 1.5
       assert df.loc[3, "past_expanding_mean"] == 3.0 and df.loc[3, "past_ewm"] == 3.75
       ''')

recipe("P27", "日频转月频：价格取期末，收益复利聚合",
       "生成月度价格或累计收益，理解 last 与 compounded return 的区别。",
       "单资产 date、price、daily_return；每日收益为小数，本例仅提供稀疏片段。",
       "用 pd.offsets.MonthEnd()，兼容不同 pandas 的月末别名；改变聚合字段和覆盖检查。",
       "月末价格、观测行数、有效收益数与“已提供观测区间”的复合收益。",
       "月收益不能把日收益简单相加；prod 默认跳过缺失，会伪造完整收益。样本从月中开始或缺交易日时，不能称为完整月收益。",
       r'''
       df = pd.DataFrame({"date": pd.to_datetime(["2024-01-29", "2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02"]),
                          "price": [100., 102., 101., 103., 104.],
                          "daily_return": [0.01, 0.02, 101.0 / 102.0 - 1.0, 103.0 / 101.0 - 1.0, np.nan]}).set_index("date")
       month_rule = pd.offsets.MonthEnd()
       grouped = df.resample(month_rule, closed="right", label="right")
       monthly = grouped.agg(last_price=("price", "last"), rows=("daily_return", "size"), valid_returns=("daily_return", "count"))
       compounded = grouped["daily_return"].apply(lambda s: (1.0 + s).prod(min_count=1) - 1.0)
       monthly["return_over_observed_rows"] = compounded.where(monthly["rows"] == monthly["valid_returns"])
       display(monthly)
       print("这些日期只是演示片段：无交易日历覆盖证明，不标注为完整月收益。")
       assert np.isclose(monthly.iloc[0]["return_over_observed_rows"], 1.01 * 1.02 * (101.0 / 102.0) - 1.0)
       assert pd.isna(monthly.iloc[1]["return_over_observed_rows"])
       ''')

recipe("P28", "日内 OHLCV 与日线聚合：先定义 bar 边界及交易会话",
       "把单市场日内成交记录转为 5 分钟 bar 或单日 OHLCV。",
       "timestamp 是交易所当地无时区时间（此玩具样例只有同一天）；price、volume 为逐笔数据。",
       "修改 bar_size、origin、offset 和交易会话规则；真实数据先处理时区。",
       "5 分钟 bar 与单日汇总，每行含 open / high / low / close / volume。",
       "[09:30,09:35) 的 bar 在 09:35 才完整可知；日 OHLC 到收盘才可知。夜盘应使用交易所会话标签，不能盲目 normalize 到自然日。",
       r'''
       ticks = pd.DataFrame({"timestamp": pd.to_datetime(["2024-01-02 09:30", "2024-01-02 09:31", "2024-01-02 09:34", "2024-01-02 09:36", "2024-01-02 09:39"]),
                             "price": [100., 102., 101., 103., 102.], "volume": [10., 20., 30., 40., 50.]})
       ticks = ticks.sort_values("timestamp").set_index("timestamp")
       aggregation = {"open": ("price", "first"), "high": ("price", "max"),
                      "low": ("price", "min"), "close": ("price", "last"),
                      "volume": ("volume", lambda s: s.sum(min_count=1))}
       bars = ticks.resample("5min", closed="left", label="right", origin="start_day", offset="9h30min").agg(**aggregation)
       bars = bars.dropna(subset=["open", "close"])
       # 本例仅含同一白天交易会话；真实隔夜市场必须使用外部 session 映射。
       daily = ticks.groupby(ticks.index.normalize()).agg(**aggregation)
       display(bars)
       display(daily)
       assert bars.iloc[0]["open"] == 100.0 and bars.iloc[0]["close"] == 101.0
       assert bars.iloc[0]["volume"] == 60.0 and daily.iloc[0]["volume"] == 150.0
       ''')

recipe("P29", "reindex 补齐期望网格：区分未观测与休市",
       "检查交易日缺行或建立资产×交易日面板，同时保留缺失原因。",
       "观察值 date、price；expected_sessions 来自题目提供或核实后的会话清单。",
       "替换显式会话列表；此处只是已知样例日历，不是可用于任意市场的日历。",
       "完整日期索引、原始价格、row_was_present 标记。",
       "pd.bdate_range 只识别周末，不知道交易所假日；不能用它冒充交易日历。reindex 产生的 NaN 不自动意味着价格不变。",
       r'''
       expected_sessions = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"])
       observed = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05", "2024-01-08"]),
                                "price": [100., 101., np.nan, 103.]}).set_index("date")
       assert observed.index.is_unique
       observed["row_was_present"] = True
       aligned = observed.reindex(expected_sessions)
       aligned.index.name = "date"
       aligned["row_was_present"] = aligned["row_was_present"].eq(True)
       aligned["missing_existing_value"] = aligned["row_was_present"] & aligned["price"].isna()
       display(aligned)
       assert not aligned.loc["2024-01-04", "row_was_present"]
       assert aligned.loc["2024-01-05", "missing_existing_value"]
       ''')

recipe("P30", "时区与夏令时：localize 指定含义，convert 改显示时区",
       "合并跨市场时间戳，或数据含美国夏令时切换时的不存在 / 重复本地时间。",
       "local_clock 是纽约当地无时区钟表时间；并非已经标记 UTC 的字符串。",
       "按元数据设置原始时区；不存在与歧义时间的处理必须有明确证据。",
       "原始钟表时间、带时区纽约时间和 UTC 时间；DST 问题记录标为 NaT 待审查。",
       "对当地时间直接 pd.to_datetime(..., utc=True) 会误当 UTC；tz_localize 不移动钟表值，tz_convert 保持同一瞬间。这里用 NaT 审计，真实流程可选 raise。",
       r'''
       df = pd.DataFrame({"local_clock": ["2024-03-08 09:30", "2024-03-11 09:30", "2024-03-10 02:30", "2024-11-03 01:30"]})
       naive = pd.to_datetime(df["local_clock"], format="%Y-%m-%d %H:%M")
       df["new_york"] = naive.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
       df["utc"] = df["new_york"].dt.tz_convert("UTC")
       df["needs_dst_review"] = df["new_york"].isna()
       display(df)
       assert df["needs_dst_review"].sum() == 2
       assert df.loc[0, "utc"].hour == 14 and df.loc[1, "utc"].hour == 13
       ''')

recipe("P31", "字符串规范化与 category：先清洗身份，再优化内存",
       "资产代码、分类标签存在大小写、空白或低基数重复；需要节省大表内存。",
       "asset 字符串、sector 标签；标识符的大小写是否有意义由数据定义决定。",
       "修改 strip / upper 规则；仅将低基数稳定分类转 category。",
       "清洗后的标识、分类计数、object 与 category 的实际字节对比。",
       "不要把 000001 转整数；高基数 ID 转 category 可能不省内存；category 新增取值前需扩展类别或转回字符串。",
       r'''
       df = pd.DataFrame({"asset": [" a ", "B", " a", None], "sector": ["Tech", "Energy", "Tech", "Tech"]})
       df["asset_clean"] = df["asset"].astype("string").str.strip().str.upper()
       repeated = pd.Series(["Technology", "Energy"] * 1000, name="sector")
       categorical = repeated.astype("category")
       memory = pd.DataFrame({"representation": ["object", "category"],
                              "bytes_deep": [repeated.memory_usage(deep=True), categorical.memory_usage(deep=True)]})
       df["sector"] = df["sector"].astype("category")
       display(df)
       display(df["sector"].value_counts(dropna=False).rename("rows").to_frame())
       display(memory)
       assert df.loc[0, "asset_clean"] == "A" and pd.isna(df.loc[3, "asset_clean"])
       assert memory.loc[1, "bytes_deep"] < memory.loc[0, "bytes_deep"]
       ''')

recipe("P32", "向量化：条件分支、分箱和安全除法",
       "大量行需要计算比率、规则标签或离散区间，避免逐行 apply。",
       "numerator、denominator、score 均为数值，可能为 0 或缺失。",
       "修改有效分母条件与 np.select 条件顺序；第一个满足的条件优先。",
       "ratio、decision、score_band 三个向量化结果列。",
       "np.where 条件为假也可能先计算除法分支；要彻底避免除零，可使用 np.divide 的 where + out。np.select 的缺失默认值要显式设置。",
       r'''
       df = pd.DataFrame({"numerator": [10., 20., 30., np.nan], "denominator": [2., 0., np.nan, 5.],
                          "score": [-2., 0.2, 2., np.nan]})
       numerator = df["numerator"].to_numpy(dtype=float)
       denominator = df["denominator"].to_numpy(dtype=float)
       valid = np.isfinite(numerator) & np.isfinite(denominator) & (denominator != 0)
       df["ratio"] = np.divide(numerator, denominator, out=np.full(len(df), np.nan), where=valid)
       df["decision"] = np.select([df["score"].isna(), df["score"] > 1, df["score"] < -1],
                                   ["missing", "positive", "negative"], default="neutral")
       df["score_band"] = pd.cut(df["score"], [-np.inf, -1, 1, np.inf], labels=["low", "middle", "high"])
       display(df)
       assert df.loc[0, "ratio"] == 5.0 and df["ratio"].notna().sum() == 1
       assert df.loc[3, "decision"] == "missing"
       ''')

recipe("P33", "大 CSV 分块：可合并的统计量与不可盲分块的 rolling",
       "文件太大无法一次读入，需要按块累计组内 sum / count / mean。",
       "CSV 包含 asset、value；本单元使用 StringIO，因此离线即可运行。",
       "将 StringIO(csv_text) 替换为路径并调大 chunksize；只读必要列。",
       "每资产全文件总和、有效样本数和均值，和一次性读取结果一致。",
       "不能平均每块均值；sum / count 可以合并。rolling、diff、去重可能跨块，需要保留边界状态或按完整组分区。",
       r'''
       from io import StringIO
       csv_text = "asset,value\nA,1\nA,2\nB,10\nA,3\nB,\nB,20\n"
       partials = []
       for chunk in pd.read_csv(StringIO(csv_text), chunksize=2, usecols=["asset", "value"]):
           partial = chunk.groupby("asset")["value"].agg(["sum", "count"])
           partials.append(partial)
       totals = pd.concat(partials).groupby(level="asset")[["sum", "count"]].sum()
       totals["mean"] = totals["sum"] / totals["count"].replace(0, np.nan)
       direct = pd.read_csv(StringIO(csv_text)).groupby("asset")["value"].mean()
       display(totals)
       assert np.allclose(totals["mean"], direct.reindex(totals.index))
       assert totals.loc["A", "mean"] == 2.0 and totals.loc["B", "mean"] == 15.0
       ''')

recipe("P34", "横截面去极值与标准化：同一时点、同一已知资产池",
       "每天在当时可知的资产池内截尾分数，再做横截面 z-score。",
       "decision_at、asset、score；所有 score 必须在 decision_at 前已可知且时间对齐。",
       "修改分位阈值、最小横截面样本数和 ddof；本例 5 个资产仅展示代码机制。",
       "每行对应当日的上下界、截尾 score 和横截面 z-score。",
       "不能对整段时间用未来分位数截尾；横截面操作仍可能泄漏：各市场当日收盘时间不同、事后资产池选择都需要处理。",
       r'''
       df = pd.DataFrame({"decision_at": pd.to_datetime(["2024-01-02 17:00"] * 5 + ["2024-01-03 17:00"] * 5),
                          "asset": list("ABCDE") * 2, "score": [1., 2., 3., 4., 100., -50., 2., 3., 4., 5.]})
       assert not df.duplicated(["decision_at", "asset"]).any()
       group = df.groupby("decision_at")["score"]
       min_cross_section = 3
       enough = group.transform("count") >= min_cross_section
       df["n_available"] = group.transform("count")
       df["lower"] = group.transform(lambda s: s.quantile(0.10))
       df["upper"] = group.transform(lambda s: s.quantile(0.90))
       df["score_winsor"] = df["score"].clip(lower=df["lower"], upper=df["upper"]).where(enough)
       clipped_group = df.groupby("decision_at")["score_winsor"]
       center = clipped_group.transform("mean")
       scale = clipped_group.transform(lambda s: s.std(ddof=0)).replace(0, np.nan)
       df["score_z"] = (df["score_winsor"] - center) / scale
       display(df)
       assert np.allclose(df.groupby("decision_at")["score_z"].mean(), 0, atol=1e-12)
       assert np.allclose(df.groupby("decision_at")["score_z"].std(ddof=0), 1)
       ''')

recipe("P35", "时间切分与标签边界：训练标签不能伸进验证期",
       "h 步前瞻标签覆盖未来一段时间，需要在训练 / 验证边界清除重叠标签。",
       "feature_at 是特征可用时点；label_end 是该样本标签完成时点；target 是标签。",
       "修改 valid_start、test_start；本例使用严格小于边界的保守规则。",
       "每条样本标记 train / validation / test / purge_or_unlabeled，并显示每组数量。",
       "仅按 feature_at 切分会让训练末端标签包含验证期信息；若标签还存在发布延迟，应改用 label_available_at 判定。",
       r'''
       df = pd.DataFrame({"feature_at": pd.date_range("2024-01-01", periods=10), "price": np.arange(100., 110.)})
       horizon = 2
       df["label_end"] = df["feature_at"].shift(-horizon)
       df["target"] = df["price"].shift(-horizon) / df["price"] - 1.0
       valid_start = pd.Timestamp("2024-01-05")
       test_start = pd.Timestamp("2024-01-08")
       train = (df["feature_at"] < valid_start) & (df["label_end"] < valid_start)
       valid = (df["feature_at"] >= valid_start) & (df["feature_at"] < test_start) & (df["label_end"] < test_start)
       test = (df["feature_at"] >= test_start) & df["target"].notna()
       df["split"] = np.select([train, valid, test], ["train", "validation", "test"], default="purge_or_unlabeled")
       display(df)
       display(df["split"].value_counts().rename("rows").to_frame())
       assert (df.loc[train, "label_end"] < valid_start).all()
       assert (df.loc[valid, "label_end"] < test_start).all()
       assert train.sum() == 2 and valid.sum() == 1 and test.sum() == 1
       ''')

recipe("P36", "宽表组合计算：先写时间线，再滞后权重",
       "练习收益矩阵与权重矩阵对齐，检查全缺失行、无持仓行与真实收益的区别。",
       "宽价格表 index=date，columns=asset；样例每日收盘价只是用于演示。",
       "修改 score、归一化规则和 execution_lag。这里收盘 t 计算信号，t+1 收盘执行，赚 t+1 到 t+2 的收益，因此收益行滞后 2 行。",
       "目标权重、作用于当行收益区间的持仓权重、简单组合收益。",
       "这不是完整回测：没有成本、滑点、持仓漂移、可交易性或退市处理。shift(1) 是否够取决于价格/信号/执行定义，不能机械复制。",
       r'''
       prices = pd.DataFrame({"A": [100., 101., 103., 102., 104., 105., 103.],
                              "B": [100., 99., 98., 100., 99., 101., 102.],
                              "C": [100., 100., 101., 101., 100., 99., 100.]},
                             index=pd.date_range("2024-01-02", periods=7))
       returns = prices.pct_change(fill_method=None)  # 行 t 代表 t-1 收盘到 t 收盘的收益。
       score = prices.pct_change(periods=2, fill_method=None)
       centered = score.sub(score.mean(axis=1), axis=0)
       gross = centered.abs().sum(axis=1, min_count=len(prices.columns)).replace(0, np.nan)
       target = centered.div(gross, axis=0)  # 横截面净权重 0、绝对权重之和 1。
       execution_lag = 2
       held_for_return = target.shift(execution_lag)
       assert not ((held_for_return.abs() > 0) & returns.isna()).any().any(), "有持仓但缺收益，不能默认填 0"
       # 只有明确零持仓的资产才可将该资产缺失收益视为不影响组合。
       effective_returns = returns.where(held_for_return.ne(0), 0.0)
       portfolio_return = (held_for_return * effective_returns).sum(axis=1, min_count=len(prices.columns))
       report = portfolio_return.rename("toy_portfolio_return").to_frame()
       report["weights_known"] = held_for_return.notna().all(axis=1)
       display(target.add_prefix("target_"))
       display(held_for_return.add_prefix("held_"))
       display(report)
       active = held_for_return.notna().all(axis=1)
       assert np.allclose(held_for_return.loc[active].sum(axis=1), 0.0, atol=1e-12)
       assert np.allclose(held_for_return.loc[active].abs().sum(axis=1), 1.0)
       assert report.iloc[:4]["toy_portfolio_return"].isna().all()
       ''')

recipe("P37", "相关性与滚动相关：计数与有效配对同样重要",
       "比较两条收益序列的同期线性 / 单调关系，或观察历史相关性随时间变化。",
       "date 索引下 A、B 两条已对齐收益，均为小数；有少量缺失。",
       "修改窗口与最小配对数量；若要作当期预测特征，先把两列一起滞后。",
       "相关矩阵、有效配对数量矩阵、基于过去 3 行的滚动相关。",
       "DataFrame.corr 使用成对完整样本，各对相关系数可能用不同样本；同期相关不等于预测能力；不要对趋势价格相关直接解释策略。",
       r'''
       df = pd.DataFrame({"A": [0.01, -0.02, 0.03, 0.01, -0.01, 0.02, 0.00],
                          "B": [0.02, -0.01, 0.01, np.nan, -0.02, 0.01, 0.01]},
                         index=pd.date_range("2024-01-02", periods=7))
       valid = df.notna().astype("int64")
       pair_counts = valid.T.dot(valid)
       correlations = df.corr(method="pearson", min_periods=3)
       past = df.shift(1)
       history = df.copy()
       history["past_3row_corr"] = past["A"].rolling(3, min_periods=3).corr(past["B"])
       display(correlations)
       display(pair_counts)
       display(history)
       assert pair_counts.loc["A", "B"] == 6
       assert history["past_3row_corr"].iloc[:3].isna().all()
       ''')

recipe("P38", "分资产不规则时间窗口：用行 ID 明确恢复原始行序",
       "每个资产有不规则时间戳，需要各自计算过去 3 天均值，并保持原表行序。",
       "asset、date、value；同资产时间戳唯一；原表可以交错排列。",
       "修改 time_window 与 closed；保留 row_id，不依赖 groupby.apply 的跨版本索引行为。",
       "与原表同样行序和行数，新增 past_3d_mean。",
       "赋值错位会得到看似合理却属于别的资产的特征。这里按组循环是为了清晰保留时间索引，不逐行循环。",
       r'''
       df = pd.DataFrame({"asset": ["B", "A", "A", "B", "A", "B"],
                          "date": pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-08", "2024-01-08"]),
                          "value": [10., 1., 2., 20., 3., 30.]})
       df["row_id"] = np.arange(len(df))
       assert not df.duplicated(["asset", "date"]).any()
       parts = []
       for asset, group in df.groupby("asset", sort=False):
           group = group.sort_values("date")
           series = group.set_index("date")["value"]
           feature = series.rolling("3D", closed="left", min_periods=1).mean()
           assert feature.index.equals(pd.DatetimeIndex(group["date"]))
           parts.append(pd.DataFrame({"row_id": group["row_id"].to_numpy(), "past_3d_mean": feature.to_numpy()}))
       features = pd.concat(parts, ignore_index=True)
       result = df.merge(features, on="row_id", how="left", validate="one_to_one").sort_values("row_id")
       display(result)
       assert result["row_id"].tolist() == list(range(len(df)))
       assert result.loc[2, "past_3d_mean"] == 1.0 and result.loc[3, "past_3d_mean"] == 10.0
       assert pd.isna(result.loc[4, "past_3d_mean"]) and pd.isna(result.loc[5, "past_3d_mean"])
       ''')

recipe("P39", "时间切片：用半开区间防止相邻批次重复",
       "按日期范围切分数据，或提取当地交易时段；需要明确边界是否包含。",
       "utc_time 为已知 UTC 的时间戳、value 为测量；本例转换为纽约当地时间。",
       "修改本地时区、start / stop、交易时段；本例时段 [09:30,16:00) 排除 16:00。",
       "完整当地日期切片及该日期内的时段切片。",
       "loc[start:end] 通常包括两端；相邻批次用 >= start 且 < stop 更明确。between_time 不识别假日和午间休市；收盘记录是否应包含要单独定义。",
       r'''
       df = pd.DataFrame({"utc_time": pd.to_datetime(["2024-01-02 14:29", "2024-01-02 14:30", "2024-01-02 20:59", "2024-01-02 21:00", "2024-01-03 14:30"], utc=True),
                          "value": [1., 2., 3., 4., 5.]})
       local = df.set_index("utc_time").tz_convert("America/New_York").sort_index()
       local.index.name = "local_time"
       start = pd.Timestamp("2024-01-02", tz="America/New_York")
       stop = pd.Timestamp("2024-01-03", tz="America/New_York")
       date_slice = local.loc[(local.index >= start) & (local.index < stop)]
       intraday = date_slice.between_time("09:30", "16:00", inclusive="left")
       display(date_slice)
       display(intraday)
       assert len(date_slice) == 4 and intraday["value"].tolist() == [2.0, 3.0]
       ''')

recipe("P40", "给特征模板加检查：未来扰动不应改变过去特征",
       "写完时间序列特征后，自动检查主键、排序与因果方向；防止误用 centered rolling 或未来归一化。",
       "asset、date、price；函数内只使用各资产之前两条价格。",
       "替换 build_features 内的逻辑；修改 cutoff 之后的数据，比较 cutoff 之前的特征。",
       "特征表和未来扰动测试结果；如果未来被用于过去，assert 会失败。",
       "通过此测试只是必要条件，不证明没有任何泄漏；错误的发布时间、幸存者偏差和数据修订仍需从数据含义审查。",
       r'''
       def build_features(frame):
           result = frame.sort_values(["asset", "date"]).reset_index(drop=True).copy()
           assert result[["asset", "date"]].notna().all().all()
           assert not result.duplicated(["asset", "date"]).any()
           result["past_2row_mean"] = result.groupby("asset")["price"].transform(
               lambda s: s.shift(1).rolling(2, min_periods=2).mean())
           return result

       raw = pd.DataFrame({"asset": ["A"] * 6 + ["B"] * 6,
                           "date": list(pd.date_range("2024-01-01", periods=6)) * 2,
                           "price": [100., 101., 102., 103., 104., 105., 50., 51., 52., 53., 54., 55.]})
       cutoff = pd.Timestamp("2024-01-05")
       original = build_features(raw)
       perturbed_raw = raw.copy()
       perturbed_raw.loc[perturbed_raw["date"] >= cutoff, "price"] *= 10.0
       perturbed = build_features(perturbed_raw)
       columns = ["asset", "date", "past_2row_mean"]
       before_original = original.loc[original["date"] < cutoff, columns].reset_index(drop=True)
       before_perturbed = perturbed.loc[perturbed["date"] < cutoff, columns].reset_index(drop=True)
       pd.testing.assert_frame_equal(before_original, before_perturbed)
       display(original)
       print("通过：修改未来价格，没有改变此前特征。")
       assert original.groupby("asset").head(2)["past_2row_mean"].isna().all()
       ''')


intro = r'''
# 01 · pandas 时间序列代码模板

**用途：先按问题定位模板，修改字段与口径，再复制运行。** 这不是按 API 字母顺序排列的手册，而是从未知表格到可靠时间序列特征的 40 个常见场景。

- **语言与版本目标：** Python 3.8 语法；pandas 1.5.3 与 NumPy 1.24 系列。代码避免 `format='mixed'`、`resample('ME')`、新 `groupby.apply` 参数等较新写法。现场先确认实际库版本；FAQ 只给出了 Python 版本。
- **独立可复制：** 先运行一次初始化。每个 Pxx 代码格都自建微型数据，**不依赖前一个 Pxx 代码格产生的变量**；复制到新 notebook 时，只需要初始化和选中的代码格。
- **从样例换成真数据：** 保留复制片段中的排序、主键检查和时间定义；把构造 `DataFrame(...)` 的部分换成你的表。先跑 `head()`，再跑全量数据。
- **输出可见：** 每个模板已保留示例表格和关键检查；`assert` 描述了这个模板依赖的条件。如果对真实数据失败，先查原因，不要删除检查来强行运行。
- **数据来源：** 本文件的所有小表都是人工构造的教学数据，不是真实证券价格，也不用于声称某种策略有效。

> 时间序列模板的第一条规则：**“观察所属时间”“实际可获知时间”“预测起点”“标签终点”“交易执行时间”可能不同。** pandas 只执行操作，不会替你保证这些时点正确。

## 先运行一次：公共初始化
'''

setup = '''
from pathlib import Path
import numpy as np
import pandas as pd
from IPython.display import display

# 支持从仓库根目录或 notebooks/ 启动；不写入任何文件。
ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 140)
pd.set_option("display.max_rows", 16)
print("pandas:", pd.__version__, "| numpy:", np.__version__)
print("运行方式：先执行本格，再执行任意一个 Pxx；各模板之间没有状态依赖。")
'''

groups = [
    ("读取与认识数据", "P01", "P05"),
    ("筛选、索引与清洗", "P06", "P12"),
    ("分组、连接与表结构", "P13", "P21"),
    ("时间窗口、聚合与时区", "P22", "P30"),
    ("性能与研究安全检查", "P31", "P40"),
]

quick = '''
## 按问题查找

| 你遇到的问题 | 模板 |
|---|---|
| 证券代码前导零没了；日期解析出现 NaT | [P02 读 CSV](#p02) · [P03 多格式日期](#p03) |
| 表有多大、缺什么、主键是否重复 | [P01 结构](#p01) · [P05 审计](#p05) · [P11 重复](#p11) |
| 筛选后的赋值不生效；两列相加出现 NaN | [P06 筛选](#p06) · [P07 对齐](#p07) · [P08 安全赋值](#p08) |
| 缺失是未成交、缺报价还是解析失败 | [P09 限龄 ffill](#p09) · [P10 训练填补](#p10) · [P12 非法值](#p12) |
| 每资产统计 vs 每行附一个组统计 | [P13 agg/transform](#p13) · [P15 样本量](#p15) |
| 连接后行数暴涨；想取当时最新已发布数据 | [P17 merge](#p17) · [P18 merge_asof](#p18) |
| 数据是长表，但要画资产相关矩阵 | [P19 pivot](#p19) · [P20 melt](#p20) · [P37 相关性](#p37) |
| 收益跨资产计算了；group rolling 赋回错位 | [P22 分组收益](#p22) · [P25 rolling 对齐](#p25) |
| 最近 5 条和最近 5 天有什么区别 | [P24 行/时间窗口](#p24) · [P38 分资产时间窗口](#p38) |
| 日频转月频、tick 转 bar，什么时候可知 | [P27 月频](#p27) · [P28 OHLCV](#p28) |
| 日期缺行，是休市还是数据漏了 | [P29 交易日网格](#p29) · [P30 时区/DST](#p30) |
| 表太大；逐行 apply 太慢 | [P31 category](#p31) · [P32 向量化](#p32) · [P33 分块](#p33) |
| 横截面标准化、未来标签、时间切分怎么写 | [P14 排名](#p14) · [P23 标签](#p23) · [P34 截尾](#p34) · [P35 切分](#p35) |
| 权重应该 shift 几行；怎么查未来泄漏 | [P36 权重时间线](#p36) · [P40 未来扰动测试](#p40) |

## 完整目录
'''
for group_title, first, last in groups:
    quick += "\n**{}**\n\n".format(group_title)
    for r in recipes:
        if first <= r["id"] <= last:
            quick += "- [{0} · {1}](#{2})\n".format(r["id"], r["title"], r["id"].lower())

cells = [nbf.v4.new_markdown_cell(dedent(intro).strip())]
setup_cell = nbf.v4.new_code_cell(dedent(setup).strip())
setup_cell["metadata"]["tags"] = ["setup"]
cells.append(setup_cell)
cells.append(nbf.v4.new_markdown_cell(quick.strip()))

for r in recipes:
    explanation = '''<a id="{anchor}"></a>
## {code_id} · {title}

**使用场景：** {scenario}

| 复制前确认 | 本模板约定 |
|---|---|
| 输入字段 | {inputs} |
| 需要改的参数 | {change} |
| 输出形状与含义 | {output} |

**最容易踩的坑：** {pitfall}
'''.format(anchor=r["id"].lower(), code_id=r["id"], title=r["title"], scenario=r["scenario"],
           inputs=r["inputs"], change=r["change"], output=r["output"], pitfall=r["pitfall"])
    if r["extra"]:
        explanation += "\n" + r["extra"] + "\n"
    cells.append(nbf.v4.new_markdown_cell(explanation.strip()))
    cell = nbf.v4.new_code_cell(r["code"])
    cell["metadata"]["recipe_id"] = r["id"]
    cell["metadata"]["tags"] = ["recipe:" + r["id"]]
    cells.append(cell)

cells.append(nbf.v4.new_markdown_cell('''## 快速自测：不用 AI 的 30 分钟练习

1. 用 P02/P05 读一份表，写下“一行是什么、主键是什么、单位是什么、时间何时可知”。
2. 用 P11/P17 找重复和未匹配键，解释处理规则，而不是只展示代码。
3. 用 P22/P25 为每个资产产生一列历史收益与历史窗口特征，抽一个资产手算前三行。
4. 用 P23/P35 产生未来标签与时间切分，指出被清除的边界样本。
5. 用 P40 扰动未来数据；确认过去特征不变。

**继续到 02：** 从“会写操作”转为“知道什么问题适合什么清洗方法和图表”。

## 现场排错顺序

- `KeyError`：先看 `df.columns.tolist()` 和 `df.index.names`，检查空格、大小写、字段是否已移入索引。
- 日期比较失败：看双方 dtype、是否同为 timezone-aware、是否同一时区。
- `cannot reindex` / 对齐异常：检查 `index.is_unique`、业务主键重复和 rolling 结果的索引层。
- 连接后行数增加：检查右表键唯一性与 `validate`，不要先删多余行。
- 结果都是 NaN：检查窗口 `min_periods`、前序缺失、分组样本数、权重与收益标签是否对齐。
- 所有运算都对但结果异常漂亮：检查未来标签是否误入特征、预处理是否看过测试期，以及多次尝试后是否只保留了最好结果。

## 官方文档入口

这些链接用于理解 API；若现场版本不同，请切换到相应版本文档。

- [pandas 1.5.3：10 minutes to pandas](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/10min.html)
- [pandas 1.5.3：索引与选择](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/indexing.html)
- [pandas 1.5.3：缺失数据](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/missing_data.html)
- [pandas 1.5.3：合并与连接](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/merging.html)
- [pandas 1.5.3：merge_asof](https://pandas.pydata.org/pandas-docs/version/1.5.3/reference/api/pandas.merge_asof.html)
- [pandas 1.5.3：时间序列与时区](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/timeseries.html)
- [pandas 1.5.3：窗口函数](https://pandas.pydata.org/pandas-docs/version/1.5.3/user_guide/window.html)
'''))

notebook = nbf.v4.new_notebook(cells=cells)
notebook["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.8.20"},
    "title": "pandas 时间序列代码模板",
    "recipe_count": len(recipes),
    "target_environment": {"python": "3.8-compatible syntax", "pandas": "1.5.3", "numpy": "1.24.4"},
}
out = ROOT / "notebooks" / "01_pandas_time_series_templates.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, out)
print("Wrote {} ({} cells, {} recipes)".format(out, len(cells), len(recipes)))
