# -*- coding: utf-8 -*-
r"""
tools/train_lgbm.py — L1 LightGBM CTR 预测模型训练（PoC）

输入：data/cnn_backup_cleaned.xlsx（48307 行 CNN 历史投放数据）
输出：data/lgbm_model_v1.pkl（模型）+ data/lgbm_feature_meta.json（特征元信息）

口径（用户 2026-08-28 拍板）：
- 极端值：触达<50 丢 + CTR>P95 截断
- Plan 颗粒度：按 Plan ID 聚合（3624 个 Plan，每个 Plan 1 行）
- 切分：80/20 随机（Plan 聚合后天然防泄漏）
- 模型：单一模型看 4 渠道（带"渠道"特征）
- 目标函数：logit(plan_ctr) = log(p/(1-p))
- 特征：渠道/用券/工作日 one-hot + 标题长度/含emoji/含数字 + 计划类型 target encoding
- 评估：分渠道 MAE / MAPE + 分桶误差（小/中/大 Plan）

约束：
- 训练脚本只读源数据 + 写模型文件，不动 ctr_baseline.json（L0 保留）
- 不接 LLM，不接 services，纯训练+评估
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "cnn_backup_cleaned.xlsx"
MODEL_PATH = ROOT / "data" / "lgbm_model_v1.pkl"
META_PATH = ROOT / "data" / "lgbm_feature_meta.json"
EFFECTIVE_WORDS_PATH = ROOT / "data" / "effective_words.json"


# ── 训练参数（用户拍板口径）─────────────────────────────────
MIN_REACH = 50            # 触达<50 丢（防小样本 CTR 不稳）
CTR_UPPER_PCT = 95        # CTR>P95 截断（防极端值带偏模型）
RANDOM_SEED = 42
TEST_SIZE = 0.20
LGB_PARAMS = {
    "objective": "regression",
    "metric": "mae",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 6,
    "min_data_in_leaf": 20,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbose": -1,
    "seed": RANDOM_SEED,
}
NUM_BOOST_ROUND = 500
EARLY_STOPPING = 30


# ── 工具函数 ────────────────────────────────────────────────
def _load_effective_words(path: Path = EFFECTIVE_WORDS_PATH) -> set:
    """加载历史高效词集合（来自 services.text_analyzer.word_frequency，差值>0.5）。"""
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return set(doc.get("top_words", []))


def _count_effective_words(title: str, words: set) -> int:
    """标题里命中高效词的数量（jieba 切词后求交集，比子串匹配更准）。"""
    if not title or not words:
        return 0
    try:
        import jieba
        toks = set(jieba.lcut(str(title)))
        return len(toks & words)
    except Exception:
        # 退化：子串匹配
        s = str(title)
        return sum(1 for w in words if w in s)


def _has_emoji(text: str) -> bool:
    """标题/正文是否含 emoji（复用 services/text_analyzer 的 emoji regex）。"""
    if not text:
        return False
    return bool(re.search(
        r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
        r"\U00002B00-\U00002BFF\U00002190-\U000021FF\U0000231A-\U0000231B]",
        str(text),
    ))


def _has_digit(text: str) -> bool:
    return bool(re.search(r"\d", str(text or "")))


def _has_question(text: str) -> bool:
    return "？" in str(text or "") or "?" in str(text or "")


def _workday_type(date_str) -> str:
    """从 sent_date 推工作日类型（复用 core/data_window.classify_date_type）。"""
    try:
        from core.data_window import classify_date_type
        return classify_date_type(pd.to_datetime(date_str).date())
    except Exception:
        return ""


def _safe_logit(p: float) -> float:
    """logit 变换；CTR=0 或 CTR=1 时夹到 [1e-6, 1-1e-6] 避免 ±inf。"""
    p = max(min(p, 1 - 1e-6), 1e-6)
    return float(np.log(p / (1 - p)))


def _safe_sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


# ── 数据加载 + 清洗 ────────────────────────────────────────
def load_and_clean(path: Path) -> pd.DataFrame:
    """读取 + 清洗：触达<50 丢 + CTR>P95 截断。"""
    print(f"[load] 读取 {path.name}")
    df = pd.read_excel(path, sheet_name=0)
    print(f"[load] 原始 {len(df)} 行")

    # 计算原始 CTR
    df["_ctr_raw"] = df["点击人次"] / df["触达成功"].replace(0, np.nan)

    # 计算 P95 截断阈值（在触达>=50 的样本上）
    reach_floor = df[df["触达成功"] >= MIN_REACH].copy()
    ctr_p95 = reach_floor["_ctr_raw"].quantile(CTR_UPPER_PCT / 100)
    print(f"[clean] 触达<{MIN_REACH} 丢: {(df['触达成功'] < MIN_REACH).sum()} 行")
    print(f"[clean] CTR>P{CTR_UPPER_PCT}({ctr_p95*100:.2f}%) 截断: {(reach_floor['_ctr_raw'] > ctr_p95).sum()} 行")

    # 清洗
    df = df[df["触达成功"] >= MIN_REACH].copy()
    df["_ctr"] = df["_ctr_raw"].clip(upper=ctr_p95)

    print(f"[clean] 清洗后剩 {len(df)} 行 ({(len(df)/len(reach_floor))*100:.1f}%)")
    return df


# ── Plan 聚合 ─────────────────────────────────────────────
def aggregate_by_plan(df: pd.DataFrame) -> pd.DataFrame:
    """按 Plan ID 聚合：plan_ctr = sum(click) / sum(reach)（plan 加权）。"""
    print(f"[plan-agg] 按 Plan ID 聚合...")
    # Plan 级特征：取该 Plan 第一次出现的 channel / 计划类型 / 工作日 / owner
    plan_meta = df.groupby("Plan ID").agg(
        channel=("渠道", "first"),
        plan_type=("计划类型", "first"),
        owner=("预算owner", "first"),
        sample_title=("标题", "first"),       # 用于特征工程
        sample_content=("内容", "first"),     # 用于特征工程
        sent_date=("发送日期", "first"),
    ).reset_index()

    # Plan 加权 CTR
    plan_reach_click = df.groupby("Plan ID").agg(
        reach=("触达成功", "sum"),
        click=("点击人次", "sum"),
    ).reset_index()
    plan_reach_click["plan_ctr"] = plan_reach_click["click"] / plan_reach_click["reach"].replace(0, np.nan)

    plan_df = plan_meta.merge(plan_reach_click, on="Plan ID", how="inner")
    plan_df = plan_df.dropna(subset=["plan_ctr"]).reset_index(drop=True)
    print(f"[plan-agg] 聚合后 {len(plan_df)} 个 Plan")
    return plan_df


# ── 特征工程 ─────────────────────────────────────────────
def build_features(plan_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, dict]:
    """构造特征矩阵 X、目标 y、特征元信息 meta。

    特征：
    - 数值：title_len / has_emoji / has_digit / has_question / content_len
    - 类别 one-hot：channel / coupon / workday_type
    - 类别 target encoding：plan_type
    """
    print("[feature] 构造特征...")
    feat = pd.DataFrame()
    feat["plan_id"] = plan_df["Plan ID"]

    # 数值特征
    title = plan_df["sample_title"].fillna("").astype(str)
    content = plan_df["sample_content"].fillna("").astype(str)
    feat["title_len"] = title.str.len()
    feat["content_len"] = content.str.len()
    feat["has_emoji"] = title.apply(_has_emoji).astype(int)
    feat["has_digit"] = title.apply(_has_digit).astype(int)
    feat["has_question"] = title.apply(_has_question).astype(int)

    # Step 2: 高效词命中数（jieba 切词 + 交集）
    eff_words = _load_effective_words()
    if eff_words:
        feat["eff_word_count"] = title.apply(lambda s: _count_effective_words(s, eff_words))
        print(f"[feature] 高效词命中数已加（词典 {len(eff_words)} 词）")
    else:
        feat["eff_word_count"] = 0
        print("[feature] 未找到 effective_words.json，跳过高效词特征")

    # 类别 one-hot
    plan_df["workday_type"] = plan_df["sent_date"].apply(_workday_type)
    plan_df["coupon"] = plan_df["是否用券"].fillna("未知") if "是否用券" in plan_df.columns else "未知"
    for col in ["channel", "coupon", "workday_type"]:
        dummies = pd.get_dummies(plan_df[col].fillna("未知"), prefix=col, dtype=int)
        # LightGBM 内部会把空格改下划线，统一替换避免训练/评估列名不一致
        dummies.columns = [c.replace(" ", "_") for c in dummies.columns]
        feat = pd.concat([feat, dummies], axis=1)

    # Step 4: 渠道 × 工作日 交叉特征
    plan_df["_ch_x_wd"] = plan_df["channel"].astype(str) + "_" + plan_df["workday_type"].astype(str)
    ch_x_wd = pd.get_dummies(plan_df["_ch_x_wd"].fillna("未知"), prefix="ch_x_wd", dtype=int)
    ch_x_wd.columns = [c.replace(" ", "_") for c in ch_x_wd.columns]
    feat = pd.concat([feat, ch_x_wd], axis=1)
    print(f"[feature] 渠道×工作日 交叉特征已加（{ch_x_wd.shape[1]} 维）")

    # 目标
    y = plan_df["plan_ctr"].apply(_safe_logit)

    # 计划类型 target encoding（在 80% 训练集上算 mean，避免泄漏）
    plan_type_te_map = {}  # 占位，下面 train_test_split 后再算

    # 元信息
    meta = {
        "feature_columns": [c for c in feat.columns if c != "plan_id"],
        "ctr_p95": float(plan_df["plan_ctr"].quantile(CTR_UPPER_PCT / 100)),
        "min_reach": MIN_REACH,
        "n_plans": len(plan_df),
        "target_transform": "logit",
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }
    return feat, y, meta


def add_target_encoding(X_train: pd.DataFrame, X_test: pd.DataFrame,
                         plan_df_train: pd.DataFrame, plan_df_test: pd.DataFrame,
                         meta: dict) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """计划类型 target encoding（仅用训练集均值，测试集用同一映射）。

    返回更新后的 X_train / X_test / meta（含 plan_type_te_map）。
    """
    train_te_map = plan_df_train.groupby("plan_type")["plan_ctr"].mean()
    global_mean = plan_df_train["plan_ctr"].mean()
    train_te_map = train_te_map.fillna(global_mean).to_dict()

    X_train = X_train.copy()
    X_test = X_test.copy()
    X_train["plan_type_te"] = plan_df_train["plan_type"].map(train_te_map).fillna(global_mean)
    X_test["plan_type_te"] = plan_df_test["plan_type"].map(train_te_map).fillna(global_mean)

    meta["plan_type_te_map"] = {k: float(v) for k, v in train_te_map.items()}
    meta["plan_type_global_mean"] = float(global_mean)
    meta["feature_columns"] = meta["feature_columns"] + ["plan_type_te"]
    return X_train, X_test, meta


# ── 训练 ──────────────────────────────────────────────────
def train(X_train: pd.DataFrame, y_train: pd.Series,
          X_val: pd.DataFrame, y_val: pd.Series,
          meta: dict, sample_weight=None) -> lgb.Booster:
    """LightGBM 训练 + 早停。

    sample_weight: Step 3 时间衰减权重；None 则等权。
    """
    feat_cols = meta["feature_columns"]
    print(f"[train] 训练集 {len(X_train)} 行 / 验证集 {len(X_val)} 行 / 特征 {len(feat_cols)} 维")

    train_set = lgb.Dataset(X_train[feat_cols], label=y_train, weight=sample_weight)
    val_set = lgb.Dataset(X_val[feat_cols], label=y_val, reference=train_set)

    model = lgb.train(
        params=LGB_PARAMS,
        train_set=train_set,
        num_boost_round=NUM_BOOST_ROUND,
        valid_sets=[train_set, val_set],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(EARLY_STOPPING), lgb.log_evaluation(0)],
    )
    print(f"[train] 最佳轮次: {model.best_iteration}, 验证 MAE: {model.best_score['val']['l1']:.4f}")
    meta["best_iteration"] = int(model.best_iteration)
    meta["best_val_mae"] = float(model.best_score["val"]["l1"])
    meta["time_decay_half_life_days"] = 180 if sample_weight is not None else None
    return model


# ── 主流程 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="L1 LightGBM 训练（PoC）")
    parser.add_argument("--data", default=str(DATA_PATH), help="训练数据 Excel")
    parser.add_argument("--model-out", default=str(MODEL_PATH), help="模型输出路径")
    parser.add_argument("--meta-out", default=str(META_PATH), help="特征元信息输出路径")
    parser.add_argument("--exclude-channels", nargs="*", default=[],
                        help="剔除的渠道列表（精确匹配渠道名）")
    args = parser.parse_args()

    data_path = Path(args.data)
    model_out = Path(args.model_out)
    meta_out = Path(args.meta_out)

    # 1) 加载 + 清洗
    df = load_and_clean(data_path)

    # 2) 剔除指定渠道（Step 1）
    if args.exclude_channels:
        before = len(df)
        df = df[~df["渠道"].isin(args.exclude_channels)].copy()
        print(f"[exclude] 剔除渠道 {args.exclude_channels}: {before} → {len(df)} 行")

    # 3) Plan 聚合
    plan_df = aggregate_by_plan(df)

    # 3) 特征工程
    feat_df, y, meta = build_features(plan_df)

    # 4) 80/20 切分
    feat_train, feat_test, y_train, y_test, idx_train, idx_test = train_test_split(
        feat_df, y, plan_df.index, test_size=TEST_SIZE, random_state=RANDOM_SEED,
    )
    plan_df_train = plan_df.loc[idx_train].reset_index(drop=True)
    plan_df_test = plan_df.loc[idx_test].reset_index(drop=True)
    print(f"[split] 训练 {len(feat_train)} / 测试 {len(feat_test)}")

    # 5) Target encoding（仅用训练集均值）
    feat_train, feat_test, meta = add_target_encoding(
        feat_train, feat_test, plan_df_train, plan_df_test, meta,
    )

    # 6) 训练
    # Step 3: 历史时间衰减权重（最近样本权重更高，让模型跟上季节/营销节奏）
    sample_weight = None
    if "time_decay" in meta.get("feature_flags", []) or True:  # 默认开
        sent_train = plan_df_train["sent_date"]
        sent_train = pd.to_datetime(sent_train, errors="coerce")
        max_date = sent_train.max()
        days_back = (max_date - sent_train).dt.days.fillna(365)
        # 半衰期 180 天：weight = 0.5^(days_back / 180)
        half_life = 180
        sample_weight = (0.5 ** (days_back / half_life)).values
        print(f"[train] 时间衰减权重已启用（half_life={half_life} 天，max_date={max_date.date()}）")

    model = train(feat_train, y_train, feat_test, y_test, meta, sample_weight=sample_weight)

    # 7) 测试集预测 + 反变换
    feat_cols = meta["feature_columns"]
    y_pred_logit = model.predict(feat_test[feat_cols])
    y_pred = pd.Series(y_pred_logit).apply(_safe_sigmoid).values
    y_true = y_test.apply(_safe_sigmoid).values

    # 8) 整体评估
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"\n[test] 整体 MAE={mae*100:.3f}% RMSE={rmse*100:.3f}% R²={r2:.4f}")

    # 9) 分渠道评估
    print("\n[test] 分渠道 MAE / MAPE:")
    test_plan_ids = feat_test["plan_id"].values
    test_plans = plan_df_test.set_index("Plan ID").loc[test_plan_ids]
    test_result = pd.DataFrame({
        "channel": test_plans["channel"].values,
        "reach": test_plans["reach"].values,
        "true_ctr": y_true,
        "pred_ctr": y_pred,
    })
    test_result["abs_err"] = (test_result["true_ctr"] - test_result["pred_ctr"]).abs()
    test_result["mape"] = test_result["abs_err"] / test_result["true_ctr"].clip(lower=1e-6)

    by_channel = test_result.groupby("channel").agg(
        n_plans=("channel", "count"),
        mae=("abs_err", "mean"),
        mape=("mape", "mean"),
        true_ctr_mean=("true_ctr", "mean"),
        pred_ctr_mean=("pred_ctr", "mean"),
    )
    by_channel["mae_pct"] = by_channel["mae"] * 100
    by_channel["true_ctr_pct"] = by_channel["true_ctr_mean"] * 100
    by_channel["pred_ctr_pct"] = by_channel["pred_ctr_mean"] * 100
    by_channel["mape_pct"] = by_channel["mape"] * 100
    print(by_channel[["n_plans", "mae_pct", "mape_pct", "true_ctr_pct", "pred_ctr_pct"]].round(3))

    # 10) 分桶误差（小/中/大 Plan 按 reach 桶）
    test_result["reach_bucket"] = pd.cut(
        test_result["reach"],
        bins=[0, 1000, 10000, float("inf")],
        labels=["小(<1k)", "中(1k-10k)", "大(>10k)"],
    )
    print("\n[test] 分桶误差（按 Plan 总触达）:")
    by_bucket = test_result.groupby("reach_bucket", observed=True).agg(
        n_plans=("channel", "count"),
        mae=("abs_err", "mean"),
        mape=("mape", "mean"),
    )
    by_bucket["mae_pct"] = by_bucket["mae"] * 100
    by_bucket["mape_pct"] = by_bucket["mape"] * 100
    print(by_bucket[["n_plans", "mae_pct", "mape_pct"]].round(3))

    # 11) 写模型 + 元信息
    model_out.parent.mkdir(parents=True, exist_ok=True)
    with open(model_out, "wb") as f:
        pickle.dump(model, f)
    print(f"\n[save] 模型 → {model_out}")

    meta["test_metrics"] = {
        "overall_mae_pct": float(mae * 100),
        "overall_rmse_pct": float(rmse * 100),
        "overall_r2": float(r2),
        "by_channel": by_channel.to_dict(orient="index"),
        "by_reach_bucket": by_bucket.to_dict(orient="index"),
    }
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[save] 元信息 → {meta_out}")

    print("\n[done] L1 PoC 训练完成。运行 evaluate_lgbm.py 看 L1 vs L0 对比。")


if __name__ == "__main__":
    main()
