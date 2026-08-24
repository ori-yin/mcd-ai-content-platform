# -*- coding: utf-8 -*-
r"""
tests/verify.py — 无 pytest 依赖的集成验证

范式：仿 C:\ideon\mcd-ctr-predictor\tests\verify.py
- 用 ast.parse + exec 注入 namespace（兼容旧项目的 @st.cache_data）
- 直接 import 纯 函数（适合新项目已解耦的函数）
- 无依赖，CI 友好，跨平台

Phase 0：空骨架，仅占位 + 5 个最小用例
Phase 1+：逐步添加 CTR Adapter / Rule Engine / Generation Service 用例

运行：python tests/verify.py
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ============================================================
# Test helpers
# ============================================================

_passed = 0
_failed = 0


def _check(name: str, condition: bool, detail: str = ""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"[PASS] {name}")
    else:
        _failed += 1
        print(f"[FAIL] {name}: {detail}")


def _section(title: str):
    print(f"\n--- {title} ---")


# ============================================================
# 1) 项目骨架完整性
# ============================================================

_section("1) 项目骨架")

def test_project_skeleton():
    required_files = [
        "PRD.md",
        "Handoff.md",
        "CLAUDE.md",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "setup_and_run.bat",
        "data/ctr_baseline.json",
        "data/custom_dict.txt",
        "data/stopwords.txt",
        "data/frameworks.json",
        ".claude/agents/code-reviewer.md",
        ".claude/agents/integration-helper.md",
        ".claude/agents/test-runner.md",
    ]
    for f in required_files:
        path = ROOT / f
        _check(f"file exists: {f}", path.exists(), f"missing: {path}")


# ============================================================
# 2) baseline JSON 契约（CTR 域事实基础）
# ============================================================

_section("2) baseline JSON 契约")

def test_baseline_json():
    import json
    path = ROOT / "data" / "ctr_baseline.json"
    if not path.exists():
        _check("ctr_baseline.json exists", False, "missing")
        return
    bl = json.loads(path.read_text(encoding="utf-8"))

    _check("baseline has version", "version" in bl, "missing version")
    _check("baseline has dimensions", "dimensions" in bl, "missing dimensions")

    dims = bl.get("dimensions", {})
    expected_dims = ["渠道", "渠道_x_是否用券", "渠道_x_计划类型", "渠道_x_工作日类型", "渠道_x_标题字数"]
    for d in expected_dims:
        _check(f"baseline has dimension: {d}", d in dims, f"missing: {d}")

    # 渠道白名单
    channel_data = dims.get("渠道", {}).get("data", {})
    if channel_data:
        for ch, ctr in list(channel_data.items())[:3]:
            _check(f"channel {ch} CTR is float", isinstance(ctr, (int, float)),
                   f"got {type(ctr).__name__}: {ctr}")


# ============================================================
# 3) 词典文件可读性
# ============================================================

_section("3) 词典文件")

def test_dict_files():
    custom = ROOT / "data" / "custom_dict.txt"
    stop = ROOT / "data" / "stopwords.txt"
    _check("custom_dict.txt exists", custom.exists(), "missing")
    _check("stopwords.txt exists", stop.exists(), "missing")

    if custom.exists():
        lines = custom.read_text(encoding="utf-8").strip().split("\n")
        _check(f"custom_dict has lines (got {len(lines)})", len(lines) > 0,
               "empty dict")

    if stop.exists():
        content = stop.read_text(encoding="utf-8")
        _check("stopwords.txt non-empty", len(content) > 0, "empty")


# ============================================================
# 4) frameworks.json 结构
# ============================================================

_section("4) frameworks.json")

def test_frameworks():
    import json
    path = ROOT / "data" / "frameworks.json"
    if not path.exists():
        _check("frameworks.json exists", False, "missing")
        return
    fw = json.loads(path.read_text(encoding="utf-8"))
    _check("frameworks is list or dict",
           isinstance(fw, (list, dict)),
           f"got {type(fw).__name__}")


# ============================================================
# 5) PRD 三处补充章节存在
# ============================================================

_section("5) PRD 三处补充")

def test_prd_supplements():
    prd = ROOT / "PRD.md"
    if not prd.exists():
        _check("PRD.md exists", False, "missing")
        return
    content = prd.read_text(encoding="utf-8")

    _check("PRD §4.0 CTR 三入口", "## 4.0" in content and "CTR 预测三入口" in content,
           "missing §4.0")
    _check("PRD §13.5 Adapter 策略", "## 13.5" in content and "Adapter 策略" in content,
           "missing §13.5")
    _check("PRD §15.A 工程化配套", "## 15.A" in content and "工程化配套" in content,
           "missing §15.A")


# ============================================================
# 6) CTR Adapter 纯函数（Phase 1a）
# ============================================================

_section("6) CTR Adapter — baseline_lookup")

def test_adapter_baseline_lookup():
    from adapters.ctr_predictor_adapter import (
        get_baseline_ctr, get_time_multiplier, get_baseline,
    )
    bl = get_baseline()

    # baseline JSON 必含 optimal_chars（CLAUDE.md §4.3 强制）
    _check("baseline has optimal_chars", "optimal_chars" in bl,
           "missing optimal_chars field")

    # 渠道整体
    v = get_baseline_ctr("APP Push")
    _check("APP Push 渠道整体 CTR is float",
           isinstance(v, (int, float)) and 0 < v < 1,
           f"got {v!r}")

    # 字段优先级：char_range 命中应优先于其他
    v_cr = get_baseline_ctr("APP Push", char_range="5-6字")
    _check("APP Push_5-6字 命中标题字数维度",
           isinstance(v_cr, (int, float)) and 0 < v_cr < 1,
           f"got {v_cr!r}")

    # 渠道不存在 → None（不抛异常）
    v_none = get_baseline_ctr("不存在的渠道")
    _check("unknown channel → None", v_none is None, f"got {v_none!r}")

    # 时段系数 clamp 到 [0.5, 2.5]
    tm_work = get_time_multiplier("9:30")
    _check("时段系数 9:30 in [0.5, 2.5]", 0.5 <= tm_work <= 2.5, f"got {tm_work}")
    tm_none = get_time_multiplier("")
    _check("空时间 → 1.0", tm_none == 1.0, f"got {tm_none}")


_section("7) CTR Adapter — char_utils")

def test_adapter_char_utils():
    from adapters.ctr_predictor_adapter import (
        count_chars, get_char_range, suggest_char_range, get_baseline,
    )
    bl = get_baseline()

    _check("count_chars('') = 0", count_chars("") == 0, "non-zero")
    _check("count_chars(' hello ') = 5", count_chars(" hello ") == 5, "wrong")

    # 字数区间
    _check("get_char_range 5字 → '5-6字'", get_char_range("五字标题") == "5-6字",
           f"got {get_char_range('五字标题')}")
    _check("get_char_range 30字 → '30字'", get_char_range("a" * 30) == "30字",
           f"got {get_char_range('a' * 30)}")

    # suggest_char_range 从 baseline.optimal_chars 读
    s_ok = suggest_char_range("APP Push", "测试标题啊", baseline=bl)  # 5 字
    _check("suggest APP Push 5字 → 在5-12字最优区间内",
           "5-12字" in s_ok and "最优" in s_ok, f"got {s_ok!r}")

    s_short = suggest_char_range("企微1v1", "太短", baseline=bl)
    _check("suggest 企微1v1 2字 → 偏短",
           "偏短" in s_short and "13-18字" in s_short, f"got {s_short!r}")

    s_long = suggest_char_range("企微1v1", "a" * 30, baseline=bl)
    _check("suggest 企微1v1 30字 → 偏长",
           "偏长" in s_long and "13-18字" in s_long, f"got {s_long!r}")


_section("8) CTR Adapter — column_mapping")

def test_adapter_column_mapping():
    from adapters.ctr_predictor_adapter import auto_detect, auto_detect_all

    cols = ["标题title", "内容", "渠道", "用券", "工作日", "发送时间", "plan_type", "Owner"]
    from adapters.ctr_predictor_adapter import KNOWN_TITLE_ALIASES
    _check("auto_detect '标题title' (alias 严格匹配)",
           auto_detect(cols, KNOWN_TITLE_ALIASES) == "标题title",
           "not matched")
    # 严格匹配：'title' 不应误匹配 'subtitle'
    _check("strict match: 'title' ≠ 'subtitle'",
           auto_detect(["subtitle", "title"], ["title"]) == "title",
           "loose match")

    m = auto_detect_all(cols)
    _check("auto_detect_all 8 字段全命中",
           all(m[k] is not None for k in [
               "标题", "正文", "渠道", "是否用券", "工作日类型",
               "发送时间", "计划类型", "预算Owner"]),
           f"miss: {m}")


_section("9) CTR Adapter — prompt_builder")

def test_adapter_prompt_builder():
    from adapters.ctr_predictor_adapter import (
        build_context_for_llm, enrich_rows_for_llm, get_baseline,
    )
    bl = get_baseline()

    ctx = build_context_for_llm(baseline=bl)
    _check("context 包含 '麦当劳Push CTR基准参考'",
           "麦当劳Push CTR基准参考" in ctx, "missing header")
    _check("context 包含渠道标题",
           "各渠道CTR基准" in ctx and "APP Push" in ctx, "missing channel data")

    # enrich 单行
    rows = [{"标题": "测试", "内容": "正文", "渠道": "APP Push",
             "是否用券": "否", "工作日类型": "工作日",
             "发送时间": "9:30", "计划类型": "普通Plan", "预算Owner": ""}]
    enriched = enrich_rows_for_llm(rows, baseline=bl)
    _check("enrich 返回 list", isinstance(enriched, list) and len(enriched) == 1,
           "wrong shape")
    _check("enrich 行新增 _bl_str",
           "_bl_str" in enriched[0] and isinstance(enriched[0]["_bl_str"], str),
           f"missing _bl_str: {enriched[0]}")
    _check("enrich 行新增 _tm",
           "_tm" in enriched[0] and isinstance(enriched[0]["_tm"], (int, float)),
           f"missing _tm: {enriched[0]}")
    _check("enrich _tm in [0.5, 2.5]",
           0.5 <= enriched[0]["_tm"] <= 2.5, f"got {enriched[0]['_tm']}")


# ============================================================
# 10) PredictionResult 四态（Phase 1b — core/schemas.py）
# ============================================================

_section("10) PredictionResult 四态")

def test_prediction_result():
    from core import PredictionResult

    # 四态构造合法
    p1 = PredictionResult.baseline_only(0.0357)
    _check("baseline_only pred_ctr set", p1.pred_ctr == 0.0357, f"got {p1.pred_ctr}")
    _check("baseline_only has_ctr=True", p1.has_ctr, "should be aggregable")

    p2 = PredictionResult.model_prediction(0.04, 0.8, "加emoji")
    _check("model_prediction pred_ctr+confidence", p2.pred_ctr == 0.04 and p2.confidence == 0.8,
           f"got {p2.pred_ctr}/{p2.confidence}")

    p3 = PredictionResult.demo(0.03, suggestion="演示数据")
    _check("demo is_demo=True", p3.is_demo, "wrong is_demo")

    p4 = PredictionResult.unavailable("API 限流")
    _check("unavailable has_ctr=False", not p4.has_ctr, "should not aggregate")
    _check("unavailable error set", p4.error == "API 限流", f"got {p4.error}")

    # 非法 result_type 应抛 ValueError
    raised = False
    try:
        PredictionResult(result_type="prediction_accuracy_77", pred_ctr=0.03)
    except ValueError:
        raised = True
    _check("非法 result_type → ValueError", raised, "should reject")

    # pred_ctr 越界应抛
    raised = False
    try:
        PredictionResult(result_type="model_prediction", pred_ctr=1.5)
    except ValueError:
        raised = True
    _check("pred_ctr>1 → ValueError", raised, "should reject")

    # confidence 越界应抛
    raised = False
    try:
        PredictionResult(result_type="model_prediction", pred_ctr=0.03, confidence=1.5)
    except ValueError:
        raised = True
    _check("confidence>1 → ValueError", raised, "should reject")

    # to_dict 序列化
    d = p1.to_dict()
    _check("to_dict 含 result_type", d["result_type"] == "baseline_only",
           f"got {d['result_type']}")
    _check("label 四态映射",
           p1.label == "历史基准" and p2.label == "LLM 预测"
           and p3.label == "演示数据" and p4.label == "无结果",
           f"got {[p1.label, p2.label, p3.label, p4.label]}")


# ============================================================
# 11) ProviderRouter JSON 解析（Phase 1b — core/llm_gateway.py）
# ============================================================

_section("11) ProviderRouter JSON 解析")

def test_provider_router_parse():
    from core import ProviderRouter

    # 标准 JSON 数组
    raw = '[{"pred_ctr": 0.04, "confidence": 0.8, "suggestion": "ok"}]'
    rows = ProviderRouter.parse_json_response(raw, expected_count=1)
    _check("标准 JSON 解析", rows[0]["pred_ctr"] == 0.04, f"got {rows[0]}")

    # markdown ```json``` 包裹
    raw_md = '```json\n[{"pred_ctr": 0.05, "confidence": 0.7, "suggestion": "x"}]\n```'
    rows = ProviderRouter.parse_json_response(raw_md, expected_count=1)
    _check("markdown 包裹解析", rows[0]["pred_ctr"] == 0.05, f"got {rows[0]}")

    # 多余前缀文字
    raw_pre = '好的，以下是结果 [{"pred_ctr": 0.06, "confidence": 0.9, "suggestion": "y"}]'
    rows = ProviderRouter.parse_json_response(raw_pre, expected_count=1)
    _check("多余前缀解析", rows[0]["pred_ctr"] == 0.06, f"got {rows[0]}")

    # 长度不匹配 → 截断/补空
    raw_short = '[{"pred_ctr": 0.01, "confidence": 0.5, "suggestion": "1"}, {"pred_ctr": 0.02, "confidence": 0.6, "suggestion": "2"}]'
    rows = ProviderRouter.parse_json_response(raw_short, expected_count=3)
    _check("长度不匹配补空", len(rows) == 3 and rows[2].get("pred_ctr") is None,
           f"got len={len(rows)} last={rows[2]}")

    # _error 标记 → 返回全部 _error 行
    raw_err = '{"_error": "API错误: rate limit"}'
    rows = ProviderRouter.parse_json_response(raw_err, expected_count=2)
    _check("_error 标记返回 2 行 _error",
           len(rows) == 2 and "_error" in rows[0].get("suggestion", "") or "错误" in rows[0].get("suggestion", ""),
           f"got {rows}")

    # 完全 JSON 失败 → 全部 _error 行
    rows = ProviderRouter.parse_json_response("not json at all", expected_count=2)
    _check("完全 JSON 失败", len(rows) == 2 and "JSON失败" in rows[0]["suggestion"],
           f"got {rows}")

    # 空响应
    rows = ProviderRouter.parse_json_response("", expected_count=1)
    _check("空响应", len(rows) == 1, f"got {len(rows)}")

    # 非法 provider 应抛 ValueError
    raised = False
    try:
        ProviderRouter(provider="unknown")
    except ValueError:
        raised = True
    _check("非法 provider → ValueError", raised, "should reject")


# ============================================================
# 12) CTRPredictionAdapter 四态行为（Phase 1b — adapters/）
# ============================================================

_section("12) CTRPredictionAdapter 四态")

def test_ctr_prediction_adapter():
    from adapters.ctr_predictor_adapter import CTRPredictionAdapter

    rows = [{"标题": "测试标题", "内容": "正文", "渠道": "APP Push",
             "是否用券": "否", "工作日类型": "工作日",
             "发送时间": "9:30", "计划类型": "普通Plan", "预算Owner": ""}]

    # mode = "baseline_only"
    a_bl = CTRPredictionAdapter(mode="baseline_only")
    res_bl = a_bl.predict_batch(rows)
    _check("baseline_only 返回 1 条",
           len(res_bl) == 1 and res_bl[0].result_type == "baseline_only",
           f"got {res_bl}")
    _check("baseline_only baseline_ctr set",
           res_bl[0].baseline_ctr is not None and 0 < res_bl[0].baseline_ctr < 1,
           f"got {res_bl[0].baseline_ctr}")

    # mode = "demo"
    a_demo = CTRPredictionAdapter(mode="demo")
    res_demo = a_demo.predict_batch(rows)
    _check("demo 返回 1 条",
           len(res_demo) == 1 and res_demo[0].result_type == "demo",
           f"got {res_demo}")
    _check("demo is_demo=True + pred_ctr in (0,1)",
           res_demo[0].is_demo and 0 < res_demo[0].pred_ctr < 1,
           f"got {res_demo[0]}")

    # mode = "unavailable"
    a_off = CTRPredictionAdapter(mode="unavailable")
    res_off = a_off.predict_batch(rows)
    _check("unavailable 返回 1 条 + has_ctr=False",
           len(res_off) == 1 and res_off[0].result_type == "unavailable"
           and not res_off[0].has_ctr,
           f"got {res_off}")

    # mode = "existing_predictor" 无 router → 降级 unavailable
    a_no_router = CTRPredictionAdapter(mode="existing_predictor", router=None)
    res_nr = a_no_router.predict_batch(rows)
    _check("existing_predictor 无 router → unavailable",
           res_nr[0].result_type == "unavailable" and "ProviderRouter" in res_nr[0].error,
           f"got {res_nr[0]}")

    # 非法 mode → ValueError
    raised = False
    try:
        CTRPredictionAdapter(mode="prediction_accuracy_77")
    except ValueError:
        raised = True
    _check("非法 mode → ValueError", raised, "should reject")

    # 空 rows → 空 list
    _check("空 rows → 空 list", a_bl.predict_batch([]) == [], "wrong shape")

    # predict_one 便捷方法
    res_one = a_bl.predict_one(rows[0])
    _check("predict_one 兼容", res_one.result_type == "baseline_only",
           f"got {res_one}")


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("MCD AI 内容运营工作台 — 集成验证")
    print("=" * 60)

    test_project_skeleton()
    test_baseline_json()
    test_dict_files()
    test_frameworks()
    test_prd_supplements()
    test_adapter_baseline_lookup()
    test_adapter_char_utils()
    test_adapter_column_mapping()
    test_adapter_prompt_builder()
    test_prediction_result()
    test_provider_router_parse()
    test_ctr_prediction_adapter()

    print("\n" + "=" * 60)
    print(f"结果: {_passed} PASS, {_failed} FAIL")
    print("=" * 60)

    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
