# -*- coding: utf-8 -*-
"""
ui/notice.py — 页面级提示横幅（进阶能力弱化 / CTR 反哺免责）

Handoff 决策文档（Demo 范围 §2 / §3）：
- .advanced-notice    → 02/03/04/05 页面顶部，标识"非 demo 主线"
- .ctr-feedback-notice → 01/04/05 页面顶部 + 尾部，标识"机制就绪 / 口径待定"
"""

from __future__ import annotations

import streamlit as st


def render_advanced_notice() -> None:
    """进阶能力 banner。02/03/04/05 页面顶部调用，统一风格。

    文案来源：决策文档 Demo 范围 §2 ——"面向运营/分析的扩展工具，非本次 demo 主线"。
    """
    st.markdown(
        '<div class="advanced-notice">'
        '<b>进阶能力 · </b>面向运营 / 内容的扩展工具，非本次 demo 主线。'
        '主要功能在侧边栏 01 内容创作。'
        '</div>',
        unsafe_allow_html=True,
    )


def render_ctr_feedback_notice() -> None:
    """CTR 反哺闭环免责 banner。01/04/05 页面调用。

    文案来源：决策文档 Demo 范围 §3 ——"机制已就绪，基准待回流数据校准；
    业务确认前不接真实数据，避免口径返工"。
    """
    st.markdown(
        '<div class="advanced-notice">'
        '<b>CTR 反哺闭环 · </b>机制已就绪（指纹 / 反馈库 / baseline 自动校准三件套），'
        '当前为 <b>演示口径</b>，基准待回流数据校准。'
        '业务确认前不接真实数据，避免口径变更导致的返工。'
        '</div>',
        unsafe_allow_html=True,
    )
