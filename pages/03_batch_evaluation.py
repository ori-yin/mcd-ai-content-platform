# -*- coding: utf-8 -*-
r"""
pages/03_batch_evaluation.py — 03 批量评估（PRD §4.3 入口 C）

PRD §4.3：
- 上传 CSV 或 Excel
- 批量解析文案
- 批量规则检查
- 批量 CTR 参考或预测
- 批量优化建议
- 下载结果

实现：
- services/batch_evaluation_service.parse_batch_file / evaluate_batch / rows_to_csv_bytes
- services/rule_engine.check_one（每行规则）
- services/ctr_prediction_service.predict_one（每行 CTR 入口 B）

复用清单（Handoff §3）：
- services/batch_evaluation_service.*（Phase 4.2 新建）
- services/rule_engine.check_one
- services/ctr_prediction_service.predict_one
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from core.schemas import CHANNELS
from services.batch_evaluation_service import (
    parse_batch_file, evaluate_batch, rows_to_dataframe, rows_to_csv_bytes,
)
from ui.llm_status import render_banner
from ui.notice import render_advanced_notice
from ui.plotly_helpers import rate_value
from ui.styles import inject_base_css


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="03 批量评估",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()

# 进阶能力 banner（决策文档 Demo 范围 §2）
render_advanced_notice()

# LLM 未配置提示（业务确认 #10）
render_banner()

st.markdown(
    """
    <div class="mcd-header">
        <h1>03 批量评估</h1>
        <p>CSV / Excel 批量导入 · 规则 + CTR 批量评估 · 优化建议 · 结果导出</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# session_state
# ============================================================
def _init_state():
    defaults = {
        "batch_filename": "",
        "batch_df_raw": None,
        "batch_rows": [],
        "batch_eval_done": False,
        "batch_save_to_records": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ============================================================
# 渲染：上传 + 解析
# ============================================================
def _render_uploader():
    st.markdown("### 1 上传文件")
    st.caption(
        "支持 CSV / Excel。必填列：title + body + channel。兼容别名："
        "「标题」「headline」「内容」「content」等。"
    )
    uploaded = st.file_uploader(
        "选择文件",
        type=("csv", "xlsx", "xls"),
        accept_multiple_files=False,
    )
    if uploaded is None:
        st.session_state.batch_filename = ""
        st.session_state.batch_df_raw = None
        st.session_state.batch_eval_done = False
        return
    if uploaded.name == st.session_state.batch_filename and st.session_state.batch_df_raw is not None:
        return

    try:
        file_bytes = uploaded.read()
        df = parse_batch_file(file_bytes, uploaded.name)
    except Exception as e:
        st.error(f"解析失败：{e}")
        return

    st.session_state.batch_filename = uploaded.name
    st.session_state.batch_df_raw = df
    st.session_state.batch_rows = []
    st.session_state.batch_eval_done = False
    st.success(f"已读取 {len(df)} 行（{uploaded.name}）")


# ============================================================
# 渲染：预览 + 列名校验
# ============================================================
def _render_preview():
    df: Optional[pd.DataFrame] = st.session_state.batch_df_raw
    if df is None:
        return

    st.markdown("### 2 解析预览")
    cols1, cols2, cols3 = st.columns(3)
    cols1.metric("总行数", len(df))
    has_title = "title" in df.columns and df["title"].astype(str).str.len().gt(0).any()
    has_body = "body" in df.columns and df["body"].astype(str).str.len().gt(0).any()
    has_channel = "channel" in df.columns
    cols2.metric(
        "必备列",
        f"title {'✓' if has_title else '✗'} / body {'✓' if has_body else '✗'} / channel {'✓' if has_channel else '✗'}",
    )
    ch_set = set(df["channel"].dropna().astype(str).tolist()) if has_channel else set()
    valid_ch = ch_set & set(CHANNELS)
    cols3.metric("命中渠道数", f"{len(valid_ch)} / {len(ch_set) if ch_set else 0}")

    # 前 5 行预览
    st.caption("前 5 行预览：")
    preview_cols = [c for c in ("title", "body", "channel", "plan_type", "coupon") if c in df.columns]
    st.dataframe(df[preview_cols].head(5), use_container_width=True, hide_index=True)

    # 启动评估按钮
    can_eval = has_body and has_channel
    if not can_eval:
        st.markdown(
            '<div class="warning-banner">缺 body 或 channel 列，无法启动评估</div>',
            unsafe_allow_html=True,
        )
        return

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("开始批量评估", type="primary", use_container_width=True):
            _run_evaluation()
    with c2:
        st.session_state.batch_save_to_records = st.checkbox(
            "保存预测到 records.db（用于漂移监控 + 后续校准）",
            value=st.session_state.batch_save_to_records,
            help="勾选后，评估完成的每行 CTR 预测会落档 records.db（带 signature）。"
                 "下次上传真实 CTR 到 pages/05 时可自动 join 算误差。"
                 "默认关，按需开启（每行 1 条 record，1000 行 ≈ 1000 条）。",
        )


# ============================================================
# 评估主流程
# ============================================================
def _run_evaluation():
    df = st.session_state.batch_df_raw
    if df is None:
        return

    progress = st.progress(0.0, text="评估中…")
    status = st.empty()

    def _cb(done: int, total: int):
        progress.progress(done / total, text=f"评估中… {done}/{total}")
        status.caption(f"已完成 {done}/{total}")

    rows = evaluate_batch(df, ctr_mode="demo", progress_cb=_cb)
    progress.empty()
    status.empty()

    st.session_state.batch_rows = rows
    st.session_state.batch_eval_done = True
    st.success(f"评估完成：{len(rows)} 行")

    # Phase 22 D：用户勾选后把预测落档 records.db
    if st.session_state.get("batch_save_to_records"):
        try:
            from services.batch_evaluation_service import save_predictions_to_records
            n_saved = save_predictions_to_records(rows)
            if n_saved > 0:
                st.info(f"已保存 {n_saved} 条预测到 records.db（带 signature，下次上传真实 CTR 可 join）")
            else:
                st.warning("无可保存的预测（所有行都无 CTR 结果）")
        except Exception as e:
            st.error(f"保存到 records.db 失败：{e}")


# ============================================================
# 渲染：结果表格 + 汇总
# ============================================================
def _render_results():
    rows = st.session_state.batch_rows
    if not st.session_state.batch_eval_done or not rows:
        return

    st.markdown("### 3 评估结果")

    df = rows_to_dataframe(rows)

    # 汇总指标
    n = len(df)
    n_blocked = int((df["rule_fail_count"] > 0).sum())
    n_warn = int(((df["rule_fail_count"] == 0) & (df["rule_warn_count"] > 0)).sum())
    n_pass = int((df["rule_fail_count"] == 0) & (df["rule_warn_count"] == 0)).sum()
    n_err = int((df["error"] != "").sum())
    n_ctr_ok = int(df["ctr_pred"].notna().sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("总行数", n)
    c2.metric("规则通过", n_pass)
    c3.metric("规则提醒", n_warn)
    c4.metric("规则阻断", n_blocked)
    c5.metric("CTR 有效", n_ctr_ok)

    if n_err:
        st.markdown(
            f'<div class="warning-banner">{n_err} 行有解析错误，请检查必填列与渠道枚举。</div>',
            unsafe_allow_html=True,
        )

    # 渠道分布
    if "channel" in df.columns:
        ch_counts = df["channel"].value_counts().to_dict()
        if ch_counts:
            chips = " · ".join(f"{k} {v}" for k, v in ch_counts.items())
            st.caption(f"渠道分布：{chips}")

    # 结果表（行号 / 标题 / 渠道 / 规则状态 / CTR 区间 / 建议）
    display = df.copy()
    display["CTR 预测"] = display["ctr_pred"].apply(
        lambda v: rate_value(v) if pd.notna(v) else "—"
    )
    display["基准 CTR"] = display["ctr_baseline"].apply(
        lambda v: rate_value(v) if pd.notna(v) else "—"
    )
    display["置信度"] = display["ctr_confidence"].apply(
        lambda v: f"{v:.2f}" if pd.notna(v) else "—"
    )
    display = display.rename(columns={
        "row_index": "行号", "title": "标题", "body": "正文",
        "channel": "渠道", "rule_status": "规则",
        "rule_fail_count": "阻断数", "rule_warn_count": "提醒数",
        "ctr_result_type": "CTR 态", "error": "错误",
    })

    show_cols = [c for c in (
        "行号", "标题", "正文", "渠道", "规则",
        "阻断数", "提醒数", "CTR 预测", "基准 CTR", "置信度",
        "建议", "错误",
    ) if c in display.columns]

    # 还原建议列：rename 不影响 df（df 是原表），直接选原 df 的 suggestion 列填回 display
    if "suggestion" in df.columns and "建议" not in display.columns:
        display["建议"] = df["suggestion"]
    if show_cols:
        st.dataframe(
            display[[c for c in show_cols if c in display.columns]],
            use_container_width=True, hide_index=True, height=480,
        )

    # 下载 CSV
    csv_bytes = rows_to_csv_bytes(rows)
    st.download_button(
        "下载结果 CSV（UTF-8 BOM，Excel 可直接打开）",
        data=csv_bytes,
        file_name="batch_evaluation_result.csv",
        mime="text/csv",
        type="primary",
        use_container_width=False,
    )


# ============================================================
# 主流程
# ============================================================
def main():
    _render_uploader()
    if st.session_state.batch_df_raw is not None:
        st.markdown("---")
        _render_preview()
    if st.session_state.batch_eval_done:
        st.markdown("---")
        _render_results()


main()