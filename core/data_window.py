# -*- coding: utf-8 -*-
r"""
core/data_window.py — 数据取数时间窗口工具（v3.1 取数铁律）

依据 docs/ctr-kpi-definition-proposal-v0.2.md §3：
- 回收真实 CTR 时，时间基准按 bi_dt T-1 快照
- 当天 12 点前的查询 → 必须避开当天未生成的快照，用 INTERVAL 2 取前天
- 当天 12 点后 → 可用 T-1（即昨天的快照）
- 跨日边界用 UTC+8（北京时间，麦当劳业务默认时区）

用法：
    from core.data_window import resolve_bi_dt_window
    bi_dt = resolve_bi_dt_window()           # 当前时间
    bi_dt = resolve_bi_dt_window(now=dt)     # 指定时间（测试用）
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


# 麦当劳业务默认时区：UTC+8（北京时间）
# 测试时可注入；默认 None 表示用本地时间
DEFAULT_TZ_OFFSET_HOURS = 8
SNAPSHOT_CUTOFF_HOUR = 12  # 12 点前用 INTERVAL 2


def _to_local(now: datetime, tz_offset_hours: int) -> datetime:
    """把 datetime 转成业务时区（默认 UTC+8）。

    简化实现：naive datetime 直接用，aware datetime 用 astimezone 转。
    """
    if now.tzinfo is None:
        return now
    # aware datetime：用 timedelta 偏移近似处理（避免依赖 zoneinfo）
    from datetime import timezone
    return now.astimezone(timezone(timedelta(hours=tz_offset_hours))).replace(tzinfo=None)


def resolve_bi_dt_window(
    now: Optional[datetime] = None,
    tz_offset_hours: int = DEFAULT_TZ_OFFSET_HOURS,
    cutoff_hour: int = SNAPSHOT_CUTOFF_HOUR,
) -> str:
    """计算取数用的 bi_dt（YYYY-MM-DD 字符串）。

    返回：
    - 当前时间 ≥ cutoff_hour → T-1（昨天）
    - 当前时间 < cutoff_hour → T-2（前天，INTERVAL 2）

    参数：
    - now: 给定当前时间；None 用 datetime.now()
    - tz_offset_hours: 业务时区偏移（默认 UTC+8 北京时间）
    - cutoff_hour: 快照生成截止小时（默认 12 点）
    """
    if now is None:
        now = datetime.now()
    local_now = _to_local(now, tz_offset_hours)

    if local_now.hour >= cutoff_hour:
        bi_dt = (local_now - timedelta(days=1)).date()
    else:
        bi_dt = (local_now - timedelta(days=2)).date()

    return bi_dt.isoformat()


__all__ = [
    "resolve_bi_dt_window",
    "DEFAULT_TZ_OFFSET_HOURS",
    "SNAPSHOT_CUTOFF_HOUR",
]
