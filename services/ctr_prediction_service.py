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
"""

from __future__ import annotations

from typing import List, Optional

from adapters.ctr_predictor_adapter import CTRPredictionAdapter
from core.schemas import TaskInput, Candidate, PredictionResult


# 渠道 → 维度字段映射（PRD §6.2 / §12.5）
def _candidate_to_row(candidate: Candidate, task: TaskInput) -> dict:
    """把 Candidate + TaskInput 转 CTR Adapter 的 row dict。"""
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
    """单条文案 CTR 预测（入口 B 用）。"""
    fake_task = TaskInput(
        product_benefit="(诊断模式)", audience="(诊断)", channel=channel,
        objective="(诊断)", stage="(诊断)", scene="(诊断)", tone="(诊断)",
        plan_type=plan_type or "未知", coupon=coupon or "未知",
    )
    from core.schemas import Candidate
    c = Candidate(id="X", strategy="diagnose", title=title, body=body)
    return predict_for_candidates([c], fake_task, mode=mode)[0]


__all__ = ["predict_for_candidates", "predict_one"]
