# -*- coding: utf-8 -*-
"""trace_studio.py — 单独 import web.app 然后跑一次 /studio 路由 context，看时间分布"""

import sys
import time
import cProfile
import pstats
from pathlib import Path

ROOT = Path(r"C:\ideon\mcd-ai-content-platform")
sys.path.insert(0, str(ROOT / "web"))

# 模拟 ASGI 调用
print("[import] start ...")
t0 = time.perf_counter()
from app import app, _01_context, templates  # noqa
t_import = time.perf_counter() - t0
print(f"[import] done in {t_import:.2f}s")

# 模拟一次 TemplateResponse（不真发 HTTP）
from starlette.requests import Request
scope = {
    "type": "http",
    "method": "GET",
    "path": "/studio",
    "query_string": b"",
    "headers": [(b"host", b"127.0.0.1")],
}
req = Request(scope)

print("[ctx] start ...")
t0 = time.perf_counter()
ctx = _01_context()
t_ctx = time.perf_counter() - t0
print(f"[ctx] done in {t_ctx:.4f}s, keys={len(ctx)}")

print("[template] start ...")
t0 = time.perf_counter()
tmpl = templates.env.get_template("pages/01_内容工坊.html")
t_tmpl_lookup = time.perf_counter() - t0
print(f"[template] lookup in {t_tmpl_lookup:.4f}s")

print("[render] start ...")
t0 = time.perf_counter()
html = tmpl.render(ctx)
t_render = time.perf_counter() - t0
print(f"[render] done in {t_render:.4f}s, size={len(html)} chars")

# 用 cProfile 跑一次完整 ctx + render
print("\n[cProfile] full ctx + render ...")

def full():
    ctx2 = _01_context()
    tmpl2 = templates.env.get_template("pages/01_内容工坊.html")
    tmpl2.render(ctx2)

profiler = cProfile.Profile()
profiler.enable()
full()
profiler.disable()

stats = pstats.Stats(profiler).strip_dirs().sort_stats("cumulative")
stats.print_stats(30)
