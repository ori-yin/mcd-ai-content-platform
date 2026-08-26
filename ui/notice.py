# -*- coding: utf-8 -*-
"""
ui/notice.py — 页面级提示横幅（进阶能力弱化 / CTR 反哺免责）

Handoff 决策文档（Demo 范围 §2 / §3）：
- .advanced-notice → 02/03/04/05 页面顶部，标识"非 demo 主线"
- .ctr-feedback-notice → 01/04/05 页面顶部 + 尾部，标识"机制就绪 / 口径待定"

具体业务文案见 render_advanced_notice / render_ctr_feedback_notice 两个 wrapper。
"""

from __future__ import annotations

import streamlit as st


def render_notice(prefix: str, body: str, css_class: str = "advanced-notice") -> None:
    """页面级 banner 渲染器（统一 HTML 包装，仅文案/CSS 类不同）。"""
    st.markdown(
        f'<div class="{css_class}">'
        f'<b>{prefix}</b>　{body}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_advanced_notice() -> None:
    """进阶能力 banner。02/03/04/05 页面顶部调用。

    文案来源：决策文档 Demo 范围 §2 ——"面向运营/分析的扩展工具，非本次 demo 主线"。
    """
    render_notice(
        "进阶能力 ·",
        "面向运营 / 内容的扩展工具，非本次 demo 主线。主要功能在侧边栏 01 内容创作。",
    )


def render_ctr_feedback_notice() -> None:
    """CTR 反哺闭环免责 banner。01/04/05 页面调用。

    文案来源：决策文档 Demo 范围 §3 ——"机制已就绪，基准待回流数据校准；
    业务确认前不接真实数据，避免口径返工"。
    """
    render_notice(
        "CTR 反哺闭环 ·",
        "机制已就绪（指纹 / 反馈库 / baseline 自动校准三件套），"
        "当前为 <b>演示口径</b>，基准待回流数据校准。"
        "业务确认前不接真实数据，避免口径变更导致的返工。",
    )