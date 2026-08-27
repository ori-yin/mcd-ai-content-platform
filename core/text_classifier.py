# -*- coding: utf-8 -*-
r"""
core/text_classifier.py — 文案内容分类器（Phase 12 #11 用券双字段）

功能：
- classify_coupon_in_text(title, body) → "是"/"否"
  判断标题/正文是否含券词（优惠券/折扣/链接等）

复用：
- 关键词词典在 config/coupon_keywords.yaml（v1.0）
- 风格对齐 core/data_window.classify_date_type（纯函数 + lru_cache 加载 yaml）

不消费：
- form 字段"实际是否用券"（plan 维度）—— 用 TaskInput.coupon
- baseline_lookup 的渠道 × 用券维度 —— 走 `渠道_x_是否用券`
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Optional


DEFAULT_KEYWORDS_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "coupon_keywords.yaml"
)


@functools.lru_cache(maxsize=1)
def _load_keywords(path: str = str(DEFAULT_KEYWORDS_PATH)) -> list:
    """加载优惠券关键词词典（discount + coupon + link 三类合并成 pattern 列表）。"""
    p = Path(path)
    if not p.exists():
        return []
    try:
        import yaml
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    patterns = []
    for cat in ("discount", "coupon", "link"):
        for kw in doc.get(cat, []) or []:
            try:
                patterns.append(re.compile(kw))
            except re.error:
                # yaml 配错正则时跳过这一条，不阻塞其他
                continue
    return patterns


def classify_coupon_in_text(
    title: Optional[str],
    body: Optional[str] = None,
    keywords_path: Optional[str] = None,
) -> str:
    """判断标题/正文是否含券词。

    返回："是" / "否"（与 form `coupon` 字段口径一致，便于 baseline_lookup 复用）。

    参数：
    - title: 文案标题（短信/企微可为空）
    - body: 文案正文
    - keywords_path: 自定义词典路径（默认 config/coupon_keywords.yaml）

    边界：
    - title + body 都为空 → "否"
    - 任一关键词命中 → "是"
    """
    patterns = _load_keywords(keywords_path) if keywords_path else _load_keywords()
    if not patterns:
        return "否"
    text = " ".join([t for t in (title or "", body or "") if t])
    if not text.strip():
        return "否"
    for p in patterns:
        if p.search(text):
            return "是"
    return "否"


__all__ = ["classify_coupon_in_text"]
