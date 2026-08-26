# -*- coding: utf-8 -*-
r"""
core/data_window.py — 数据取数时间窗口工具（v3.1 取数铁律）

依据 docs/ctr-kpi-definition-proposal-v0.2.md §3：
- 回收真实 CTR 时，时间基准按 bi_dt T-1 快照
- 当天 12 点前的查询 → 必须避开当天未生成的快照，用 INTERVAL 2 取前天
- 当天 12 点后 → 可用 T-1（即昨天的快照）

用法：
    from core.data_window import resolve_bi_dt_window
    bi_dt = resolve_bi_dt_window()           # 当前时间
    bi_dt = resolve_bi_dt_window(now=dt)     # 指定时间（测试用）
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


SNAPSHOT_CUTOFF_HOUR = 12  # 12 点前用 INTERVAL 2


def resolve_bi_dt_window(
    now: Optional[datetime] = None,
    cutoff_hour: int = SNAPSHOT_CUTOFF_HOUR,
) -> str:
    """计算取数用的 bi_dt（YYYY-MM-DD 字符串）。

    返回：
    - 当前时间 ≥ cutoff_hour → T-1（昨天）
    - 当前时间 < cutoff_hour → T-2（前天，INTERVAL 2）

    参数：
    - now: 给定当前时间；None 用 datetime.now()
    - cutoff_hour: 快照生成截止小时（默认 12 点）
    """
    if now is None:
        now = datetime.now()
    days_back = 1 if now.hour >= cutoff_hour else 2
    return (now - timedelta(days=days_back)).date().isoformat()


__all__ = ["resolve_bi_dt_window"]