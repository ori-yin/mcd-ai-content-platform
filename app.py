# -*- coding: utf-8 -*-
"""
app.py — MCD AI 内容运营工作台入口

导航方式：pages/ 自动发现（Streamlit 默认行为，避坑 st.Page 自引用递归）

启动：streamlit run app.py（端口默认 8510）

页面清单（pages/ 下自动扫描）：
- pages/00_home.py：首页（项目状态 / 决策 / 资产）
- pages/01_content_studio.py：01 内容创作（Phase 16.5 上线）
- pages/02_copy_diagnosis.py：02 文案诊断（Phase 16.5 上线）
- pages/03_batch_evaluation.py：03 批量评估（Phase 16.5 上线）
- pages/04_historical_insights.py：04 历史洞察（Phase 16.5 上线）
"""

from __future__ import annotations

import streamlit as st

from ui.styles import inject_base_css


# 入口页面配置
st.set_page_config(
    page_title="MCD AI 内容运营工作台",
    page_icon="🍟",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()
