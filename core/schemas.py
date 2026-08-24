# -*- coding: utf-8 -*-
r"""
core/schemas.py — 业务 dataclass 契约层

Phase 1b 范围：
- PredictionResult: CTR 预测四态分明（CLAUDE.md §4.2 强制）
- 未来补：TaskInput / Candidate / CopyAnalysis / etc.

四态定义：
- model_prediction: 真实 LLM 预测（基于 baseline + 推理）
- baseline_only:    仅历史基准，无 LLM
- demo:              演示数据稳定占位（UI 必标"演示数据"）
- unavailable:       无有效结果（error 必填）

UI 红线：
- 不得把 demo / baseline_only 标成"预测准确率 XX%"
- 不得让 unavailable 的 pred_ctr 进入计算
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Any


# ── 四态类型别名 ───────────────────────────────────────────────────────
ResultType = Literal["model_prediction", "baseline_only", "demo", "unavailable"]
VALID_RESULT_TYPES: tuple = ("model_prediction", "baseline_only", "demo", "unavailable")


@dataclass
class PredictionResult:
    """CTR 预测结果统一结构。

    字段语义：
    - result_type: 四态枚举，必填
    - pred_ctr:    预测 CTR（小数，0.025 = 2.5%）；baseline_only / unavailable 可为 None
    - confidence:  置信度 0-1；baseline_only / unavailable 可为 None
    - suggestion:  改进建议（30 字内，文案本身）；unavailable 必填原因
    - source:      数据来源（e.g. "ctr_predictor_adapter/baseline_lookup"）
    - error:       错误描述（仅 unavailable / 异常路径用）
    - baseline_ctr: 历史基准 CTR（任何态都可能存在，便于 UI 对比展示）
    - time_multiplier: 时段系数（任何态都可能存在）
    """
    result_type: str
    pred_ctr: Optional[float] = None
    confidence: Optional[float] = None
    suggestion: str = ""
    source: str = ""
    error: Optional[str] = None
    baseline_ctr: Optional[float] = None
    time_multiplier: Optional[float] = None

    def __post_init__(self):
        # 四态校验（防止 UI 层误传 demo / unavailable 又标"预测准确率 77%"）
        if self.result_type not in VALID_RESULT_TYPES:
            raise ValueError(
                f"result_type must be one of {VALID_RESULT_TYPES}, got {self.result_type!r}"
            )
        # unavailable 必须有 error
        if self.result_type == "unavailable" and not self.error:
            self.error = "无有效结果"
        # pred_ctr 范围校验
        if self.pred_ctr is not None and not (0 <= self.pred_ctr <= 1):
            raise ValueError(f"pred_ctr must be in [0, 1], got {self.pred_ctr}")
        # confidence 范围校验
        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")

    # ── 工厂方法（便于测试和 UI 构造） ─────────────────────────────────
    @classmethod
    def baseline_only(
        cls, baseline_ctr: Optional[float], suggestion: str = "无 LLM，仅历史基准",
        time_multiplier: Optional[float] = None, source: str = "ctr_predictor_adapter/baseline_lookup",
    ) -> "PredictionResult":
        return cls(
            result_type="baseline_only",
            pred_ctr=baseline_ctr,
            confidence=None,
            suggestion=suggestion,
            source=source,
            baseline_ctr=baseline_ctr,
            time_multiplier=time_multiplier,
        )

    @classmethod
    def model_prediction(
        cls, pred_ctr: float, confidence: float, suggestion: str,
        baseline_ctr: Optional[float] = None, time_multiplier: Optional[float] = None,
        source: str = "ctr_predictor_adapter/llm",
    ) -> "PredictionResult":
        return cls(
            result_type="model_prediction",
            pred_ctr=pred_ctr,
            confidence=confidence,
            suggestion=suggestion,
            source=source,
            baseline_ctr=baseline_ctr,
            time_multiplier=time_multiplier,
        )

    @classmethod
    def demo(
        cls, pred_ctr: float, confidence: float = 0.5, suggestion: str = "演示数据",
        baseline_ctr: Optional[float] = None, time_multiplier: Optional[float] = None,
        source: str = "ctr_predictor_adapter/demo",
    ) -> "PredictionResult":
        return cls(
            result_type="demo",
            pred_ctr=pred_ctr,
            confidence=confidence,
            suggestion=suggestion,
            source=source,
            baseline_ctr=baseline_ctr,
            time_multiplier=time_multiplier,
        )

    @classmethod
    def unavailable(cls, error: str, suggestion: str = "无有效结果") -> "PredictionResult":
        return cls(
            result_type="unavailable",
            pred_ctr=None,
            confidence=None,
            suggestion=suggestion,
            source="ctr_predictor_adapter/none",
            error=error,
        )

    # ── 序列化 ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def has_ctr(self) -> bool:
        """是否可用于聚合计算（unavailable 不可用）。"""
        return self.result_type in ("model_prediction", "baseline_only", "demo") \
            and self.pred_ctr is not None

    @property
    def is_demo(self) -> bool:
        return self.result_type == "demo"

    @property
    def label(self) -> str:
        """UI 展示标签。"""
        return {
            "model_prediction": "LLM 预测",
            "baseline_only":    "历史基准",
            "demo":             "演示数据",
            "unavailable":      "无结果",
        }.get(self.result_type, self.result_type)