# -*- coding: utf-8 -*-
r"""
pages/01_content_studio.py — 01 内容创作（三栏主流程）

PRD §4.1 主流程：
定义经营任务 → 生成 3 条候选 → 查看历史证据与规则诊断 →
比较 CTR 参考 → 渠道预览 → 人工编辑和选择 → 保存

三栏布局：
- 左：定义经营任务（PRD §6.2）
- 中：选择候选内容（PRD §7.2 / §7.3）
- 右：预览并比较预测结果（PRD §8.2 / §8.3 / §8.4 / §8.5）

session_state（PRD §17）：
- task_input: dict（form 提交后保存）
- candidates: list[Candidate]
- selected_id: str
- rule_results: list[RuleResult]
- ctr_results: list[PredictionResult]
- similar_summary: dict
- last_generated_signature: str（任务签名，左栏字段变 → toast 提示重新生成）

CLAUDE.md §4 红线：
- 不直 import 旧项目（统一走 services/）
- 不写死 Prompt（统一走 prompts/）
- 不散落数据库操作（统一走 record_service）
- CTR 四态分明（result_type 标签化）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

from core.data_window import classify_today_type
from core.schemas import (
    TaskInput, Candidate, RuleResult, PredictionResult,
    TARGET_AUDIENCE, OBJECTIVES, CHANNELS, STAGES, SCENES,
    TONES, ACTIONS, PLAN_TYPES, COUPON_FLAGS,
)
from services.generation_service import generate, build_record, GenerationError, rank_candidates_by_ctr
from services.rule_engine import load_rules, check_candidates
from services.ctr_prediction_service import predict_for_candidates
from services.similarity_service import find_similar, summarize_similar
from services.record_service import save_generation
from ui.llm_status import render_banner
from ui.plotly_helpers import rate_value
from ui.styles import inject_base_css


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="01 内容创作",
    page_icon="🍟",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_css()

# LLM 未配置提示（业务确认 #10）
render_banner()

st.markdown(
    """
    <div class="mcd-header">
        <h1>01 内容创作</h1>
        <p>定义任务 · 生成 3 条候选 · 规则 + CTR 评估 · 渠道预览 · 人工选择</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# session_state 初始化
# ============================================================
def _init_state():
    defaults = {
        "task_input": None,           # TaskInput dict
        "candidates": [],             # list[Candidate]
        "selected_id": "A",
        "rule_results": [],           # list[RuleResult]
        "ctr_results": [],            # list[PredictionResult]
        "similar_summary": {},        # dict
        "last_generated_signature": "",
        "saved_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ============================================================
# 工具：任务签名（PRD §17 字段变化 → 提示重新生成）
# ============================================================
def _task_signature(t: dict) -> str:
    keys = ("product_benefit", "audience", "channel", "objective",
            "stage", "scene", "tone", "expected_action",
            "plan_type", "coupon", "extra_requirements")
    return "|".join(str(t.get(k, "")) for k in keys)


# ============================================================
# 左栏：定义经营任务（PRD §6）
# ============================================================
def _render_left_column(channel_rules: dict) -> Optional[TaskInput]:
    """左栏 form。提交后返回 TaskInput。"""
    st.markdown("### 1 定义经营任务")
    st.caption(
        "必填 5 项（人群/渠道/阶段/场景/语气）；产品与权益 + 投放目标 为 Demo 阶段占位，"
        "二期接入。AI 结果仅作为候选，投放前人工确认。"
    )

    cur = st.session_state.task_input or {}

    with st.form("task_form", clear_on_submit=False):
        # 产品与权益：Demo 阶段灰态（PRD §26 业务确认 + 演示口径决策）
        product_benefit = st.text_area(
            "产品与权益（待开发·二期接入）",
            value=cur.get("product_benefit", ""),
            height=80,
            disabled=True,
            help="后续开放，敬请期待。本期不参与生成（决策文档 Demo 范围 §1）。",
            placeholder="二期接入后可填写（如：Chiikawa 合作款 + 限定小卡）",
        )
        c1, c2 = st.columns(2)
        with c1:
            audience = st.selectbox(
                "目标人群 *", TARGET_AUDIENCE,
                index=TARGET_AUDIENCE.index(cur.get("audience", "常规大盘"))
                if cur.get("audience") in TARGET_AUDIENCE else 0,
            )
            # 投放目标：Demo 阶段灰态
            objective = st.selectbox(
                "投放目标（待开发·二期接入）", OBJECTIVES,
                index=OBJECTIVES.index(cur.get("objective", "建立认知"))
                if cur.get("objective") in OBJECTIVES else 0,
                disabled=True,
                help="后续开放，敬请期待。本期不参与生成（决策文档 Demo 范围 §1）。",
            )
            stage = st.selectbox(
                "活动阶段 *", STAGES,
                index=STAGES.index(cur.get("stage", "活动预热"))
                if cur.get("stage") in STAGES else 0,
            )
            tone = st.selectbox(
                "内容语气 *", TONES,
                index=TONES.index(cur.get("tone", "直接利益型"))
                if cur.get("tone") in TONES else 0,
            )
        with c2:
            channel = st.selectbox(
                "投放渠道 *", CHANNELS,
                index=CHANNELS.index(cur.get("channel", "APP Push"))
                if cur.get("channel") in CHANNELS else 0,
            )
            scene = st.selectbox(
                "消费场景 *", SCENES,
                index=SCENES.index(cur.get("scene", "早餐"))
                if cur.get("scene") in SCENES else 0,
            )
            expected_action = st.selectbox(
                "期望动作", ACTIONS,
                index=ACTIONS.index(cur.get("expected_action", "点击"))
                if cur.get("expected_action") in ACTIONS else 0,
            )
            plan_type = st.selectbox(
                "Plan 类型", PLAN_TYPES,
                index=PLAN_TYPES.index(cur.get("plan_type", "普通 Plan"))
                if cur.get("plan_type") in PLAN_TYPES else 0,
            )

        c3, c4 = st.columns(2)
        with c3:
            coupon = st.selectbox(
                "是否用券", COUPON_FLAGS,
                index=COUPON_FLAGS.index(cur.get("coupon", "否"))
                if cur.get("coupon") in COUPON_FLAGS else 1,
            )
        with c4:
            # Phase 11 · 用户口径 2026-08-27：去掉日期选择器，只选工作日/非工作日
            # 默认按今日自动算（classify_today_type 走 weekday 逻辑）
            # 法定节假日 / 调休 暂不支持，详 Handoff §6.2 #12
            _default_today_type = classify_today_type()
            planned_send_date = st.selectbox(
                "计划投放日期类型",
                ["工作日", "非工作日"],
                index=0 if _default_today_type == "工作日" else 1,
                help="按计划投放当天选择：周一~周五=工作日，周六周日=非工作日；暂不支持法定节假日细分",
            )

        extra_requirements = st.text_area(
            "额外要求（可选）",
            value=cur.get("extra_requirements", ""),
            height=60,
            placeholder="必须出现 / 不得出现 / 法务或业务补充",
        )

        submitted = st.form_submit_button(
            "生成 3 条候选内容", type="primary", use_container_width=True,
        )

    if submitted:
        form_dict = {
            "product_benefit": product_benefit.strip(),
            "audience": audience,
            "channel": channel,
            "objective": objective,
            "stage": stage,
            "scene": scene,
            "tone": tone,
            "expected_action": expected_action,
            "plan_type": plan_type,
            "coupon": coupon,
            "planned_send_date": str(planned_send_date) if planned_send_date else None,
            "extra_requirements": extra_requirements.strip(),
        }
        try:
            task = TaskInput.from_form(form_dict)
        except ValueError as e:
            st.error(f"必填字段缺失：{e}")
            return None

        # PRD §17 字段变更检测
        sig = _task_signature(form_dict)
        if (st.session_state.candidates
                and sig != st.session_state.last_generated_signature):
            st.toast("检测到字段已变更，请重新点击「生成」按钮", icon="⚠")

        return task

    return None


# ============================================================
# 中栏：选择候选内容（PRD §7）
# ============================================================
def _render_middle_column(task: TaskInput, channel_rules: dict):
    st.markdown("### 2 选择候选内容")
    candidates = st.session_state.candidates
    selected_id = st.session_state.selected_id

    if not candidates:
        st.info("尚未生成候选。请先在左侧填字段，点击「生成 3 条候选内容」。")
        return

    # 切换候选（单选 + 金色描边）
    cols = st.columns(3)
    for i, c in enumerate(candidates):
        with cols[i]:
            is_selected = (c.id == selected_id)
            border_color = "#FFC72C" if is_selected else "#E0E0E0"
            border_w = "3px" if is_selected else "1px"
            edited_tag = "  · 已编辑" if c.is_edited else ""
            st.markdown(
                f"""
                <div class="candidate-card" style="border-color:{border_color};
                     border-width:{border_w};">
                    <div class="cand-header">
                        <b>{c.id}</b> · {c.strategy.split('_', 1)[1] if '_' in c.strategy else c.strategy}{edited_tag}
                    </div>
                    <div class="cand-title">{c.effective_title or '（无标题）'}</div>
                    <div class="cand-body">{c.effective_body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # 单选按钮
            if st.button(
                f"选 {c.id}", key=f"sel_{c.id}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_id = c.id
                st.rerun()

    st.markdown("---")

    # 选中候选的编辑区
    selected_cand = next((c for c in candidates if c.id == selected_id), candidates[0])
    _render_edit_area(selected_cand, task, channel_rules)


def _render_edit_area(c: Candidate, task: TaskInput, channel_rules: dict):
    """编辑选中候选的 title / body；编辑后重算规则。"""
    st.markdown(f"#### 编辑候选 {c.id}")

    title_disabled = task.channel in ("短信", "企微 1v1")
    new_title = st.text_input(
        "标题",
        value=c.effective_title,
        disabled=title_disabled,
        key=f"edit_title_{c.id}_{c.is_edited}",
    )
    new_body = st.text_area(
        "正文",
        value=c.effective_body,
        height=80,
        key=f"edit_body_{c.id}_{c.is_edited}",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("恢复 AI 原文", key=f"reset_{c.id}", use_container_width=True):
            c.reset_edit()
            # 恢复后重算规则
            cr, br = load_rules()
            st.session_state.rule_results = check_candidates(
                st.session_state.candidates, task.channel, cr, br,
            )
            st.rerun()

    # 编辑后即时更新（PRD §17 规则检查在编辑后重新执行）
    if new_title != c.effective_title or new_body != c.effective_body:
        c.title_edited = new_title if new_title != c.title else None
        c.body_edited = new_body if new_body != c.body else None
        # 重算规则
        cr, br = load_rules()
        st.session_state.rule_results = check_candidates(
            st.session_state.candidates, task.channel, cr, br,
        )


# ============================================================
# 右栏：预览 + CTR / 投放理由 / 可信程度 + 规则诊断 + 推荐结论（PRD §8）
# ============================================================
def _render_right_column(task: TaskInput, channel_rules: dict):
    st.markdown("### 3 预览并比较预测结果")
    candidates = st.session_state.candidates
    selected_id = st.session_state.selected_id
    rule_results: list = st.session_state.rule_results
    ctr_results: list = st.session_state.ctr_results
    similar_summary: dict = st.session_state.similar_summary

    if not candidates:
        st.info("生成候选后此处显示渠道预览和 CTR 参考。")
        return

    selected = next((c for c in candidates if c.id == selected_id), candidates[0])
    selected_idx = candidates.index(selected)
    selected_rule: RuleResult = rule_results[selected_idx] if selected_idx < len(rule_results) else RuleResult()
    selected_ctr: Optional[PredictionResult] = ctr_results[selected_idx] if selected_idx < len(ctr_results) else None

    # ── 渠道预览（PRD §8.2 P0 = APP Push）
    _render_channel_preview(task, selected)

    st.markdown("---")

    # ── 卡片一：CTR 参考（PRD §8.3）
    _render_ctr_card(selected_ctr)

    # ── 卡片二：投放理由（PRD §8.3）
    _render_reason_card(task, selected, selected_rule)

    # ── 卡片三：可信程度（PRD §8.3）
    _render_confidence_card(selected_ctr, similar_summary)

    st.markdown("---")

    # ── 规则诊断（PRD §8.4）
    _render_rule_diagnostics(selected_rule)

    st.markdown("---")

    # ── 推荐结论（PRD §8.5）
    _render_recommendation(task, selected, selected_rule)


def _render_channel_preview(task: TaskInput, c: Candidate):
    ch = task.channel
    title = c.effective_title or "（无标题）"
    body = c.effective_body
    if ch == "APP Push":
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">'
            f"McDonald&apos;s · {datetime.now().strftime('%H:%M')}</div>"
            f'<div class="pv-title">{title}</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">APP Push · 点击查看</div>'
            f'</div>'
        )
    elif ch == "企微 1v1":
        # 仿企业微信聊天气泡（头像 + 服务名 + 卡片 + 时间戳）
        preview_html = (
            f'<div class="wechat-bubble-wrap">'
            f'<div class="wc-avatar">M</div>'
            f'<div class="wechat-bubble">'
            f'<div class="wc-name">麦当劳会员服务</div>'
            f'<div class="wc-title">{title}</div>'
            f'<div class="wc-body">{body}</div>'
            f'<div class="wc-meta">今天 {datetime.now().strftime("%H:%M")} · 已送达</div>'
            f'</div>'
            f'</div>'
        )
    elif ch == "短信":
        seg = max(1, (len(body) + 69) // 70)
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">106xxxxxxxx</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">短信 · {len(body)} 字 / {seg} 段</div>'
            f'</div>'
        )
    elif ch == "站内信":
        preview_html = (
            f'<div class="preview-card">'
            f'<div style="font-size:0.78em;opacity:0.55;margin-bottom:0.4rem;">'
            f"McDonald&apos;s App · 消息中心</div>"
            f'<div class="pv-title">{title}</div>'
            f'<div class="pv-body">{body}</div>'
            f'<div class="pv-meta">站内信 · 查看详情</div>'
            f'</div>'
        )
    else:
        preview_html = '<div class="warning-banner">该渠道预览待 P1 实现（PRD §8.2）</div>'

    st.markdown("**渠道预览**")
    st.markdown(preview_html, unsafe_allow_html=True)


def _render_ctr_card(ctr: Optional[PredictionResult]):
    st.markdown("**CTR 参考结果**")
    if ctr is None:
        st.markdown('<div class="warning-banner">CTR 参考：暂不可用</div>',
                    unsafe_allow_html=True)
        return
    label = ctr.label
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
    st.markdown(f'<div class="kpi-tile"><div class="label">状态：{label}</div>'
                + "".join(f'<div>{p}</div>' for p in parts)
                + '</div>',
                unsafe_allow_html=True)
    if ctr.suggestion:
        st.caption(f"建议：{ctr.suggestion}")


def _render_reason_card(task: TaskInput, c: Candidate, rule: RuleResult):
    st.markdown("**投放理由**")
    reasons = []
    if rule.passes:
        reasons.append(f"规则通过 {len(rule.passes)} 项")
    if c.reason:
        reasons.append(c.reason)
    reasons.append(f"匹配 {task.objective} + {task.stage} 目标" if task.objective else f"匹配 {task.stage} 目标")
    if task.scene and task.scene != "其他":
        reasons.append(f"场景：{task.scene}")
    if not reasons:
        st.caption("无")
        return
    st.markdown(
        '<div class="decision-card"><ul>'
        + "".join(f"<li>{r}</li>" for r in reasons)
        + '</ul></div>',
        unsafe_allow_html=True,
    )


def _render_confidence_card(ctr: Optional[PredictionResult], similar: dict):
    st.markdown("**可信程度**")
    sim_count = similar.get("count", 0)
    level = "低"
    reasons = []
    if ctr is not None:
        if ctr.result_type == "model_prediction" and ctr.confidence is not None:
            if ctr.confidence >= 0.7:
                level = "高"
            elif ctr.confidence >= 0.4:
                level = "中"
            reasons.append(f"使用模型预测（置信度 {ctr.confidence:.2f}）")
        elif ctr.result_type == "baseline_only":
            level = "中"
            reasons.append("仅历史基准，无 LLM 预测")
        elif ctr.result_type == "demo":
            level = "中"
            reasons.append("演示数据，非正式投放承诺")
        else:
            reasons.append("无有效结果")
    else:
        reasons.append("无 CTR 结果")
    if sim_count >= 3:
        if level == "低":
            level = "中"
        reasons.append(f"找到 {sim_count} 条相似历史内容")
    elif sim_count == 0:
        reasons.append("未找到相似历史内容")
    st.markdown(
        f'<div class="kpi-tile"><div class="label">参考可信度</div>'
        f'<div class="value">{level}</div>'
        + "".join(f'<div class="sub">{r}</div>' for r in reasons)
        + '</div>',
        unsafe_allow_html=True,
    )


def _render_rule_diagnostics(rule: RuleResult):
    st.markdown("**规则诊断**")
    if not rule.items:
        st.caption("无规则结果")
        return
    for it in rule.items:
        cls = {
            "pass": "rule-pass",
            "warn": "rule-warn",
            "fail": "rule-fail",
        }.get(it.severity, "rule-pass")
        sug = f"<br><small>建议：{it.suggestion}</small>" if it.suggestion else ""
        st.markdown(
            f'<div class="{cls}"><b>[{it.severity.upper()}]</b> '
            f'<b>{it.category}</b>：{it.message}{sug}</div>',
            unsafe_allow_html=True,
        )


def _render_recommendation(task: TaskInput, c: Candidate, rule: RuleResult):
    st.markdown("**推荐结论**")
    if rule.has_blocking:
        st.markdown(
            '<div class="warning-banner"><b>存在阻断项，不推荐正式使用。</b>'
            '请先修改后再次评估。</div>',
            unsafe_allow_html=True,
        )
        return
    objective_part = f" + {task.objective}" if task.objective else ""
    text = (
        f"参考结论：当前版本符合 {task.channel} 基础规则，与「{task.stage}"
        f"{objective_part}」目标匹配。三条候选已按 CTR 预测降序展示（演示口径），"
        f"不代表正式投放承诺，建议结合业务判断后使用。"
    )
    st.markdown(f'<div class="decision-card">{text}</div>', unsafe_allow_html=True)

    # 保存按钮
    st.markdown("---")
    if st.button("保存当前选择", type="primary", use_container_width=True):
        _save_current(task)


# ============================================================
# 保存
# ============================================================
def _save_current(task: TaskInput):
    rec = build_record(
        task=task,
        candidates=st.session_state.candidates,
        selected_id=st.session_state.selected_id,
        rule_results=st.session_state.rule_results,
        ctr_results=st.session_state.ctr_results,
        similar_summary=st.session_state.similar_summary,
    )
    try:
        rid = save_generation(rec)
        st.session_state.saved_id = rid
        st.success(f"已保存（id={rid}）")
    except Exception as e:
        st.error(f"保存失败：{e}")


# ============================================================
# 主流程
# ============================================================
def main():
    channel_rules, brand_rules = load_rules()

    left, middle, right = st.columns([1.1, 1.5, 1.3], gap="medium")

    with left:
        new_task = _render_left_column(channel_rules)

    # 生成按钮触发（form 内提交）
    if new_task is not None:
        st.session_state.task_input = new_task.to_dict()
        with st.spinner("正在生成 3 条候选…"):
            try:
                candidates = generate(new_task, channel_rules=channel_rules)
            except GenerationError as e:
                st.error(f"生成失败：{e}")
                return
        st.session_state.candidates = candidates
        st.session_state.selected_id = "A"
        # 重算规则 + CTR + 相似
        st.session_state.rule_results = check_candidates(
            candidates, new_task.channel, channel_rules, brand_rules,
        )
        ctr_mode = "demo"  # Phase 3.1 默认 demo；Phase 4 接 LLM 时按环境变量切
        ctr_results = predict_for_candidates(
            candidates, new_task, mode=ctr_mode,
        )
        # 反哺影响排序（Phase 7.2 #6 拍板）：按 pred_ctr 降序，title 长度兜底
        candidates, ctr_results = rank_candidates_by_ctr(candidates, ctr_results)
        st.session_state.candidates = candidates
        st.session_state.ctr_results = ctr_results
        # 默认选中 CTR 最高的那条（rank 后第 1 条）
        st.session_state.selected_id = candidates[0].id
        # 历史相似（仅第一条候选）
        first = candidates[0]
        sim_df = find_similar(first.effective_title, first.effective_body, new_task.channel)
        st.session_state.similar_summary = summarize_similar(sim_df)
        st.session_state.last_generated_signature = _task_signature(new_task.to_dict())
        st.rerun()

    with middle:
        task_for_display = (
            TaskInput.from_form(st.session_state.task_input)
            if st.session_state.task_input else None
        )
        if task_for_display:
            _render_middle_column(task_for_display, channel_rules)

    with right:
        if task_for_display:
            _render_right_column(task_for_display, channel_rules)


main()
