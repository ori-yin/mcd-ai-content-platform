# -*- coding: utf-8 -*-
"""
ui/styles.py — 全局 CSS 注入

Phase 0：基础样式（header / decision-card / metric 卡片）
Phase 1+：业务卡（candidate / rule-pass / rule-fail / preview / kpi-tile / warning）

注入方式：st.markdown(unsafe_allow_html=True)
注意：不复用 mcd-copy-analyzer 的 inject_css（项目特定 hack 太多）
约定：所有样式 token 在本文件定义，不在页面里 inline 写颜色
"""

from __future__ import annotations

import streamlit as st

from ui.theme_tokens import (
    MCD_RED, MCD_GOLD, MCD_DARK_RED, MCD_BG, MCD_BG_DARK,
    MCD_GRAY, MCD_LIGHT_GRAY, MCD_GREEN, MCD_YELLOW, MCD_BORDER,
    FONT_FAMILY,
)


# 阴影 / 圆角 token（页面层不直接用，全走 class）
SHADOW_SM = "0 1px 3px rgba(0,0,0,0.06)"
SHADOW_MD = "0 2px 8px rgba(0,0,0,0.08)"
RADIUS_SM = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"


def inject_base_css() -> None:
    """注入全局基础样式。Phase 3 业务页面也走这套 token。"""
    st.markdown(
        f"""
        <style>
        /* ====== 全局 ====== */
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
        }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* ====== Header ====== */
        .mcd-header {{
            background: linear-gradient(135deg, {MCD_RED} 0%, {MCD_DARK_RED} 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: {RADIUS_LG};
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(218, 41, 28, 0.2);
        }}
        .mcd-header h1 {{
            color: white !important;
            margin: 0 0 0.25rem 0;
            font-size: 1.8rem;
        }}
        .mcd-header p {{ margin: 0; opacity: 0.85; }}

        /* ====== 决策卡（首页用） ====== */
        .decision-card {{
            background: {MCD_LIGHT_GRAY};
            border-left: 4px solid {MCD_GOLD};
            padding: 1.2rem 1.5rem;
            border-radius: {RADIUS_MD};
            margin: 1rem 0;
        }}
        .decision-card ul {{ margin: 0; padding-left: 1.2rem; }}
        .decision-card li {{ margin: 0.4rem 0; line-height: 1.6; }}

        /* ====== 代码 ====== */
        code {{
            background: {MCD_LIGHT_GRAY};
            color: {MCD_DARK_RED};
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }}

        /* ====== Metric 卡片边框 ====== */
        [data-testid="stMetric"] {{
            background: {MCD_BG};
            border: 1px solid {MCD_BORDER};
            border-radius: {RADIUS_MD};
            padding: 0.8rem;
        }}

        /* ====== 按钮 ====== */
        .stButton > button {{
            border-radius: {RADIUS_MD};
            font-weight: 500;
        }}

        /* ====== KPI Tile（大数字块，深色背景） ====== */
        .kpi-tile {{
            background: {MCD_BG_DARK};
            color: white;
            padding: 1rem 1.2rem;
            border-radius: {RADIUS_MD};
            box-shadow: {SHADOW_MD};
        }}
        .kpi-tile .label {{
            font-size: 0.85em;
            opacity: 0.7;
            margin-bottom: 0.3rem;
        }}
        .kpi-tile .value {{
            font-size: 1.8em;
            font-weight: 600;
            color: {MCD_GOLD};
            line-height: 1.2;
        }}
        .kpi-tile .sub {{
            font-size: 0.8em;
            opacity: 0.6;
            margin-top: 0.2rem;
        }}

        /* ====== 候选卡（Phase 3 01_content_studio 主流程） ====== */
        .candidate-card {{
            background: {MCD_BG};
            border: 1px solid {MCD_BORDER};
            border-radius: {RADIUS_MD};
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
            box-shadow: {SHADOW_SM};
            transition: box-shadow 0.15s;
        }}
        .candidate-card:hover {{ box-shadow: {SHADOW_MD}; }}
        .candidate-card .cand-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.6rem;
            font-size: 0.85em;
            color: {MCD_GRAY};
        }}
        .candidate-card .cand-title {{
            font-weight: 600;
            font-size: 1.05em;
            color: #1a1a1a;
            margin-bottom: 0.3rem;
        }}
        .candidate-card .cand-body {{
            color: #333;
            line-height: 1.5;
            font-size: 0.95em;
        }}

        /* ====== 规则项 ====== */
        .rule-pass {{
            background: #E8F5E9;
            border-left: 4px solid {MCD_GREEN};
            padding: 0.6rem 0.9rem;
            border-radius: {RADIUS_SM};
            margin: 0.3rem 0;
            font-size: 0.92em;
        }}
        .rule-fail {{
            background: #FFEBEE;
            border-left: 4px solid {MCD_RED};
            padding: 0.6rem 0.9rem;
            border-radius: {RADIUS_SM};
            margin: 0.3rem 0;
            font-size: 0.92em;
        }}
        .rule-warn {{
            background: #FFF8E1;
            border-left: 4px solid {MCD_YELLOW};
            padding: 0.6rem 0.9rem;
            border-radius: {RADIUS_SM};
            margin: 0.3rem 0;
            font-size: 0.92em;
        }}

        /* ====== 预览卡（手机式深色边框） ====== */
        .preview-card {{
            background: {MCD_BG};
            border: 2px solid #2c2c2c;
            border-radius: 16px;
            padding: 1rem;
            max-width: 360px;
            margin: 0.5rem auto;
            box-shadow: {SHADOW_MD};
        }}
        .preview-card .pv-title {{
            font-weight: 600;
            font-size: 1em;
            color: #111;
            margin-bottom: 0.4rem;
        }}
        .preview-card .pv-body {{
            color: #333;
            font-size: 0.92em;
            line-height: 1.5;
        }}
        .preview-card .pv-meta {{
            margin-top: 0.6rem;
            padding-top: 0.6rem;
            border-top: 1px dashed {MCD_BORDER};
            font-size: 0.78em;
            color: {MCD_GRAY};
        }}

        /* ====== 警告横幅 ====== */
        .warning-banner {{
            background: #FFF8E1;
            border: 1px solid {MCD_YELLOW};
            border-radius: {RADIUS_MD};
            padding: 0.8rem 1rem;
            margin: 0.8rem 0;
            font-size: 0.92em;
            color: #6b5400;
        }}
        .warning-banner b {{ color: #8a6d00; }}

        /* ====== 企微 1v1 聊天气泡（仿企业微信） ====== */
        .wechat-bubble-wrap {{
            display: flex;
            align-items: flex-start;
            gap: 0.6rem;
            max-width: 380px;
            margin: 0.4rem auto;
        }}
        .wechat-bubble-wrap .wc-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 6px;
            background: #DA291C;
            color: #FFC72C;
            font-weight: 800;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-family: 'Arial Black', sans-serif;
        }}
        .wechat-bubble {{
            background: #FFFFFF;
            border: 1px solid #E5E5E5;
            border-radius: 6px;
            padding: 0.7rem 0.9rem;
            flex: 1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .wechat-bubble .wc-name {{
            font-weight: 600;
            font-size: 0.82em;
            color: #666;
            margin-bottom: 0.3rem;
        }}
        .wechat-bubble .wc-title {{
            font-weight: 700;
            font-size: 1.02em;
            color: #111;
            margin-bottom: 0.3rem;
            line-height: 1.35;
        }}
        .wechat-bubble .wc-body {{
            color: #555;
            font-size: 0.88em;
            line-height: 1.5;
            margin-bottom: 0.4rem;
        }}
        .wechat-bubble .wc-meta {{
            font-size: 0.7em;
            color: #999;
            text-align: right;
            margin-top: 0.3rem;
        }}

        /* ====== LLM 未配置 banner（暗黄提示） ====== */
        .llm-warning {{
            background: #FFF3CD;
            border-left: 4px solid #FFC107;
            border-radius: {RADIUS_SM};
            padding: 0.6rem 1rem;
            margin: 0.6rem 0;
            font-size: 0.88em;
            color: #856404;
        }}
        .llm-warning b {{ color: #664d03; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
