# -*- coding: utf-8 -*-
"""trace_studio_v2.py — 拆解 /studio 1.2s cold 的真实时间分布（不经过 HTTP）"""

import sys
import time
from pathlib import Path

ROOT = Path(r"C:\ideon\mcd-ai-content-platform")
sys.path.insert(0, str(ROOT / "web"))

print("[import] ...")
t = time.perf_counter()
from app import app, _01_context, templates, get_product_categories, get_benefit_types, get_custom_label, get_llm_status
print(f"[import] {time.perf_counter()-t:.2f}s")

# 检查字典是否已预热（lru_cache 命中？= 立即返回）
print("\n[dict warm?]")
t = time.perf_counter()
get_product_categories()
print(f"  product_categories: {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter()
get_benefit_types()
print(f"  benefit_types:      {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter()
get_custom_label()
print(f"  custom_label:       {(time.perf_counter()-t)*1000:.2f}ms")
t = time.perf_counter()
get_llm_status()
print(f"  llm_status:         {(time.perf_counter()-t)*1000:.2f}ms")

# 模拟路由 handler
from starlette.requests import Request
scope = {
    "type": "http", "method": "GET", "path": "/studio",
    "query_string": b"", "headers": [(b"host", b"127.0.0.1")],
}
req = Request(scope)

print("\n[/studio cold path]")
t = time.perf_counter()
ctx = _01_context()
print(f"  _01_context:   {(time.perf_counter()-t)*1000:.2f}ms")

t = time.perf_counter()
tmpl = templates.env.get_template("pages/01_内容工坊.html")
print(f"  get_template:  {(time.perf_counter()-t)*1000:.2f}ms")

t = time.perf_counter()
resp = templates.TemplateResponse(req, "pages/01_内容工坊.html", ctx)
print(f"  TemplateResponse: {(time.perf_counter()-t)*1000:.2f}ms")

print(f"  resp body size: {len(resp.body)} chars")
