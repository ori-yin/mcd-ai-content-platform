# -*- coding: utf-8 -*-
"""pages/04_historical_insights.py — 04 历史洞察（Phase 4 占位）

PRD §4.4：高效 Plan 排行 / 高低表现词 / emoji / 字数 / 相似 / 每日趋势 / Owner 对比。
本文件占位，Phase 4 实现。
"""

import streamlit as st

st.set_page_config(page_title="04 历史洞察", page_icon="📈", layout="wide")

st.markdown(
    """
    <div class="mcd-header">
        <h1>04 历史洞察</h1>
        <p>高效 Plan · 高低表现词 · Emoji · 字数 · 相似 · 每日趋势 · Owner 对比（PRD §4.4）</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="warning-banner">
        <b>Phase 4 待实现</b>。本页对应 PRD §4.4，所有底层分析已就绪：
        <ul>
            <li>services/analytics/high_effort_plans.rank_plans（高效 Plan 排行）</li>
            <li>services/analytics/similarity.find_similar_plans（相似 Plan）</li>
            <li>services/analytics/daily_trend.daily_aggregate（每日趋势 + 周环比）</li>
            <li>services/analytics/owner_compare.owner_compare（Owner 对比）</li>
            <li>services/text_analyzer.word_frequency（词频 + emoji）</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
