# -*- coding: utf-8 -*-
r"""
tools/calibrate_baseline.py — CTR baseline 校准工具（PRD §回流闭环）

docs/feedback-ctr.md §3 baseline 校准机制：
- 口径：plan 加权 CTR = sum(click) / sum(reach)
- 冷启动 vs 热更新：
  - n_plans < 5 → 用旧 baseline 不动（样本不足）
  - 5 ≤ n_plans < 20 → 指数滑动 α=0.3（新数据 30% 权重）
  - n_plans ≥ 20 → 全量覆盖 α=1.0
- 输入：data/feedback.db（回流数据）+ data/ctr_baseline.json（旧版）
- 输出：data/ctr_baseline_v3.x.json（版本号 + 1，旧版备份为 .bak）

CLI 用法：
    python tools/calibrate_baseline.py                # 校准（写文件）
    python tools/calibrate_baseline.py --dry-run      # 看 diff 不写
    python tools/calibrate_baseline.py --min-reach 1000  # 触达过滤阈值
    python tools/calibrate_baseline.py --definition v3.1  # 校准口径版本标注

约束：
- 只覆盖"渠道"和"渠道_x_是否用券"两个核心维度（避免 schema 破坏）
- 其它维度保持 v3.0 不动；扩展维度在 Phase 6 单独做
- --definition 默认 v3.1（口径详 docs/ctr-kpi-definition-proposal-v0.2.md）
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "data" / "ctr_baseline.json"
BACKUP_PATH = ROOT / "data" / "ctr_baseline.bak.json"


# ── 校准参数 ────────────────────────────────────────────────────
MIN_REACH_DEFAULT = 1000     # 单维度总触达 < 该值跳过（v3.1 Q5 兜底阈值）
MIN_PLANS_DEFAULT = 5        # n_plans < 该值用旧 baseline
ALPHA_LOW = 0.3              # 5 ≤ n_plans < 20 时滑动系数
ALPHA_HIGH = 1.0             # n_plans ≥ 20 时
DEFINITION_DEFAULT = "v3.1"  # 校准口径版本（详 docs/ctr-kpi-definition-proposal-v0.2.md）


# ── 回流数据聚合 ────────────────────────────────────────────────
def aggregate_feedback(db_path) -> Tuple[Dict[Tuple[str, str], dict], Dict[str, dict]]:
    """从 feedback.db 聚合：
    1) (channel, coupon) → {reach, click, n_plans}
    2) channel → {reach, click, n_plans}

    每个 channel 的 n_plans = 该 channel 下独立 signature 数（近似 plan 数）。
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # 按 (channel, coupon) 聚合
        by_cp: dict = {}
        rows = conn.execute("""
            SELECT channel, COALESCE(coupon, '未知') AS coupon,
                   task_signature,
                   SUM(reach_success) AS reach,
                   SUM(click_count) AS click
            FROM feedback_records
            GROUP BY channel, coupon, task_signature
        """).fetchall()
        # 第一遍：按 (ch, coupon) 累积
        for r in rows:
            key = (r["channel"], r["coupon"])
            by_cp.setdefault(key, {"reach": 0, "click": 0, "sigs": set()})
            by_cp[key]["reach"] += int(r["reach"] or 0)
            by_cp[key]["click"] += int(r["click"] or 0)
            by_cp[key]["sigs"].add(r["task_signature"])

        # 转 n_plans + ctr
        by_cp_out: dict = {}
        for (ch, cp), v in by_cp.items():
            n_plans = len(v["sigs"])
            ctr = v["click"] / v["reach"] if v["reach"] > 0 else 0.0
            by_cp_out[(ch, cp)] = {
                "reach": v["reach"], "click": v["click"],
                "n_plans": n_plans, "ctr": ctr,
            }

        # 按 channel 聚合（不区分 coupon）
        by_ch: dict = {}
        for (ch, _cp), v in by_cp_out.items():
            by_ch.setdefault(ch, {"reach": 0, "click": 0, "sigs": set()})
            by_ch[ch]["reach"] += v["reach"]
            by_ch[ch]["click"] += v["click"]
            # 不在 by_cp 里记 sig，这里重新查
        # 第二遍：按 channel 单独聚合（拿 sig 集合）
        rows2 = conn.execute("""
            SELECT channel, task_signature,
                   SUM(reach_success) AS reach,
                   SUM(click_count) AS click
            FROM feedback_records
            GROUP BY channel, task_signature
        """).fetchall()
        for r in rows2:
            ch = r["channel"]
            by_ch.setdefault(ch, {"reach": 0, "click": 0, "sigs": set()})
            by_ch[ch]["reach"] += int(r["reach"] or 0)
            by_ch[ch]["click"] += int(r["click"] or 0)
            by_ch[ch]["sigs"].add(r["task_signature"])

        by_ch_out: dict = {}
        for ch, v in by_ch.items():
            n_plans = len(v["sigs"])
            ctr = v["click"] / v["reach"] if v["reach"] > 0 else 0.0
            by_ch_out[ch] = {
                "reach": v["reach"], "click": v["click"],
                "n_plans": n_plans, "ctr": ctr,
            }
        return by_cp_out, by_ch_out
    finally:
        conn.close()


# ── 校准核心 ────────────────────────────────────────────────────
def _calibrate_value(new: float, old: float, n_plans: int) -> Tuple[float, str]:
    """按 n_plans 返回新 baseline 值 + 说明。"""
    if n_plans < MIN_PLANS_DEFAULT:
        return old, f"n_plans={n_plans}<5 跳过（保留 {old*100:.4f}%）"
    if n_plans < 20:
        merged = ALPHA_LOW * new + (1 - ALPHA_LOW) * old
        return merged, f"n_plans={n_plans} 指数滑动 α=0.3（{new*100:.4f}%×0.3+{old*100:.4f}%×0.7={merged*100:.4f}%）"
    return new, f"n_plans={n_plans} 全量覆盖（{old*100:.4f}% → {new*100:.4f}%）"


def calibrate(baseline: dict, by_cp: dict, by_ch: dict,
              min_reach: int, definition: str = DEFINITION_DEFAULT) -> Tuple[dict, list]:
    """返回 (new_baseline, changes) — changes 是 diff 列表。

    definition: 校准口径版本标注（默认 v3.1），写入 json 的 _definition_version
    与 _definition_ref 字段，便于校准溯源（详 docs/ctr-kpi-definition-proposal-v0.2.md）。
    """
    new_baseline = json.loads(json.dumps(baseline))  # 深拷贝
    changes: list = []

    # 1) 渠道维度
    dim_ch = new_baseline.get("dimensions", {}).get("渠道", {})
    data_ch = dim_ch.get("data", {})
    for ch, v in by_ch.items():
        if v["reach"] < min_reach:
            changes.append(f"[渠道/{ch}] 触达 {v['reach']}<{min_reach} 跳过")
            continue
        old = float(data_ch.get(ch, 0.0))
        merged, note = _calibrate_value(v["ctr"], old, v["n_plans"])
        data_ch[ch] = round(merged, 6)
        changes.append(f"[渠道/{ch}] {note}")

    # 2) 渠道_x_是否用券维度
    dim_cp = new_baseline.get("dimensions", {}).get("渠道_x_是否用券", {})
    data_cp = dim_cp.get("data", {})
    for (ch, cp), v in by_cp.items():
        if v["reach"] < min_reach:
            changes.append(f"[渠道×用券/{ch}_{cp}] 触达 {v['reach']}<{min_reach} 跳过")
            continue
        key = f"{ch}_{cp}"
        old = float(data_cp.get(key, 0.0))
        merged, note = _calibrate_value(v["ctr"], old, v["n_plans"])
        data_cp[key] = round(merged, 6)
        changes.append(f"[渠道×用券/{key}] {note}")

    # 更新元信息
    new_baseline["version"] = _bump_version(baseline.get("version", "v3.0"))
    new_baseline["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    new_baseline["last_refreshed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_baseline["last_refreshed_by"] = "tools/calibrate_baseline.py"
    new_baseline["_calibration_log"] = changes
    # v3.1 口径标注（Phase 6 P2 落）：溯源用，baseline_lookup 不读这两个字段
    new_baseline["_definition_version"] = definition
    new_baseline["_definition_ref"] = "docs/ctr-kpi-definition-proposal-v0.2.md"
    return new_baseline, changes


def _bump_version(v: str) -> str:
    """v3.0 → v3.1 → v3.2 ..."""
    parts = v.lstrip("v").split(".")
    try:
        major, minor = int(parts[0]), int(parts[1])
    except Exception:
        return "v3.1"
    return f"v{major}.{minor + 1}"


# ── CLI ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CTR baseline 校准工具")
    parser.add_argument("--dry-run", action="store_true",
                        help="只看 diff 不写文件")
    parser.add_argument("--min-reach", type=int, default=MIN_REACH_DEFAULT,
                        help=f"单维度触达过滤阈值（默认 {MIN_REACH_DEFAULT}）")
    parser.add_argument("--db", type=str, default=str(ROOT / "data" / "feedback.db"),
                        help="feedback.db 路径")
    parser.add_argument("--baseline", type=str, default=str(BASELINE_PATH),
                        help="baseline JSON 路径")
    parser.add_argument("--definition", type=str, default=DEFINITION_DEFAULT,
                        help=f"校准口径版本标注（默认 {DEFINITION_DEFAULT}）")
    args = parser.parse_args()

    db_path = Path(args.db)
    baseline_path = Path(args.baseline)

    # 读 baseline
    if not baseline_path.exists():
        print(f"[FAIL] baseline 文件不存在：{baseline_path}")
        sys.exit(1)
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    print(f"[INFO] 读取 baseline {baseline.get('version', '?')} ({baseline_path})")
    print(f"[INFO] 校准口径 {args.definition}（详 docs/ctr-kpi-definition-proposal-v0.2.md）")

    # 读 feedback.db
    if not db_path.exists():
        print(f"[FAIL] feedback.db 不存在：{db_path}")
        sys.exit(1)

    by_cp, by_ch = aggregate_feedback(db_path)
    n_ch = len(by_ch)
    n_cp = len(by_cp)
    total_reach = sum(v["reach"] for v in by_ch.values())
    print(f"[INFO] 回流数据：{n_ch} 渠道 / {n_cp} 渠道×用券组合 / 总触达 {total_reach:,}")

    new_baseline, changes = calibrate(baseline, by_cp, by_ch, args.min_reach, args.definition)

    print(f"\n[CHANGES] {len(changes)} 条（按 n_plans 阈值 {MIN_PLANS_DEFAULT} / 20）")
    for c in changes:
        print(f"  - {c}")

    if args.dry_run:
        print(f"\n[DRY-RUN] 不写文件。新版本：{new_baseline['version']}")
        return

    # 备份旧版
    if BACKUP_PATH.exists():
        BACKUP_PATH.unlink()
    shutil.copy2(baseline_path, BACKUP_PATH)
    print(f"[INFO] 旧版备份 → {BACKUP_PATH}")

    # 写新版本（v3.x.json）
    new_version = new_baseline["version"]
    new_path = baseline_path.parent / f"ctr_baseline_{new_version}.json"
    with new_path.open("w", encoding="utf-8") as f:
        json.dump(new_baseline, f, ensure_ascii=False, indent=2)
    print(f"[OK] 新版写入 → {new_path}")
    print(f"[INFO] 注意：当前 _demo_pred 走 baseline 仍用 ctr_baseline.json（手动切换）")


if __name__ == "__main__":
    main()