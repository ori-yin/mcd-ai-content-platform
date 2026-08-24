# -*- coding: utf-8 -*-
r"""
ui/theme_tokens.py — 麦当劳品牌配色 token

复用自 C:\ideon\mcd-copy-analyzer\config.py（颜色常量部分）
新项目不直接 import 旧项目，token 在此独立维护

按 CLAUDE.md §4.3 数据契约：颜色集中维护，不散落 UI 文件
"""

from __future__ import annotations


# ============================================================
# 麦当劳品牌色（商标色，UI 必须严格使用）
# ============================================================

MCD_RED = "#DA291C"      # 麦当劳红（主品牌色，慎用大面积）
MCD_GOLD = "#FFC72C"     # 麦当劳金（按钮、选中态）
MCD_DARK_RED = "#A11918"  # 深红（hover / 阻断项）
MCD_BG = "#FFFFFF"        # 主背景
MCD_BG_DARK = "#1E1E1E"   # 深色背景（候选区）
MCD_GRAY = "#5C5C5C"      # 深灰文字
MCD_LIGHT_GRAY = "#F5F5F5"  # 浅灰背景
MCD_GREEN = "#008000"     # 通过项
MCD_YELLOW = "#FFC72C"    # 提醒项（同金色，保持品牌一致）
MCD_BORDER = "#E0E0E0"    # 边框


# ============================================================
# Plotly 配色（图表）
# ============================================================

PLOTLY_PRIMARY = MCD_RED
PLOTLY_SECONDARY = MCD_GOLD
PLOTLY_NEUTRAL = MCD_GRAY
PLOTLY_SEQUENCE = [MCD_RED, MCD_GOLD, "#7A8B9B", "#A8B5C2", "#D4DAE0"]


# ============================================================
# 字体
# ============================================================

FONT_FAMILY = '"PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif'
