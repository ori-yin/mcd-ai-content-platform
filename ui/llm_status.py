# -*- coding: utf-8 -*-
"""
ui/llm_status.py — LLM 配置状态检测（业务确认 #10）

读 config/llm_settings.yaml，判断 4 字段是否全部为空：
- 全空 → Demo 模式，入口页需显示 banner 提示
- 有任一字段非空 → 视作已配置（按字段完整性校验）

约束：
- 不抛异常（yaml 不存在或格式错视作未配置）
- 用 PyYAML（同 services/rule_engine.py），单进程 lru_cache，配置改后需重启应用
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "llm_settings.yaml"
REQUIRED_FIELDS = ("provider", "base_url", "model", "api_key")


@functools.lru_cache(maxsize=1)
def _load_yaml() -> dict:
    """加载并过滤到 REQUIRED_FIELDS（单进程内缓存，配置改后需重启）。"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return {}
    return {k: str(data.get(k, "")).strip() for k in REQUIRED_FIELDS}


def missing_fields() -> list:
    """返回空字段列表（用于 banner 文案）。"""
    cfg = _load_yaml()
    return [k for k in REQUIRED_FIELDS if not cfg.get(k, "")]


def is_configured() -> bool:
    """4 字段是否全部非空。"""
    return not missing_fields()


def load_config() -> dict:
    """返回完整 4 字段 dict（缺失字段为 ""）；给需要构造 ProviderRouter 的调用方用。

    Phase 17 增：pages/02_copy_diagnosis.py 之前误 `from core.config import settings`
    （模块不存在），导致 LLM 配置正确时仍走 Demo。改走 load_config() 真实判断。
    """
    return _load_yaml()


def render_banner():
    """在入口页渲染"LLM 未配置"banner。已配置则不渲染。"""
    import streamlit as st
    miss = missing_fields()
    if not miss:
        return
    msg = "LLM 未配置（Demo 模式）" if len(miss) == 4 else f"LLM 配置不完整：缺 {', '.join(miss)}"
    st.markdown(
        f'<div class="llm-warning">'
        f"<b>{msg}</b>　编辑 <code>config/llm_settings.yaml</code> 填 4 字段（provider / base_url / model / api_key）后重启应用启用 LLM 模式。"
        f"</div>",
        unsafe_allow_html=True,
    )


__all__ = ["is_configured", "missing_fields", "render_banner", "load_config", "CONFIG_PATH"]