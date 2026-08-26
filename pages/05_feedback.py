# -*- coding: utf-8 -*-
r"""
pages/05_feedback.py — 05 真实结果回流（PRD §4.5 第④步）

PRD v0.2 §步骤④ + docs/feedback-ctr.md §P1：
- CSV / Excel 上传真实投放结果
- 必填列：task_signature + channel + reach_success + click_count
- 兼容别名：签名/渠道/触达/点击 等
- 校验失败拒收，校验通过写入 data/feedback.db
- 列表 + 按 signature 聚合展示（去 docs/feedback-ctr.md §5 P4 "UI 显示反哺状态"做基础）

约束（CLAUDE.md §4）：
- 页面层不直 import 旧项目（不适用此处，纯新模块）
- 不散落数据库操作（走 repositories/feedback_repository）
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from services.feedback_service import import_feedback
from repositories import feedback_repository
from ui.notice import render_advanced_notice, render_ctr_feedback_notice
from ui.plotly_helpers import rate_value
from ui.styles import inject_base_css


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="05 真实结果回流",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()

# 进阶能力 + CTR 反哺 banner（决策文档 Demo 范围 §2 / §3）
render_advanced_notice()
render_ctr_feedback_notice()

st.markdown(
    """
    <div class="mcd-header">
        <h1>05 真实结果回流</h1>
        <p>真实投放数据回流 · 校验入库 · 按 signature 聚合 · CTR 反哺闭环数据源</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 渲染：上传区
# ============================================================
def _render_uploader():
    st.markdown("### 1 上传回流数据")
    st.caption(
        "支持 CSV / Excel。必填列：task_signature + channel + reach_success + click_count。"
        "兼容别名：签名 / 渠道 / 触达成功 / 点击人次。"
        "如缺 task_signature，按 channel + coupon + plan_type 自动兜底生成。"
    )
    uploaded = st.file_uploader(
        "选择文件",
        type=("csv", "xlsx", "xls"),
        accept_multiple_files=False,
        key="fb_upload",
    )
    source_label = st.text_input(
        "来源标签（可选）",
        value="",
        placeholder="例：Chiikawa松饼堡活动 8 月回流",
        key="fb_source",
    )

    if uploaded is None:
        return
    if st.button("导入并校验", type="primary", key="fb_import_btn"):
        _do_import(uploaded, source_label)


def _do_import(uploaded, source_label: str):
    file_bytes = uploaded.read()
    with st.spinner("校验中…"):
        result = import_feedback(
            file_bytes, filename=uploaded.name,
            source_label=source_label or uploaded.name,
        )
    errs = result.get("errors") or []
    n = result.get("n", 0)
    if errs:
        st.markdown(
            f'<div class="warning-banner"><b>校验失败</b>：{len(errs)} 条问题（前 5 条）<br>'
            + "<br>".join(errs[:5])
            + "</div>",
            unsafe_allow_html=True,
        )
        return
    st.success(f"已导入 {n} 条回流数据")


# ============================================================
# 渲染：汇总 + 列表
# ============================================================
def _render_summary():
    total = feedback_repository.count()
    if total == 0:
        st.markdown("---")
        st.markdown(
            '<div class="warning-banner">暂无回流数据。先在上方上传。</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("---")
    st.markdown("### 2 数据汇总")

    agg = feedback_repository.aggregate_by_signature()
    n_sig = len(agg)

    total_reach = sum(v["reach"] for v in agg.values())
    total_click = sum(v["click"] for v in agg.values())
    overall_ctr = round(total_click / total_reach * 100, 2) if total_reach else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总记录数", total)
    c2.metric("独立 signature", n_sig)
    c3.metric("总触达", f"{total_reach:,}")
    c4.metric("整体 CTR", f"{overall_ctr:.2f}%")

    # 按 signature 聚合表
    rows = []
    for sig, v in agg.items():
        rows.append({
            "signature": sig,
            "channel": v["channel"],
            "n_records": v["n_records"],
            "触达": v["reach"],
            "点击": v["click"],
            "加权CTR%": v["ctr"],
            "订单": v["order_n"],
            "日期范围": f"{v['date_min'] or '—'} ~ {v['date_max'] or '—'}",
        })
    df_agg = pd.DataFrame(rows).sort_values("触达", ascending=False).reset_index(drop=True)

    st.markdown("**按 signature 聚合**")
    st.dataframe(df_agg, use_container_width=True, hide_index=True, height=360)

    # 列表（前 50 条详情）
    st.markdown("---")
    st.markdown("### 3 最近记录（前 50 条）")
    rows = feedback_repository.list_all(limit=50)
    df_list = pd.DataFrame(rows)
    if "id" in df_list.columns:
        df_list = df_list.drop(columns=["id"])
    st.dataframe(df_list, use_container_width=True, hide_index=True, height=360)

    # 与 records.db 关联情况
    st.markdown("---")
    st.markdown("### 4 与生成记录 join 情况")
    _render_join_status(agg)


def _render_join_status(agg: dict):
    """检查 feedback.signature 与 generation_records.signature 的 join 命中情况。"""
    try:
        from repositories import sqlite_repository
        rows = sqlite_repository.list_all(limit=10000)
        gen_sigs = {r.get("signature") for r in rows if r.get("signature")}
        feedback_sigs = set(agg.keys())

        joined = feedback_sigs & gen_sigs
        only_feedback = feedback_sigs - gen_sigs
        only_gen = gen_sigs - feedback_sigs

        c1, c2, c3 = st.columns(3)
        c1.metric("回流 signature 数", len(feedback_sigs))
        c2.metric("已 join 生成记录", len(joined))
        c3.metric("生成侧未回流", len(only_gen))

        if only_feedback:
            st.caption(
                f"{len(only_feedback)} 个 signature 没有对应生成记录"
                f"（可能手填或人工发放）"
            )
    except Exception as e:
        st.caption(f"join 检查失败：{e}")


# ============================================================
# 主流程
# ============================================================
def main():
    _render_uploader()
    _render_summary()


main()