# -*- coding: utf-8 -*-
r"""
pages/04_historical_insights.py — 04 历史洞察（PRD §4.4）

PRD §4.4 七个分析模块：
1. 高效 Plan 排行       — services.analytics.high_effort_plans.rank_plans
2. 高低表现词          — services.text_analyzer.word_frequency + compare_token
3. Emoji 表现         — services.text_analyzer.emoji_frequency
4. 标题字数表现        — title_len 切桶（自有轻量聚合）
5. 历史相似内容        — services.analytics.similarity.find_similar_plans
6. 每日趋势           — services.analytics.daily_trend.daily_aggregate + daily_summary
7. Owner 对比         — services.analytics.owner_compare.owner_compare

数据源：data_loader.build() 后的 DataFrame（必填触达成功 + 点击人次）。
无数据时所有 tab 显示"请上传历史计划数据"。

CLAUDE.md §9：
- CTR 一律 plan 加权
- 默认 min_plans=3
- 样本量透明：每词对比显示 n_plans + n_records + 触达数
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from services.data_loader import build
from services.text_analyzer import (
    add_tokens, word_frequency, emoji_frequency, compare_token,
)
from services.analytics.high_effort_plans import rank_plans
from services.analytics.similarity import find_similar_plans
from services.analytics.daily_trend import daily_aggregate, daily_summary
from services.analytics.owner_compare import owner_compare
from ui.plotly_helpers import rate_value
from ui.styles import inject_base_css


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="04 历史洞察",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()

st.markdown(
    """
    <div class="mcd-header">
        <h1>04 历史洞察</h1>
        <p>高效 Plan 排行 · 高低表现词 · Emoji · 标题字数 · 历史相似 · 每日趋势 · Owner 对比</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# session_state
# ============================================================
def _init_state():
    defaults = {
        "ins_filename": "",
        "ins_df": None,
        "ins_meta": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ============================================================
# 渲染：上传
# ============================================================
def _render_uploader():
    st.markdown("### 1 上传历史数据")
    st.caption(
        "支持 Excel（含「触达成功」「点击人次」必填列）。"
        "列名模糊匹配（兼容「发送日期/日期」「渠道/channel」等）。"
    )
    uploaded = st.file_uploader(
        "选择历史数据文件",
        type=("xlsx", "xls", "csv"),
        accept_multiple_files=False,
    )
    if uploaded is None:
        st.session_state.ins_filename = ""
        st.session_state.ins_df = None
        st.session_state.ins_meta = None
        return
    if uploaded.name == st.session_state.ins_filename and st.session_state.ins_df is not None:
        return

    file_bytes = uploaded.read()
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(__import__("io").BytesIO(file_bytes))
            meta = {"n_rows": len(df), "sheet_name": "csv", "all_sheets": ["csv"]}
        else:
            df, meta = build(file_bytes)
    except Exception as e:
        st.error(f"解析失败：{e}")
        return

    # 加 _tokens 列（给相似检索 / 词频用）
    try:
        df = add_tokens(df)
    except Exception as e:
        st.warning(f"分词失败（部分功能受限）：{e}")

    st.session_state.ins_filename = uploaded.name
    st.session_state.ins_df = df
    st.session_state.ins_meta = meta
    st.success(f"已加载 {len(df)} 行（{uploaded.name}）")


def _render_overview():
    df: Optional[pd.DataFrame] = st.session_state.ins_df
    meta = st.session_state.ins_meta or {}
    if df is None:
        return

    st.markdown("### 2 数据概览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总记录数", meta.get("n_rows", len(df)))
    has_copy = meta.get("n_has_copy")
    c2.metric("含文案记录", has_copy if has_copy is not None else "—")
    channels = meta.get("channels") or []
    c3.metric("渠道数", len(channels))
    if "date_min" in meta and meta["date_min"]:
        c4.metric("日期范围", f"{meta['date_min']} ~ {meta['date_max']}")

    if channels:
        st.caption("渠道：" + " · ".join(channels))


# ============================================================
# Tab 1: 高效 Plan 排行
# ============================================================
def _render_rank_plans(df: pd.DataFrame):
    st.markdown("**按 plan 加权 CTR 降序排列**（plan 触达 < 1000 自动过滤）")
    min_reach = st.slider(
        "最小触达过滤", min_value=100, max_value=10000, value=1000, step=100,
        key="rank_min_reach",
    )
    top_n = st.number_input(
        "显示前 N 条", min_value=5, max_value=200, value=30, step=5,
        key="rank_top_n",
    )

    out = rank_plans(df, min_reach=min_reach, top_n=int(top_n))
    if out.empty:
        st.markdown(
            '<div class="warning-banner">无符合条件的高效 Plan（调低最小触达过滤或上传更多数据）</div>',
            unsafe_allow_html=True,
        )
        return

    # 展示
    show = out.copy()
    show["加权CTR%"] = show["加权CTR%"].apply(lambda v: f"{v:.2f}%")
    st.dataframe(show, use_container_width=True, hide_index=True, height=480)


# ============================================================
# Tab 2: 高低表现词
# ============================================================
def _render_word_freq(df: pd.DataFrame):
    col1, col2 = st.columns([1, 1])
    with col1:
        min_plans = st.slider("最少 plan 数", 1, 50, 3, key="wf_min_plans")
        top_n = st.number_input("前 N 个词", 5, 200, 50, 5, key="wf_top_n")

    wf = word_frequency(df, min_plans=min_plans).head(int(top_n))
    if wf.empty:
        st.markdown('<div class="warning-banner">词频为空（数据不足或 _tokens 未生成）</div>',
                    unsafe_allow_html=True)
        return

    # 高效词（差值 > 0）/ 低效词（差值 < 0）
    high = wf[wf["差值"] > 0].head(15)
    low = wf[wf["差值"] < 0].head(15)

    st.markdown("**高效词 Top15**（差值 > 0）")
    if not high.empty:
        st.dataframe(high, use_container_width=True, hide_index=True)

    st.markdown("**低效词 Top15**（差值 < 0）")
    if not low.empty:
        st.dataframe(low, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**单词对比**（含 vs 不含的 plan 加权 CTR）")
    sel_word = st.selectbox(
        "选词对比", options=wf[wf.columns[0]].tolist()[:50], index=0,
        key="wf_compare_sel",
    )
    if sel_word:
        cmp = compare_token(df, sel_word)
        if cmp:
            c1, c2, c3 = st.columns(3)
            reach_with = cmp.get("reach_with", 0)
            reach_without = cmp.get("reach_without", 0)
            c1.metric("含该词 plan 触达", f"{reach_with:,}")
            c2.metric("不含 plan 触达", f"{reach_without:,}")
            c3.metric(
                "差值（pp）",
                f"{cmp.get('delta_pp', 0):.2f}",
            )
            c4, c5 = st.columns(2)
            c4.metric("含 CTR", f"{cmp.get('ctr_with', 0):.2f}%")
            c5.metric("不含 CTR", f"{cmp.get('ctr_without', 0):.2f}%")
            st.caption(
                f"含该词 plan {cmp.get('n_plans_with', 0)} 个 / "
                f"不含 plan {cmp.get('n_plans_without', 0)} 个"
            )


# ============================================================
# Tab 3: Emoji 表现
# ============================================================
def _render_emoji(df: pd.DataFrame):
    min_plans = st.slider("最少 plan 数", 1, 50, 3, key="ef_min_plans")
    top_n = st.number_input("前 N 个 emoji", 5, 100, 20, 5, key="ef_top_n")

    ef = emoji_frequency(df, min_plans=min_plans).head(int(top_n))
    if ef.empty:
        st.markdown('<div class="warning-banner">emoji 数据为空</div>', unsafe_allow_html=True)
        return
    st.markdown("**emoji 表现排行**")
    st.dataframe(ef, use_container_width=True, hide_index=True, height=400)


# ============================================================
# Tab 4: 标题字数表现
# ============================================================
def _render_title_length(df: pd.DataFrame):
    """标题字数切桶，看加权 CTR。"""
    if "标题" not in df.columns or "Plan ID" not in df.columns:
        st.markdown(
            '<div class="warning-banner">缺「标题」或「Plan ID」列</div>',
            unsafe_allow_html=True,
        )
        return

    work = df.copy()
    work["_title_len"] = work["标题"].astype(str).str.len()
    # 切桶：0 / 1-5 / 6-10 / 11-15 / 16-20 / 21+
    bins = [-1, 0, 5, 10, 15, 20, 1000]
    labels = ["空", "1-5", "6-10", "11-15", "16-20", "21+"]
    work["_bucket"] = pd.cut(work["_title_len"], bins=bins, labels=labels)

    g = work.groupby("_bucket", dropna=False, observed=True)
    rows = []
    for bucket, sub in g:
        reach = int(sub["触达成功"].sum())
        click = int(sub["点击人次"].sum())
        if reach == 0:
            continue
        n_plans = int(sub["Plan ID"].nunique()) if "Plan ID" in sub.columns else 0
        rows.append({
            "字数桶": str(bucket),
            "n_plans": n_plans,
            "触达成功": reach,
            "点击": click,
            "加权CTR%": round(click / reach * 100, 2),
        })

    if not rows:
        st.markdown('<div class="warning-banner">无有效标题字数数据</div>', unsafe_allow_html=True)
        return
    out = pd.DataFrame(rows).sort_values("加权CTR%", ascending=False).reset_index(drop=True)
    st.markdown("**标题字数桶 CTR**（plan 加权）")
    st.dataframe(out, use_container_width=True, hide_index=True)


# ============================================================
# Tab 5: 历史相似内容
# ============================================================
def _render_similar(df: pd.DataFrame):
    st.caption("输入查询文案，从历史 plan 中找 Top-K 相似（TF-IDF + 余弦）")
    c1, c2 = st.columns(2)
    with c1:
        q_title = st.text_input("查询标题", value="", key="sim_title")
    with c2:
        q_body = st.text_input("查询正文", value="", key="sim_body")
    top_k = st.slider("Top-K", 1, 20, 5, key="sim_topk")

    if not (q_title or q_body):
        st.info("填入查询文案后显示相似结果")
        return

    sim = find_similar_plans(df, q_title, q_body, top_k=int(top_k))
    if sim is None or sim.empty:
        st.markdown(
            '<div class="warning-banner">未找到相似 Plan（数据不足或 _tokens 未生成）</div>',
            unsafe_allow_html=True,
        )
        return

    show_cols = [c for c in ("plan_id", "plan_name", "channel", "ctr", "similarity") if c in sim.columns]
    if show_cols:
        st.dataframe(sim[show_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(sim, use_container_width=True, hide_index=True)


# ============================================================
# Tab 6: 每日趋势
# ============================================================
def _render_daily_trend(df: pd.DataFrame):
    summary = daily_summary(df)
    if not summary:
        st.markdown(
            '<div class="warning-banner">无有效日期数据</div>',
            unsafe_allow_html=True,
        )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总触达", f"{summary.get('总触达', 0):,}")
    c2.metric("总点击", f"{summary.get('总点击', 0):,}")
    c3.metric("整体 CTR", f"{summary.get('整体CTR%', 0):.2f}%")
    c4.metric("活跃天数", summary.get("活跃天数", 0))

    peak = summary.get("峰值日")
    trough = summary.get("谷值日")
    if peak and trough:
        st.caption(
            f"峰值日：{peak}（{summary.get('峰值CTR%', 0):.2f}%）"
            f" · 谷值日：{trough}（{summary.get('谷值CTR%', 0):.2f}%）"
            f" · 日均 CTR {summary.get('日均CTR%', 0):.2f}%"
        )

    st.markdown("---")

    by_channel = st.checkbox("按渠道拆分", value=False, key="daily_by_channel")
    out = daily_aggregate(df, channel_col="渠道" if by_channel else None)
    if out.empty:
        st.markdown('<div class="warning-banner">聚合为空</div>', unsafe_allow_html=True)
        return

    show_cols = [c for c in (
        "date", "channel", "n_records", "触达成功", "点击", "加权CTR%", "周环比%",
    ) if c in out.columns]
    st.dataframe(out[show_cols], use_container_width=True, hide_index=True, height=480)


# ============================================================
# Tab 7: Owner 对比
# ============================================================
def _render_owner(df: pd.DataFrame):
    c1, c2 = st.columns(2)
    with c1:
        min_plans = st.slider("最少 plan 数", 1, 50, 3, key="oc_min_plans")
    with c2:
        min_reach = st.slider("最少触达", 100, 100000, 1000, 100, key="oc_min_reach")

    out = owner_compare(df, min_plans=int(min_plans), min_reach=int(min_reach))
    if out.empty:
        st.markdown(
            '<div class="warning-banner">无有效 owner 数据</div>',
            unsafe_allow_html=True,
        )
        return
    st.dataframe(out, use_container_width=True, hide_index=True, height=480)


# ============================================================
# 渲染：7 个 Tab
# ============================================================
def _render_insights():
    df: Optional[pd.DataFrame] = st.session_state.ins_df
    if df is None:
        return

    tabs = st.tabs([
        "高效 Plan 排行",
        "高低表现词",
        "Emoji 表现",
        "标题字数",
        "历史相似",
        "每日趋势",
        "Owner 对比",
    ])
    with tabs[0]:
        _render_rank_plans(df)
    with tabs[1]:
        _render_word_freq(df)
    with tabs[2]:
        _render_emoji(df)
    with tabs[3]:
        _render_title_length(df)
    with tabs[4]:
        _render_similar(df)
    with tabs[5]:
        _render_daily_trend(df)
    with tabs[6]:
        _render_owner(df)


# ============================================================
# 主流程
# ============================================================
def main():
    _render_uploader()
    if st.session_state.ins_df is not None:
        _render_overview()
        st.markdown("---")
        _render_insights()


main()