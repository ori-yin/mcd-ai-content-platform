# -*- coding: utf-8 -*-
r"""
tools/evaluate_lgbm.py — L1 LightGBM vs L0 baseline 同口径对比

目的：回答"该不该把 L0 baseline 替换成 L1 LightGBM"。

对比逻辑：
1) 对测试集每个 Plan：
   - L0 预测 = ctr_baseline.json 查表（按 channel/coupon/workday 回退兜底）
   - L1 预测 = lgbm_model_v1.pkl 预测
2) 分渠道 MAE / MAPE 对比
3) 分桶误差（小/中/大 Plan）对比
4) 输出：L1 vs L0 胜出渠道数、整体误差比

如果 L1 整体 MAE < L0 且多数渠道 MAE < L0 → 建议切 L1
否则 → 保留 L0 baseline，L1 不带来收益
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "data" / "ctr_baseline.json"
MODEL_PATH = ROOT / "data" / "lgbm_model_v1.pkl"
META_PATH = ROOT / "data" / "lgbm_feature_meta.json"
DATA_PATH = ROOT / "data" / "cnn_backup_cleaned.xlsx"
EFFECTIVE_WORDS_PATH = ROOT / "data" / "effective_words.json"

# 与 train_lgbm.py 保持一致
MIN_REACH = 50
CTR_UPPER_PCT = 95
RANDOM_SEED = 42
TEST_SIZE = 0.20


# ── L0 baseline 查表 ────────────────────────────────────────
def lookup_l0_baseline(baseline: dict, channel: str, coupon: str = "",
                       workday: str = "") -> Optional[float]:
    """按 (channel, coupon) → (channel, workday) → (channel) 顺序回退查 L0 baseline。

    返回 CTR float 或 None（没查到）。
    注：baseline.json 的 data 直接是 float，不是 dict。
    """
    dims = baseline.get("dimensions", {})
    ch_dim = dims.get("渠道", {}).get("data", {})

    # 1) 渠道 × 用券
    if coupon:
        cp_dim = dims.get("渠道_x_是否用券", {}).get("data", {})
        # baseline 里 key 格式是 "{channel}_{coupon}" 或 "{channel}|{coupon}"
        for sep in ["_", "|"]:
            key = f"{channel}{sep}{coupon}"
            if key in cp_dim:
                v = cp_dim[key]
                return float(v.get("ctr", 0) if isinstance(v, dict) else v)
    # 2) 渠道 × 工作日
    if workday:
        wd_dim = dims.get("渠道_x_工作日类型", {}).get("data", {})
        for sep in ["_", "|"]:
            key = f"{channel}{sep}{workday}"
            if key in wd_dim:
                v = wd_dim[key]
                return float(v.get("ctr", 0) if isinstance(v, dict) else v)
    # 3) 渠道
    if channel in ch_dim:
        v = ch_dim[channel]
        return float(v.get("ctr", 0) if isinstance(v, dict) else v)
    return None


# ── 数据 + 模型加载 ────────────────────────────────────────
def load_test_data():
    """重跑 train_lgbm 的清洗/聚合/切分，拿到同一份测试集。"""
    df = pd.read_excel(DATA_PATH, sheet_name=0)
    df["_ctr_raw"] = df["点击人次"] / df["触达成功"].replace(0, np.nan)
    reach_floor = df[df["触达成功"] >= MIN_REACH]
    ctr_p95 = reach_floor["_ctr_raw"].quantile(CTR_UPPER_PCT / 100)
    df = df[df["触达成功"] >= MIN_REACH].copy()
    df["_ctr"] = df["_ctr_raw"].clip(upper=ctr_p95)

    # Plan 聚合
    plan_meta = df.groupby("Plan ID").agg(
        channel=("渠道", "first"),
        plan_type=("计划类型", "first"),
        sample_title=("标题", "first"),
        sample_content=("内容", "first"),
        sent_date=("发送日期", "first"),
    ).reset_index()
    plan_reach_click = df.groupby("Plan ID").agg(
        reach=("触达成功", "sum"),
        click=("点击人次", "sum"),
    ).reset_index()
    plan_reach_click["plan_ctr"] = plan_reach_click["click"] / plan_reach_click["reach"].replace(0, np.nan)
    plan_df = plan_meta.merge(plan_reach_click, on="Plan ID", how="inner").dropna(subset=["plan_ctr"]).reset_index(drop=True)

    # 80/20 切分（必须用同一种子）
    from sklearn.model_selection import train_test_split
    train_idx, test_idx = train_test_split(
        plan_df.index, test_size=TEST_SIZE, random_state=RANDOM_SEED,
    )
    return plan_df.loc[test_idx].reset_index(drop=True)


# ── 评估指标 ──────────────────────────────────────────────
def per_channel_metrics(test_df: pd.DataFrame, true_col: str, pred_col: str) -> pd.DataFrame:
    test_df = test_df.copy()
    test_df["_err"] = (test_df[true_col] - test_df[pred_col]).abs()
    test_df["_mape"] = test_df["_err"] / test_df[true_col].clip(lower=1e-6)
    by_ch = test_df.groupby("channel").agg(
        n_plans=("channel", "count"),
        mae=("_err", "mean"),
        mape=("_mape", "mean"),
        true_mean=(true_col, "mean"),
        pred_mean=(pred_col, "mean"),
    )
    by_ch["mae_pct"] = by_ch["mae"] * 100
    by_ch["mape_pct"] = by_ch["mape"] * 100
    by_ch["true_pct"] = by_ch["true_mean"] * 100
    by_ch["pred_pct"] = by_ch["pred_mean"] * 100
    return by_ch


def per_bucket_metrics(test_df: pd.DataFrame, true_col: str, pred_col: str) -> pd.DataFrame:
    test_df = test_df.copy()
    test_df["_err"] = (test_df[true_col] - test_df[pred_col]).abs()
    test_df["_mape"] = test_df["_err"] / test_df[true_col].clip(lower=1e-6)
    test_df["reach_bucket"] = pd.cut(
        test_df["reach"],
        bins=[0, 1000, 10000, float("inf")],
        labels=["小(<1k)", "中(1k-10k)", "大(>10k)"],
    )
    by_bk = test_df.groupby("reach_bucket", observed=True).agg(
        n_plans=("channel", "count"),
        mae=("_err", "mean"),
        mape=("_mape", "mean"),
    )
    by_bk["mae_pct"] = by_bk["mae"] * 100
    by_bk["mape_pct"] = by_bk["mape"] * 100
    return by_bk


# ── 主流程 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="L1 vs L0 baseline 同口径对比")
    parser.add_argument("--model", default=str(MODEL_PATH), help="L1 模型路径")
    parser.add_argument("--meta", default=str(META_PATH), help="L1 特征元信息")
    parser.add_argument("--baseline", default=str(BASELINE_PATH), help="L0 baseline JSON")
    parser.add_argument("--data", default=str(DATA_PATH), help="源数据 Excel")
    parser.add_argument("--exclude-channels", nargs="*", default=[],
                        help="剔除的渠道列表（训练集剔除；评估时也从测试集剔除）")
    args = parser.parse_args()

    # 1) 加载 L0 / L1
    with open(args.baseline, encoding="utf-8") as f:
        baseline = json.load(f)
    with open(args.model, "rb") as f:
        model = pickle.load(f)
    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)

    # 2) 加载测试集
    test_df = load_test_data()
    if args.exclude_channels:
        before = len(test_df)
        test_df = test_df[~test_df["channel"].isin(args.exclude_channels)].reset_index(drop=True)
        print(f"[exclude] 测试集剔除 {args.exclude_channels}: {before} → {len(test_df)} Plan")
    print(f"[test] {len(test_df)} 个 Plan 用于对比")

    # 3) L0 baseline 预测
    print("\n[l0] 用 baseline 查表...")
    test_df["l0_pred_ctr"] = test_df.apply(
        lambda r: lookup_l0_baseline(
            baseline, str(r["channel"]), "", "",
        ) or 0.0,
        axis=1,
    )

    # 4) L1 LightGBM 预测
    print("[l1] 用 LightGBM 预测...")
    # 重建特征矩阵（与 train_lgbm.py 保持一致）
    feat = pd.DataFrame()
    title = test_df["sample_title"].fillna("").astype(str)
    content = test_df["sample_content"].fillna("").astype(str)
    feat["title_len"] = title.str.len()
    feat["content_len"] = content.str.len()
    # has_emoji 用 Python re（PyArrow 后端不支持 \U 转义）
    import re as _re
    _emoji_pat = _re.compile(
        "[\\U0001F300-\\U0001FAFF\\U00002600-\\U000027BF\\U0001F000-\\U0001F0FF"
        "\\U00002B00-\\U00002BFF\\U00002190-\\U000021FF\\U0000231A-\\U0000231B]"
    )
    feat["has_emoji"] = title.apply(lambda s: 1 if _emoji_pat.search(str(s or "")) else 0)
    feat["has_digit"] = title.str.contains(r"\d", regex=True, na=False).astype(int)
    feat["has_question"] = title.str.contains(r"[?？]", regex=True, na=False).astype(int)
    # Step 2: 高效词命中数（jieba 切词 + 交集）
    if EFFECTIVE_WORDS_PATH.exists():
        with open(EFFECTIVE_WORDS_PATH, encoding="utf-8") as f:
            eff_words = set(json.load(f).get("top_words", []))
        import jieba as _jieba
        feat["eff_word_count"] = title.apply(
            lambda s: len(set(_jieba.lcut(str(s))) & eff_words)
        )
        print(f"[l1] 高效词命中数已加（词典 {len(eff_words)} 词）")
    else:
        feat["eff_word_count"] = 0
    # 工作日类型（直接 weekday 逻辑，不依赖 import 避免路径问题）
    test_df["workday_type"] = test_df["sent_date"].apply(
        lambda d: "非工作日" if (pd.notna(d) and pd.to_datetime(d).weekday() >= 5) else "工作日"
    )
    test_df["coupon"] = "未知"  # baseline 数据无此字段
    for col in ["channel", "coupon", "workday_type"]:
        dummies = pd.get_dummies(test_df[col].fillna("未知"), prefix=col, dtype=int)
        dummies.columns = [c.replace(" ", "_") for c in dummies.columns]
        feat = pd.concat([feat, dummies], axis=1)
    # Step 4: 渠道 × 工作日 交叉
    test_df["_ch_x_wd"] = test_df["channel"].astype(str) + "_" + test_df["workday_type"].astype(str)
    ch_x_wd = pd.get_dummies(test_df["_ch_x_wd"].fillna("未知"), prefix="ch_x_wd", dtype=int)
    ch_x_wd.columns = [c.replace(" ", "_") for c in ch_x_wd.columns]
    feat = pd.concat([feat, ch_x_wd], axis=1)

    # Target encoding
    te_map = meta.get("plan_type_te_map", {})
    global_mean = meta.get("plan_type_global_mean", 0.01)
    feat["plan_type_te"] = test_df["plan_type"].map(te_map).fillna(global_mean)

    # 对齐训练时的特征列（缺失列补 0）
    for c in meta["feature_columns"]:
        if c not in feat.columns:
            feat[c] = 0
    feat = feat[meta["feature_columns"]]

    # 预测（logit 反变换）
    y_pred_logit = model.predict(feat)
    test_df["l1_pred_ctr"] = 1.0 / (1.0 + np.exp(-y_pred_logit))

    # 5) 整体对比
    y_true = test_df["plan_ctr"].values
    l0_pred = test_df["l0_pred_ctr"].values
    l1_pred = test_df["l1_pred_ctr"].values

    l0_mae = mean_absolute_error(y_true, l0_pred)
    l1_mae = mean_absolute_error(y_true, l1_pred)
    l0_rmse = np.sqrt(mean_squared_error(y_true, l0_pred))
    l1_rmse = np.sqrt(mean_squared_error(y_true, l1_pred))
    l0_r2 = r2_score(y_true, l0_pred)
    l1_r2 = r2_score(y_true, l1_pred)

    print(f"\n=== 整体对比 ===")
    print(f"  L0 baseline  MAE={l0_mae*100:.3f}%  RMSE={l0_rmse*100:.3f}%  R²={l0_r2:.4f}")
    print(f"  L1 LightGBM  MAE={l1_mae*100:.3f}%  RMSE={l1_rmse*100:.3f}%  R²={l1_r2:.4f}")
    if l1_mae < l0_mae:
        improvement = (l0_mae - l1_mae) / l0_mae * 100
        print(f"  → L1 胜出！MAE 降 {improvement:.1f}%（{(l0_mae - l1_mae)*100:.3f}pp）")
    else:
        worse = (l1_mae - l0_mae) / l0_mae * 100
        print(f"  → L0 胜出！L1 MAE 高 {worse:.1f}%（{(l1_mae - l0_mae)*100:.3f}pp），不建议切换")

    # 6) 分渠道对比
    print(f"\n=== 分渠道对比 ===")
    l0_by_ch = per_channel_metrics(test_df, "plan_ctr", "l0_pred_ctr")
    l1_by_ch = per_channel_metrics(test_df, "plan_ctr", "l1_pred_ctr")
    cmp = pd.DataFrame({
        "n_plans": l0_by_ch["n_plans"],
        "L0_MAE%": l0_by_ch["mae_pct"],
        "L1_MAE%": l1_by_ch["mae_pct"],
    })
    cmp["L1_胜出"] = cmp["L1_MAE%"] < cmp["L0_MAE%"]
    cmp["L1降pp"] = (cmp["L0_MAE%"] - cmp["L1_MAE%"]).round(3)
    print(cmp.round(3))

    # 7) 分桶对比
    print(f"\n=== 分桶对比（按 Plan 总触达）===")
    l0_by_bk = per_bucket_metrics(test_df, "plan_ctr", "l0_pred_ctr")
    l1_by_bk = per_bucket_metrics(test_df, "plan_ctr", "l1_pred_ctr")
    cmp_bk = pd.DataFrame({
        "n_plans": l0_by_bk["n_plans"],
        "L0_MAE%": l0_by_bk["mae_pct"],
        "L1_MAE%": l1_by_bk["mae_pct"],
    })
    cmp_bk["L1_胜出"] = cmp_bk["L1_MAE%"] < cmp_bk["L0_MAE%"]
    cmp_bk["L1降pp"] = (cmp_bk["L0_MAE%"] - cmp_bk["L1_MAE%"]).round(3)
    print(cmp_bk.round(3))

    # 8) 决策建议
    n_channels_l1_win = int(cmp["L1_胜出"].sum())
    n_channels = len(cmp)
    print(f"\n=== 决策建议 ===")
    if l1_mae < l0_mae and n_channels_l1_win >= n_channels / 2:
        print(f"  L1 在 {n_channels_l1_win}/{n_channels} 个渠道胜出，建议替换 L0 baseline")
    elif l1_mae < l0_mae:
        print(f"  L1 整体胜出但仅 {n_channels_l1_win}/{n_channels} 个渠道胜出，**分渠道考虑**：")
        print(f"    胜出渠道直接切 L1；其他保留 L0 + 分渠道重训小模型")
    else:
        print(f"  L0 整体胜出，建议不切 L1。原因可能是：")
        print(f"    - 样本量对 LightGBM 偏小（3624 Plan）")
        print(f"    - 4 渠道 CTR 差 8 倍，统一模型难捕捉")
        print(f"    - 特征工程不足（缺正文 jieba 分词 TF-IDF）")


if __name__ == "__main__":
    main()
