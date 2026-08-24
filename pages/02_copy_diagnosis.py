# -*- coding: utf-8 -*-
"""pages/02_copy_diagnosis.py — 02 文案诊断（Phase 4 占位）

PRD §4.2 入口 B：用户手动输入标题+正文，无需 AI 生成，立刻调 CTR Adapter。
本文件占位，Phase 4 实现。
"""

import streamlit as st

st.set_page_config(page_title="02 文案诊断", page_icon="🔍", layout="wide")

st.markdown(
    """
    <div class="mcd-header">
        <h1>02 文案诊断</h1>
        <p>单条文案本地规则 + 词语表现 + 历史相似 + AI 改写（PRD §4.2）</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="warning-banner">
        <b>Phase 4 待实现</b>。本页对应 PRD §4.2 入口 B，CTR Adapter 必须能脱离 AI 生成上下文
        独立工作，仅根据 title+body+channel+维度返回 PredictionResult。
        已就绪：
        <ul>
            <li>services/ctr_prediction_service.predict_one（单条 CTR 入口 B 接口）</li>
            <li>services/copy_analysis_service.diagnose（本地诊断）</li>
            <li>services/similarity_service.find_similar（历史相似 Plan）</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
