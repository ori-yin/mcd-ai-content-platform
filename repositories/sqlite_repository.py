# -*- coding: utf-8 -*-
r"""
repositories/sqlite_repository.py — SQLite 存储

PRD §18 数据保存：生成记录允许存储完整文案（待业务确认项 §26-12 → 配置化）。

表 schema：
- generation_records(id, task_json, candidates_json, rule_results_json,
                     ctr_results_json, similar_summary_json,
                     selected_id, created_at)

约定：
- 用 stdlib sqlite3，避免引入额外依赖
- 路径 data/records.db，相对项目根
- 入参/出参都是 dict（业务层用 GenerationRecord.to_row() 转 dict）
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional, List


DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "records.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS generation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_json TEXT NOT NULL,
    candidates_json TEXT NOT NULL,
    rule_results_json TEXT,
    ctr_results_json TEXT,
    similar_summary_json TEXT,
    selected_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """获取连接（自动建表）。"""
    _ensure_dir()
    p = db_path or str(DB_PATH)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def save(record: dict, db_path: Optional[str] = None) -> int:
    """保存一条生成记录。返回 id。

    record: 必须含 task_json / candidates_json / selected_id / created_at 字段
            （GenerationRecord.to_row() 自动产出）
    """
    required = ("task_json", "candidates_json", "selected_id", "created_at")
    for k in required:
        if k not in record:
            raise ValueError(f"record 缺少必填字段：{k}")

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO generation_records
                (task_json, candidates_json, rule_results_json,
                 ctr_results_json, similar_summary_json,
                 selected_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["task_json"],
                record["candidates_json"],
                record.get("rule_results_json"),
                record.get("ctr_results_json"),
                record.get("similar_summary_json"),
                record["selected_id"],
                record["created_at"],
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_all(limit: int = 50, db_path: Optional[str] = None) -> List[dict]:
    """列出最近 limit 条记录（按 id DESC）。"""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM generation_records ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            # 解析 JSON 字段方便使用
            for jk in ("task_json", "candidates_json", "rule_results_json",
                       "ctr_results_json", "similar_summary_json"):
                if d.get(jk):
                    try:
                        d[jk.replace("_json", "")] = json.loads(d[jk])
                    except Exception:
                        pass
            out.append(d)
        return out
    finally:
        conn.close()


def get_by_id(record_id: int, db_path: Optional[str] = None) -> Optional[dict]:
    """按 id 取单条。"""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM generation_records WHERE id = ?", (record_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        d = dict(r)
        for jk in ("task_json", "candidates_json", "rule_results_json",
                   "ctr_results_json", "similar_summary_json"):
            if d.get(jk):
                try:
                    d[jk.replace("_json", "")] = json.loads(d[jk])
                except Exception:
                    pass
        return d
    finally:
        conn.close()


__all__ = ["save", "list_all", "get_by_id", "DB_PATH"]
