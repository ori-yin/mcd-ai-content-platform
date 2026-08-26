# -*- coding: utf-8 -*-
"""
ui/llm_status.py — LLM 配置状态检测（业务确认 #10）

读 config/llm_settings.yaml，判断 4 字段是否全部为空：
- 全空 → Demo 模式，入口页需显示 banner 提示
- 有任一字段非空 → 视作已配置（按字段完整性校验）

约束：
- 不抛异常（yaml 不存在或格式错视作未配置）
- 简单实现：手写 yaml 行解析，避 PyYAML 依赖
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "llm_settings.yaml"
REQUIRED_FIELDS = ("provider", "base_url", "model", "api_key")


def _read_yaml(path: Path) -> Dict[str, str]:
    """极简 yaml 解析（只支持 key: value 单行）。

    处理：
    - 行内注释（# 后）
    - 前后引号（" / '）
    - 空字符串（"" / ''）
    """
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        # 整行注释
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        # 去掉行内注释（只在 value 端）
        if "#" in val:
            val = val.split("#", 1)[0]
        val = val.strip()
        # 去引号
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if key in REQUIRED_FIELDS:
            out[key] = val
    return out


def is_configured() -> bool:
    """4 字段是否全部非空。"""
    cfg = _read_yaml(CONFIG_PATH)
    return all(cfg.get(k, "").strip() for k in REQUIRED_FIELDS)


def missing_fields() -> list:
    """返回空字段列表（用于 banner 文案）。"""
    cfg = _read_yaml(CONFIG_PATH)
    return [k for k in REQUIRED_FIELDS if not cfg.get(k, "").strip()]


def render_banner():
    """在入口页渲染"LLM 未配置"banner。已配置则不渲染。"""
    import streamlit as st
    if is_configured():
        return
    miss = missing_fields()
    msg = "LLM 未配置（Demo 模式）" if len(miss) == 4 else f"LLM 配置不完整：缺 {', '.join(miss)}"
    st.markdown(
        f'<div class="llm-warning">'
        f"<b>{msg}</b>　编辑 <code>config/llm_settings.yaml</code> 填 4 字段（provider / base_url / model / api_key）后重启应用启用 LLM 模式。"
        f"</div>",
        unsafe_allow_html=True,
    )


__all__ = ["is_configured", "missing_fields", "render_banner", "CONFIG_PATH"]