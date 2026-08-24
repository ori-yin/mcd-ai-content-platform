# -*- coding: utf-8 -*-
"""
ui/styles.py — 全局 CSS 注入

Phase 0：基础样式（header / decision-card / metric 卡片）
Phase 1+：按需扩展（候选卡片 / 规则卡 / 预览卡 / KPI 卡）

注入方式：st.markdown(unsafe_allow_html=True)
注意：不复用 mcd-copy-analyzer 的 inject_css（项目特定 hack 太多）
"""

from __future__ import annotations

import streamlit as st

from ui.theme_tokens import (
    MCD_RED, MCD_GOLD, MCD_DARK_RED, MCD_BG, MCD_BG_DARK,
    MCD_GRAY, MCD_LIGHT_GRAY, MCD_GREEN, MCD_YELLOW, MCD_BORDER,
    FONT_FAMILY,
)


def inject_base_css() -> None:
    """注入全局基础样式。Phase 0 版本，后续按页面扩展。"""
    st.markdown(
        f"""
        <style>
        /* 全局字体 */
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
        }}

        /* 麦当劳红 header */
        .mcd-header {{
            background: linear-gradient(135deg, {MCD_RED} 0%, {MCD_DARK_RED} 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(218, 41, 28, 0.2);
        }}
        .mcd-header h1 {{
            color: white !important;
            margin: 0 0 0.25rem 0;
            font-size: 1.8rem;
        }}

        /* 决策卡 */
        .decision-card {{
            background: {MCD_LIGHT_GRAY};
            border-left: 4px solid {MCD_GOLD};
            padding: 1.2rem 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        .decision-card ul {{
            margin: 0;
            padding-left: 1.2rem;
        }}
        .decision-card li {{
            margin: 0.4rem 0;
            line-height: 1.6;
        }}

        /* 代码 */
        code {{
            background: {MCD_LIGHT_GRAY};
            color: {MCD_DARK_RED};
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }}

        /* Metric 卡片边框 */
        [data-testid="stMetric"] {{
            background: {MCD_BG};
            border: 1px solid {MCD_BORDER};
            border-radius: 8px;
            padding: 0.8rem;
        }}

        /* 按钮 hover */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
        }}

        /* 隐藏 Streamlit 默认元素 */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
