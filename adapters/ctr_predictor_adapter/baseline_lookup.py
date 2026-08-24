# -*- coding: utf-8 -*-
r"""
baseline_lookup.py — CTR baseline 查找（纯函数）

来源：C:\ideon\mcd-ctr-predictor\ctr_predictor.py 第 54-120 行（机械搬迁）。

Phase 1a 约束：
- 移除 @st.cache_data（CLAUDE.md §3 架构：cache_adapter 替 Streamlit 缓存）
- baseline dict 通过参数注入，避免模块级全局读取
- lazy load 单进程内 lru_cache 仅作性能优化，可被注入 baseline 覆盖
"""

from __future__ import annotations
import json
import re
import functools
from pathlib import Path
from typing import Optional


DEFAULT_BASELINE_PATH = Path(__file__).resolve().parents[2] / "data" / "ctr_baseline.json"


@functools.lru_cache(maxsize=1)
def _load_default_baseline() -> dict:
    """加载内置默认 baseline JSON（单进程内缓存）。"""
    p = DEFAULT_BASELINE_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_baseline(path: Optional[str] = None, baseline: Optional[dict] = None) -> dict:
    """获取 baseline dict。优先级：参数 baseline > 参数 path > 内置默认。"""
    if baseline is not None:
        return baseline
    if path is not None:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return {}
    return _load_default_baseline()


def get_baseline_ctr(
    channel: str,
    coupon: Optional[str] = None,
    workday: Optional[str] = None,
    plan_type: Optional[str] = None,
    owner: Optional[str] = None,
    char_range: Optional[str] = None,
    baseline: Optional[dict] = None,
) -> Optional[float]:
    """按优先级回退查找 CTR：标题字数 > 计划类型 > Owner > 用券 > 工作日 > 渠道整体。

    来源：ctr_predictor.py:54-85
    """
    ch = channel.strip()
    d = get_baseline(baseline=baseline).get("dimensions", {})

    # 标题字数优先
    if char_range and f"{ch}_{char_range}" in d.get("渠道_x_标题字数", {}).get("data", {}):
        return d["渠道_x_标题字数"]["data"][f"{ch}_{char_range}"]

    # 渠道 × 计划类型
    if plan_type in ("AARRPlan", "普通Plan") and f"{ch}_{plan_type}" in d.get("渠道_x_计划类型", {}).get("data", {}):
        return d["渠道_x_计划类型"]["data"][f"{ch}_{plan_type}"]

    # 渠道 × 预算owner
    if owner and f"{ch}_{owner}" in d.get("渠道_x_预算owner", {}).get("data", {}):
        return d["渠道_x_预算owner"]["data"][f"{ch}_{owner}"]

    # 渠道 × 是否用券
    if coupon in ("是", "否"):
        v = d.get("渠道_x_是否用券", {}).get("data", {}).get(f"{ch}_{coupon}")
        if v:
            return v

    # 渠道 × 工作日类型
    if workday in ("工作日", "非工作日"):
        v = d.get("渠道_x_工作日类型", {}).get("data", {}).get(f"{ch}_{workday}")
        if v:
            return v

    # 渠道整体
    return d.get("渠道", {}).get("data", {}).get(ch, None)


def get_time_multiplier(time_str: str, baseline: Optional[dict] = None) -> float:
    """时段系数（0.5 ~ 2.5）。四级回退：HH:MM > 区间 > HH时 > 任意数字。

    来源：ctr_predictor.py:88-120
    区间分支必须在 HH时 之前（否则 "8-10时" 会被抢先匹配成 10）。
    """
    if not time_str:
        return 1.0
    s = str(time_str).strip()
    hour = None
    m = re.search(r"(\d{1,2})\s*:\s*\d{1,2}", s)
    if m:
        hour = int(m.group(1))
    else:
        m = re.search(r"(\d{1,2})\s*[-~]\s*(\d{1,2})", s)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            hour = (lo + hi) // 2 if lo <= hi else (hi + lo) // 2
        else:
            m = re.search(r"(\d{1,2})\s*时", s)
            if m:
                hour = int(m.group(1))
            else:
                m = re.search(r"(\d{1,2})", s)
                if m:
                    hour = int(m.group(1))
    if hour is None or not (0 <= hour <= 23):
        return 1.0
    td = get_baseline(baseline=baseline).get("dimensions", {}).get("时段_小时", {}).get("data", {})
    if not td:
        return 1.0
    vals = list(td.values())
    overall_avg = sum(vals) / len(vals) if vals else 0.002
    hour_ctr = td.get(f"{hour}时", overall_avg)
    mult = hour_ctr / overall_avg if overall_avg else 1.0
    return max(0.5, min(2.5, mult))