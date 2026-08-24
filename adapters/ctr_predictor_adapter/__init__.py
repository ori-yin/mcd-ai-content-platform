# -*- coding: utf-8 -*-
r"""
adapters/ctr_predictor_adapter — CTR 预测旧项目适配层

Phase 1a 导出（4 个纯函数模块）：
- baseline_lookup:  get_baseline / get_baseline_ctr / get_time_multiplier
- char_utils:       count_chars / get_char_range / suggest_char_range
- column_mapping:   auto_detect / auto_detect_all + 8 组 KNOWN_*_ALIASES
- prompt_builder:   build_context_for_llm / enrich_rows_for_llm

Phase 1b 待补：
- PredictionResult dataclass
- CTRPredictionAdapter 统一入口（四态分明）
- core/llm_gateway.py ProviderRouter（OpenAI/Anthropic 协议分流）

红线（CLAUDE.md §4.1）：
- 页面层不得 import 此 adapter 的内部模块，统一通过此 __init__.py
- 本 adapter 不得 import openai / anthropic SDK（Phase 1b 由 core/llm_gateway 承担）
"""

from .baseline_lookup import get_baseline, get_baseline_ctr, get_time_multiplier
from .char_utils import count_chars, get_char_range, suggest_char_range
from .column_mapping import (
    KNOWN_TITLE_ALIASES,
    KNOWN_BODY_ALIASES,
    KNOWN_CHANNEL_ALIASES,
    KNOWN_COUPON_ALIASES,
    KNOWN_WORKDAY_ALIASES,
    KNOWN_TIME_ALIASES,
    KNOWN_PLAN_ALIASES,
    KNOWN_OWNER_ALIASES,
    auto_detect,
    auto_detect_all,
)
from .prompt_builder import build_context_for_llm, enrich_rows_for_llm

__all__ = [
    # baseline_lookup
    "get_baseline",
    "get_baseline_ctr",
    "get_time_multiplier",
    # char_utils
    "count_chars",
    "get_char_range",
    "suggest_char_range",
    # column_mapping
    "KNOWN_TITLE_ALIASES",
    "KNOWN_BODY_ALIASES",
    "KNOWN_CHANNEL_ALIASES",
    "KNOWN_COUPON_ALIASES",
    "KNOWN_WORKDAY_ALIASES",
    "KNOWN_TIME_ALIASES",
    "KNOWN_PLAN_ALIASES",
    "KNOWN_OWNER_ALIASES",
    "auto_detect",
    "auto_detect_all",
    # prompt_builder
    "build_context_for_llm",
    "enrich_rows_for_llm",
]