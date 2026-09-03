# -*- coding: utf-8 -*-
"""trace_01.py — 拆解 _01_context() 内部哪一步慢"""

import sys
import time
from pathlib import Path

ROOT = Path(r"C:\ideon\mcd-ai-content-platform")
sys.path.insert(0, str(ROOT / "web"))

print("[import] ...")
t = time.perf_counter()
from app import app, _01_context, base_context
from app import get_product_categories, get_benefit_types, get_custom_label, get_llm_status
from app import options_with_custom, TARGET_AUDIENCE, OBJECTIVES, STAGES, TONES, CHANNELS, SCENES, ACTIONS, PLAN_TYPES, COUPON_FLAGS
from app import S_01
from app import predict_l1
print(f"[import] {time.perf_counter()-t:.2f}s")

t = time.perf_counter(); base_context("studio"); print(f"  base_context:           {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = get_product_categories(); print(f"  get_product_categories: {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = get_benefit_types(); print(f"  get_benefit_types:      {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = get_custom_label(); print(f"  get_custom_label:       {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = options_with_custom(get_product_categories()); print(f"  options_with_custom:    {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = get_llm_status(); print(f"  get_llm_status:         {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); x = predict_l1(title="t", body="b", channel="APP Push", plan_type="未知", coupon="未知", workday="通用"); print(f"  predict_l1:             {(time.perf_counter()-t)*1000:.2f}ms")

# _01_context 完整跑
t = time.perf_counter()
ctx = _01_context()
print(f"\n  _01_context total:      {(time.perf_counter()-t)*1000:.2f}ms, keys={len(ctx)}")

# 第二次再跑
t = time.perf_counter()
ctx = _01_context()
print(f"  _01_context warm:       {(time.perf_counter()-t)*1000:.2f}ms")
