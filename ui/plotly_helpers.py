# -*- coding: utf-8 -*-
r"""
ui/plotly_helpers.py — Plotly 辅助函数

仅保留 `rate_value`（table/text 用）。`axis_rate`（Plotly 轴用）于 2026-08-31 清死代码：
项目未启用 Plotly，零调用方。`theme_tokens.py` 的 `PLOTLY_*` 同列待清理（不在本文件范围）。
"""

from __future__ import annotations


def rate_value(rate: float, decimals: int = 2) -> str:
    """把 0.0355 格式化成 '3.55%' 字符串（用于表格 / 文本显示）"""
    if rate is None:
        return "—"
    return f"{rate * 100:.{decimals}f}%"
