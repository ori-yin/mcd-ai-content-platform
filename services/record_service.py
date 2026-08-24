# -*- coding: utf-8 -*-
r"""
services/record_service.py — 生成记录 service 包装

repositories/sqlite_repository 的薄壳，业务层不直接调 sqlite。
接收 GenerationRecord dict，输出 list[dict]（UI 用）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from core.schemas import GenerationRecord
from repositories import sqlite_repository


def save_generation(record: GenerationRecord, db_path: Optional[str] = None) -> int:
    """保存一次生成。返回 id。"""
    if not record.created_at:
        record.created_at = datetime.now().isoformat(timespec="seconds")
    return sqlite_repository.save(record.to_row(), db_path=db_path)


def list_generations(limit: int = 50, db_path: Optional[str] = None) -> List[dict]:
    """列出最近 limit 条。"""
    return sqlite_repository.list_all(limit=limit, db_path=db_path)


def get_generation(record_id: int, db_path: Optional[str] = None) -> Optional[dict]:
    """按 id 取单条。"""
    return sqlite_repository.get_by_id(record_id, db_path=db_path)


__all__ = ["save_generation", "list_generations", "get_generation"]
