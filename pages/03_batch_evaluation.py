# -*- coding: utf-8 -*-
"""pages/03_batch_evaluation.py — 03 批量评估（Phase 4 占位）

PRD §4.3 入口 C：上传 CSV/Excel，逐条 CTR + 优化建议 + 字数建议 + 时段建议，导出。
本文件占位，Phase 4 实现。
"""

import streamlit as st

st.set_page_config(page_title="03 批量评估", page_icon="📊", layout="wide")

st.markdown(
    """
    <div class="mcd-header">
        <h1>03 批量评估</h1>
        <p>批量文案 CTR 评估 + 优化建议 + 下载（PRD §4.3）</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="warning-banner">
        <b>Phase 4 待实现</b>。本页对应 PRD §4.3 入口 C，复用
        services/ctr_prediction_service.predict_for_candidates 批量接口。
        已就绪：
        <ul>
            <li>CTR 批量预测接口（predict_for_candidates）</li>
            <li>services/rule_engine.check_candidates（批量规则）</li>
            <li>services/data_loader.load_sheet（CSV/Excel 解析）</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
