# -*- coding: utf-8 -*-
"""trace_01b.py — 复制 _01_context 步骤逐行计时"""
import sys, time
from pathlib import Path
ROOT = Path(r"C:\ideon\mcd-ai-content-platform")
sys.path.insert(0, str(ROOT / "web"))

t = time.perf_counter()
from app import base_context, get_product_categories, get_benefit_types, get_custom_label
from app import options_with_custom, TARGET_AUDIENCE, OBJECTIVES, STAGES, TONES, CHANNELS, SCENES, ACTIONS, PLAN_TYPES, COUPON_FLAGS
from app import S_01, predict_l1
print(f"import: {time.perf_counter()-t:.2f}s\n")

# 1) base_context
t = time.perf_counter(); ctx = base_context("studio"); print(f"1) base_context:           {(time.perf_counter()-t)*1000:.2f}ms")

# 2) 字典 3 项
t = time.perf_counter(); product_cats = get_product_categories(); print(f"2) get_product_categories: {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); benefit_types = get_benefit_types(); print(f"3) get_benefit_types:      {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); custom_label = get_custom_label(); print(f"4) get_custom_label:       {(time.perf_counter()-t)*1000:.2f}ms")

# 3) options_with_custom
t = time.perf_counter(); pc = options_with_custom(product_cats); print(f"5) options_with_custom p:  {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter(); bt = options_with_custom(benefit_types); print(f"6) options_with_custom b:  {(time.perf_counter()-t)*1000:.2f}ms")

# 4) ctx.update 一次性
t = time.perf_counter()
ctx.update({
    "product_categories": pc, "benefit_types": bt,
    "audience_opts": TARGET_AUDIENCE, "objective_opts": OBJECTIVES,
    "stage_opts": STAGES, "tone_opts": TONES, "channel_opts": CHANNELS,
    "scene_opts": SCENES, "action_opts": ACTIONS, "plan_type_opts": PLAN_TYPES,
    "coupon_opts": COUPON_FLAGS, "ctr_mode_options": S_01["ctr_mode_options"],
    "task_input": S_01["task_input"] or {},
    "candidates": S_01["candidates"],
    "selected_id": S_01["selected_id"],
    "rule_results": S_01["rule_results"],
    "ctr_results": S_01["ctr_results"],
    "similar_summary": S_01["similar_summary"],
    "show_l1": S_01["show_l1"],
    "ctr_mode": S_01["ctr_mode"],
    "last_error": S_01["last_error"],
})
print(f"7) ctx.update (16 keys):   {(time.perf_counter()-t)*1000:.2f}ms")

# 5) 派生 cand/rule/ctr
t = time.perf_counter()
sel_id = S_01["selected_id"]
cand_idx = next((i for i, c in enumerate(S_01["candidates"]) if c.get("id") == sel_id), 0) if S_01["candidates"] else 0
selected_cand = S_01["candidates"][cand_idx] if S_01["candidates"] else {}
selected_rule = S_01["rule_results"][cand_idx] if S_01["rule_results"] and cand_idx < len(S_01["rule_results"]) else None
selected_ctr = S_01["ctr_results"][cand_idx] if S_01["ctr_results"] and cand_idx < len(S_01["ctr_results"]) else None
print(f"8) derived cand/rule/ctr:  {(time.perf_counter()-t)*1000:.2f}ms")

# 6) L1 派生 (默认走 l1_ctr=None)
t = time.perf_counter()
l1_ctr = None
show_l1 = S_01["show_l1"]
print(f"   show_l1={show_l1}, candidates={len(S_01['candidates'])}")
print(f"9) L1 derive (default off): {(time.perf_counter()-t)*1000:.2f}ms")
