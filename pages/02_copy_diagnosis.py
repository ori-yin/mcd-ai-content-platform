# -*- coding: utf-8 -*-
r"""
pages/02_copy_diagnosis.py — 02 文案诊断（PRD §4.2 入口 B）

PRD §4.0 入口 B：用户手动输入 title + body + channel，无需 AI 生成，立刻调 CTR Adapter。
CTR Adapter 必须脱离 AI 生成上下文独立工作（PRD §4.0 末段）。

流程：
1. 输入标题 / 正文 / 渠道
2. 本地规则检查（rule_engine.check_one）
3. 词语表现参考（copy_analysis_service.diagnose）
4. 历史相似 Plan（similarity_service.find_similar）
5. CTR 入口 B（ctr_prediction_service.predict_one）
6. AI 改写候选（copy_rewrite prompt + llm_adapter.call_llm）

复用清单（Handoff §3）：
- services/rule_engine.check_one          → 单条规则入口
- services/copy_analysis_service.diagnose  → 词语表现
- services/similarity_service.find_similar → 历史相似
- services/ctr_prediction_service.predict_one → CTR 入口 B
- prompts/copy_rewrite.* + adapters/llm_adapter.call_llm → AI 改写
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

from core.schemas import (
    CHANNELS, RuleResult, PredictionResult,
    SEVERITY_FAIL, SEVERITY_WARN, SEVERITY_PASS,
)
from services.rule_engine import load_rules, check_one
from services.copy_analysis_service import diagnose
from services.similarity_service import find_similar, summarize_similar
from services.ctr_prediction_service import predict_one
from prompts import copy_rewrite
from adapters.llm_adapter import call_llm
from ui.llm_status import render_banner
from ui.notice import render_advanced_notice
from ui.plotly_helpers import rate_value
from ui.styles import inject_base_css


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="02 文案诊断",
    page_icon="🔍",
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
        <h1>02 文案诊断</h1>
        <p>单条文案诊断 · 本地规则 · 词语表现 · 历史相似 · CTR 入口 B · AI 改写</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# session_state
# ============================================================
def _init_state():
    defaults = {
        "diag_title": "",
        "diag_body": "",
        "diag_channel": "APP Push",
        "diag_action": "regen",
        "diag_rule": None,           # RuleResult
        "diag_diagnose": None,       # dict
        "diag_similar_summary": {},
        "diag_similar_df": None,
        "diag_ctr": None,            # PredictionResult
        "diag_rewrites": [],         # list[dict]
        "diag_rewrite_error": "",
        "diag_signatures": "",       # 上次评估签名（字段变更检测）
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ============================================================
# 工具
# ============================================================
def _signature(title: str, body: str, channel: str) -> str:
    """诊断输入签名。"""
    return f"{channel}|{title.strip()}|{body.strip()}"


def _confidence_label(confidence: Optional[float]) -> str:
    """置信度 → 等级标签（PRD v0.2 §5.3 口径 A）。"""
    if confidence is None:
        return "未知"
    if confidence >= 0.75:
        return "高"
    if confidence >= 0.50:
        return "中"
    return "低"


# ============================================================
# 渲染：输入区
# ============================================================
def _render_input():
    st.markdown("### 1 输入文案")
    st.caption("选渠道，填标题和正文。本页不依赖 AI 生成，可直接调 CTR Adapter。")

    cur_title = st.session_state.diag_title
    cur_body = st.session_state.diag_body
    cur_channel = st.session_state.diag_channel

    with st.form("diag_input", clear_on_submit=False):
        channel = st.selectbox(
            "投放渠道 *", CHANNELS,
            index=CHANNELS.index(cur_channel) if cur_channel in CHANNELS else 0,
        )
        title = st.text_input(
            "标题（短信 / 企微 1v1 可空）",
            value=cur_title,
            max_chars=200,
            placeholder="例：新品小卡来啦",
        )
        body = st.text_area(
            "正文 *",
            value=cur_body,
            height=120,
            max_chars=500,
            placeholder="例：新品优惠 + 限定小卡，点击查看详情。",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button(
                "开始诊断", type="primary", use_container_width=True,
            )
        with col2:
            action = st.selectbox(
                "AI 改写策略（可选）",
                ("regen", "shorten", "direct", "scene", "cta", "safer"),
                index=("regen", "shorten", "direct", "scene", "cta", "safer").index(
                    st.session_state.diag_action
                ),
                help="选择下方「AI 改写」按钮时生效",
            )

    if submitted:
        if not body.strip():
            st.error("正文不能为空")
            return
        st.session_state.diag_title = title
        st.session_state.diag_body = body
        st.session_state.diag_channel = channel
        st.session_state.diag_action = action
        # 触发诊断
        _run_diagnosis()


# ============================================================
# 诊断主流程
# ============================================================
def _run_diagnosis():
    title = st.session_state.diag_title
    body = st.session_state.diag_body
    channel = st.session_state.diag_channel

    channel_rules, brand_rules = load_rules()

    # 1. 规则
    rule_result = check_one(title, body, channel, channel_rules, brand_rules)
    st.session_state.diag_rule = rule_result

    # 2. 词语表现
    diag_result = diagnose(title, body, channel=channel)
    st.session_state.diag_diagnose = diag_result

    # 3. 历史相似
    sim_df = find_similar(title, body, channel)
    st.session_state.diag_similar_df = sim_df
    st.session_state.diag_similar_summary = summarize_similar(sim_df)

    # 4. CTR 入口 B
    ctr_mode = "demo"  # 默认 demo；Phase 5 接 LLM 时按环境变量切
    st.session_state.diag_ctr = predict_one(
        title=title, body=body, channel=channel, mode=ctr_mode,
    )

    # 5. 清空改写
    st.session_state.diag_rewrites = []
    st.session_state.diag_rewrite_error = ""
    st.session_state.diag_signatures = _signature(title, body, channel)


# ============================================================
# 渲染：左栏（规则 + 词语表现）
# ============================================================
def _render_left_column():
    st.markdown("### 2 本地诊断")

    rule: Optional[RuleResult] = st.session_state.diag_rule
    if rule is None:
        st.info("请先在左侧输入文案并点击「开始诊断」。")
        return

    # 规则总览
    status_label = {"pass": "全部通过", "warn": "有提醒", "fail": "存在阻断"}.get(
        rule.status, rule.status,
    )
    st.markdown(
        f'<div class="kpi-tile">'
        f'<div class="label">规则状态</div>'
        f'<div class="value">{status_label}</div>'
        f'<div class="sub">通过 {len(rule.passes)} / 提醒 {len(rule.warns)} / 阻断 {len(rule.fails)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if rule.has_blocking:
        st.markdown(
            '<div class="warning-banner"><b>存在阻断项</b>，请先修改后再次评估。</div>',
            unsafe_allow_html=True,
        )

    st.markdown("**规则项**")
    for it in rule.items:
        cls = {
            SEVERITY_PASS: "rule-pass",
            SEVERITY_WARN: "rule-warn",
            SEVERITY_FAIL: "rule-fail",
        }.get(it.severity, "rule-pass")
        sug = f"<br><small>建议：{it.suggestion}</small>" if it.suggestion else ""
        st.markdown(
            f'<div class="{cls}"><b>[{it.severity.upper()}]</b> '
            f'<b>{it.category}</b>：{it.message}{sug}</div>',
            unsafe_allow_html=True,
        )

    # 词语表现
    st.markdown("---")
    st.markdown("**词语表现**")
    diag = st.session_state.diag_diagnose or {}
    if not diag:
        st.caption("无")
        return
    score = diag.get("score")
    grade = diag.get("grade", "—")
    if score is not None:
        st.markdown(
            f'<div class="kpi-tile">'
            f'<div class="label">文案评分</div>'
            f'<div class="value">{score} / 100 · {grade}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    d = diag.get("diag") or {}
    hit = d.get("hit_words") or []
    miss = (d.get("miss_top") or [])[:8]
    if hit:
        st.caption(f"命中高效词：{', '.join(hit)}")
    if miss:
        st.caption(f"未出现的高频高 CTR 词：{', '.join(miss)}")
    if not hit and not miss:
        st.caption("无历史高频词数据（需上传历史计划）")

    problems = diag.get("problems") or []
    if problems:
        st.markdown("**问题清单**")
        for p in problems[:5]:
            msg = p.get("label", "")
            so_what = p.get("so_what", "")
            sug = p.get("suggested", "")
            sug_html = f"<br><small>建议：{sug}</small>" if sug else ""
            so_html = f"<br><small>{so_what}</small>" if so_what else ""
            st.markdown(
                f'<div class="rule-warn"><b>{msg}</b>{so_html}{sug_html}</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# 渲染：中栏（渠道预览 + CTR 入口 B）
# ============================================================
def _render_middle_column():
    st.markdown("### 3 渠道预览与 CTR 参考")

    if st.session_state.diag_rule is None:
        st.info("诊断后此处显示渠道预览和 CTR 参考。")
        return

    title = st.session_state.diag_title
    body = st.session_state.diag_body
    channel = st.session_state.diag_channel
    _render_channel_preview(channel, title, body)

    st.markdown("---")
    _render_ctr_card(st.session_state.diag_ctr)


def _render_channel_preview(channel: str, title: str, body: str):
    st.markdown("**渠道预览**")
    show_title = title or "（无标题）"

    if channel == "APP Push":
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">'
            f'McDonald\'s · {datetime.now().strftime("%H:%M")}</div>'
            f'<div class="pv-title">{show_title}</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">APP Push · 点击查看</div>'
            f'</div>'
        )
    elif channel == "企微 1v1":
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.6;margin-bottom:0.4rem;">麦当劳客服 · 现在</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">企微 1v1 · 立即查看</div>'
            f'</div>'
        )
    elif channel == "短信":
        seg = max(1, (len(body) + 69) // 70)
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">106xxxxxxxx</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">短信 · {len(body)} 字 / {seg} 段</div>'
            f'</div>'
        )
    elif channel == "站内信":
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">'
            f'McDonald\'s App · 消息中心</div>'
            f'<div class="pv-title">{show_title}</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">站内信 · 查看详情</div>'
            f'</div>'
        )
    else:
        preview_html = '<div class="warning-banner">该渠道预览待实现</div>'

    st.markdown(preview_html, unsafe_allow_html=True)


def _render_ctr_card(ctr: Optional[PredictionResult]):
    st.markdown("**CTR 参考结果**")
    if ctr is None:
        st.markdown(
            '<div class="warning-banner">CTR 参考：暂不可用</div>',
            unsafe_allow_html=True,
        )
        return

    if ctr.result_type == "unavailable":
        st.markdown(
            f'<div class="warning-banner">CTR 参考：暂不可用；原因：{ctr.error or "无足够基准数据"}</div>',
            unsafe_allow_html=True,
        )
        return

    parts = []
    if ctr.pred_ctr is not None:
        parts.append(f"**预测 CTR**：{rate_value(ctr.pred_ctr)}")
    if ctr.baseline_ctr is not None:
        parts.append(f"**历史基准**：{rate_value(ctr.baseline_ctr)}")
    if ctr.pred_ctr is not None and ctr.baseline_ctr is not None and ctr.baseline_ctr > 0:
        diff_pp = (ctr.pred_ctr - ctr.baseline_ctr) * 100
        sign = "+" if diff_pp >= 0 else ""
        parts.append(f"**相对基准**：{sign}{diff_pp:.2f} 个百分点")
    if ctr.confidence is not None:
        label = _confidence_label(ctr.confidence)
        parts.append(f"**置信度**：{label}（基于历史样本）")

    st.markdown(
        f'<div class="kpi-tile">'
        f'<div class="label">状态：{ctr.label}</div>'
        + "".join(f'<div>{p}</div>' for p in parts)
        + '</div>',
        unsafe_allow_html=True,
    )
    if ctr.suggestion:
        st.caption(f"建议：{ctr.suggestion}")


# ============================================================
# 渲染：右栏（历史相似 + AI 改写）
# ============================================================
def _render_right_column():
    st.markdown("### 4 历史相似 & AI 改写")

    if st.session_state.diag_rule is None:
        st.info("诊断后此处显示相似历史内容和 AI 改写候选。")
        return

    # 历史相似
    summary = st.session_state.diag_similar_summary or {}
    sim_count = summary.get("count", 0)
    avg_ctr = summary.get("avg_ctr")
    st.markdown("**历史相似 Plan**")
    if sim_count == 0:
        st.markdown(
            '<div class="warning-banner">未找到相似历史 Plan（需上传历史计划文件）</div>',
            unsafe_allow_html=True,
        )
    else:
        avg_ctr_html = f"{rate_value(avg_ctr / 100)}" if avg_ctr is not None else "—"
        st.markdown(
            f'<div class="kpi-tile">'
            f'<div class="label">相似 Plan 数</div>'
            f'<div class="value">{sim_count}</div>'
            f'<div class="sub">平均 CTR：{avg_ctr_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        df = st.session_state.diag_similar_df
        if df is not None and not df.empty:
            display_cols = [c for c in ("title", "body", "ctr", "similarity") if c in df.columns]
            if display_cols:
                st.dataframe(df[display_cols].head(3), use_container_width=True, hide_index=True)

    st.markdown("---")

    # AI 改写
    st.markdown("**AI 改写候选**")
    if st.button(
        f"生成改写（{st.session_state.diag_action}）",
        type="secondary",
        use_container_width=True,
    ):
        _run_rewrite()

    err = st.session_state.diag_rewrite_error
    if err:
        st.markdown(
            f'<div class="warning-banner">改写失败：{err}</div>',
            unsafe_allow_html=True,
        )
    rewrites = st.session_state.diag_rewrites or []
    for i, rw in enumerate(rewrites, 1):
        t = rw.get("title", "")
        b = rw.get("body", "")
        reason = rw.get("reason", "")
        st.markdown(
            f'<div class="candidate-card">'
            f'<div class="cand-header">改写 {i}</div>'
            f'<div class="cand-title">{t or "（无标题）"}</div>'
            f'<div class="cand-body">{b}</div>'
            + (f'<div class="cand-body" style="margin-top:0.4rem;font-size:0.82em;'
               f'color:#888;">理由：{reason}</div>' if reason else "")
            + '</div>',
            unsafe_allow_html=True,
        )


def _run_rewrite():
    """调 LLM 做单条改写（PRD §7.5）。无 API Key → Demo 占位。"""
    title = st.session_state.diag_title
    body = st.session_state.diag_body
    channel = st.session_state.diag_channel
    action = st.session_state.diag_action

    channel_rules, _brand_rules = load_rules()
    channel_max = (channel_rules.get("channels") or {}).get(channel, {})

    # 拼 local_diagnose（LLM 需要）
    diag = st.session_state.diag_diagnose or {}
    local = (diag.get("diag") or {}).copy()
    local.setdefault("hit_words", [])
    local.setdefault("miss_top", [])
    local.setdefault("emoji_count", 0)

    # Demo 模式：本地拼 2 条改写占位（PRD §19.1）
    # Phase 17 修 bug：原来 `from core.config import settings` 模块不存在
    # 导致 router 永远为 None、页面永远走 Demo。改成走 ui.llm_status 真实判断。
    from core.llm_gateway import ProviderRouter
    from ui.llm_status import load_config
    router = None
    try:
        cfg = load_config()  # {provider, base_url, model, api_key} dict
        if cfg.get("api_key"):
            router = ProviderRouter(
                provider=cfg["provider"],
                api_key=cfg["api_key"],
                model=cfg["model"],
            )
    except Exception:
        router = None

    if router is None or not getattr(router, "api_key", None):
        # Demo 占位：3 条差异化改写
        st.session_state.diag_rewrites = [
            {
                "title": f"{channel}改写1",
                "body": f"【改写】{body[:40]}… 立即查看。",
                "reason": f"Demo 占位：{action} 策略示例 1",
            },
            {
                "title": f"{channel}改写2",
                "body": f"限时优惠：{body[:30]}… 别错过。",
                "reason": f"Demo 占位：{action} 策略示例 2",
            },
        ]
        st.session_state.diag_rewrite_error = ""
        return

    # LLM 模式
    user_prompt = copy_rewrite.build_user_prompt(
        action=action, title=title, body=body,
        channel_max=channel_max, extra_context="",
    )
    full_prompt = (
        f"{copy_rewrite.get_system_prompt(action)}\n\n{user_prompt}"
    )
    raw = router.call(full_prompt)
    parsed = copy_rewrite.parse_response(raw)
    if "error" in parsed:
        st.session_state.diag_rewrite_error = parsed.get("error", "未知错误")
        st.session_state.diag_rewrites = []
        return
    st.session_state.diag_rewrite_error = ""
    st.session_state.diag_rewrites = [parsed]


# ============================================================
# 主流程
# ============================================================
def main():
    _render_input()
    st.markdown("---")
    left, middle, right = st.columns([1.1, 1.2, 1.3], gap="medium")
    with left:
        _render_left_column()
    with middle:
        _render_middle_column()
    with right:
        _render_right_column()


main()