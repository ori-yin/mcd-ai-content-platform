# -*- coding: utf-8 -*-
r"""
repositories/feedback_repository.py — 真实投放结果回流库（PRD §回流闭环）

docs/feedback-ctr.md §2.3 schema：
- feedback_records(id, task_signature, channel, coupon, plan_type,
                  sent_date, reach_success, click_count, order_count,
                  source, imported_at)

v3.1 口径标注（2026-08-26 业务拍板；Q1 去重点击 / Q2 触达成功 / bi_dt T-1
12 点前 INTERVAL 2；详 docs/ctr-kpi-definition-proposal-v0.2.md）。
click_count / reach_success 列名保留（避免破坏 Phase 5 已上传数据）；
上游导出口径必须按 v0.2 §2 去重后再入库，否则反哺算出的 CTR 会系统性偏高。

约定：
- 与 records.db 同目录；路径 data/feedback.db，相对项目根
- 业务层用 dict 入参/出参（不入 dataclass，避免侵入 core/schemas）
- task_signature 是 join 锚点（与 generation_records.significance 对齐）
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional, List


DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "feedback.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_signature TEXT NOT NULL,
    channel TEXT NOT NULL,
    coupon TEXT,
    plan_type TEXT,
    sent_date TEXT,
    reach_success INTEGER NOT NULL DEFAULT 0,
    click_count INTEGER NOT NULL DEFAULT 0,
    order_count INTEGER NOT NULL DEFAULT 0,
    source TEXT,
    imported_at TEXT,
    text_has_coupon TEXT
);
CREATE INDEX IF NOT EXISTS idx_feedback_sig ON feedback_records(task_signature);
CREATE INDEX IF NOT EXISTS idx_feedback_channel ON feedback_records(channel);
CREATE INDEX IF NOT EXISTS idx_feedback_date ON feedback_records(sent_date);
CREATE INDEX IF NOT EXISTS idx_feedback_text ON feedback_records(text_has_coupon);
"""


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """获取连接（自动建表）。"""
    _ensure_dir()
    p = db_path or str(DB_PATH)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    # 老库（无 text_has_coupon 列）需先 ALTER，否则 CREATE INDEX 会报
    # "no such column"（SQLite 不容忍缺失列，不像 PG）。
    # 先做最小检查；老库 ADD COLUMN 后再 executescript(SCHEMA)。
    try:
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(feedback_records)").fetchall()]
        if cols and "text_has_coupon" not in cols:
            conn.execute(
                "ALTER TABLE feedback_records ADD COLUMN text_has_coupon TEXT")
            conn.commit()
    except sqlite3.OperationalError:
        # 表还不存在（首次启动），让 SCHEMA 自己建
        pass
    conn.executescript(SCHEMA)
    return conn


def save(record: dict, db_path: Optional[str] = None) -> int:
    """保存一条回流数据。返回 id。

    record 必填：task_signature / channel / reach_success / click_count
    可选：coupon / plan_type / sent_date / order_count / source / imported_at / text_has_coupon
    """
    required = ("task_signature", "channel", "reach_success", "click_count")
    for k in required:
        if k not in record:
            raise ValueError(f"feedback record 缺少必填字段：{k}")

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO feedback_records
                (task_signature, channel, coupon, plan_type,
                 sent_date, reach_success, click_count, order_count,
                 source, imported_at, text_has_coupon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["task_signature"],
                record["channel"],
                record.get("coupon"),
                record.get("plan_type"),
                record.get("sent_date"),
                int(record.get("reach_success") or 0),
                int(record.get("click_count") or 0),
                int(record.get("order_count") or 0),
                record.get("source"),
                record.get("imported_at"),
                record.get("text_has_coupon"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def save_batch(records: List[dict], db_path: Optional[str] = None) -> int:
    """批量保存。返回插入条数。"""
    if not records:
        return 0
    conn = get_connection(db_path)
    try:
        rows = [
            (
                r["task_signature"],
                r["channel"],
                r.get("coupon"),
                r.get("plan_type"),
                r.get("sent_date"),
                int(r.get("reach_success") or 0),
                int(r.get("click_count") or 0),
                int(r.get("order_count") or 0),
                r.get("source"),
                r.get("imported_at"),
                r.get("text_has_coupon"),
            )
            for r in records
        ]
        cur = conn.executemany(
            """
            INSERT INTO feedback_records
                (task_signature, channel, coupon, plan_type,
                 sent_date, reach_success, click_count, order_count,
                 source, imported_at, text_has_coupon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def list_all(limit: int = 100, db_path: Optional[str] = None) -> List[dict]:
    """列出最近 limit 条。"""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM feedback_records ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def aggregate_by_signature(db_path: Optional[str] = None) -> dict:
    """按 signature 聚合：总触达 / 总点击 / plan 加权 CTR / n_records。

    返回 {signature: {"reach": N, "click": N, "ctr": pct, "n": M, "channels": set, ...}}
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            SELECT task_signature, channel,
                   SUM(reach_success) AS reach,
                   SUM(click_count) AS click,
                   SUM(order_count) AS order_n,
                   COUNT(*) AS n_records,
                   MIN(sent_date) AS date_min,
                   MAX(sent_date) AS date_max
            FROM feedback_records
            GROUP BY task_signature
            """
        )
        out: dict = {}
        for r in cur.fetchall():
            d = dict(r)
            sig = d["task_signature"]
            reach = int(d["reach"] or 0)
            click = int(d["click"] or 0)
            ctr = round(click / reach * 100, 2) if reach > 0 else 0.0
            out[sig] = {
                "reach": reach,
                "click": click,
                "ctr": ctr,
                "order_n": int(d["order_n"] or 0),
                "n_records": int(d["n_records"] or 0),
                "channel": d["channel"],
                "date_min": d["date_min"],
                "date_max": d["date_max"],
            }
        return out
    finally:
        conn.close()


def count(db_path: Optional[str] = None) -> int:
    """总记录数。"""
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM feedback_records")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def count_distinct_plans(db_path: Optional[str] = None) -> int:
    """distinct task_signature 数（≈ plan 数）。

    给上层业务用（例如未来想做"回灌就绪状态"看板）。
    adapter 层不调用本函数（CLAUDE.md §4.1 adapter 不能依赖 repository）；
    adapter 走 adapters/ctr_predictor_adapter/feedback_lookup.py 直接 sqlite3。
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT COUNT(DISTINCT task_signature) FROM feedback_records")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


__all__ = [
    "save", "save_batch", "list_all", "aggregate_by_signature",
    "count", "count_distinct_plans", "get_connection", "DB_PATH",
]