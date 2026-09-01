# -*- coding: utf-8 -*-
r"""
ui/sidebar_brand.py — 左侧栏顶部品牌块

Streamlit 原生侧栏布局：
  [stSidebarHeader]   "APP" 标题 + 折叠按钮   （用 CSS 隐藏）
  [stSidebarNav]      自动发现的 pages/ 列表   （CSS 重排到品牌块下方）
  [stSidebarUserContent]  st.sidebar.* 注入的内容   （品牌块注入在此）

通过 CSS order: 1/2 把品牌块提到最上方，隐藏 APP 标题，6 个导航样式贴近 v2。

页面接入：
- 子页面（01-05）：page_setup() 自动调 render_brand()
- 首页（00）：app.py 入口单独调 render_brand()，因为它不走 page_setup
"""

from __future__ import annotations

import streamlit as st

from ui.theme_tokens import MCD_GOLD


def render_brand() -> None:
    """注入侧栏顶部品牌块。多次调用安全（Streamlit 自身会按位置拼接）。"""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <span class="m-logo">M</span>
            <span class="brand-text">McD AI 内容平台</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_bottom() -> None:
    """侧栏底部品牌占位（占位用，避免侧栏底部太空）。"""
    st.sidebar.markdown(
        """
        <div class="sidebar-bottom-mark">
            <span>v2 · Phase 16.5</span>
        </div>
        """,
        unsafe_allow_html=True,
    )