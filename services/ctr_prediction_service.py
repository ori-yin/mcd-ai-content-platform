# -*- coding: utf-8 -*-
r"""
services/ctr_prediction_service.py — CTR 预测 service 包装

PRD §4.0 CTR 三入口（A/B/C）共用同一份 CTR Adapter：
- 入口 A（创作页）：AI 生成 3 条候选后，CTR Adapter 给每条候选预测
- 入口 B（诊断页）：单条 title+body+channel+维度 → PredictionResult
- 入口 C（批量页）：批量行 → list[PredictionResult]

本 service 是 CTRPredictionAdapter 的薄壳：
- 接收 list[Candidate] + TaskInput
- 调用 CTRPredictionAdapter.predict_batch
- 严格保持四态分明（model_prediction / baseline_only / demo / unavailable）

v3.1 口径（2026-08-26 业务拍板；Q1 去重点击 / Q2 触达成功 / Q3 全周期不截断
/ Q4 渠道不聚合 / Q5 min_reach 兜底 / bi_dt T-1 12 点前 INTERVAL 2；
详 docs/ctr-kpi-definition-proposal-v0.2.md）。
"""

from __future__ import annotations

from typing import List, Optional

from adapters.ctr_predictor_adapter import CTRPredictionAdapter
from core.schemas import TaskInput, Candidate, PredictionResult, task_signature


# 渠道 → 维度字段映射（PRD §6.2 / §12.5）
def _candidate_to_row(candidate: Candidate, task: TaskInput) -> dict:
    """把 Candidate + TaskInput 转 CTR Adapter 的 row dict。

    _signature 字段：Phase-B demo 回灌用，按 task + title 算 SHA1 截 12 位
    （与 records.db / feedback.db 的 task_signature 字段对齐，Phase 5 P0 约定）。
    """
    title = candidate.effective_title
    body = candidate.effective_body
    return {
        "channel": task.channel,
        "title": title,
        "body": body,
        "plan_type": task.plan_type if task.plan_type != "未知" else None,
        "coupon": task.coupon if task.coupon != "未知" else None,
        "owner": None,  # PRD §26 第 12 项待确认
        "title_len": len(title),
        "_signature": task_signature(task, candidates=[candidate], selected_id=candidate.id),
    }


def predict_for_candidates(
    candidates: List[Candidate],
    task: TaskInput,
    mode: str = "demo",
    adapter: Optional[CTRPredictionAdapter] = None,
) -> List[PredictionResult]:
    """批量 CTR 预测。返回 list[PredictionResult]，长度 == len(candidates)。

    mode: baseline_only / demo / existing_predictor / unavailable
    adapter: 注入复用；缺省按 mode 新建一个
    """
    if adapter is None:
        adapter = CTRPredictionAdapter(mode=mode)

    rows = [_candidate_to_row(c, task) for c in candidates]
    results = adapter.predict_batch(rows)

    # 长度对齐（兜底）
    if len(results) != len(candidates):
        results = (results + [PredictionResult.unavailable("返回长度不匹配")] * len(candidates))[:len(candidates)]
    return results


def predict_one(
    title: str,
    body: str,
    channel: str,
    plan_type: Optional[str] = None,
    coupon: Optional[str] = None,
    mode: str = "demo",
) -> PredictionResult:
    """单条文案 CTR 预测（PRD §4.0 入口 B 用）。

    脱离 AI 生成上下文：仅 title+body+channel 即可，不构造 Candidate（避免 id=A/B/C 限制）。
    """
    adapter = CTRPredictionAdapter(mode=mode)
    # 构造临时 TaskInput + Candidate 算 signature（predict_one 无 task 入参）
    tmp_task = TaskInput(
        channel=channel,
        audience="未知",
        stage="未知",
        scene="未知",
        tone="未知",
        plan_type=plan_type or "",
        coupon=coupon or "",
    )
    tmp_cand = Candidate(id="A", strategy="diagnose", title=title, body=body)
    row = {
        "channel": channel,
        "title": title,
        "body": body,
        "plan_type": plan_type if plan_type and plan_type != "未知" else None,
        "coupon": coupon if coupon and coupon != "未知" else None,
        "owner": None,
        "title_len": len(title),
        "_signature": task_signature(tmp_task, candidates=[tmp_cand], selected_id=tmp_cand.id),
    }
    results = adapter.predict_batch([row])
    if not results:
        return PredictionResult.unavailable("CTR Adapter 返回空")
    return results[0]


__all__ = ["predict_for_candidates", "predict_one"]
