# -*- coding: utf-8 -*-
r"""
ui/plotly_helpers.py — Plotly 辅助函数

复用自 C:\ideon\mcd-copy-analyzer\config.py 的 axis_rate 函数
新项目不直接 import 旧项目，在此独立维护

Phase 0：仅 axis_rate 基础函数
Phase 2+：按需扩展（color sequences / themes / figure helpers）
"""

from __future__ import annotations


def axis_rate(axis, decimals: int = 2) -> None:
    """
    把 Plotly y/x 轴的 0.0355 格式化成 3.55% 显示。

    用法：
        fig.update_yaxes(axis_rate(fig.yaxis))
    或：
        axis_rate(fig.layout.yaxis)

    复用自 mcd-copy-analyzer/config.py:axis_rate
    """
    axis.tickformat = f".{decimals}%"


def rate_value(rate: float, decimals: int = 2) -> str:
    """把 0.0355 格式化成 '3.55%' 字符串（用于表格 / 文本显示）"""
    if rate is None:
        return "—"
    return f"{rate * 100:.{decimals}f}%"
