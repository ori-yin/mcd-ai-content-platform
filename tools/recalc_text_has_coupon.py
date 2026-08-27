# -*- coding: utf-8 -*-
r"""
tools/recalc_text_has_coupon.py — 一次性脚本：补 baseline "渠道 × 文案含券词" 维度

Phase 15 · 2026-08-27 用户拍板：
- Phase 12 #11 加了 text_has_coupon 字段，但 baseline JSON 没建对应维度 key
- baseline_lookup.py:97-101 永远走不到 → text_has_coupon 选了等于空跑
- 用本脚本从 data/cnn_backup_cleaned.xlsx（48307 行）按指数衰减 λ=0.01 半衰期 69.3 天
  聚合"渠道 × 文案含券词"维度，写入 baseline JSON（v3.2 → v3.3 预留）

为什么走一次性脚本而不是 calibrate_baseline.py：
- feedback.db 是空的（0 行 feedback_records）
- calibrate_baseline.py 当前只覆盖 2 个维度（渠道 / 用券），没 text_has_coupon 聚合分支
- 等后续扩展 calibrate_baseline.py + feedback_records 表 schema 加字段后才用得上

指数衰减算法（与 baseline JSON v3.0+ metadata 对齐）：
- lambda = 0.01，半衰期 69.3 天
- weight(days_ago) = exp(-0.01 * days_ago)
- 2026-08-27（今天）：w = 1.0
- 2026-06-19（69 天前）：w = 0.5
- 2025-08-27（一年前）：w = 0.026
- 2024-10-15（数据最早）：w = 0.025（接近 0）
- weighted_click / weighted_reach = 加权 CTR

用法：
    python tools/recalc_text_has_coupon.py                # 直接写 baseline JSON（备份到 .bak.json）
    python tools/recalc_text_has_coupon.py --dry-run      # 只看聚合结果不写
    python tools/recalc_text_has_coupon.py --ref-date 2026-08-27  # 调整基准日期（默认今天）
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# 项目根
ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT / "data" / "cnn_backup_cleaned.xlsx"
BASELINE_PATH = ROOT / "data" / "ctr_baseline.json"
BACKUP_PATH = ROOT / "data" / "ctr_baseline.bak.json"

# ── 校准参数（与 baseline JSON metadata 对齐）─────────────────────
LAMBDA = 0.01                 # 指数衰减系数
HALF_LIFE_DAYS = 69.3         # 半衰期（与 calibration_half_life_days 一致）
MIN_REACH = 1000              # 单维度总触达 < 该值跳过（v3.1 Q5 兜底）
DEFINITION_VERSION = "v3.1"   # 口径标注


def exp_decay_weight(days_ago: float, lam: float = LAMBDA) -> float:
    """指数衰减权重：weight = exp(-lam * days_ago)。"""
    if days_ago < 0:
        return 1.0  # 未来日期（理论上不会出现）按 1.0 兜底
    return math.exp(-lam * days_ago)


def infer_text_has_coupon(df: pd.DataFrame) -> pd.Series:
    """对每行推断文案是否含券词，返回 Series 与 df 同 index。

    用 Phase 12 #11 的 classify_coupon_in_text(title, body) 工具函数。
    """
    # 避免循环依赖：tools/ → ../core/text_classifier.py
    sys.path.insert(0, str(ROOT))
    from core.text_classifier import classify_coupon_in_text

    def _row_infer(row):
        title = str(row.get("标题", "") or "")
        body = str(row.get("内容", "") or "")
        v = classify_coupon_in_text(title, body)
        return v if v in ("是", "否") else "否"  # 默认"否"兜底

    return df.apply(_row_infer, axis=1)


def aggregate_by_channel_text(df: pd.DataFrame, ref_date: pd.Timestamp) -> pd.DataFrame:
    """按 渠道 × text_has_coupon 分组，指数衰减加权聚合 CTR。

    输入 df 需含列：渠道 / 触达成功 / 点击人次 / 发送日期 + text_has_coupon
    返回 DataFrame：index=[(ch, thc)]，列 reach/click/ctr/weight_sum/n_plans
    """
    df = df.copy()
    df["days_ago"] = (ref_date - pd.to_datetime(df["发送日期"])).dt.days.clip(lower=0)
    df["weight"] = df["days_ago"].apply(exp_decay_weight)

    # 加权
    df["w_reach"] = df["触达成功"] * df["weight"]
    df["w_click"] = df["点击人次"] * df["weight"]

    grp = df.groupby(["渠道", "text_has_coupon"], as_index=False).agg(
        n_plans=("Plan ID", "nunique"),  # 用 Plan ID 近似 plan 数（去重 plan）
        w_reach=("w_reach", "sum"),
        w_click=("w_click", "sum"),
        reach_total=("触达成功", "sum"),
        click_total=("点击人次", "sum"),
    )
    grp["ctr"] = grp["w_click"] / grp["w_reach"].replace(0, pd.NA)
    return grp


def build_new_dimension(grp: pd.DataFrame, min_reach: int = MIN_REACH) -> tuple[dict, list]:
    """构造 baseline 新维度 dict + changes 列表。

    返回：(dimension_dict, change_log_lines)
    - dimension_dict: 写入 baseline["dimensions"]["渠道_x_文案含券词"]
    - change_log_lines: 给 _calibration_log 用
    """
    data: dict = {}
    description = (
        "渠道 × 标题正文是否含券词（Phase 15 · 2026-08-27 新增维度；用 classify_coupon_in_text "
        "推断每行 text_has_coupon；指数衰减加权 λ=0.01 半衰期 69.3 天；min_reach="
        f"{min_reach} 兜底）"
    )
    dim = {"description": description, "data": data}
    changes = []

    for _, row in grp.iterrows():
        ch = row["渠道"]
        thc = row["text_has_coupon"]
        reach_total = int(row["reach_total"])
        w_reach = float(row["w_reach"])
        w_click = float(row["w_click"])
        ctr = float(row["ctr"]) if pd.notna(row["ctr"]) else None
        n_plans = int(row["n_plans"])

        key = f"{ch}_{thc}"
        if reach_total < min_reach:
            changes.append(f"[渠道×文案含券词/{key}] 触达 {reach_total}<{min_reach} 跳过")
            continue
        if ctr is None or w_reach <= 0:
            changes.append(f"[渠道×文案含券词/{key}] 数据不足跳过（w_reach={w_reach:.0f}）")
            continue
        data[key] = round(ctr, 6)
        changes.append(
            f"[渠道×文案含券词/{key}] n_plans={n_plans} reach={reach_total} "
            f"加权CTR={ctr*100:.4f}%（已落 baseline v3.2）"
        )
    return dim, changes


def main():
    parser = argparse.ArgumentParser(
        description="补 baseline '渠道 × 文案含券词' 维度（Phase 15 一次性脚本）"
    )
    parser.add_argument("--dry-run", action="store_true", help="只聚合不写文件")
    parser.add_argument(
        "--ref-date", default=datetime.now().strftime("%Y-%m-%d"),
        help=f"指数衰减基准日期（默认今天；格式 YYYY-MM-DD）",
    )
    parser.add_argument("--min-reach", type=int, default=MIN_REACH)
    parser.add_argument("--excel", default=str(EXCEL_PATH))
    parser.add_argument("--baseline", default=str(BASELINE_PATH))
    args = parser.parse_args()

    excel_path = Path(args.excel)
    baseline_path = Path(args.baseline)

    if not excel_path.exists():
        sys.exit(f"[FAIL] 清洗后 Excel 不存在：{excel_path}")
    if not baseline_path.exists():
        sys.exit(f"[FAIL] baseline JSON 不存在：{baseline_path}")

    ref_date = pd.Timestamp(args.ref_date)
    print(f"[INFO] 指数衰减基准日期：{ref_date.date()}（λ={LAMBDA} 半衰期 {HALF_LIFE_DAYS} 天）")

    # 1) 读 Excel
    df = pd.read_excel(excel_path)
    print(f"[INFO] 读入 {len(df)} 行（{excel_path.name}）")
    print(f"      渠道分布：{dict(df['渠道'].value_counts())}")

    # 2) 推断 text_has_coupon
    df["text_has_coupon"] = infer_text_has_coupon(df)
    print(f"[INFO] text_has_coupon 推断分布：{dict(df['text_has_coupon'].value_counts())}")

    # 3) 按渠道 × text_has_coupon 聚合
    grp = aggregate_by_channel_text(df, ref_date)
    print(f"[INFO] 聚合 {len(grp)} 组（渠道 × text_has_coupon）")
    print()
    print(grp.to_string(index=False))
    print()

    # 4) 构造新维度
    new_dim, changes = build_new_dimension(grp, args.min_reach)
    print(f"[INFO] 写入 baseline['dimensions']['渠道_x_文案含券词']，{len(new_dim['data'])} keys")
    for line in changes:
        print(f"  {line}")

    if args.dry_run:
        print()
        print("[DRY-RUN] 不写文件，退出")
        return

    # 5) 备份 + 写 baseline JSON
    if BACKUP_PATH.exists():
        print(f"[INFO] 备份已存在（{BACKUP_PATH.name}）；本次覆盖前先备份到 .bak2.json")
        shutil.copy2(baseline_path, ROOT / "data" / "ctr_baseline.bak2.json")

    shutil.copy2(baseline_path, BACKUP_PATH)
    print(f"[OK] 备份 → {BACKUP_PATH.name}")

    with baseline_path.open("r", encoding="utf-8") as f:
        b = json.load(f)

    old_version = b.get("version", "v3.0")
    # 版本号 +1：v3.1.1 → v3.2
    parts = old_version.lstrip("v").split(".")
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
        new_version = f"v{major}.{minor + 1}" if patch == 0 else f"v{major}.{minor}.{patch + 1}"
    except Exception:
        new_version = "v3.2"

    b.setdefault("dimensions", {})["渠道_x_文案含券词"] = new_dim
    b["version"] = new_version
    b["last_updated"] = ref_date.strftime("%Y-%m-%d")
    b["last_refreshed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    b["last_refreshed_by"] = "tools/recalc_text_has_coupon.py"
    b["_calibration_log"] = changes
    b["_definition_version"] = DEFINITION_VERSION
    b["_definition_ref"] = "docs/ctr-kpi-definition-proposal-v0.2.md"

    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=2)
    print(f"[OK] baseline 已写 → {baseline_path}（version {old_version} → {new_version}）")

    # 6) 校验 baseline_lookup 能命中
    print()
    print("[VERIFY] 抽样校验 baseline_lookup 命中：")
    sys.path.insert(0, str(ROOT))
    from adapters.ctr_predictor_adapter.baseline_lookup import get_baseline_ctr
    for ch in df["渠道"].unique():
        for thc in ("是", "否"):
            v = get_baseline_ctr(ch, coupon=None, workday=None, plan_type=None,
                                 text_has_coupon=thc)
            print(f"  {ch} × text_has_coupon={thc} → {v*100 if v else 'None':.4f}%")


if __name__ == "__main__":
    main()