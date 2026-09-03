# -*- coding: utf-8 -*-
"""bench_routes.py — 测 4 个路由首/二次访问延迟，输出可对比的表格

用法:
    python tools/_archive/bench_routes.py [tag]

tag 用于在结果前加注释（基线 / 优化B后 / 优化D后 / 优化A后）
"""

import sys
import time
import statistics
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "http://127.0.0.1:8530"
ROUTES = ["/", "/studio", "/insights", "/feedback"]
WARM_N = 7  # 每个路由 warm 取 7 次，剔首尾取中位数
COLD_N = 1  # cold 取 1 次


def fetch(path: str) -> float:
    url = BASE + path
    req = urllib.request.Request(url, method="GET")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
            code = r.status
    except Exception as e:
        return -1.0
    return time.perf_counter() - t0


def bench_one(path: str):
    # cold 1 次
    cold = fetch(path)
    # warm N 次
    warm = [fetch(path) for _ in range(WARM_N)]
    warm_sorted = sorted(warm)
    # 剔首尾
    trim = warm_sorted[1:-1]
    median = statistics.median(trim)
    p10 = warm_sorted[1]
    p90 = warm_sorted[-2]
    return {
        "path": path,
        "cold_ms": cold * 1000,
        "warm_p10_ms": p10 * 1000,
        "warm_median_ms": median * 1000,
        "warm_p90_ms": p90 * 1000,
        "all_warm_ms": [round(x * 1000, 1) for x in warm],
    }


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "未命名"
    print(f"=== bench · {tag} ===")
    print(f"{'path':<14} {'cold':>8} {'p10':>8} {'median':>8} {'p90':>8}  raw warm")
    rows = []
    for r in ROUTES:
        row = bench_one(r)
        rows.append(row)
        print(
            f"{row['path']:<14} "
            f"{row['cold_ms']:>7.1f}ms "
            f"{row['warm_p10_ms']:>7.1f}ms "
            f"{row['warm_median_ms']:>7.1f}ms "
            f"{row['warm_p90_ms']:>7.1f}ms  "
            f"{row['all_warm_ms']}"
        )
    print()


if __name__ == "__main__":
    main()
