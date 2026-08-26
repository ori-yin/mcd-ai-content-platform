# -*- coding: utf-8 -*-
"""
pages/00_home.py — 首页（项目状态总览）

由 Streamlit pages/ 自动发现进入侧边栏导航。
启动顺序：app.py → pages/00_home.py / 01-04_*.py
"""

from __future__ import annotations

import streamlit as st

from ui.llm_status import render_banner
from ui.theme_tokens import MCD_RED, MCD_GOLD


# LLM 未配置提示（业务确认 #10，全留空时显示）
render_banner()

st.markdown(
    f"""
    <div class="mcd-header">
        <h1>🍟 MCD AI 内容运营工作台</h1>
        <p style="margin:0; opacity:0.85;">
            历史洞察 · AI 文案生成 · CTR 预测 · 人工决策
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("## 项目状态")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Phase 0（首批交付）", "完成", "工程化资产 + 项目骨架")
with col2:
    st.metric("Phase 1（CTR Adapter）", "完成", "4 纯函数模块 + PredictionResult + ProviderRouter")
with col3:
    st.metric("Phase 2（copy-analyzer Adapter）", "完成", "抽文案分析纯函数")
with col4:
    st.metric("Phase 3（业务页面）", "进行中", "01 内容创作完成；02-04 待 Phase 4")

st.markdown("## 关键决策")

st.markdown(
    f"""
    <div class="decision-card">
        <ul>
            <li><b>项目位置：</b><code>C:\\ideon\\mcd-ai-content-platform\\</code></li>
            <li><b>复用策略：</b>Adapter 模式，import 旧项目纯函数，不修改源</li>
            <li><b>旧项目：</b><code>mcd-copy-analyzer</code> + <code>mcd-ctr-predictor</code> 保持独立运行</li>
            <li><b>PRD：</b>v2.1（含 §4.0 CTR 三入口 / §13.5 Adapter 策略 / §15.A 工程化配套）</li>
            <li><b>应用模式：</b><code>APP_MODE=demo</code>（默认无 API） / <code>internal_llm</code></li>
            <li><b>CTR 模式：</b><code>existing_predictor</code> / <code>baseline_only</code> / <code>demo</code> / <code>unavailable</code></li>
            <li><b>配色：</b><span style="color:{MCD_RED}; font-weight:bold;">麦当劳红 #DA291C</span> +
                <span style="color:{MCD_GOLD}; font-weight:bold;">金 #FFC72C</span></li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("## 验证命令")

st.code(
    """# 跑集成验证（无需 pytest）
python tests/verify.py

# 启动工作台（端口 8510）
setup_and_run.bat
# 或：streamlit run app.py --server.port=8510""",
    language="bash",
)

st.markdown(
    """
    <div style="text-align:center; opacity:0.6; font-size:0.85em; margin-top:2rem;">
        MCD AI 内容运营工作台 · Phase 3 · 详见
        <code>Handoff.md</code> / <code>PRD.md</code> / <code>CLAUDE.md</code>
    </div>
    """,
    unsafe_allow_html=True,
)
