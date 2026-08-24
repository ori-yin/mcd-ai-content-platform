# -*- coding: utf-8 -*-
"""
MCD AI 内容运营工作台 — Streamlit 入口

Phase 0 placeholder：仅显示项目信息 + 启动验证
Phase 3：实现完整的 pages/ 多页面导航

启动：streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ui.styles import inject_base_css
from ui.theme_tokens import MCD_RED, MCD_GOLD


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="MCD AI 内容运营工作台",
    page_icon="🍟",  # 仅 page_icon 用 emoji，UI 内容仍按规范不用
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()


# ============================================================
# Header
# ============================================================

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
# 项目状态卡
# ============================================================

st.markdown("## 项目状态")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Phase 0（首批交付）", "完成", "工程化资产 + 项目骨架")
with col2:
    st.metric("Phase 1（CTR Adapter）", "待开始", "抽 ctr_predictor 纯函数")
with col3:
    st.metric("Phase 2（copy-analyzer Adapter）", "待开始", "抽文案分析纯函数")
with col4:
    st.metric("Phase 3（业务页面）", "待开始", "4 个 page + Rule Engine + SQLite")


# ============================================================
# PRD 关键决策速查
# ============================================================

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


# ============================================================
# 工程化资产清单
# ============================================================

st.markdown("## 工程化资产（首批交付）")

assets = [
    ("PRD.md", "v2.1 产品需求文档（1351 行 v2.0 + 3 处补充）"),
    ("Handoff.md", "项目记忆（14 章节，仿 mcd-copy-analyzer 范式）"),
    ("CLAUDE.md", "给 AI 看的项目说明（10 章节）"),
    (".claude/agents/code-reviewer.md", "5 基线审查 sub-agent"),
    (".claude/agents/integration-helper.md", "指导 import 旧模块 sub-agent"),
    (".claude/agents/test-runner.md", "运行 verify + pytest sub-agent"),
    ("setup_and_run.bat", "一键启动脚本（仿 mcd-reach-trend）"),
    ("tests/verify.py", "32 用例集成验证（无 pytest 依赖）"),
    ("data/ctr_baseline.json", "CTR 7 维度基准（v3.0）"),
    ("data/custom_dict.txt", "jieba 自定义词典（65 行）"),
    ("data/stopwords.txt", "停用词 + 禁词段"),
    ("data/frameworks.json", "6 条高 CTR 框架"),
]

for name, desc in assets:
    st.markdown(f"- `{name}` — {desc}")


# ============================================================
# 验证命令
# ============================================================

st.markdown("## 验证命令")

st.code(
    """# 跑集成验证（无需 pytest）
python tests/verify.py

# 启动工作台
setup_and_run.bat
# 或：streamlit run app.py --server.port=8510""",
    language="bash",
)


# ============================================================
# Footer
# ============================================================

st.markdown("---")

st.markdown(
    f"""
    <div style="text-align:center; opacity:0.6; font-size:0.85em;">
        MCD AI 内容运营工作台 · Phase 0 placeholder ·
        详见 <code>Handoff.md</code> / <code>PRD.md</code> / <code>CLAUDE.md</code>
    </div>
    """,
    unsafe_allow_html=True,
)
