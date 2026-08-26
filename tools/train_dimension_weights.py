# -*- coding: utf-8 -*-
r"""
tools/train_dimension_weights.py — 维度权重训练工具（Handoff §6.3 P3 落地）

按 docs/feedback-ctr.md 思路：维度权重从 feedback.db 反向校准，
让 diagnose_score 和 get_baseline_ctr 的"硬编码等权"变成可学习参数。

校准策略（仿 tools/calibrate_baseline.py 三段阈值）：
- n_plans < 5  → 保留旧权重（样本不足）
- 5 ≤ n_plans < 20 → 指数滑动 α=0.3
- n_plans ≥ 20 → 全量覆盖

约束：
- v0.1 训练算法占位（业务确认前不接真实数据，Handoff §6.3 红线）
- 元信息写入 dimension_weights.yaml（version / last_updated / _trained_by / _log /
  _definition_version / _definition_ref）
- 写盘前 .bak 备份，仿 calibrate_baseline.py:243-246

CLI 用法：
    python tools/train_dimension_weights.py                # 训练（写文件）
    python tools/train_dimension_weights.py --dry-run      # 看 diff 不写
    python tools/train_dimension_weights.py --definition v0.2  # 口径版本标注

后续（v0.2+）：
- 接诊断分项 vs 真实 CTR 的相关性 → 算 dimensions 相对权重
- 接渠道维度组合 vs 整体 CTR 的差异 → 算 baseline_modifiers
- 样本 ≥ 1000 时切 GBDT（与 §6.3 L1 LightGBM 联动）
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, List


# ── 路径 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = ROOT / "config" / "dimension_weights.yaml"
BACKUP_PATH = ROOT / "config" / "dimension_weights.bak.yaml"


# ── 训练参数 ────────────────────────────────────────────────────
MIN_PLANS_DEFAULT = 5       # n_plans < 该值用旧权重（保留兜底）
ALPHA_LOW = 0.3             # 5 ≤ n_plans < 20 时滑动系数
ALPHA_HIGH = 1.0            # n_plans ≥ 20 时
DEFINITION_DEFAULT = "v0.1" # 训练口径版本


# ── 维度键名契约 ────────────────────────────────────────────────
# 诊断 5 维度：必须与 services/text_analyzer.py diagnose_score 返回 breakdown 一致
DIAGNOSIS_DIMS = ["标题字数", "正文字数", "Emoji", "命中高效词", "框架命中"]
# baseline 6 维度：必须与 adapters/ctr_predictor_adapter/baseline_lookup.py 回退分支键一致
BASELINE_DIMS = ["渠道_x_标题字数", "渠道_x_计划类型", "渠道_x_预算owner",
                 "渠道_x_是否用券", "渠道_x_工作日类型", "渠道"]


# ── 回流数据查询 ────────────────────────────────────────────────
def count_distinct_plans(db_path: Path) -> int:
    """feedback.db 里独立 task_signature 数（≈ plan 数）。DB 缺失/异常 → 0。"""
    import sqlite3
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute("SELECT COUNT(DISTINCT task_signature) FROM feedback_records")
            return int(cur.fetchone()[0])
        finally:
            conn.close()
    except Exception:
        return 0


# ── 三段训练核心 ────────────────────────────────────────────────
def _train_value(new: float, old: float, n_plans: int) -> Tuple[float, str]:
    """按 n_plans 返回新权重值 + 说明。仿 calibrate_baseline._calibrate_value。"""
    if n_plans < MIN_PLANS_DEFAULT:
        return old, f"n_plans={n_plans}<{MIN_PLANS_DEFAULT} 跳过（保留 {old}）"
    if n_plans < 20:
        merged = ALPHA_LOW * new + (1 - ALPHA_LOW) * old
        return merged, f"n_plans={n_plans} 指数滑动 α={ALPHA_LOW}（{new}×0.3+{old}×0.7={merged:.4f}）"
    return new, f"n_plans={n_plans} 全量覆盖（{old} → {new}）"


# ── 训练主函数（v0.1 占位） ─────────────────────────────────────
def train(yaml_doc: dict, db_path: Path, definition: str) -> Tuple[dict, List[str]]:
    """返回 (new_yaml, changes)。

    v0.1 算法占位：业务确认前不接真实数据 → 5 diagnosis_dim + 6 baseline_modifiers 全部
    保持默认值 1.0，仅维护元信息（version / last_updated / _trained_by / _log / _definition_version）。

    v0.2 计划：
      1. 读 records.db 的 generation_records 关联 feedback.db，按诊断分项 × 真实 CTR
         算维度相关性 → 归一化成 dimensions 权重；
      2. 按 baseline 维度组合的 CTR 偏差 → 算 baseline_modifiers。
    """
    n_plans = count_distinct_plans(db_path)
    changes: list = []

    if n_plans == 0:
        changes.append("无反馈数据：所有维度权重保持默认值 1.0")
        changes.append("（Handoff §6.3 红线：业务确认前不接真实数据）")
    else:
        # v0.1 占位：有数据但不实际训练，留给 v0.2
        changes.append(f"检测到 {n_plans} plans（v0.1 算法占位，未实际训练权重）")
        changes.append("v0.2 计划：诊断分项 × 真实 CTR 相关性 + baseline 维度 CTR 偏差")

    # 深拷贝 + 更新元信息（仿 calibrate_baseline.calibrate:172-181）
    import copy
    new_doc = copy.deepcopy(yaml_doc)
    new_doc["version"] = _bump_version(yaml_doc.get("version", "v0.1"))
    new_doc["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    new_doc["_trained_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_doc["_trained_by"] = "tools/train_dimension_weights.py"
    new_doc["_training_log"] = changes
    new_doc["_definition_version"] = definition
    new_doc["_definition_ref"] = "docs/feedback-ctr.md"
    new_doc["_n_plans_observed"] = n_plans

    return new_doc, changes


def _bump_version(v: str) -> str:
    """v0.1 → v0.2 → v0.3 ..."""
    parts = v.lstrip("v").split(".")
    try:
        major, minor = int(parts[0]), int(parts[1])
    except Exception:
        return "v0.1"
    return f"v{major}.{minor + 1}"


# ── CLI ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="维度权重训练工具（Handoff §6.3 P3）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只看 diff 不写文件")
    parser.add_argument("--db", type=str, default=str(ROOT / "data" / "feedback.db"),
                        help="feedback.db 路径")
    parser.add_argument("--yaml", type=str, default=str(WEIGHTS_PATH),
                        help="dimension_weights.yaml 路径")
    parser.add_argument("--definition", type=str, default=DEFINITION_DEFAULT,
                        help=f"训练口径版本标注（默认 {DEFINITION_DEFAULT}）")
    args = parser.parse_args()

    db_path = Path(args.db)
    yaml_path = Path(args.yaml)

    # 读 yaml
    if not yaml_path.exists():
        print(f"[FAIL] yaml 文件不存在：{yaml_path}")
        sys.exit(1)

    import yaml  # PyYAML 已在 services/rule_engine.py:54 使用
    with yaml_path.open("r", encoding="utf-8") as f:
        yaml_doc = yaml.safe_load(f) or {}
    print(f"[INFO] 读取 weights {yaml_doc.get('version', '?')} ({yaml_path})")
    print(f"[INFO] 训练口径 {args.definition}（详 docs/feedback-ctr.md）")

    # 训练
    n_plans = count_distinct_plans(db_path)
    print(f"[INFO] feedback.db: {n_plans} plans")

    new_doc, changes = train(yaml_doc, db_path, args.definition)

    print(f"\n[CHANGES] {len(changes)} 条")
    for c in changes:
        print(f"  - {c}")

    if args.dry_run:
        print(f"\n[DRY-RUN] 不写文件。新版本：{new_doc['version']}")
        return

    # 备份旧版（仿 calibrate_baseline.py:243-246）
    if BACKUP_PATH.exists():
        BACKUP_PATH.unlink()
    shutil.copy2(yaml_path, BACKUP_PATH)
    print(f"[INFO] 旧版备份 → {BACKUP_PATH}")

    # 写新版本
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(new_doc, f, allow_unicode=True, sort_keys=False)
    print(f"[OK] 新版写入 → {yaml_path}（{new_doc['version']}）")
    print(f"[INFO] 注意：当前 baseline_lookup / text_analyzer 读 dimension_weights.yaml 实时生效")


if __name__ == "__main__":
    main()