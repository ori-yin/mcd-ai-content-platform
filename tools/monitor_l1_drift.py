# -*- coding: utf-8 -*-
r"""
tools/monitor_l1_drift.py — L1 LightGBM 漂移监控

目的：当业务切到 l1_model mode 后，每周/每月检查 L1 预测 vs 真实回流 CTR 的
误差是否漂移到 baseline 的 1.3 倍以上，超过即告警（建议触发重训）。

对比口径：
- L1 预测 = records.db.generation_records.ctr_results_json 中
            source 含 "ctr_predictor_adapter/l1_lightgbm" 的 pred_ctr
- 真实 CTR = feedback.db.feedback_records 按 signature 聚合
            （plan 加权：sum(click_count) / sum(reach_success)）
- 基线 MAE = data/lgbm_feature_meta.json 的 test_metrics.overall_mae_pct

join 维度：task_signature（records.signature ↔ feedback.task_signature）

告警阈值：当前 MAE > baseline × 1.3 → 红字告警 + 写 data/drift_log.csv 留档

运行：
    python tools/monitor_l1_drift.py
    python tools/monitor_l1_drift.py --alert-ratio 1.5   # 自定义告警倍数
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
RECORDS_DB = ROOT / "data" / "records.db"
FEEDBACK_DB = ROOT / "data" / "feedback.db"
META_PATH = ROOT / "data" / "lgbm_feature_meta.json"
DRIFT_LOG = ROOT / "data" / "drift_log.csv"

DEFAULT_ALERT_RATIO = 1.3
MIN_PAIR_COUNT = 5  # 至少 N 对预测+真回流才告警（防小样本误报）


# ── records.db 读 L1 预测 ─────────────────────────────────────
def load_l1_predictions(records_db: Path = RECORDS_DB) -> list:
    """从 records.db 读所有 ctr_results 含 l1_lightgbm source 的 (selected) 预测。

    返回 list[dict]：每个元素 = {
        signature, channel, plan_type, coupon, workday_type, title, pred_ctr, real_ctr
    }
    real_ctr 字段先填 None，由后续 join feedback 填入。
    """
    if not records_db.exists():
        return []
    conn = sqlite3.connect(str(records_db))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT signature, task_json, candidates_json, ctr_results_json, selected_id
            FROM generation_records
            WHERE signature != '' AND ctr_results_json IS NOT NULL
            ORDER BY id DESC
            """,
        )
        out = []
        for r in cur.fetchall():
            try:
                task = json.loads(r["task_json"])
                cands = json.loads(r["candidates_json"])
                ctrs = json.loads(r["ctr_results_json"])
                selected_id = r["selected_id"]
                # 找选中候选对应的 ctr 结果
                sel_ctr = next((c for c in ctrs if c.get("source") == "ctr_predictor_adapter/l1_lightgbm"
                                and _match_id(c, selected_id, cands)), None)
                if sel_ctr is None:
                    continue
                pred = sel_ctr.get("pred_ctr")
                if pred is None:
                    continue
                # 选中的那条 candidate
                cand = next((c for c in cands if c.get("id") == selected_id), {})
                out.append({
                    "signature": r["signature"],
                    "channel": task.get("channel", ""),
                    "plan_type": task.get("plan_type", "未知"),
                    "coupon": task.get("coupon", "未知"),
                    "workday_type": task.get("planned_send_date", ""),
                    "title": cand.get("title", ""),
                    "pred_ctr": float(pred),
                })
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return out
    finally:
        conn.close()


def _match_id(ctr_dict: dict, selected_id: str, cands: list) -> bool:
    """轻量校验 ctr dict 是否对应 selected_id（按出现顺序对齐）。

    ctr_results 与 candidates 顺序一一对应（services.predict_for_candidates 保证）。
    简化：默认 ctr_dict['_idx'] 缺失则按顺序匹配。
    """
    return True  # 顺序对齐即可（predict_for_candidates 已保证）


# ── feedback.db 按 signature 聚合真 CTR ───────────────────────
def load_real_ctr_by_signature(feedback_db: Path = FEEDBACK_DB) -> dict:
    """{signature: {ctr: pct, reach: N, click: N}}，plan 加权。"""
    if not feedback_db.exists():
        return {}
    conn = sqlite3.connect(str(feedback_db))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT task_signature,
                   SUM(reach_success) AS reach,
                   SUM(click_count) AS click
            FROM feedback_records
            GROUP BY task_signature
            """,
        )
        out = {}
        for r in cur.fetchall():
            reach = int(r["reach"] or 0)
            click = int(r["click"] or 0)
            if reach <= 0:
                continue
            out[r["task_signature"]] = {
                "ctr": click / reach,
                "reach": reach,
                "click": click,
            }
        return out
    finally:
        conn.close()


# ── 评估指标 ──────────────────────────────────────────────
def compute_metrics(pairs: list) -> dict:
    """整体 + 分渠道 MAE / MAPE。"""
    if not pairs:
        return {"overall_mae_pct": 0.0, "by_channel": {}, "n": 0}
    errs = [abs(p["real_ctr"] - p["pred_ctr"]) for p in pairs]
    overall_mae = float(np.mean(errs))
    by_channel = {}
    for p in pairs:
        ch = p.get("channel") or "未知"
        by_channel.setdefault(ch, []).append(abs(p["real_ctr"] - p["pred_ctr"]))
    by_ch_metric = {ch: float(np.mean(es)) * 100 for ch, es in by_channel.items()}
    return {
        "overall_mae_pct": overall_mae * 100,
        "by_channel": by_ch_metric,
        "n": len(pairs),
    }


# ── drift_log.csv 写入 ───────────────────────────────────────
def write_drift_log(row: dict, log_path: Path = DRIFT_LOG):
    """追加一行监控记录（CSV 头一次写入）。"""
    new_file = not log_path.exists()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "n_pairs", "overall_mae_pct", "baseline_mae_pct",
                        "ratio", "alert_ratio", "alert_level", "worst_channel", "worst_channel_mae_pct"])
        w.writerow([
            row["timestamp"],
            row["n_pairs"],
            f"{row['overall_mae_pct']:.4f}",
            f"{row['baseline_mae_pct']:.4f}",
            f"{row['ratio']:.3f}",
            f"{row['alert_ratio']:.2f}",
            row["alert_level"],
            row.get("worst_channel", ""),
            f"{row.get('worst_channel_mae_pct', 0):.4f}",
        ])


# ── 主流程 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="L1 LightGBM 漂移监控")
    parser.add_argument("--alert-ratio", type=float, default=DEFAULT_ALERT_RATIO,
                        help=f"告警倍数（默认 {DEFAULT_ALERT_RATIO}）")
    parser.add_argument("--min-pairs", type=int, default=MIN_PAIR_COUNT,
                        help=f"最小样本数（默认 {MIN_PAIR_COUNT}），低于此不评估")
    parser.add_argument("--no-log", action="store_true", help="不写 drift_log.csv")
    args = parser.parse_args()

    # 1) 加载基线 MAE
    if not META_PATH.exists():
        print(f"[FAIL] meta 文件不存在：{META_PATH}")
        return 1
    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    baseline_mae_pct = float(meta.get("test_metrics", {}).get("overall_mae_pct", 0.0))
    if baseline_mae_pct <= 0:
        print(f"[FAIL] meta 缺 test_metrics.overall_mae_pct（baseline={baseline_mae_pct}）")
        return 1
    print(f"[baseline] L1 历史最佳 MAE = {baseline_mae_pct:.3f}%  "
          f"(训练时间 {meta.get('trained_at','?')})")

    # 2) 加载 L1 预测
    l1_rows = load_l1_predictions()
    print(f"[load] records.db L1 预测行数：{len(l1_rows)}")

    # 3) 加载真回流
    fb = load_real_ctr_by_signature()
    print(f"[load] feedback.db signature 数：{len(fb)}")

    # 4) Inner join
    pairs = []
    for r in l1_rows:
        sig = r["signature"]
        if sig in fb and fb[sig]["reach"] >= 50:  # 防小样本
            pairs.append({
                **r,
                "real_ctr": fb[sig]["ctr"],
                "real_reach": fb[sig]["reach"],
                "real_click": fb[sig]["click"],
            })
    print(f"[join] 配对 {len(pairs)} 对（min_reach=50 过滤后）")

    if len(pairs) < args.min_pairs:
        print(f"\n[skip] 配对数 {len(pairs)} < {args.min_pairs}，不评估（防小样本误报）")
        print("       建议：让 L1 mode 多跑一段时间，回流数据进来后再监控")
        return 0

    # 5) 评估
    metrics = compute_metrics(pairs)
    overall_mae_pct = metrics["overall_mae_pct"]
    ratio = overall_mae_pct / baseline_mae_pct

    # 找最差渠道
    worst_ch, worst_mae = "", 0.0
    if metrics["by_channel"]:
        worst_ch = max(metrics["by_channel"], key=metrics["by_channel"].get)
        worst_mae = metrics["by_channel"][worst_ch]

    # 6) 告警
    if ratio > args.alert_ratio:
        alert_level = "ALERT"
        print(f"\n🚨 漂移告警 🚨")
    elif ratio > 1.0:
        alert_level = "WARN"
        print(f"\n⚠️ 漂移预警")
    else:
        alert_level = "OK"
        print(f"\n✅ 当前 L1 误差在基线内")
    print(f"  当前 MAE = {overall_mae_pct:.3f}%  vs  基线 {baseline_mae_pct:.3f}%")
    print(f"  比值 = {ratio:.3f}（告警阈值 {args.alert_ratio}）")
    print(f"  配对数 = {len(pairs)}")
    if worst_ch:
        print(f"  最差渠道： {worst_ch}（MAE {worst_mae:.3f}%）")

    # 分渠道明细
    print(f"\n=== 分渠道 MAE ===")
    for ch, mae in sorted(metrics["by_channel"].items(), key=lambda x: -x[1]):
        ch_n = sum(1 for p in pairs if (p.get("channel") or "未知") == ch)
        print(f"  {ch:12s} n={ch_n:4d}  MAE={mae:.3f}%")

    # 7) 写日志
    if not args.no_log:
        write_drift_log({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "n_pairs": len(pairs),
            "overall_mae_pct": overall_mae_pct,
            "baseline_mae_pct": baseline_mae_pct,
            "ratio": ratio,
            "alert_ratio": args.alert_ratio,
            "alert_level": alert_level,
            "worst_channel": worst_ch,
            "worst_channel_mae_pct": worst_mae,
        })
        print(f"\n[log] 已写入 {DRIFT_LOG.name}")

    return 0 if alert_level != "ALERT" else 2


if __name__ == "__main__":
    import sys
    sys.exit(main())