# -*- coding: utf-8 -*-
"""
ui/styles.py — 全局 CSS 注入（v2 重构）

【设计原则】
- 品牌色降级为 accent：MCD_RED 仅做左侧 3px 识别条 / 主按钮 / 选中态
- 中性色建立结构：GRAY_50..900 + 1px 边框
- Shadow 仅留给真正浮起的元素（弹窗/下拉）；静态层禁止使用
- 所有 token 集中在 theme_tokens.py；本文件只引用，不写裸值

【class 名约定】以下 class 名是公开契约，pages/ 直接引用，禁止改名：
  .mcd-header / .decision-card / .kpi-tile / .candidate-card / .rule-pass
  .rule-fail / .rule-warn / .preview-card / .wechat-bubble* / .warning-banner
  .llm-warning / .advanced-notice / .home-section / .home-section-core
  .home-section-advanced / .l1-pill
"""

from __future__ import annotations

import streamlit as st

from ui.theme_tokens import (
    # 品牌色
    MCD_RED, MCD_GOLD, MCD_DARK_RED, MCD_GREEN, MCD_YELLOW,
    # 中性色阶
    GRAY_50, GRAY_100, GRAY_200, GRAY_300, GRAY_400,
    GRAY_500, GRAY_600, GRAY_700, GRAY_900,
    # scale
    TEXT_XS, TEXT_SM, TEXT_BASE, TEXT_MD, TEXT_LG, TEXT_XL, TEXT_2XL,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_6, SPACE_8,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    SHADOW_FLOAT,
    FONT_FAMILY,
)


def inject_base_css() -> None:
    """注入全局样式。所有 6 个页面通过 page_setup() 间接调用。"""
    st.markdown(
        f"""
        <style>
        /* ===========================================================
           1. 全局
           =========================================================== */
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
            font-size: {TEXT_BASE};
            color: {GRAY_900};
        }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        a {{ color: {MCD_DARK_RED}; text-decoration: none; }}
        a:hover {{ color: {MCD_RED}; }}

        /* ===========================================================
           2. 顶部信息条（每页都有）
           从 96px 红渐变块 → 64px 中性标题行；左侧 3px MCD_RED 作 brand accent
           =========================================================== */
        .mcd-header {{
            background: {GRAY_50};
            border-bottom: 1px solid {GRAY_200};
            border-left: 3px solid {MCD_RED};
            padding: {SPACE_3} {SPACE_6};
            margin-bottom: {SPACE_4};
            border-radius: 0;
            min-height: 56px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .mcd-header h1 {{
            color: {GRAY_900} !important;
            margin: 0;
            font-size: {TEXT_LG};
            font-weight: 600;
            line-height: 1.3;
            letter-spacing: -0.2px;
        }}
        .mcd-header p {{
            margin: 2px 0 0 0;
            color: {GRAY_500};
            font-size: {TEXT_SM};
            line-height: 1.4;
        }}

        /* ===========================================================
           3. 首页分组卡（核心 / 进阶）
           去渐变 → 靠左 3px 竖条区分级别
           =========================================================== */
        .home-section {{
            padding: {SPACE_4};
            border-radius: {RADIUS_LG};
            margin: {SPACE_3} 0 {SPACE_4} 0;
            background: #fff;
            border: 1px solid {GRAY_200};
        }}
        .home-section-core {{
            border-left: 3px solid {MCD_RED};
        }}
        .home-section-core h2 {{
            color: {GRAY_900};
            margin: 0 0 {SPACE_2} 0;
            font-size: {TEXT_MD};
            font-weight: 600;
        }}
        .home-section-core a {{
            color: {MCD_DARK_RED};
            font-weight: 600;
        }}
        .home-section-advanced {{
            border-left: 3px solid {GRAY_300};
        }}
        .home-section-advanced h2 {{
            color: {GRAY_900};
            margin: 0 0 {SPACE_2} 0;
            font-size: {TEXT_MD};
            font-weight: 600;
        }}
        .home-section-advanced a {{
            color: {MCD_DARK_RED};
            text-decoration: none;
        }}
        .home-section-advanced ul {{
            margin: {SPACE_2} 0 0 1.2rem;
            padding: 0;
            color: {GRAY_700};
            font-size: {TEXT_BASE};
        }}
        .home-section-advanced li {{ margin: {SPACE_1} 0; }}

        /* ===========================================================
           4. 决策卡 / 关键信息卡
           =========================================================== */
        .decision-card {{
            background: {GRAY_50};
            border: 1px solid {GRAY_200};
            border-left: 3px solid {MCD_GOLD};
            padding: {SPACE_4};
            border-radius: {RADIUS_MD};
            margin: {SPACE_3} 0;
            color: {GRAY_700};
            font-size: {TEXT_BASE};
        }}
        .decision-card ul {{ margin: 0; padding-left: 1.2rem; }}
        .decision-card li {{ margin: {SPACE_1} 0; line-height: 1.6; }}
        .decision-card code {{
            background: #fff;
            border: 1px solid {GRAY_200};
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 0.92em;
            color: {GRAY_700};
        }}

        /* ===========================================================
           5. 代码块（行内 code）
           =========================================================== */
        code {{
            background: {GRAY_50};
            color: {MCD_DARK_RED};
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 0.92em;
            font-family: "SFMono-Regular", Consolas, monospace;
        }}

        /* ===========================================================
           6. KPI Tile / Streamlit Metric
           去深色背景 + 金色数字；改白底灰边 + GRAY_900 数字
           数字色按语义分：正向绿、负向红、其余深灰
           =========================================================== */
        .kpi-tile {{
            background: #fff;
            border: 1px solid {GRAY_200};
            border-radius: {RADIUS_MD};
            padding: {SPACE_4};
        }}
        .kpi-tile .label {{
            font-size: {TEXT_XS};
            color: {GRAY_500};
            margin-bottom: {SPACE_2};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 500;
        }}
        .kpi-tile .value {{
            font-size: {TEXT_XL};
            font-weight: 600;
            color: {GRAY_900};
            line-height: 1.2;
            font-feature-settings: "tnum";
        }}
        .kpi-tile .value.positive {{ color: {MCD_GREEN}; }}
        .kpi-tile .value.negative {{ color: {MCD_RED}; }}
        .kpi-tile .sub {{
            font-size: {TEXT_XS};
            color: {GRAY_400};
            margin-top: {SPACE_1};
        }}

        /* Streamlit 原生 st.metric */
        [data-testid="stMetric"] {{
            background: #fff;
            border: 1px solid {GRAY_200};
            border-radius: {RADIUS_MD};
            padding: {SPACE_3} {SPACE_4};
        }}
        [data-testid="stMetric"] label {{
            color: {GRAY_500} !important;
            font-size: {TEXT_XS} !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {GRAY_900} !important;
            font-size: {TEXT_XL} !important;
            font-weight: 600;
            font-feature-settings: "tnum";
        }}
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            font-size: {TEXT_XS} !important;
        }}

        /* ===========================================================
           7. 按钮
           =========================================================== */
        .stButton > button {{
            border-radius: {RADIUS_MD};
            border: 1px solid {GRAY_300};
            background: #fff;
            color: {GRAY_700};
            font-weight: 500;
            font-size: {TEXT_BASE};
            padding: {SPACE_2} {SPACE_4};
            transition: all 0.12s ease;
        }}
        .stButton > button:hover {{
            border-color: {MCD_RED};
            color: {MCD_RED};
        }}
        .stButton > button[kind="primary"] {{
            background: {MCD_RED};
            color: #fff;
            border-color: {MCD_RED};
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {MCD_DARK_RED};
            border-color: {MCD_DARK_RED};
            color: #fff;
        }}
        .stButton > button:focus {{
            box-shadow: 0 0 0 2px {GRAY_200};
        }}
        .stButton > button[kind="primary"]:focus {{
            box-shadow: 0 0 0 2px {MCD_RED}40;
        }}
        .stDownloadButton > button {{
            border-radius: {RADIUS_MD};
        }}

        /* ===========================================================
           8. 候选卡（01_content_studio 主流程）
           =========================================================== */
        .candidate-card {{
            background: #fff;
            border: 1px solid {GRAY_200};
            border-radius: {RADIUS_MD};
            padding: {SPACE_4};
            margin-bottom: {SPACE_3};
            transition: border-color 0.12s ease;
        }}
        .candidate-card:hover {{ border-color: {MCD_RED}; }}
        .candidate-card .cand-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: {SPACE_2};
            font-size: {TEXT_XS};
            color: {GRAY_500};
        }}
        .candidate-card .cand-title {{
            font-weight: 600;
            font-size: {TEXT_MD};
            color: {GRAY_900};
            margin-bottom: {SPACE_1};
            line-height: 1.4;
        }}
        .candidate-card .cand-body {{
            color: {GRAY_700};
            line-height: 1.55;
            font-size: {TEXT_BASE};
        }}

        /* ===========================================================
           9. 规则项（3 状态：✓ / ✗ / !）
           去色块 → 白底 + 左 3px 竖条 + icon
           =========================================================== */
        .rule-pass, .rule-fail, .rule-warn {{
            background: #fff;
            padding: {SPACE_2} {SPACE_3};
            border-radius: {RADIUS_SM};
            margin: {SPACE_1} 0;
            font-size: {TEXT_SM};
            color: {GRAY_700};
            display: flex;
            align-items: flex-start;
            gap: {SPACE_2};
            border: 1px solid {GRAY_200};
        }}
        .rule-pass {{ border-left: 3px solid {MCD_GREEN}; }}
        .rule-pass::before {{
            content: "✓"; color: {MCD_GREEN}; font-weight: 700; flex: none;
        }}
        .rule-fail {{ border-left: 3px solid {MCD_RED}; }}
        .rule-fail::before {{
            content: "✗"; color: {MCD_RED}; font-weight: 700; flex: none;
        }}
        .rule-warn {{ border-left: 3px solid {MCD_GOLD}; }}
        .rule-warn::before {{
            content: "!"; color: {MCD_DARK_RED}; font-weight: 700; flex: none;
        }}

        /* ===========================================================
           10. 预览卡（Push / 企微 收件箱样式）
           去 2px 黑色实心 → 1px 中性边；不再假装手机壳
           =========================================================== */
        .preview-card {{
            background: #fff;
            border: 1px solid {GRAY_300};
            border-radius: {RADIUS_LG};
            padding: {SPACE_4};
            max-width: 360px;
            margin: {SPACE_2} auto;
            position: relative;
        }}
        .preview-card::before {{
            content: "Push 预览";
            position: absolute;
            top: -10px;
            left: 12px;
            background: {GRAY_50};
            padding: 0 {SPACE_2};
            font-size: {TEXT_XS};
            color: {GRAY_400};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .preview-card .pv-title {{
            font-weight: 600;
            font-size: {TEXT_MD};
            color: {GRAY_900};
            margin-bottom: {SPACE_2};
            line-height: 1.4;
        }}
        .preview-card .pv-body {{
            color: {GRAY_700};
            font-size: {TEXT_SM};
            line-height: 1.5;
        }}
        .preview-card .pv-meta {{
            margin-top: {SPACE_3};
            padding-top: {SPACE_2};
            border-top: 1px dashed {GRAY_200};
            font-size: {TEXT_XS};
            color: {GRAY_400};
        }}

        /* ===========================================================
           11. 告警 / 提示（统一语言）
           三档：warning 黄 / error 红 / info 灰
           =========================================================== */
        .warning-banner {{
            background: {GRAY_50};
            border: 1px solid {GRAY_200};
            border-left: 3px solid {MCD_GOLD};
            border-radius: {RADIUS_MD};
            padding: {SPACE_3} {SPACE_4};
            margin: {SPACE_3} 0;
            font-size: {TEXT_SM};
            color: {GRAY_700};
        }}
        .warning-banner b {{ color: {GRAY_900}; }}

        .llm-warning {{
            background: {GRAY_50};
            border-left: 3px solid {MCD_GOLD};
            border-radius: {RADIUS_SM};
            padding: {SPACE_2} {SPACE_3};
            margin: {SPACE_2} 0;
            font-size: {TEXT_SM};
            color: {GRAY_700};
        }}
        .llm-warning b {{ color: {GRAY_900}; }}

        .advanced-notice {{
            background: #fff;
            border: 1px solid {GRAY_200};
            border-left: 3px solid {GRAY_400};
            border-radius: {RADIUS_SM};
            padding: {SPACE_2} {SPACE_3};
            margin: {SPACE_2} 0 {SPACE_4} 0;
            font-size: {TEXT_SM};
            color: {GRAY_500};
        }}
        .advanced-notice b {{ color: {GRAY_700}; }}

        /* Streamlit 原生 stAlert 覆盖 */
        .stAlert {{
            border-radius: {RADIUS_MD};
            padding: {SPACE_3} {SPACE_4};
            font-size: {TEXT_SM};
        }}
        div[data-baseweb="notification"] {{ border-radius: {RADIUS_MD}; }}

        /* ===========================================================
           12. 企微气泡
           头像去品牌色 → 中性灰 + M 字母
           =========================================================== */
        .wechat-bubble-wrap {{
            display: flex;
            align-items: flex-start;
            gap: {SPACE_2};
            max-width: 380px;
            margin: {SPACE_2} auto;
        }}
        .wechat-bubble-wrap .wc-avatar {{
            width: 32px;
            height: 32px;
            border-radius: {RADIUS_SM};
            background: {GRAY_100};
            color: {GRAY_700};
            font-weight: 700;
            font-size: {TEXT_MD};
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .wechat-bubble {{
            background: #fff;
            border: 1px solid {GRAY_200};
            border-radius: {RADIUS_MD};
            padding: {SPACE_3};
            flex: 1;
        }}
        .wechat-bubble .wc-name {{
            font-weight: 500;
            font-size: {TEXT_XS};
            color: {GRAY_500};
            margin-bottom: {SPACE_1};
        }}
        .wechat-bubble .wc-title {{
            font-weight: 600;
            font-size: {TEXT_MD};
            color: {GRAY_900};
            margin-bottom: {SPACE_1};
            line-height: 1.4;
        }}
        .wechat-bubble .wc-body {{
            color: {GRAY_700};
            font-size: {TEXT_SM};
            line-height: 1.5;
            margin-bottom: {SPACE_2};
        }}
        .wechat-bubble .wc-meta {{
            font-size: {TEXT_XS};
            color: {GRAY_400};
            text-align: right;
        }}

        /* ===========================================================
           13. L1 实验预测 pill
           =========================================================== */
        .l1-pill {{
            display: inline-flex;
            align-items: center;
            gap: {SPACE_2};
            padding: {SPACE_1} {SPACE_2};
            margin: {SPACE_1} 0;
            background: {GRAY_50};
            border: 1px solid {MCD_GOLD};
            border-radius: {RADIUS_SM};
            font-size: {TEXT_SM};
        }}
        .l1-label {{ color: {GRAY_500}; font-weight: 500; }}
        .l1-value {{ color: {MCD_DARK_RED}; font-weight: 600; font-feature-settings: "tnum"; }}
        .l1-meta {{ color: {GRAY_400}; font-size: {TEXT_XS}; }}

        /* ===========================================================
           14. Streamlit 原生组件覆盖（消除 "Streamlit 一眼假"）
           =========================================================== */

        /* 14.1 左侧栏（v2 视觉：品牌块 + 6 导航，贴近参考稿） */
        [data-testid="stSidebar"] {{
            background: #fafbfc;
            border-right: 1px solid {GRAY_200};
            display: flex;
            flex-direction: column;
        }}
        /* 隐藏 Streamlit 默认的 "APP" 标题 */
        [data-testid="stSidebarHeader"] {{ display: none; }}

        /* 用 CSS order 把品牌块（注入在 stSidebarUserContent 里）提到最上方，
           紧随其后是 6 个自动发现的导航项 */
        [data-testid="stSidebarUserContent"] {{ order: 1; padding: 0; }}
        [data-testid="stSidebarNav"] {{ order: 2; padding: 0 18px; display: flex; flex-direction: column; gap: 8px; }}

        /* 品牌块（由 ui/sidebar_brand.render_brand 注入） */
        .sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 9px;
            height: 88px;
            padding: 0 20px;
            font-size: 15px;
            font-weight: 650;
            color: {GRAY_900};
            white-space: nowrap;
            border-bottom: 1px solid {GRAY_200};
        }}
        .sidebar-brand .m-logo {{
            color: {MCD_GOLD};
            font-size: 26px;
            line-height: 1;
            font-weight: 700;
            letter-spacing: -5px;
            transform: scaleX(.78);
            display: inline-block;
            flex: none;
            margin-right: 2px;
        }}
        .sidebar-brand .brand-text {{
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* 6 个导航项（贴近 v2 设计：44px 高 / 8px 圆角 / 浅灰 hover / 米色 active） */
        [data-testid="stSidebarNavLink"] {{
            height: 44px;
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 0 14px;
            border-radius: 8px;
            color: {GRAY_700};
            text-decoration: none;
            transition: background-color .15s ease, color .15s ease;
            font-weight: 500;
            font-size: 14px;
        }}
        [data-testid="stSidebarNavLink"]:hover {{
            background: {GRAY_100};
            color: {GRAY_900};
        }}
        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: #efede8;
            color: {GRAY_900};
        }}

        /* 侧栏底部占位 */
        .sidebar-bottom-mark {{
            margin-top: auto;
            padding: 18px 20px;
            border-top: 1px solid {GRAY_200};
            color: {GRAY_500};
            font-size: 12px;
            text-align: left;
        }}

        /* 14.2 Tab */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            border-bottom: 1px solid {GRAY_200};
        }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border-radius: 0;
            padding: {SPACE_2} {SPACE_4};
            color: {GRAY_500};
            font-size: {TEXT_BASE};
            font-weight: 500;
            border-bottom: 2px solid transparent;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: {MCD_RED};
            border-bottom-color: {MCD_RED};
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {GRAY_700};
        }}

        /* 14.3 DataFrame 表格 */
        .stDataFrame {{
            border: 1px solid {GRAY_200};
            border-radius: {RADIUS_MD};
            overflow: hidden;
        }}
        .stDataFrame [data-testid="stTable"] th {{
            background: {GRAY_50};
            color: {GRAY_700};
            font-weight: 600;
            font-size: {TEXT_SM};
        }}

        /* 14.4 Selectbox / Input / Textarea */
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextInput div[data-baseweb="input"] > div,
        .stTextArea div[data-baseweb="textarea"] > div,
        .stNumberInput div[data-baseweb="input"] > div {{
            border-radius: {RADIUS_SM};
            border-color: {GRAY_300};
        }}
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stTextInput div[data-baseweb="input"] > div:focus-within,
        .stTextArea div[data-baseweb="textarea"] > div:focus-within {{
            border-color: {MCD_RED};
            box-shadow: 0 0 0 1px {MCD_RED};
        }}

        /* 14.5 Slider */
        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background: {MCD_RED};
            border-color: {MCD_RED};
        }}

        /* 14.6 Checkbox */
        .stCheckbox label span[data-checked="true"] {{
            background-color: {MCD_RED};
            border-color: {MCD_RED};
        }}

        /* 14.7 Radio */
        .stRadio label[data-checked="true"] {{
            color: {GRAY_900};
            font-weight: 600;
        }}

        /* 14.8 标题层级 */
        h1, h2, h3, h4 {{
            color: {GRAY_900};
            font-weight: 600;
            letter-spacing: -0.2px;
        }}
        h1 {{ font-size: {TEXT_LG}; }}
        h2 {{ font-size: {TEXT_MD}; }}
        h3 {{ font-size: {TEXT_BASE}; }}

        /* 14.9 分隔线 */
        hr {{
            border-color: {GRAY_200};
            margin: {SPACE_3} 0;
        }}

        /* 14.10 进度条 */
        .stProgress > div > div > div > div {{
            background-color: {MCD_RED};
        }}

        /* 14.11 Caption */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {GRAY_500};
            font-size: {TEXT_SM};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )