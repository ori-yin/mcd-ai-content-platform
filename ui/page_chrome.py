# -*- coding: utf-8 -*-
r"""
ui/page_chrome.py — 5 个子页面统一的页面骨架

把每个 page 的三段重复样板压成一行 page_setup(page_id, subtitle)：

  ① st.set_page_config(...)        5 行
  ② inject_base_css()              1 行
  ③ st.markdown(<div class="mcd-header">...</div>)  9 行

约束（CLAUDE.md §9）：
- UI 不放 emoji，h1 不带 emoji
- 所有子页面统一 layout="wide"，侧边栏默认展开

页面级 banner（render_advanced_notice / render_ctr_feedback_notice / render_banner）
调用顺序与是否启用随页面而异，由各 page 在 page_setup 之后自己调。

00_home 是 app 主体（不是子页），不用 page_setup。
"""

from __future__ import annotations

import streamlit as st

from ui.styles import inject_base_css


def page_setup(page_id: str, subtitle: str) -> None:
    """统一 5 个子页面顶部骨架（zero visual change 目标）。

    等价于：
        st.set_page_config(page_title=page_id, page_icon=None,
                           layout="wide", initial_sidebar_state="expanded")
        inject_base_css()
        st.markdown(f'''
            <div class="mcd-header">
                <h1>{page_id}</h1>
                <p>{subtitle}</p>
            </div>
        ''', unsafe_allow_html=True)
    """
    st.set_page_config(
        page_title=page_id,
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_base_css()
    st.markdown(
        f"""
        <div class="mcd-header">
            <h1>{page_id}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )