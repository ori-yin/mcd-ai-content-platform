# -*- coding: utf-8 -*-
r"""
tools/print_feature_importance.py — L1 LightGBM 特征重要性月报

目的：每月跑一次，看 L1 模型"认为哪些特征影响 CTR"，靠这个判断下阶段要不要
扩特征 / 砍无用维度 / 调权重。

口径：
- importance_type = "gain"（默认，对 CTR 这种回归任务最直观）
- 与上一次快照对比，输出名次变化（±2 名以内视为稳定，不打标记）
- 输出：打印 Top N + 写两份留档（JSON 快照 + .txt 报告）

运行：
    python tools/print_feature_importance.py
    python tools/print_feature_importance.py --top 15
    python tools/print_feature_importance.py --threshold 3        # 名次变化阈值
    python tools/print_feature_importance.py --importance-type split  # split 而非 gain

产物：
- data/feature_importance_history/importance_YYYY-MM-DD_HHMMSS.json
- data/reports/feature_importance_YYYY-MM-DD.txt
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Windows console 默许 GBK，强制 UTF-8 防乱码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "data" / "lgbm_model_v1.pkl"
META_PATH = ROOT / "data" / "lgbm_feature_meta.json"
HISTORY_DIR = ROOT / "data" / "feature_importance_history"
REPORTS_DIR = ROOT / "data" / "reports"

DEFAULT_TOP = 10
DEFAULT_THRESHOLD = 2  # 名次变化超过 ±N 算"涨/跌"
DEFAULT_IMPORTANCE_TYPE = "gain"


# ── 特征名 humanizer ─────────────────────────────────────────────
def humanize_feature(col: str) -> str:
    """把内部列名翻成人话（按 prefix 拆解）。"""
    # 一级前缀
    if col.startswith("channel_"):
        # LightGBM 把空格存成下划线，反向还原 "APP_Push" → "APP Push"
        return f"渠道: {col[len('channel_'):].replace('_', ' ')}"
    if col.startswith("coupon_"):
        return f"用券: {col[len('coupon_'):] or '(空)'}"
    if col.startswith("workday_type_"):
        return f"工作日类型: {col[len('workday_type_'):] or '(空)'}"
    if col.startswith("ch_x_wd_"):
        # 形如 ch_x_wd_APP_Push_工作日 → 渠道×工作日 APP Push × 工作日
        tail = col[len("ch_x_wd_"):]
        # tail 末段是工作日，前段是渠道（中间用 _ 分隔）
        if "_" in tail:
            ch, wd = tail.rsplit("_", 1)
            return f"渠道×工作日: {ch.replace('_', ' ')} × {wd or '(空)'}"
        return f"渠道×工作日: {tail.replace('_', ' ')}"
    # 数值特征
    mapping = {
        "title_len": "标题长度",
        "content_len": "正文长度",
        "has_emoji": "含 Emoji",
        "has_digit": "含数字",
        "has_question": "含问号",
        "eff_word_count": "高效词命中数",
        "plan_type_te": "计划类型 (target encoding)",
    }
    return mapping.get(col, col)


# ── 加载模型 + 元信息 ─────────────────────────────────────────────
def load_model_and_meta(model_path: Path = MODEL_PATH,
                        meta_path: Path = META_PATH) -> tuple:
    """加载 LightGBM 模型 + 特征元信息。"""
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model, meta


# ── 计算 importance ─────────────────────────────────────────────
def compute_importance(model, feature_cols: list, importance_type: str) -> pd.DataFrame:
    """算每个特征的重要性百分比，返回 DataFrame（rank, feature, importance_pct）。"""
    raw = model.feature_importance(importance_type=importance_type)
    total = float(raw.sum()) or 1.0
    df = pd.DataFrame({
        "feature": feature_cols,
        "importance_raw": raw,
    })
    df["importance_pct"] = df["importance_raw"] / total * 100
    df = df.sort_values("importance_pct", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


# ── 与历史快照对比 ─────────────────────────────────────────────
def find_latest_snapshot(history_dir: Path = HISTORY_DIR) -> Path | None:
    """找最近一次的历史快照 JSON（按文件名排序）。"""
    if not history_dir.exists():
        return None
    files = sorted(history_dir.glob("importance_*.json"))
    return files[-1] if files else None


def diff_with_history(current: pd.DataFrame, snapshot_path: Path,
                      threshold: int) -> pd.DataFrame:
    """把当前 importance 与历史快照对比，加 rank_change / delta_importance 列。

    名次变化 = old_rank - new_rank（正数=上升，负数=下降）。
    """
    with open(snapshot_path, encoding="utf-8") as f:
        prev = json.load(f)
    prev_rank = {item["feature"]: item["rank"] for item in prev["items"]}
    prev_imp = {item["feature"]: item["importance_pct"] for item in prev["items"]}

    current["prev_rank"] = current["feature"].map(prev_rank)
    current["rank_change"] = current["prev_rank"] - current["rank"]  # 正=升
    current["prev_importance_pct"] = current["feature"].map(prev_imp)
    current["delta_importance"] = current["importance_pct"] - current["prev_importance_pct"].fillna(0)

    def mark_change(row):
        if pd.isna(row["prev_rank"]):
            return "新"
        rc = row["rank_change"]
        if rc >= threshold:
            return f"↑{int(rc)}"
        if rc <= -threshold:
            return f"↓{abs(int(rc))}"
        return ""

    current["change"] = current.apply(mark_change, axis=1)
    return current


# ── 落档 ────────────────────────────────────────────────────────
def save_snapshot(df: pd.DataFrame, history_dir: Path = HISTORY_DIR) -> Path:
    """保存当前快照为 JSON，供下次对比。"""
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = history_dir / f"importance_{ts}.json"
    payload = {
        "snapshot_at": datetime.now().isoformat(timespec="seconds"),
        "items": [
            {
                "rank": int(row["rank"]),
                "feature": str(row["feature"]),
                "importance_pct": round(float(row["importance_pct"]), 4),
            }
            for _, row in df.iterrows()
        ],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out


def render_report(df: pd.DataFrame, snapshot_path: Path | None,
                  importance_type: str, threshold: int,
                  reports_dir: Path = REPORTS_DIR) -> Path:
    """生成 .txt 报告（人话版），保留历史留档。"""
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d")
    out = reports_dir / f"feature_importance_{ts}.txt"

    lines = []
    lines.append(f"L1 特征重要性月报 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"importance_type = {importance_type}（gain 推荐，split 可选）")
    lines.append(f"对比基线: {snapshot_path.name if snapshot_path else '(首次跑，无历史快照)'}")
    lines.append(f"名次变化阈值: ±{threshold}")
    lines.append("")
    lines.append(f"{'排名':<4} {'特征':<32} {'重要性%':>8}  {'变化':<6}")
    lines.append("-" * 60)
    for _, row in df.iterrows():
        feat_name = humanize_feature(str(row["feature"]))
        pct = row["importance_pct"]
        change = row.get("change", "")
        lines.append(f"{int(row['rank']):<4} {feat_name:<32} {pct:>7.2f}%  {change}")
    lines.append("-" * 60)
    lines.append("")
    # 涨/跌 Top 3
    diff_rows = df[df["change"].astype(str).str.startswith(("↑", "↓", "新"))].copy()
    if not diff_rows.empty:
        lines.append("变化显著的特征（名次变化 ≥ ±%d 或新特征）：" % threshold)
        for _, row in diff_rows.iterrows():
            feat_name = humanize_feature(str(row["feature"]))
            lines.append(f"  {row['change']:<4} {feat_name:<32} ({row['importance_pct']:.2f}%)")
    else:
        lines.append(f"无特征名次变化 ≥ ±{threshold}（模型稳定）。")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ── 主流程 ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="L1 LightGBM 特征重要性月报")
    parser.add_argument("--model", default=str(MODEL_PATH))
    parser.add_argument("--meta", default=str(META_PATH))
    parser.add_argument("--top", type=int, default=DEFAULT_TOP,
                        help=f"打印 Top N（默认 {DEFAULT_TOP}）")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                        help=f"名次变化阈值（默认 ±{DEFAULT_THRESHOLD}）")
    parser.add_argument("--importance-type", default=DEFAULT_IMPORTANCE_TYPE,
                        choices=["gain", "split"],
                        help=f"importance 类型（默认 {DEFAULT_IMPORTANCE_TYPE}）")
    args = parser.parse_args()

    model, meta = load_model_and_meta(Path(args.model), Path(args.meta))
    feature_cols = meta.get("feature_columns", [])
    if not feature_cols:
        raise SystemExit(f"meta 文件 {args.meta} 没有 feature_columns 字段")

    # 计算当前 importance
    df = compute_importance(model, feature_cols, args.importance_type)

    # 与历史快照对比
    snapshot = find_latest_snapshot()
    if snapshot:
        df = diff_with_history(df, snapshot, args.threshold)
        print(f"[diff] 对比基线: {snapshot.name}")
    else:
        df["prev_rank"] = None
        df["rank_change"] = None
        df["prev_importance_pct"] = None
        df["delta_importance"] = None
        df["change"] = ""
        print("[diff] 首次跑，无历史快照。")

    # 打印 Top N
    top_df = df.head(args.top)
    print(f"\n=== L1 特征重要性 Top {args.top}（type={args.importance_type}）===")
    print(f"{'排名':<4} {'特征':<32} {'重要性%':>8}  变化")
    print("-" * 60)
    for _, row in top_df.iterrows():
        feat_name = humanize_feature(str(row["feature"]))
        print(f"{int(row['rank']):<4} {feat_name:<32} {row['importance_pct']:>7.2f}%  {row.get('change', '')}")
    print("-" * 60)

    # 落档
    snap_path = save_snapshot(df)
    report_path = render_report(top_df, snapshot, args.importance_type, args.threshold)
    print(f"\n[save] 快照 → {snap_path}")
    print(f"[save] 报告 → {report_path}")


if __name__ == "__main__":
    main()
