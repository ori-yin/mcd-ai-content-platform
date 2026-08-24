# -*- coding: utf-8 -*-
r"""
services/copy_analysis_service.py — 文案本地诊断 service 包装

复用 services/text_analyzer.diagnose_score（PRD §13.3 单条文案诊断）。

返回 dict 含：score / problems / suggestions / diag（local_diagnose）
"""

from __future__ import annotations

from typing import Optional
import pandas as pd

from services.text_analyzer import diagnose_score


def diagnose(
    title: str,
    body: str,
    channel: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
    min_plans: int = 3,
) -> dict:
    """单条文案诊断。

    返回 dict：
    - score: 0-100
    - grade: A/B/C/D（diagnose_score 内部给出）
    - problems: list[{tag, label, current, suggested, so_what}]
    - suggestions: (p1_list, p2_list)
    - diag: local_diagnose dict（{len_title, len_body, emoji_count, hit_words, miss_top}）
    """
    try:
        result = diagnose_score(title, body, df=df, target_ch=channel, min_plans=min_plans)
        return result
    except Exception as e:
        return {
            "score": None,
            "grade": "—",
            "problems": [],
            "suggestions": ([], []),
            "diag": {"error": str(e)},
        }


__all__ = ["diagnose"]
