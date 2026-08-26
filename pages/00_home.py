# -*- coding: utf-8 -*-
"""
pages/00_home.py — 首页（项目状态总览）

由 Streamlit pages/ 自动发现进入侧边栏导航。
启动顺序：app.py → pages/00_home.py / 01-04_*.py

Phase 6 P1（决策文档 Demo 范围 §2）改造：
首页入口分两组「核心 · 内容生成」/「进阶能力」视觉权重，引导 demo 主流程。
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

# ============================================================
# 分组入口（决策文档 Demo 范围 §2）：核心大卡 / 进阶小卡
# ============================================================
st.markdown(
    """
    <div class="home-section home-section-core">
        <h2>🚀 核心 · 内容生成</h2>
        <p style="margin:0; opacity:0.95;">
            领导 Demo 主流程：定义经营任务 → 生成 3 条候选 → 渠道预览 → 人工选择。
        </p>
        <p style="margin:0.4rem 0 0 0;">
            <a href="01_content_studio">→ 进入 01 内容创作（主流程）</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="home-section home-section-advanced">
        <h2>进阶能力</h2>
        <p style="margin:0; color:#666;">
            面向运营 / 内容的扩展工具，非本次 demo 主线。可随时进入。
        </p>
        <ul>
            <li><a href="02_copy_diagnosis">02 文案诊断</a> · 单条规则 + 词语 + CTR + AI 改写</li>
            <li><a href="03_batch_evaluation">03 批量评估</a> · CSV/Excel 上传 + 批量规则 + CTR + 导出</li>
            <li><a href="04_historical_insights">04 历史洞察</a> · 七 Tab 排名/词频/Emoji/趋势/Owner</li>
            <li><a href="05_feedback">05 真实结果回流</a> · CTR 反哺闭环数据源（演示口径，业务确认前不接真实数据）</li>
        </ul>
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
