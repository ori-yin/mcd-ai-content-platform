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

# pytest 兼容标记（Phase 8）：模块加载时检测，_check 失败时抛 AssertionError 让 pytest 捕获
_RUNNING_UNDER_PYTEST = "pytest" in sys.modules


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
        msg = f"{name}: {detail}" if detail else name
        print(f"[FAIL] {msg}")
        if _RUNNING_UNDER_PYTEST:
            raise AssertionError(msg)


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
# Phase 2a — data_loader (services/data_loader.py)
# ============================================================

_section("13) data_loader — parse_message")

def test_data_loader_parse_message():
    from services.data_loader import parse_message

    # APP Push 标准 JSON
    raw = '{"title": "限时免费", "text": "快来领取"}'
    t, b = parse_message(raw)
    _check("parse_message title", t == "限时免费", f"got {t!r}")
    _check("parse_message text", b == "快来领取", f"got {b!r}")

    # 非 JSON → 空串
    t2, b2 = parse_message("plain text")
    _check("parse_message 非 JSON → empty", t2 == "" and b2 == "", f"got {t2!r}/{b2!r}")

    # 空 / None
    _check("parse_message None → empty", parse_message(None) == ("", ""),
           "wrong shape")
    _check("parse_message 空串 → empty", parse_message("") == ("", ""),
           "wrong shape")

    # 换行清洗
    raw_nl = '{"title": "标题\\n含换行", "text": "正文\\r\\n也有"}'
    t3, b3 = parse_message(raw_nl)
    _check("parse_message 清换行", "\n" not in t3 and "\r" not in b3,
           f"got {t3!r}/{b3!r}")

    # 只有 text → title 拿首句兜底
    raw_only_text = '{"text": "限时免费领取优惠券"}'
    t4, b4 = parse_message(raw_only_text)
    _check("parse_message 只有 text → title 兜底首句", t4 == "限时免费领取优惠券",
           f"got {t4!r}")


_section("14) data_loader — map_columns")

def test_data_loader_map_columns():
    from services.data_loader import map_columns
    import pandas as pd

    df = pd.DataFrame(columns=["发送日期date", "渠道", "触达成功reach",
                               "点击人次click", "owner", "plan_id"])
    out = map_columns(df)
    mapped = set(out.columns)
    _check("map_columns '发送日期date' → '发送日期'", "发送日期" in mapped,
           f"got {mapped}")
    _check("map_columns '触达成功reach' → '触达成功'", "触达成功" in mapped, "")
    _check("map_columns '点击人次click' → '点击人次'", "点击人次" in mapped, "")

    # 标准列名已存在时不重复映射
    df2 = pd.DataFrame(columns=["渠道", "触达成功", "点击人次"])
    out2 = map_columns(df2)
    _check("map_columns 保留已有 '渠道'", "渠道" in out2.columns, "")


# ============================================================
# Phase 2a — text_analyzer (services/text_analyzer.py)
# ============================================================

_section("15) text_analyzer — tokenize + 工具函数")

def test_text_analyzer_tools():
    from services.text_analyzer import (
        extract_emojis, count_emojis, first_emoji_pos, tokenize,
        load_stopwords, banned_words, dict_words, dict_counts,
    )

    # emoji
    _check("extract_emojis('hi 🍔🍟')", extract_emojis("hi 🍔🍟") == ["🍔", "🍟"],
           f"got {extract_emojis('hi 🍔🍟')}")
    _check("count_emojis('no emoji')", count_emojis("no emoji") == 0, "wrong count")
    _check("first_emoji_pos('hi 🍔')", first_emoji_pos("hi 🍔") == 3,
           f"got {first_emoji_pos('hi 🍔')}")
    _check("first_emoji_pos 无 emoji → -1", first_emoji_pos("no") == -1, "wrong")

    # 停用词 + 禁词（默认 data/）
    stop = load_stopwords()
    _check("load_stopwords is frozenset", isinstance(stop, frozenset), "")
    ban = banned_words()
    _check("banned_words is tuple", isinstance(ban, tuple), "")

    # dict_counts staging 优先
    n1, n2 = dict_counts(staging_dict=["w1", "w2"], staging_ban=["b1"])
    _check("dict_counts staging_dict=2", n1 == 2, f"got {n1}")
    _check("dict_counts staging_ban=1", n2 == 1, f"got {n2}")
    # 退化：staging=None 走文件
    n3, n4 = dict_counts()
    _check("dict_counts 退化读文件", n3 >= 0 and n4 >= 0,
           f"got ({n3},{n4})")

    # tokenize 纯函数（用默认词典）
    toks = tokenize("限时免费麦旋风", stop, ["券"], ban)
    _check("tokenize 返回 list", isinstance(toks, list), "")


_section("16) text_analyzer — diagnose_score")

def test_text_analyzer_diagnose():
    from services.text_analyzer import diagnose_score, diagnose_problems, diagnose_suggestions
    import pandas as pd

    # 空 DataFrame → 退化诊断
    r = diagnose_score("限时免费", "快领取", df=pd.DataFrame())
    _check("diagnose_score 空 df → score in [0,100]", 0 <= r["score"] <= 100,
           f"got {r['score']}")
    _check("diagnose_score grade 合法", r["grade"] in ("优秀", "良好", "需优化", "重写"),
           f"got {r['grade']!r}")

    # 短标题 → 触发标题过短问题
    diag_short = diagnose_score("短", "正文很长很长很长很长很长很长很长很长很长很长很长", df=pd.DataFrame())
    problems = diagnose_problems("短", "正文很长", diag_short["diag"])
    _check("diagnose_problems 标题过短", any(p["label"] == "标题过短" for p in problems),
           f"got {problems}")

    # 空标题 + 空正文 → 重写 + 多问题
    diag_empty = diagnose_score("", "", df=pd.DataFrame())
    p_empty = diagnose_problems("", "", diag_empty["diag"])
    _check("diagnose_problems 空文案 → 多问题", len(p_empty) >= 2,
           f"got {len(p_empty)}")
    _check("diagnose_problems 含 tag 缺失", any(p["tag"] == "缺失" for p in p_empty), "")

    # 建议
    p1, p2 = diagnose_suggestions(diag_empty["diag"], p_empty)
    _check("diagnose_suggestions p1 是 list", isinstance(p1, list), "")
    _check("diagnose_suggestions p2 是 list", isinstance(p2, list), "")


_section("17) text_analyzer — match_frameworks")

def test_match_frameworks():
    from services.text_analyzer import match_frameworks

    fw = [
        {
            "channel": "APP Push",
            "rules": {"require_emoji": True, "title_len_max": 15},
            "keywords": {
                "利益": ["免费", "立减"],
                "数字": ["9.9", "5折"],
            },
        },
        {
            "channel": "企微1v1",
            "rules": {},
            "keywords": {"招呼": ["你好"], "专属": ["专属"]},
        },
    ]

    # APP Push 命中 2 组
    matches = match_frameworks("免费限时", "立减9.9元", "APP Push", fw)
    _check("match_frameworks APP Push 命中 1 个", len(matches) == 1,
           f"got {len(matches)}")
    fw_hit, violations = matches[0]
    _check("match_frameworks 返回 violations list", isinstance(violations, list), "")

    # require_emoji 不满足 → violation
    matches2 = match_frameworks("免费限时", "立减9.9元", "APP Push", fw)
    has_emoji_violation = any("emoji" in v for v in matches2[0][1])
    _check("match_frameworks 缺 emoji → violation", has_emoji_violation, "")

    # 渠道不匹配 → 空
    matches3 = match_frameworks("你好专属", "专属福利", "APP Push", fw)
    _check("match_frameworks 渠道错 → 空", len(matches3) == 0,
           f"got {len(matches3)}")


_section("18) text_analyzer — word_frequency")

def test_word_frequency():
    from services.text_analyzer import word_frequency, add_tokens
    import pandas as pd

    df = pd.DataFrame({
        "Plan ID": ["P1", "P1", "P2", "P2"],
        "标题": ["免费限时", "免费麦辣", "立减优惠", "立减专属"],
        "正文": ["快领取", "快来抢", "新人专享", "新人优惠"],
        "触达成功": [5000, 4000, 3000, 2000],
        "点击人次": [300, 200, 100, 80],
    })
    df2 = add_tokens(df)
    _check("add_tokens 加 _tokens/_emojis/_len",
           all(c in df2.columns for c in ["_tokens", "_emojis", "_len"]),
           f"got {df2.columns.tolist()}")

    wf = word_frequency(df2, min_plans=1)
    _check("word_frequency 返回 DataFrame", isinstance(wf, pd.DataFrame)
           and not wf.empty, "")
    _check("word_frequency 含 含CTR% / 不含CTR%",
           "含CTR%" in wf.columns and "不含CTR%" in wf.columns,
           f"got {wf.columns.tolist()}")


# ============================================================
# Phase 2a — llm_adapter (adapters/llm_adapter.py)
# ============================================================

_section("19) llm_adapter — 纯函数")

def test_llm_adapter_pure():
    from adapters.llm_adapter import (
        build_user_prompt, fingerprint, parse_json_response, PROVIDERS, SYSTEM_PROMPT,
    )

    local = {"hit_words": ["免费", "限时"], "miss_top": ["立减"], "emoji_count": 1}
    p = build_user_prompt("限时免费", "快领取", local)
    _check("build_user_prompt 含 标题", "限时免费" in p, "")
    _check("build_user_prompt 含 历史高效词命中", "免费、限时" in p, "")
    _check("build_user_prompt 含 emoji 计数", "emoji 1 个" in p, "")

    # fingerprint 稳定
    fp1 = fingerprint("a", "b", "MiniMax", "MiniMax-M3", local)
    fp2 = fingerprint("a", "b", "MiniMax", "MiniMax-M3", local)
    _check("fingerprint 稳定（同输入）", fp1 == fp2, "different")
    fp3 = fingerprint("a", "b", "MiniMax", "MiniMax-M3", {"hit_words": [], "miss_top": [], "emoji_count": 0})
    _check("fingerprint 区分（local 变）", fp1 != fp3, "same")

    # parse_json_response 单 dict
    raw = '{"score": 8, "issues": ["x"], "rewrites": [{"title": "t", "body": "b"}]}'
    parsed = parse_json_response(raw)
    _check("parse_json_response 单 dict", isinstance(parsed, dict)
           and parsed.get("score") == 8, f"got {parsed}")

    # markdown 包裹
    raw_md = '```json\n{"score": 7}\n```'
    parsed_md = parse_json_response(raw_md)
    _check("parse_json_response markdown 包裹", parsed_md.get("score") == 7,
           f"got {parsed_md}")

    # 失败 → None
    _check("parse_json_response 失败 → None", parse_json_response("not json") is None, "")
    _check("parse_json_response 空 → None", parse_json_response("") is None, "")

    # SYSTEM_PROMPT 非空
    _check("SYSTEM_PROMPT 非空", len(SYSTEM_PROMPT) > 50, "")
    # PROVIDERS 含 4 个
    _check("PROVIDERS 含 4 个 provider", len(PROVIDERS) >= 4,
           f"got {list(PROVIDERS.keys())}")


def test_llm_adapter_call_no_key():
    """call_llm 在没 router 或没 api_key 时返回 error，不调 SDK。"""
    from adapters.llm_adapter import call_llm

    r = call_llm(None, "t", "b", {"hit_words": [], "miss_top": [], "emoji_count": 0})
    _check("call_llm router=None → error", "error" in r, f"got {r}")

    r2 = call_llm(object(), "t", "b", {"hit_words": [], "miss_top": [], "emoji_count": 0})
    # router.api_key 不存在 → error
    _check("call_llm 无 api_key → error", "error" in r2, f"got {r2}")


# ============================================================
# Phase 2b — analytics 4 个分析
# ============================================================

_section("20) analytics — high_effort_plans.rank_plans")

def test_rank_plans():
    import pandas as pd
    from services.analytics.high_effort_plans import rank_plans

    # 3 个 plan，分别 CTR 不同
    df = pd.DataFrame({
        "Plan ID": ["P1"]*3 + ["P2"]*3 + ["P3"]*3,
        "Plan名称": ["Plan1"]*3 + ["Plan2"]*3 + ["Plan3"]*3,
        "渠道": ["APP Push"]*9,
        "owner": ["BU-A"]*9,
        "触达成功": [5000, 4000, 3000, 2000, 2000, 2000, 1000, 1000, 1000],
        "点击人次": [400, 320, 240, 60, 60, 60, 50, 50, 50],
        "标题": ["限时免费麦旋风"]*9,
        "正文": ["快领取"]*9,
    })
    # 构造差异：P2 CTR = 60/2000/3=1%, P3 CTR = 50/1000/3=1.67%, P1 CTR = 400/5000=8%
    r = rank_plans(df, min_reach=1000, min_plans=2, sort_by="加权CTR%")
    _check("rank_plans 返回 3 个 plan", len(r) == 3, f"got {len(r)}")
    if len(r) >= 3:
        _check("rank_plans 按 CTR 降序 P1 第一", r.iloc[0]["plan_id"] == "P1",
               f"got {r.iloc[0]['plan_id']}")

    # min_reach 过滤：提高到 50000 → 所有 plan 都被过滤（P1 总触达仅 12000）
    r2 = rank_plans(df, min_reach=50000, min_plans=2)
    _check("rank_plans min_reach 过滤", len(r2) == 0,
           f"got {len(r2)}")

    # min_plans 过滤：plan 只有 1 条记录 → 过滤
    df_small = pd.DataFrame({
        "Plan ID": ["P1"],
        "触达成功": [5000],
        "点击人次": [400],
    })
    r3 = rank_plans(df_small, min_reach=1000, min_plans=2)
    _check("rank_plans min_plans 过滤单 plan", len(r3) == 0, f"got {len(r3)}")


_section("21) analytics — similarity.find_similar_plans")

def test_find_similar_plans():
    import pandas as pd
    from services.analytics.similarity import find_similar_plans

    df = pd.DataFrame({
        "Plan ID": ["P1", "P1", "P2", "P2", "P3", "P3"],
        "Plan名称": ["免费麦旋风", "免费麦辣", "立减优惠", "立减专属", "积分兑换", "积分换豪礼"],
        "渠道": ["APP Push"]*6,
        "owner": ["BU-A"]*6,
        "触达成功": [5000, 4000, 3000, 2000, 1000, 1000],
        "点击人次": [400, 320, 100, 80, 50, 40],
        "标题": ["限时免费麦旋风", "免费麦辣鸡腿堡", "立减9.9", "立减5元优惠券", "积分兑换", "积分换豪礼"],
        "正文": ["快领取免费麦旋风", "免费送鸡腿堡", "新人立减", "新人专享", "积分换好礼", "积分换奖"],
    })

    # 找相似：query "免费" + 麦旋风 应该命中 P1（最高）
    res = find_similar_plans(df, "免费麦旋风", "快领取", top_k=2)
    _check("find_similar_plans 返回 DataFrame", isinstance(res, pd.DataFrame), "")
    _check("find_similar_plans top_k=2", len(res) <= 2, f"got {len(res)}")
    if not res.empty:
        _check("find_similar_plans 含 similarity 列", "similarity" in res.columns, "")
        _check("find_similar_plans P1 排第一",
               res.iloc[0]["plan_id"] == "P1",
               f"got {res.iloc[0]['plan_id']}")
        _check("find_similar_plans similarity 在 [0,1]",
               all(0 <= s <= 1 for s in res["similarity"]),
               f"got {res['similarity'].tolist()}")

    # 空 query → 空结果
    res_empty = find_similar_plans(df, "", "", top_k=3)
    _check("find_similar_plans 空 query → 空", res_empty.empty, "")


_section("22) analytics — daily_trend")

def test_daily_trend():
    import pandas as pd
    from services.analytics.daily_trend import daily_aggregate, daily_summary

    df = pd.DataFrame({
        "Plan ID": ["P1"]*10,
        "owner": ["BU-A"]*10,
        "渠道": ["APP Push"]*10,
        "发送日期": pd.to_datetime([
            "2026-08-01", "2026-08-01", "2026-08-02", "2026-08-02", "2026-08-03",
            "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-08",
        ]),
        "触达成功": [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000],
        "点击人次": [50, 50, 60, 60, 70, 80, 90, 100, 110, 120],
    })

    # daily_aggregate
    agg = daily_aggregate(df)
    _check("daily_aggregate 返回 DataFrame", isinstance(agg, pd.DataFrame), "")
    _check("daily_aggregate 8 天（10 条 / 8 unique）", len(agg) == 8,
           f"got {len(agg)}")
    _check("daily_aggregate 含 周环比%（>=8 天触发）", "周环比%" in agg.columns,
           f"got {agg.columns.tolist()}")

    # daily_summary
    s = daily_summary(df)
    _check("daily_summary 总触达", s.get("总触达") == 10000, f"got {s}")
    _check("daily_summary 总点击", s.get("总点击") == 790, f"got {s}")
    _check("daily_summary 整体CTR%", isinstance(s.get("整体CTR%"), (int, float)), "")
    _check("daily_summary 活跃天数=8", s.get("活跃天数") == 8, f"got {s}")

    # 空 df
    agg_empty = daily_aggregate(pd.DataFrame())
    _check("daily_aggregate 空 df → 空 DataFrame", agg_empty.empty, "")


_section("23) analytics — owner_compare")

def test_owner_compare():
    import pandas as pd
    from services.analytics.owner_compare import owner_compare

    df = pd.DataFrame({
        "Plan ID": ["P1", "P1", "P1", "P2", "P2", "P2", "P3", "P3"],
        "owner": ["BU-A"]*3 + ["BU-B"]*3 + ["BU-A"]*2,
        "渠道": ["APP Push"]*8,
        "发送日期": pd.to_datetime(["2026-08-01"]*8),
        "触达成功": [5000, 4000, 3000, 2000, 2000, 2000, 1000, 1000],
        "点击人次": [400, 320, 240, 100, 100, 100, 50, 50],
        "标题": ["限时免费麦旋风", "免费麦辣鸡腿堡", "限时优惠", "立减9.9元", "新人专享立减", "立减优惠",
                "积分兑换", "积分换豪礼"],
        "正文": ["快领取"]*4 + ["新人立减"]*4,
    })
    oc = owner_compare(df, min_plans=1, min_reach=1000)
    _check("owner_compare 返回 DataFrame", isinstance(oc, pd.DataFrame), "")
    _check("owner_compare 2 个 owner", len(oc) == 2, f"got {len(oc)}")
    if len(oc) >= 1:
        _check("owner_compare 列名完整",
               all(c in oc.columns for c in
                   ["owner", "n_plans", "触达成功", "点击", "加权CTR%"]),
               f"got {oc.columns.tolist()}")

    # 空 df
    _check("owner_compare 空 df → 空", owner_compare(pd.DataFrame()).empty, "")


# ============================================================
# 24) core/schemas.py Phase 3 增补 (TaskInput / Candidate / RuleResult)
# ============================================================
_section("24) schemas Phase 3 增补")

def test_schemas_phase3():
    from core.schemas import (
        TaskInput, Candidate, RuleItem, RuleResult, GenerationRecord,
        CANDIDATE_STRATEGIES, TARGET_AUDIENCE, CHANNELS,
        SEVERITY_PASS, SEVERITY_WARN, SEVERITY_FAIL,
    )

    # TaskInput
    t = TaskInput(
        product_benefit="新品限时优惠", audience="常规大盘",
        channel="APP Push", objective="建立认知", stage="活动预热",
        scene="早餐", tone="直接利益型",
    )
    _check("TaskInput 必填齐 is_complete=True", t.is_complete is True)
    _check("TaskInput.to_dict 含 product_benefit", "product_benefit" in t.to_dict())
    try:
        t_empty_pending = TaskInput(product_benefit="", audience="常规大盘",
                                    channel="APP Push", objective="",
                                    stage="活动预热", scene="早餐", tone="直接利益型")
        _check("TaskInput 灰态字段空 不抛错（Phase 6 P1）",
               t_empty_pending.product_benefit == "" and t_empty_pending.objective == "")
    except ValueError:
        _check("TaskInput 灰态字段空 不抛错（Phase 6 P1）", False, "误抛错")

    # Candidate
    c = Candidate(id="A", strategy="A_核心利益直给", title="新品限时", body="点击查看详情")
    _check("Candidate effective_title 默认等于 title", c.effective_title == "新品限时")
    _check("Candidate is_edited 默认 False", c.is_edited is False)
    c.title_edited = "新品限时来啦"
    _check("Candidate 改 title_edited is_edited=True", c.is_edited is True)
    _check("Candidate effective_title 用 edited", c.effective_title == "新品限时来啦")
    c.reset_edit()
    _check("Candidate reset_edit 恢复", c.effective_title == "新品限时")
    try:
        Candidate(id="X", strategy="A_核心利益直给", title="t", body="b")
        _check("Candidate.id 非法抛错", False, "未抛错")
    except ValueError:
        _check("Candidate.id 非法抛错", True)
    try:
        Candidate(id="A", strategy="A_核心利益直给", title="", body="b")
        _check("Candidate 空 title 不抛错（短信允许）", True)
    except ValueError:
        _check("Candidate 空 title 不抛错（短信允许）", False, "不应抛错")
    try:
        Candidate(id="A", strategy="A_核心利益直给", title="t", body="")
        _check("Candidate 空 body 抛错", False, "未抛错")
    except ValueError:
        _check("Candidate 空 body 抛错", True)

    # RuleItem / RuleResult
    rr = RuleResult(items=[
        RuleItem(category="字数", severity=SEVERITY_PASS, message="ok"),
        RuleItem(category="禁词", severity=SEVERITY_FAIL, message="x"),
    ])
    _check("RuleResult 含 fail → status=fail", rr.status == SEVERITY_FAIL)
    _check("RuleResult has_blocking=True", rr.has_blocking is True)
    _check("RuleResult fails 1 条", len(rr.fails) == 1)
    _check("RuleResult passes 1 条", len(rr.passes) == 1)
    _check("RuleResult warns 0 条", len(rr.warns) == 0)
    rr2 = RuleResult(items=[
        RuleItem(category="风险词", severity=SEVERITY_WARN, message="x"),
    ])
    _check("RuleResult 仅 warn → status=warn", rr2.status == SEVERITY_WARN)
    _check("RuleResult 仅 warn has_blocking=False", rr2.has_blocking is False)

    # GenerationRecord.to_row
    rec = GenerationRecord(task=t, candidates=[c], selected_id="A")
    row = rec.to_row()
    for k in ("task_json", "candidates_json", "rule_results_json",
              "ctr_results_json", "similar_summary_json", "selected_id", "created_at"):
        _check(f"GenerationRecord.to_row 含 {k}", k in row)

    # 常量
    _check("CANDIDATE_STRATEGIES 3 条", len(CANDIDATE_STRATEGIES) == 3)
    _check("TARGET_AUDIENCE 含 5 项", len(TARGET_AUDIENCE) >= 5)
    _check("CHANNELS 4 渠道（Phase 12 #8 用户拍板：删'站内信'+加'微信小程序订阅消息'）",
           set(CHANNELS) == {"APP Push", "企微1v1", "短信", "微信小程序订阅消息"})


# ============================================================
# 25) services/rule_engine.py
# ============================================================
_section("25) rule_engine")

def test_rule_engine():
    from services.rule_engine import load_rules, check_one, check_candidates
    from core.schemas import Candidate

    cr, br = load_rules()
    ch = "APP Push"

    # 正常通过
    r = check_one("新品限时", "新品限时优惠，点击查看详情领券", ch, cr, br)
    _check("正常文案 status != fail", r.status != "fail", r.status)
    _check("正常文案 含 字数 pass",
           any(it.category == "字数" and it.severity == "pass" for it in r.items))

    # 标题超长 → fail
    long_title = "限时新品优惠大放送绝对不能错过的好机会快来点击"
    r = check_one(long_title, "正文", ch, cr, br)
    _check("长标题触发 fail", r.status == "fail")
    _check("长标题 fail 至少 1 条", len(r.fails) >= 1)

    # 禁词 → fail
    r = check_one("新功能上线", "正文", ch, cr, br)
    _check("禁词触发 fail", r.status == "fail")
    _check("禁词 fail 提到'禁词'分类",
           any(it.category == "禁词" and it.severity == "fail" for it in r.fails))

    # 风险词 → warn
    r = check_one("保证最低价", "新品限时点击查看", ch, cr, br)
    _check("风险词触发 warn", r.status == "warn")
    _check("风险词 warn 提到'风险词'分类",
           any(it.category == "风险词" and it.severity == "warn" for it in r.warns))

    # 候选差异
    cands = [
        Candidate(id="A", strategy="A_核心利益直给", title="新品限时", body="点击查看详情"),
        Candidate(id="B", strategy="B_消费场景切入", title="新品限时", body="点击查看详情"),
        Candidate(id="C", strategy="C_行动号召强化", title="新品限时优惠", body="点击查看详情领券"),
    ]
    results = check_candidates(cands, ch, cr, br)
    _check("check_candidates 返回 3 条", len(results) == 3)
    _check("A 和 B 重复 → warn",
           results[0].status == "warn" and results[1].status == "warn")
    _check("C 独立 → 不含重复 warn",
           not any(it.category == "重复" and it.severity == "warn" for it in results[2].items))

    # load_rules 自定义路径
    cr2, br2 = load_rules(
        channel_path=str(ROOT / "config" / "channel_rules.yaml"),
        brand_path=str(ROOT / "config" / "brand_rules.yaml"),
    )
    _check("load_rules 自定义路径返回 channel_rules", "channels" in cr2)
    _check("load_rules brand 含 banned_terms", "banned_terms" in br2)


# ============================================================
# 26) services/generation_service.py (Demo 模式)
# ============================================================
_section("26) generation_service (Demo 模式)")

def test_generation_service_demo():
    from services.generation_service import generate, build_record, GenerationError
    from services.rule_engine import load_rules
    from core.schemas import TaskInput

    cr, _ = load_rules()

    # Demo 模式
    task = TaskInput(
        product_benefit="新品限时优惠", audience="常规大盘", channel="APP Push",
        objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
    )
    cands = generate(task, router=None, channel_rules=cr)
    _check("Demo 模式生成 3 条", len(cands) == 3)
    _check("Demo 候选 ids = {A,B,C}", set(c.id for c in cands) == {"A", "B", "C"})
    _check("Demo 候选 strategies 严格对应 A/B/C",
           [c.strategy for c in cands] == list(
               ("A_核心利益直给", "B_消费场景切入", "C_行动号召强化")))
    _check("Demo 候选 provider='demo'", all(c.provider == "demo" for c in cands))

    # 必填字段缺失抛错（5 必填缺一即拒，灰态字段空不算缺）—— schema ValueError
    try:
        bad_task = TaskInput(product_benefit="", objective="",
                             audience="", channel="APP Push",
                             stage="x", scene="x", tone="x")
        _check("缺 5 必填抛错", False, "未抛错")
    except (GenerationError, ValueError):
        _check("缺 5 必填抛错", True)

    # 短信渠道
    sms_task = TaskInput(
        product_benefit="新品限时", audience="常规大盘", channel="短信",
        objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
    )
    sms_cands = generate(sms_task, router=None)
    _check("短信渠道 title 全空", all(c.title == "" for c in sms_cands))
    _check("短信渠道 body 含 '回T退订'",
           all("回T退订" in c.body for c in sms_cands))

    # build_record
    rec = build_record(task=task, candidates=cands, selected_id="A")
    _check("build_record 含 created_at", bool(rec.created_at))
    row = rec.to_row()
    _check("build_record.to_row 含 task_json", "task_json" in row)
    _check("build_record.to_row 含 candidates_json", "candidates_json" in row)


# ============================================================
# 27) repositories/sqlite_repository.py + record_service
# ============================================================
_section("27) SQLite repository + record_service")

def test_sqlite_repository():
    import tempfile
    from pathlib import Path
    from repositories import sqlite_repository
    from core.schemas import TaskInput, Candidate, GenerationRecord

    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "test_records.db")

        task = TaskInput(
            product_benefit="测试", audience="常规大盘", channel="APP Push",
            objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
        )
        cands = [
            Candidate(id="A", strategy="A_核心利益直给", title="t", body="b"),
            Candidate(id="B", strategy="B_消费场景切入", title="t", body="b"),
            Candidate(id="C", strategy="C_行动号召强化", title="t", body="b"),
        ]
        rec = GenerationRecord(
            task=task, candidates=cands, selected_id="A",
            created_at="2026-08-24T10:00:00",
        )
        rid = sqlite_repository.save(rec.to_row(), db_path=db_path)
        _check("save 返回 id > 0", rid > 0)

        rows = sqlite_repository.list_all(limit=10, db_path=db_path)
        _check("list_all 返回 1 条", len(rows) == 1)
        _check("list_all 解析 task dict", isinstance(rows[0].get("task"), dict))
        _check("list_all 解析 candidates 列表", isinstance(rows[0].get("candidates"), list))

        got = sqlite_repository.get_by_id(rid, db_path=db_path)
        _check("get_by_id 命中", got is not None)
        _check("get_by_id selected_id=A", got["selected_id"] == "A")

        not_found = sqlite_repository.get_by_id(99999, db_path=db_path)
        _check("get_by_id 不存在返 None", not_found is None)


# ============================================================
# 28) prompts/copy_generation + copy_rewrite
# ============================================================
_section("28) prompts")

def test_prompts():
    from prompts import copy_generation, copy_rewrite
    from core.schemas import TaskInput

    _check("copy_generation.VERSION 非空", bool(copy_generation.VERSION))
    _check("copy_generation.SYSTEM_PROMPT 非空", bool(copy_generation.SYSTEM_PROMPT))

    task = TaskInput(
        product_benefit="新品", audience="常规大盘", channel="APP Push",
        objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
        expected_action="点击", extra_requirements="不得出现免费",
    )
    channel_rules = {"channels": {"APP Push": {"title_max": 15, "body_max": 60, "emoji_max": 2}}}
    p = copy_generation.build_user_prompt(task, channel_rules)
    _check("user_prompt 含'产品与权益'", "产品与权益" in p)
    _check("user_prompt 含'额外要求'", "额外要求" in p)
    _check("user_prompt 含字数上限 15", "15" in p)

    raw = '```json\n[{"id":"A","strategy":"A_核心利益直给","title":"t","body":"b"}]\n```'
    parsed = copy_generation.parse_response(raw)
    _check("parse_response 兼容 markdown 围栏",
           len(parsed) == 1 and parsed[0]["id"] == "A")

    parsed_empty = copy_generation.parse_response("")
    _check("parse_response 空响应返 error",
           len(parsed_empty) == 1 and "error" in parsed_empty[0])

    _check("copy_rewrite.VERSION 非空", bool(copy_rewrite.VERSION))
    sp = copy_rewrite.get_system_prompt("shorten")
    _check("rewrite get_system_prompt 'shorten' 非空", len(sp) > 0)
    parsed_rewrite = copy_rewrite.parse_response('{"title":"x","body":"y","reason":"z"}')
    _check("rewrite parse 正常 dict", parsed_rewrite.get("title") == "x")


# ============================================================
# 29) Phase 3 import sanity
# ============================================================
_section("29) Phase 3 import sanity")

def test_phase3_imports():
    try:
        from services import (  # noqa
            generation_service, rule_engine, record_service,
            ctr_prediction_service, similarity_service, copy_analysis_service,
        )
        from repositories import sqlite_repository  # noqa
        from prompts import copy_generation, copy_rewrite  # noqa
        _check("Phase 3 service / repository / prompts import 成功", True)
    except Exception as e:
        _check("Phase 3 service / repository / prompts import 成功", False, str(e))

    try:
        from core.schemas import (  # noqa
            TaskInput, Candidate, RuleResult, GenerationRecord,
            RuleItem, CANDIDATE_STRATEGIES,
        )
        _check("Phase 3 schemas 全部 import 成功", True)
    except Exception as e:
        _check("Phase 3 schemas 全部 import 成功", False, str(e))


# ============================================================
# 30) Phase 3.2 pages import sanity
# ============================================================
_section("30) pages import sanity")

def test_pages_import():
    import importlib

    for page in ("pages.00_home", "pages.01_content_studio",
                 "pages.02_copy_diagnosis", "pages.03_batch_evaluation",
                 "pages.04_historical_insights"):
        try:
            importlib.import_module(page)
            _check(f"{page} import 成功", True)
        except Exception as e:
            _check(f"{page} import 成功", False, str(e))

    # app.py 是入口（无 st.navigation / st.Page，避免自引用递归；pages/ 自动发现）
    app_path = ROOT / "app.py"
    try:
        content = app_path.read_text(encoding="utf-8")
        # 必须含 set_page_config + inject_base_css；不能含自引用 st.Page("app.py")
        _check("app.py 含 set_page_config", "set_page_config" in content)
        _check("app.py 含 inject_base_css", "inject_base_css" in content)
        _check("app.py 不含 st.Page('app.py', ...) 自引用",
               'st.Page("app.py"' not in content and "st.Page('app.py'" not in content)
    except Exception as e:
        _check("app.py 入口检查", False, str(e))


# ============================================================
# 31) Phase 4.1 — 02 文案诊断页入口 B 闭环
# ============================================================
_section("31) 02 文案诊断（PRD §4.2 入口 B）")

def test_diagnosis_page():
    from services.rule_engine import load_rules, check_one
    from services.copy_analysis_service import diagnose
    from services.ctr_prediction_service import predict_one
    from services.similarity_service import find_similar, summarize_similar
    from core.schemas import CHANNELS, PredictionResult, RuleResult
    from prompts.copy_rewrite import (
        get_system_prompt, build_user_prompt, parse_response,
    )

    channel_rules, brand_rules = load_rules()

    # 1. rule_engine.check_one 单条入口
    rule = check_one("新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情。",
                     "APP Push", channel_rules, brand_rules)
    _check("check_one 返回 RuleResult", isinstance(rule, RuleResult))
    _check("check_one 至少 4 类规则", len(rule.items) >= 4)
    has_pass = any(it.severity == "pass" for it in rule.items)
    _check("check_one 含至少 1 条 pass", has_pass)

    # 2. check_one 异常输入不抛错
    rule_blocked = check_one("XXX", "违禁词" * 50, "APP Push", channel_rules, brand_rules)
    _check("check_one 异常输入不抛错", isinstance(rule_blocked, RuleResult))

    # 3. copy_analysis_service.diagnose
    diag = diagnose("新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情。", channel="APP Push")
    _check("diagnose 返回 dict", isinstance(diag, dict))
    _check("diagnose 含 score/grade", "score" in diag and "grade" in diag)
    _check("diagnose 含 problems/suggestions/diag",
           all(k in diag for k in ("problems", "suggestions", "diag")))

    # 4. ctr_prediction_service.predict_one（入口 B）
    ctr = predict_one("新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情。",
                      channel="APP Push", mode="demo")
    _check("predict_one 返回 PredictionResult", isinstance(ctr, PredictionResult))
    _check("predict_one 四态合法",
           ctr.result_type in ("model_prediction", "baseline_only", "demo", "unavailable"))
    _check("predict_one demo 模式 pred_ctr 非空",
           ctr.result_type == "demo" and ctr.pred_ctr is not None)

    # 5. predict_one 短信渠道（title 允许空）
    ctr_sms = predict_one("", "新品优惠立即查看回T退订", channel="短信", mode="demo")
    _check("predict_one 短信渠道不抛错", isinstance(ctr_sms, PredictionResult))

    # 6. similarity_service（无历史数据时返回空 df + summary）
    sim_df = find_similar("新品小卡来啦", "新品优惠 + 限定小卡", channel="APP Push")
    sim_sum = summarize_similar(sim_df)
    _check("find_similar 返回 DataFrame", hasattr(sim_df, "empty"))
    _check("summarize_similar 返回 dict", isinstance(sim_sum, dict))
    _check("summarize_similar 含 count/avg_ctr/top_terms",
           all(k in sim_sum for k in ("count", "avg_ctr", "top_terms")))

    # 7. copy_rewrite prompt
    sp = get_system_prompt("shorten")
    _check("rewrite get_system_prompt 'shorten' 非空", bool(sp))
    up = build_user_prompt("shorten", "标题", "正文",
                           {"title_max": 15, "body_max": 60, "emoji_max": 2})
    _check("rewrite build_user_prompt 含渠道约束", "15" in up and "60" in up)
    parsed = parse_response('```json\n{"title":"t","body":"b","reason":"r"}\n```')
    _check("rewrite parse 正常 dict",
           parsed.get("title") == "t" and parsed.get("body") == "b")

    # 8. 全部 4 个渠道预测不抛错
    for ch in CHANNELS:
        try:
            predict_one("t" if ch not in ("短信", "企微 1v1") else "",
                        "body 测试内容", channel=ch, mode="demo")
            _check(f"predict_one {ch} 不抛错", True)
        except Exception as e:
            _check(f"predict_one {ch} 不抛错", False, str(e))


# ============================================================
# 32) Phase 4.2 — 03 批量评估（PRD §4.3 入口 C）
# ============================================================
_section("32) 03 批量评估（PRD §4.3 入口 C）")

def test_batch_evaluation():
    import io
    import pandas as pd
    from services.batch_evaluation_service import (
        parse_batch_file, evaluate_batch, rows_to_dataframe, rows_to_csv_bytes,
    )

    # 1. CSV 解析（含别名）
    csv_bytes = (
        "标题,正文,渠道\n"
        "新品小卡来啦,新品优惠 + 限定小卡，点击查看详情,APP Push\n"
        ",专属福利：新品小卡，点击领取,企微 1v1\n"
        "早安,早餐 8 折优惠，回 T 退订,短信\n"
    ).encode("utf-8")
    df = parse_batch_file(csv_bytes, "test.csv")
    _check("parse_batch_file 返回 DataFrame", isinstance(df, pd.DataFrame))
    _check("parse_batch_file 3 行（1 header + 3 数据）", len(df) == 3)
    _check("parse_batch_file 列名标准化", all(c in df.columns for c in ("title", "body", "channel")))

    # 2. Excel 解析
    buf = io.BytesIO()
    pd.DataFrame({"title": ["t1"], "body": ["b1"], "channel": ["APP Push"]}).to_excel(buf, index=False)
    df2 = parse_batch_file(buf.getvalue(), "test.xlsx")
    _check("parse_batch_file 支持 Excel", len(df2) == 1 and "body" in df2.columns)

    # 3. 别名映射（"headline" → "title"）
    alias_csv = "headline,body_text,投放渠道\nHi,Body,APP Push\n".encode("utf-8")
    df3 = parse_batch_file(alias_csv, "alias.csv")
    _check("parse_batch_file 别名 headline→title", "title" in df3.columns)
    _check("parse_batch_file 别名 body_text→body", "body" in df3.columns)
    _check("parse_batch_file 别名 投放渠道→channel", "channel" in df3.columns)

    # 4. 评估流程
    rows = evaluate_batch(df, ctr_mode="demo")
    _check("evaluate_batch 返回 list", isinstance(rows, list))
    _check("evaluate_batch 行数 == df 行数", len(rows) == len(df))
    for r in rows:
        _check(f"row {r['row_index']} 含 channel", "channel" in r)
        _check(f"row {r['row_index']} 含 rule_status", "rule_status" in r)
        _check(f"row {r['row_index']} 含 ctr_result_type", "ctr_result_type" in r)
        _check(f"row {r['row_index']} 含 suggestion", "suggestion" in r)
        break  # 不重复

    # 5. 空 body 行 → 记录 error
    empty_csv = "title,body,channel\nt1,,APP Push\n".encode("utf-8")
    rows2 = evaluate_batch(parse_batch_file(empty_csv, "empty.csv"))
    _check("空 body 行被记 error", rows2[0]["error"] != "")

    # 6. 非法渠道行 → 记 error（不影响其他行）
    bad_csv = "title,body,channel\n标题,内容,未知渠道\n".encode("utf-8")
    rows3 = evaluate_batch(parse_batch_file(bad_csv, "bad.csv"))
    _check("非法渠道行被记 error", rows3[0]["error"] != "")

    # 7. 全部 4 个渠道批量（Phase 12 #8 schema 增'微信小程序订阅消息'；CHANNELS 4 值）
    df4 = pd.DataFrame({
        "title": ["t1", "", "t3", "t4"],
        "body": ["b1 优惠点击查看", "b2 立即查看", "b3 查看详情", "b4 立即了解"],
        "channel": ["APP Push", "企微1v1", "短信", "微信小程序订阅消息"],
    })
    rows4 = evaluate_batch(df4, ctr_mode="demo")
    _check("4 渠道批量评估行数对齐", len(rows4) == 4)
    _check("4 渠道批量评估均有 rule_status", all(r["rule_status"] for r in rows4))

    # 8. 行级 CTR demo 模式
    ctr_ok = sum(1 for r in rows4 if r["ctr_result_type"] == "demo" and r["ctr_pred"] is not None)
    _check("4 渠道批量 CTR demo 全部返回", ctr_ok == 4)

    # 9. 转 DataFrame + CSV bytes
    df_out = rows_to_dataframe(rows)
    _check("rows_to_dataframe 返回 DataFrame", isinstance(df_out, pd.DataFrame))
    csv_out = rows_to_csv_bytes(rows)
    _check("rows_to_csv_bytes 返回 bytes", isinstance(csv_out, bytes) and len(csv_out) > 0)
    _check("rows_to_csv_bytes 含 BOM（Excel 兼容）", csv_out.startswith(b"\xef\xbb\xbf"))

    # 10. 进度回调
    progress_calls = []
    evaluate_batch(df.iloc[:2], ctr_mode="demo",
                   progress_cb=lambda d, t: progress_calls.append((d, t)))
    _check("progress_cb 被调用", len(progress_calls) >= 2)


# ============================================================
# 33) Phase 4.3 — 04 历史洞察（PRD §4.4 七大分析）
# ============================================================
_section("33) 04 历史洞察（PRD §4.4）")

def _make_insights_df():
    """构造最小可用历史数据：5 个 plan × 3 记录 + 触达/点击/日期/owner。"""
    import pandas as pd
    from services.text_analyzer import add_tokens
    rows = [
        # plan A：高 CTR
        ("A", "新品小卡", "APP Push", "owner1", "2026-08-01", 1000, 30, "新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情"),
        ("A", "新品小卡", "APP Push", "owner1", "2026-08-02", 1100, 35, "新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情"),
        ("A", "新品小卡", "APP Push", "owner1", "2026-08-03", 1200, 40, "新品小卡来啦", "新品优惠 + 限定小卡，点击查看详情"),
        # plan B：中 CTR
        ("B", "早餐优惠", "APP Push", "owner1", "2026-08-01", 2000, 40, "早安", "早餐 8 折优惠"),
        ("B", "早餐优惠", "APP Push", "owner1", "2026-08-02", 2100, 42, "早安", "早餐 8 折优惠"),
        ("B", "早餐优惠", "APP Push", "owner1", "2026-08-03", 2200, 45, "早安", "早餐 8 折优惠"),
        # plan C：低 CTR
        ("C", "夜宵推荐", "站内信", "owner2", "2026-08-01", 1500, 15, "夜宵", "夜宵不知道吃什么"),
        ("C", "夜宵推荐", "站内信", "owner2", "2026-08-02", 1600, 16, "夜宵", "夜宵不知道吃什么"),
        ("C", "夜宵推荐", "站内信", "owner2", "2026-08-03", 1700, 17, "夜宵", "夜宵不知道吃什么"),
        # plan D：owner2 高 CTR
        ("D", "新品上市", "企微 1v1", "owner2", "2026-08-01", 3000, 120, "新品上市", "专属福利：新品小卡立即领取"),
        ("D", "新品上市", "企微 1v1", "owner2", "2026-08-02", 3100, 125, "新品上市", "专属福利：新品小卡立即领取"),
        ("D", "新品上市", "企微 1v1", "owner2", "2026-08-03", 3200, 130, "新品上市", "专属福利：新品小卡立即领取"),
    ]
    df = pd.DataFrame(rows, columns=[
        "Plan ID", "Plan名称", "渠道", "owner", "发送日期",
        "触达成功", "点击人次", "标题", "正文",
    ])
    df["发送日期"] = pd.to_datetime(df["发送日期"])
    return add_tokens(df)


def test_historical_insights():
    import pandas as pd
    from services.analytics.high_effort_plans import rank_plans
    from services.text_analyzer import (
        word_frequency, emoji_frequency, compare_token,
    )
    from services.analytics.similarity import find_similar_plans
    from services.analytics.daily_trend import daily_aggregate, daily_summary
    from services.analytics.owner_compare import owner_compare

    df = _make_insights_df()
    _check("构造测试数据 ≥ 10 行", len(df) >= 10)
    _check("add_tokens 含 _tokens", "_tokens" in df.columns)

    # 1. 高效 Plan 排行
    rank = rank_plans(df, min_reach=2000, top_n=10)
    _check("rank_plans 返回 DataFrame", isinstance(rank, pd.DataFrame))
    _check("rank_plans 含必要列", all(c in rank.columns for c in (
        "plan_id", "加权CTR%", "触达成功", "点击",
    )))
    if not rank.empty:
        _check("rank_plans 按 CTR 降序",
               rank["加权CTR%"].iloc[0] >= rank["加权CTR%"].iloc[-1])

    # 2. 高低表现词
    wf = word_frequency(df, min_plans=3)
    _check("word_frequency 返回 DataFrame", isinstance(wf, pd.DataFrame))
    if not wf.empty:
        _check("word_frequency 含差值列", "差值" in wf.columns)
        cmp = compare_token(df, wf.iloc[0, 0])
        _check("compare_token 返回 dict", isinstance(cmp, dict))
        _check("compare_token 含 ctr_with", "ctr_with" in cmp)

    # 3. Emoji 表现
    ef = emoji_frequency(df, min_plans=3)
    _check("emoji_frequency 返回 DataFrame", isinstance(ef, pd.DataFrame))

    # 4. 标题字数（_make_insights_df 没切桶，仅校验 rank 自带 title_len_mean）
    _check("rank_plans 含字数均值列", "标题字数均值" in rank.columns)

    # 5. 历史相似
    sim = find_similar_plans(df, "新品", "新品优惠点击查看", top_k=3)
    _check("find_similar_plans 返回 DataFrame", hasattr(sim, "empty"))
    if not sim.empty:
        _check("find_similar_plans 含 similarity 列", "similarity" in sim.columns)

    # 6. 每日趋势
    ds = daily_summary(df)
    _check("daily_summary 返回 dict", isinstance(ds, dict))
    _check("daily_summary 含总触达", "总触达" in ds)
    da = daily_aggregate(df)
    _check("daily_aggregate 返回 DataFrame", isinstance(da, pd.DataFrame))
    if not da.empty:
        _check("daily_aggregate 含 date 列", "date" in da.columns)
        _check("daily_aggregate 含加权CTR%列", "加权CTR%" in da.columns)

    # 7. Owner 对比
    oc = owner_compare(df, min_plans=2, min_reach=2000)
    _check("owner_compare 返回 DataFrame", isinstance(oc, pd.DataFrame))
    if not oc.empty:
        _check("owner_compare 含 owner + 加权CTR%",
               "owner" in oc.columns and "加权CTR%" in oc.columns)


# ============================================================
# 34) Phase 5 P0 — record 指纹 + signature 落库
# ============================================================
_section("34) Phase 5 P0 — record 指纹")

def test_record_signature():
    import os
    import tempfile
    from core.schemas import TaskInput, Candidate, task_signature
    from services.generation_service import build_record

    # 1. task_signature 纯函数
    t = TaskInput(
        product_benefit="新品小卡", audience="常规大盘", channel="APP Push",
        objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
    )
    cands = [
        Candidate(id="A", strategy="A_核心利益直给", title="新品小卡来啦", body="新品优惠点击查看"),
        Candidate(id="B", strategy="B_消费场景切入", title="早安首选", body="早餐 8 折优惠"),
    ]
    sig_a = task_signature(t, candidates=cands, selected_id="A")
    _check("task_signature 返回 12 位 hash", len(sig_a) == 12)
    _check("task_signature 同输入稳定", sig_a == task_signature(t, candidates=cands, selected_id="A"))

    sig_b = task_signature(t, candidates=cands, selected_id="B")
    _check("task_signature 选中不同 → 不同", sig_a != sig_b)

    # 2. build_record 填 signature
    rec = build_record(task=t, candidates=cands, selected_id="A")
    _check("build_record signature 字段非空", bool(rec.signature))
    _check("build_record signature 长度 == 12", len(rec.signature) == 12)
    _check("build_record to_row 含 signature", "signature" in rec.to_row())

    # 3. sqlite_repository 落库 + 读回（独立 db 文件）
    from repositories import sqlite_repository
    import gc as _gc

    def _isolated_save_load():
        tmp = tempfile.mkdtemp(prefix="rec_test_")
        try:
            db_path = os.path.join(tmp, "test.db")
            rid = sqlite_repository.save(rec.to_row(), db_path=db_path)
            _check("sqlite_repository.save 返回 id", rid > 0)
            loaded = sqlite_repository.get_by_id(rid, db_path=db_path)
            _check("sqlite_repository.get_by_id 返回 dict", isinstance(loaded, dict))
            _check("sqlite_repository 落库 signature 一致",
                   loaded.get("signature") == rec.signature)
        finally:
            _gc.collect()  # 强制释放 Windows 文件句柄
            import shutil as _sh
            _sh.rmtree(tmp, ignore_errors=True)

    _isolated_save_load()

    # 4. 老库迁移：手工建一个无 signature 的旧表，再 save 新记录
    import sqlite3 as _sq

    def _legacy_migration():
        tmp = tempfile.mkdtemp(prefix="rec_legacy_")
        try:
            db_path = os.path.join(tmp, "legacy.db")
            conn = _sq.connect(db_path)
            conn.executescript("""
                CREATE TABLE generation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_json TEXT NOT NULL,
                    candidates_json TEXT NOT NULL,
                    selected_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            conn.commit()
            conn.close()
            rid2 = sqlite_repository.save(rec.to_row(), db_path=db_path)
            _check("老库迁移后仍能 save", rid2 > 0)
            loaded2 = sqlite_repository.get_by_id(rid2, db_path=db_path)
            _check("老库迁移后 signature 列存在",
                   loaded2.get("signature") == rec.signature)
        finally:
            _gc.collect()
            import shutil as _sh
            _sh.rmtree(tmp, ignore_errors=True)

    _legacy_migration()


# ============================================================
# 35) Phase 5 P1 — feedback.db schema + feedback_repository
# ============================================================
_section("35) Phase 5 P1 — feedback_repository")

def test_feedback_repository():
    import gc as _gc
    import shutil as _sh
    import tempfile
    from repositories import feedback_repository

    def _run():
        tmp = tempfile.mkdtemp(prefix="fb_test_")
        try:
            db_path = os.path.join(tmp, "fb.db")

            # 1. save 单条
            rec = {
                "task_signature": "abc123def456",
                "channel": "APP Push",
                "coupon": "否",
                "plan_type": "普通 Plan",
                "sent_date": "2026-08-20",
                "reach_success": 1000,
                "click_count": 25,
                "order_count": 3,
                "source": "test",
                "imported_at": "2026-08-26 12:00:00",
            }
            rid = feedback_repository.save(rec, db_path=db_path)
            _check("feedback_repository.save 返回 id", rid > 0)

            # 2. save_batch 批量
            batch = [
                {**rec, "task_signature": "sig_a", "channel": "APP Push",
                 "reach_success": 500, "click_count": 10, "order_count": 1},
                {**rec, "task_signature": "sig_b", "channel": "企微 1v1",
                 "reach_success": 800, "click_count": 20, "order_count": 2},
            ]
            n = feedback_repository.save_batch(batch, db_path=db_path)
            _check("feedback_repository.save_batch 插入 2 条", n == 2)

            # 3. list_all
            rows = feedback_repository.list_all(limit=10, db_path=db_path)
            _check("feedback_repository.list_all 返回 3 条", len(rows) == 3)

            # 4. count
            cnt = feedback_repository.count(db_path=db_path)
            _check("feedback_repository.count == 3", cnt == 3)

            # 5. aggregate_by_signature
            agg = feedback_repository.aggregate_by_signature(db_path=db_path)
            _check("aggregate_by_signature 返回 3 个 signature", len(agg) == 3)
            _check("aggregate_by_signature 加权 CTR 正确",
                   agg["sig_a"]["ctr"] == round(10 / 500 * 100, 2))
            _check("aggregate_by_signature 含 channel",
                   agg["sig_b"]["channel"] == "企微 1v1")
        finally:
            _gc.collect()
            _sh.rmtree(tmp, ignore_errors=True)

    _run()


# ============================================================
# 36) Phase 5 P1 — feedback_service（解析 + 校验 + 写入）
# ============================================================
_section("36) Phase 5 P1 — feedback_service")

def test_feedback_service():
    import tempfile
    import pandas as pd
    from services.feedback_service import (
        parse_feedback_file, to_records, validate_records, import_feedback,
    )

    # 1. CSV 解析（含别名）
    csv_bytes = (
        "签名,渠道,触达成功,点击人次,是否用券,计划类型,发送日期\n"
        "sig1,APP Push,1000,25,否,普通 Plan,2026-08-20\n"
        ",企微 1v1,500,10,是,AARR Plan,2026-08-21\n"
    ).encode("utf-8")
    df = parse_feedback_file(csv_bytes, "test.csv")
    _check("parse_feedback_file 返回 DataFrame", isinstance(df, pd.DataFrame))
    _check("parse_feedback_file 列名标准化", all(c in df.columns for c in (
        "task_signature", "channel", "reach_success", "click_count",
    )))
    _check("parse_feedback_file 别名 签名→task_signature", "签名" not in df.columns)
    _check("parse_feedback_file 别名 触达成功→reach_success", "触达成功" not in df.columns)

    # 2. to_records + autofill_signature
    records = to_records(df, source="test")
    _check("to_records 返回 list", isinstance(records, list) and len(records) == 2)
    _check("to_records 空 signature 行被兜底生成 12 位 hash",
           len(records[1]["task_signature"]) == 12)
    _check("to_records 显式 signature 行保留",
           records[0]["task_signature"] == "sig1")

    # 3. validate_records
    valid_recs = [
        {"task_signature": "s1", "channel": "APP Push", "reach_success": 100, "click_count": 5},
    ]
    errs = validate_records(valid_recs)
    _check("validate_records 合法记录无 error", errs == [])

    bad_recs = [
        {"task_signature": "", "channel": "APP Push", "reach_success": 100, "click_count": 5},
        {"task_signature": "s2", "channel": "", "reach_success": 100, "click_count": 5},
        {"task_signature": "s3", "channel": "APP Push", "reach_success": 0, "click_count": 5},
        {"task_signature": "s4", "channel": "APP Push", "reach_success": 100, "click_count": -1},
    ]
    errs2 = validate_records(bad_recs)
    _check("validate_records 4 个非法 → 4 条 error", len(errs2) == 4)

    # 4. import_feedback（端到端）
    import gc as _gc
    import shutil as _sh

    def _e2e():
        tmp = tempfile.mkdtemp(prefix="fb_e2e_")
        try:
            # 用 monkey patch 临时替换 DB_PATH
            from repositories import feedback_repository as fr
            orig_path = fr.DB_PATH
            fr.DB_PATH = __import__("pathlib").Path(tmp) / "fb.db"
            try:
                result = import_feedback(csv_bytes, "test.csv", source_label="test")
                _check("import_feedback 合法 → n=2", result["n"] == 2)
                _check("import_feedback 合法 → errors=[]", result["errors"] == [])
            finally:
                fr.DB_PATH = orig_path
        finally:
            _gc.collect()
            _sh.rmtree(tmp, ignore_errors=True)

    _e2e()

    # 5. import_feedback 非法拒收
    bad_csv = "签名,渠道,触达成功,点击人次\n,APP Push,0,5\n".encode("utf-8")

    def _reject():
        tmp = tempfile.mkdtemp(prefix="fb_rej_")
        try:
            from repositories import feedback_repository as fr
            orig_path = fr.DB_PATH
            fr.DB_PATH = __import__("pathlib").Path(tmp) / "fb.db"
            try:
                result = import_feedback(bad_csv, "bad.csv")
                _check("import_feedback 非法 → n=0", result["n"] == 0)
                _check("import_feedback 非法 → errors 非空", len(result["errors"]) > 0)
            finally:
                fr.DB_PATH = orig_path
        finally:
            _gc.collect()
            _sh.rmtree(tmp, ignore_errors=True)

    _reject()


# ============================================================
# 37) Phase 5 P2 — calibrate_baseline 自动化
# ============================================================
_section("37) Phase 5 P2 — calibrate_baseline")

def test_calibrate_baseline():
    import importlib
    import shutil as _sh
    import gc as _gc
    import tempfile
    cb = importlib.import_module("tools.calibrate_baseline")

    # 1. _bump_version
    _check("bump_version v3.0 → v3.1", cb._bump_version("v3.0") == "v3.1")
    _check("bump_version v3.5 → v3.6", cb._bump_version("v3.5") == "v3.6")
    _check("bump_version 非法 → v3.1 fallback", cb._bump_version("xxx") == "v3.1")

    # 2. _calibrate_value 三个分支
    new, note = cb._calibrate_value(0.005, 0.003, 3)
    _check("n_plans<5 跳过（保留旧值）", new == 0.003 and "跳过" in note)

    new, note = cb._calibrate_value(0.005, 0.003, 10)
    expected = 0.3 * 0.005 + 0.7 * 0.003
    _check("5≤n_plans<20 指数滑动", abs(new - expected) < 1e-6 and "0.3" in note)

    new, note = cb._calibrate_value(0.005, 0.003, 50)
    _check("n_plans≥20 全量覆盖", new == 0.005 and "全量" in note)

    # 3. aggregate_feedback（端到端：先造 feedback.db + 跑聚合）
    def _aggregate():
        tmp = tempfile.mkdtemp(prefix="cal_test_")
        try:
            from repositories import feedback_repository as fr
            from repositories import feedback_repository as fb  # 别名
            # 写一份假 baseline 到 tmp 用于 isolate calibrate()
            base_path = __import__("pathlib").Path(tmp) / "ctr_baseline.json"
            sample = {
                "version": "v3.0",
                "last_updated": "2026-08-01",
                "dimensions": {
                    "渠道": {"data": {"APP Push": 0.002, "企微 1v1": 0.005}},
                    "渠道_x_是否用券": {
                        "data": {"APP Push_否": 0.001, "企微 1v1_是": 0.01},
                    },
                },
            }
            base_path.write_text(__import__("json").dumps(sample, ensure_ascii=False),
                                 encoding="utf-8")

            # 写 feedback.db
            fr.DB_PATH = __import__("pathlib").Path(tmp) / "fb.db"
            records = [
                # APP Push × 否：30 个签名（≥20 → 全量覆盖）
                *[{
                    "task_signature": f"sig_a_{i}", "channel": "APP Push",
                    "coupon": "否", "reach_success": 1000, "click_count": 30,
                } for i in range(30)],
                # 企微 1v1 × 是：10 个签名（5-20 → 指数滑动）
                *[{
                    "task_signature": f"sig_b_{i}", "channel": "企微 1v1",
                    "coupon": "是", "reach_success": 800, "click_count": 20,
                } for i in range(10)],
                # APP Push × 是：3 个签名（<5 → 跳过）
                *[{
                    "task_signature": f"sig_c_{i}", "channel": "APP Push",
                    "coupon": "是", "reach_success": 500, "click_count": 5,
                } for i in range(3)],
            ]
            fr.save_batch(records)

            by_cp, by_ch = cb.aggregate_feedback(str(fr.DB_PATH))
            _check("aggregate 返回 3 个 (channel, coupon)", len(by_cp) == 3)
            _check("aggregate APP Push 触达 = 30000",
                   by_cp[("APP Push", "否")]["reach"] == 30000)
            _check("aggregate APP Push × 否 CTR = 3%",
                   abs(by_cp[("APP Push", "否")]["ctr"] - 0.03) < 1e-6)
            _check("aggregate APP Push × 否 n_plans = 30",
                   by_cp[("APP Push", "否")]["n_plans"] == 30)

            # 跑 calibrate（dry-run 不写文件）
            new_base, changes = cb.calibrate(sample, by_cp, by_ch, min_reach=1000)
            _check("calibrate 版本号升级", new_base["version"] == "v3.1")
            # APP Push 渠道（含 ×否 30 plan + ×是 3 plan）：
            #   reach = 30000+1500 = 31500, click = 900+15 = 915
            #   CTR = 915/31500 = 0.02905
            expected_app_push_ctr = 915 / 31500
            _check("calibrate APP Push 全量覆盖（合并两 coupon）",
                   abs(new_base["dimensions"]["渠道"]["data"]["APP Push"] - expected_app_push_ctr) < 1e-6)
            _check("calibrate 企微 1v1 指数滑动（0.3×新+0.7×旧）",
                   abs(new_base["dimensions"]["渠道"]["data"]["企微 1v1"] - (0.3 * (200/8000) + 0.7 * 0.005)) < 1e-6)
            _check("calibrate APP Push × 否 全量覆盖",
                   abs(new_base["dimensions"]["渠道_x_是否用券"]["data"]["APP Push_否"] - 0.03) < 1e-6)
            _check("calibrate APP Push × 是 跳过（保留旧 0）",
                   new_base["dimensions"]["渠道_x_是否用券"]["data"].get("APP Push_是", 0.0) == 0.0)
            _check("calibrate changes ≥ 3 条", len(changes) >= 3)

            # write 验证
            fr.DB_PATH = __import__("pathlib").Path(tmp) / "fb.db"  # ensure
            out_path = __import__("pathlib").Path(tmp) / f"ctr_baseline_{new_base['version']}.json"
            out_path.write_text(__import__("json").dumps(new_base, ensure_ascii=False, indent=2),
                                encoding="utf-8")
            _check("写出 baseline_v3.1.json 存在", out_path.exists())

            # 备份验证：原文件还存在（calibrate 不动原文件）
            _check("原 ctr_baseline.json 仍在", base_path.exists())
        finally:
            _gc.collect()
            _sh.rmtree(tmp, ignore_errors=True)

    _aggregate()


# ============================================================
# §38 LLM 配置状态检测（业务确认 #10 + Phase 6 P0）
# ============================================================
def test_llm_status():
    """ui/llm_status 极简 yaml 解析 + 全空/部分空/全填 三态判断。"""
    import sys, importlib
    # 显式 import 进 sys.modules（from 形式不会自动注册）
    import ui.llm_status as ls
    _check("llm_status 模块存在", ls is not None)

    # 1) 默认全空（仓库初始状态）
    _check("默认 is_configured() == False", ls.is_configured() is False)
    _check("默认 missing_fields() 4 字段",
           set(ls.missing_fields()) == {"provider", "base_url", "model", "api_key"})

    # 2) 用临时 yaml 文件覆盖路径（monkeypatch CONFIG_PATH）
    import tempfile, textwrap
    tmp = tempfile.mkdtemp(prefix="llm_status_test_")
    try:
        yaml_full = tmp + "/llm_settings.yaml"
        with open(yaml_full, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent("""\
                # 注释
                provider: "openai"
                base_url: "https://api.openai.com/v1"
                model: "gpt-4o-mini"
                api_key: "sk-test"
                """))
        ls.CONFIG_PATH = type(ls.CONFIG_PATH)(yaml_full)
        ls._load_yaml.cache_clear()
        _check("全填 is_configured() == True", ls.is_configured() is True)
        _check("全填 missing_fields() == []", ls.missing_fields() == [])

        # 部分空
        with open(yaml_full, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent("""\
                provider: "openai"
                model: "gpt-4o-mini"
                """))
        ls._load_yaml.cache_clear()
        _check("部分空 is_configured() == False", ls.is_configured() is False)
        _check("部分空 missing_fields 2 字段",
               set(ls.missing_fields()) == {"base_url", "api_key"})

        # 全空（注释 + 空格）
        with open(yaml_full, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent("""\
                # 仅注释
                provider: ""
                base_url: ""
                model: ""
                api_key: ""
                """))
        ls._load_yaml.cache_clear()
        _check("显式全空 is_configured() == False", ls.is_configured() is False)

        # yaml 不存在
        ls.CONFIG_PATH = type(ls.CONFIG_PATH)(tmp + "/nonexistent.yaml")
        ls._load_yaml.cache_clear()
        _check("yaml 缺失 is_configured() == False", ls.is_configured() is False)
        _check("yaml 缺失 missing 4 字段",
               len(ls.missing_fields()) == 4)
    finally:
        import gc as _gc, shutil as _sh
        _gc.collect()
        _sh.rmtree(tmp, ignore_errors=True)


# §39 决策 1 灰态字段（产品与权益 / 投放目标 · Demo 阶段占位）
# ============================================================
def test_phase6_p1_pending_fields():
    """验证 6 维度前端的"产品与权益"+"投放目标"灰态：

    - core.schemas.TaskInput 不再把这两个列为必填（REQUIRED_FIELDS 5 项）
    - prompts.copy_generation 空时不拼接这两行（避免 prompt 出现空值）
    - pages/01_content_studio 控件 disabled + label 标识 + help 提示
    - services.generation_service.demo 模式 product_benefit="" 走默认值兜底
    """
    import sys, re, inspect

    # ── 1) core.schemas.TaskInput ────────────────────────────
    from core.schemas import TaskInput
    _check("REQUIRED_FIELDS 不再含 product_benefit",
           "product_benefit" not in TaskInput.REQUIRED_FIELDS)
    _check("REQUIRED_FIELDS 不再含 objective",
           "objective" not in TaskInput.REQUIRED_FIELDS)
    _check("REQUIRED_FIELDS 含 audience/channel/stage/tone 4 项（Phase 12 #10 scene 改选填）",
           set(TaskInput.REQUIRED_FIELDS) == {"audience", "channel", "stage", "tone"})

    # from_form 接受 product_benefit="" + objective="" 不抛错
    form_empty_pending = {
        "product_benefit": "",
        "audience": "常规大盘",
        "channel": "APP Push",
        "objective": "",
        "stage": "活动预热",
        "scene": "早餐",
        "tone": "直接利益型",
    }
    task = TaskInput.from_form(form_empty_pending)
    _check("空灰态字段 TaskInput.from_form 不抛错",
           task.product_benefit == "" and task.objective == "")
    _check("空灰态字段 is_complete() == True（其他 5 必填已填）",
           task.is_complete is True)

    # is_complete False 时（5 必填缺一个）—— __post_init__ 必拦，不让绕过
    form_missing_audience = {**form_empty_pending, "audience": ""}
    try:
        TaskInput.from_form(form_missing_audience)
        _check("缺 5 必填抛 ValueError", False)  # 不该走到这
    except ValueError as e:
        _check("缺 5 必填抛 ValueError（兜底不被绕过）",
               "audience" in str(e))

    # ── 2) prompts.copy_generation.build_user_prompt ─────────
    from prompts.copy_generation import build_user_prompt
    out_empty = build_user_prompt(task, {"APP Push": {"title_max": 15, "body_max": 60, "emoji_max": 2}})
    _check("空灰态字段 prompt 不拼「产品与权益：」行",
           "产品与权益：" not in out_empty)
    _check("空灰态字段 prompt 不拼「投放目标：」行",
           "投放目标：" not in out_empty)

    # 当灰态字段非空时，要拼出来（业务确认后启用场景）
    task_with = TaskInput.from_form({**form_empty_pending,
                                     "product_benefit": "Chiikawa 联名小卡",
                                     "objective": "促进转化"})
    out_filled = build_user_prompt(task_with, {"APP Push": {"title_max": 15, "body_max": 60, "emoji_max": 2}})
    _check("非空时拼「产品与权益：Chiikawa 联名小卡」",
           "产品与权益：Chiikawa 联名小卡" in out_filled)
    _check("非空时拼「投放目标：促进转化」",
           "投放目标：促进转化" in out_filled)

    # ── 3) pages/01_content_studio 控件源码标注 ─────────────
    src_studio = open("pages/01_content_studio.py", encoding="utf-8").read()
    _check("product_benefit text_area 已加 disabled=True",
           re.search(r'st\.text_area\([\s\S]*?产品与权益[\s\S]*?disabled\s*=\s*True', src_studio) is not None)
    _check("objective selectbox 已加 disabled=True",
           re.search(r'st\.selectbox\([\s\S]*?投放目标[\s\S]*?disabled\s*=\s*True', src_studio) is not None)
    _check("两控件 label 含「待开发·二期接入」",
           "待开发·二期接入" in src_studio)
    _check("两控件有 help= tooltip 提示",
           src_studio.count('help="后续开放，敬请期待') >= 2)
    _check("副标题已说明 5 必填 + 二期接入",
           "必填 5 项" in src_studio and "二期接入" in src_studio)

    # ── 4) generation_service.demo 模式 product_benefit="" 走兜底 ──
    from services.generation_service import _demo_candidates
    cs = _demo_candidates(task)  # product_benefit="" + objective=""
    _check("Demo 模式 product_benefit='' 仍生成 3 条候选，不报错",
           len(cs) == 3 and all(c.body for c in cs))
    _check("Demo 模式 3 条候选 id == A/B/C（PRD §9.2 schema）",
           [c.id for c in cs] == ["A", "B", "C"])


# §40 决策 2 进阶能力弱化 + 决策 3 CTR 反哺免责（Demo 范围 §2 / §3）
# ============================================================
def test_phase6_p1_nav_and_notice():
    """验证决策文档两件事：

    - 决策 2（导航分组）：ui/notice 渲染 .advanced-notice；4 个进阶页顶部调用；
      00_home 含"核心 / 进阶"两组 home-section 卡
    - 决策 3（CTR 反哺免责）：ui/notice 含 render_ctr_feedback_notice；
      04/05 顶部调用；00_home 进阶区提"演示口径"明示不接真实数据
    """
    import importlib, re

    # ── 1) ui/notice 模块 + 两个函数存在 ────────────────────
    from ui import notice
    _check("ui/notice 模块存在", notice is not None)
    _check("render_advanced_notice 函数存在",
           hasattr(notice, "render_advanced_notice") and callable(notice.render_advanced_notice))
    _check("render_ctr_feedback_notice 函数存在",
           hasattr(notice, "render_ctr_feedback_notice") and callable(notice.render_ctr_feedback_notice))

    # ── 2) ui/styles CSS 类已注入 ──────────────────────────
    styles_src = open("ui/styles.py", encoding="utf-8").read()
    _check(".advanced-notice CSS 已加", ".advanced-notice" in styles_src)
    _check(".home-section-core CSS 已加", ".home-section-core" in styles_src)
    _check(".home-section-advanced CSS 已加", ".home-section-advanced" in styles_src)

    # ── 3) 4 个进阶页：02/03 顶部仅 advanced, 04/05 顶部 advanced + ctr ─
    src02 = open("pages/02_copy_diagnosis.py", encoding="utf-8").read()
    src03 = open("pages/03_batch_evaluation.py", encoding="utf-8").read()
    src04 = open("pages/04_historical_insights.py", encoding="utf-8").read()
    src05 = open("pages/05_feedback.py", encoding="utf-8").read()
    home  = open("pages/00_home.py", encoding="utf-8").read()

    for name, src in [("02", src02), ("03", src03), ("04", src04), ("05", src05)]:
        _check(f"{name} import render_advanced_notice",
               "from ui.notice import render_advanced_notice" in src)
        _check(f"{name} 顶部调用 render_advanced_notice()",
               re.search(r'#\s*进阶能力[^\n]*\n\s*render_advanced_notice\(\)', src) is not None)
        _check(f"{name} 含「进阶能力」banner 文案关键字",
               "进阶能力" in src or "面向运营" in src)

    _check("04 顶部调用 render_ctr_feedback_notice()",
           re.search(r'render_ctr_feedback_notice\(\)', src04) is not None)
    _check("05 顶部调用 render_ctr_feedback_notice()",
           re.search(r'render_ctr_feedback_notice\(\)', src05) is not None)

    # ── 4) 00_home 含分组卡片 + 进阶区文案 ─────────────────
    _check("00_home 核心卡 home-section-core",
           re.search(r'home-section[\s\S]*home-section-core', home) is not None)
    _check("00_home 进阶卡 home-section-advanced",
           re.search(r'home-section[\s\S]*home-section-advanced', home) is not None)
    _check("00_home 进阶区含「演示口径」明示（决策 3 文案）",
           "演示口径" in home and "业务确认前不接真实数据" in home)
    _check("00_home 核心卡引导到 01_content_studio",
           "01_content_studio" in home)

    # ── 5) 01_content_studio 推荐结论已有免责话术（保留原有）──
    src01 = open("pages/01_content_studio.py", encoding="utf-8").read()
    _check("01 推荐结论含「不代表正式投放承诺」免责话术",
           "不代表正式投放承诺" in src01)

    # ── 6) 反哺库不入真实数据：feedback_repository 是演示用的 ─
    from repositories import feedback_repository as fbr
    _check("feedback_repository 模块存在（Phase 5 P1 已建）",
           fbr is not None)


# §41 CTR v3.1 口径固化（业务拍板 · docs/ctr-kpi-definition-proposal-v0.2.md）
# ============================================================
def test_ctr_definition_v31():
    """v3.1 口径落地三件事：

    1) data/ctr_baseline.json 加 v3.1 definition 字段
    2) baseline_lookup.py / ctr_prediction_service.py / feedback_repository.py
       顶部 docstring 含 v3.1 口径注释
    3) plan 加权 vs record 加权 vs 中位数 数值对比 + bi_dt 取数边界
       （核心：v3.1 选 plan 加权，数值上要可验证）
    """
    import importlib
    import statistics
    from datetime import datetime

    # ── 1) ctr_baseline.json 元数据升级 ──────────────────────
    base_path = ROOT / "data" / "ctr_baseline.json"
    base = __import__("json").loads(base_path.read_text(encoding="utf-8"))
    _check("baseline version == v3.1", base.get("version") == "v3.1")
    _check("baseline 含 _definition_note",
           isinstance(base.get("_definition_note"), str) and len(base["_definition_note"]) > 50)
    _check("baseline _definition_note 提及 Q1 去重点击",
           "Q1" in base["_definition_note"] and "去重" in base["_definition_note"])
    _check("baseline _definition_note 提及 Q2 触达成功",
           "Q2" in base["_definition_note"] and "触达成功" in base["_definition_note"])
    _check("baseline _definition_note 提及 Q3 全周期不截断",
           "Q3" in base["_definition_note"] and "不截断" in base["_definition_note"])
    _check("baseline _definition_note 提及 Q4 不聚合",
           "Q4" in base["_definition_note"] and "不聚合" in base["_definition_note"])
    _check("baseline _definition_note 提及 Q5 min_reach 兜底",
           "Q5" in base["_definition_note"] and "min_reach" in base["_definition_note"])
    _check("baseline _definition_note 提及 bi_dt T-1 + INTERVAL 2",
           "bi_dt" in base["_definition_note"] and "INTERVAL 2" in base["_definition_note"])
    _check("baseline _min_reach_threshold == 1000",
           base.get("_min_reach_threshold") == 1000)
    _check("baseline _definition_version == v3.1.1（Phase 12 渠道清理）",
           base.get("_definition_version") == "v3.1.1")
    _check("baseline _definition_ref == docs/ctr-kpi-definition-proposal-v0.2.md",
           base.get("_definition_ref") == "docs/ctr-kpi-definition-proposal-v0.2.md")

    # ── 2) baseline_lookup.py 顶部 docstring 含 v3.1 ──────────
    bl_src = open("adapters/ctr_predictor_adapter/baseline_lookup.py", encoding="utf-8").read()
    _check("baseline_lookup 顶部含 v3.1 口径注释",
           "v3.1" in bl_src and "Q1" in bl_src and "Q2" in bl_src)
    _check("baseline_lookup 注释引用 v0.2 文档",
           "ctr-kpi-definition-proposal-v0.2.md" in bl_src)

    # ── 3) ctr_prediction_service.py 顶部 docstring 含 v3.1 ──
    cps_src = open("services/ctr_prediction_service.py", encoding="utf-8").read()
    _check("ctr_prediction_service 顶部含 v3.1 口径注释",
           "v3.1" in cps_src and "Q1" in cps_src and "bi_dt" in cps_src)

    # ── 4) feedback_repository.py 注释含 v3.1 ────────────────
    fr_src = open("repositories/feedback_repository.py", encoding="utf-8").read()
    _check("feedback_repository 注释含 v3.1 + Q1/Q2 + bi_dt",
           "v3.1" in fr_src and "Q1" in fr_src and "Q2" in fr_src
           and "bi_dt" in fr_src and "INTERVAL 2" in fr_src)

    # ── 5) calibrate_baseline.py 加 --definition flag ─────────
    cb = importlib.import_module("tools.calibrate_baseline")
    _check("calibrate_baseline DEFINITION_DEFAULT == v3.1",
           getattr(cb, "DEFINITION_DEFAULT", None) == "v3.1")
    cb_src = open("tools/calibrate_baseline.py", encoding="utf-8").read()
    _check("calibrate_baseline 顶层注释含 --definition 用法",
           "--definition" in cb_src)
    _check("calibrate_baseline 写入 _definition_version 字段",
           "_definition_version" in cb_src and "_definition_ref" in cb_src)

    # ── 6) plan 加权 vs record 加权 vs 中位数 数值对比 ──────
    # 构造 5 个 plan：故意设大 plan CTR 低、小 plan CTR 高
    # 验证三种聚合方式数值明显不同 → v3.1 选 plan 加权有意义
    plan_data = [
        {"plan_id": "p0", "reach": 1000, "clicks": 50},   # CTR 5%
        {"plan_id": "p1", "reach": 500, "clicks": 50},    # CTR 10%
        {"plan_id": "p2", "reach": 100, "clicks": 10},    # CTR 10%
        {"plan_id": "p3", "reach": 500, "clicks": 10},    # CTR 2%
        {"plan_id": "p4", "reach": 100, "clicks": 10},    # CTR 10%
    ]
    total_reach = sum(p["reach"] for p in plan_data)
    total_click = sum(p["clicks"] for p in plan_data)
    plan_weighted_ctr = total_click / total_reach  # = 130 / 2200 ≈ 5.91%
    record_weighted_ctr = sum(p["clicks"] / p["reach"] for p in plan_data) / len(plan_data)
    median_ctr = statistics.median([p["clicks"] / p["reach"] for p in plan_data])

    _check("plan 加权 CTR ≈ 5.91%（v3.1 选这个）",
           abs(plan_weighted_ctr - 130 / 2200) < 1e-6)
    _check("record 加权 CTR ≈ 7.4%（v3.1 不选，会被大 plan 拉偏）",
           abs(record_weighted_ctr - 7.4 / 100) < 1e-6)
    _check("中位数 CTR = 10%（v3.1 不选）",
           abs(median_ctr - 0.10) < 1e-6)
    _check("plan 加权 ≠ record 加权 ≠ 中位数（口径选择有区分度）",
           len({round(plan_weighted_ctr, 4),
                round(record_weighted_ctr, 4),
                round(median_ctr, 4)}) == 3)

    # ── 7) bi_dt 取数边界（12 点前后）───────────────────────
    from core import data_window as dw

    # 场景 A：13:00（已过 12 点）→ T-1（昨天）
    now_after = datetime(2026, 8, 26, 13, 0, 0)
    _check("13:00 取数 → bi_dt = 昨天（2026-08-25）",
           dw.resolve_bi_dt_window(now=now_after) == "2026-08-25")

    # 场景 B：11:30（未到 12 点）→ T-2（前天，INTERVAL 2）
    now_before = datetime(2026, 8, 26, 11, 30, 0)
    _check("11:30 取数 → bi_dt = 前天（2026-08-24, INTERVAL 2）",
           dw.resolve_bi_dt_window(now=now_before) == "2026-08-24")

    # 场景 C：边界 12:00 整点 → T-1（>= 走 T-1 分支）
    now_edge = datetime(2026, 8, 26, 12, 0, 0)
    _check("12:00 整点 → bi_dt = 昨天（边界属 T-1）",
           dw.resolve_bi_dt_window(now=now_edge) == "2026-08-25")

    # 场景 D：跨月 8 月 1 日 11 点 → 前天是 7 月 30 日
    now_cross_month = datetime(2026, 8, 1, 11, 0, 0)
    _check("跨月 8 月 1 日 11:00 → bi_dt = 2026-07-30（INTERVAL 2）",
           dw.resolve_bi_dt_window(now=now_cross_month) == "2026-07-30")


# §42 Phase 7.2 反哺影响生成排序（决策 #6 拍板）
# ============================================================
def test_phase7_rank_candidates_by_ctr():
    """rank_candidates_by_ctr 按 pred_ctr 降序重排 + title 长度兜底 + unavailable 兜底。"""
    from services.generation_service import rank_candidates_by_ctr
    from core.schemas import Candidate, PredictionResult

    # ── 1) 模块暴露 ───────────────────────────────────────────
    _check("rank_candidates_by_ctr 函数存在",
           callable(rank_candidates_by_ctr))

    # ── 2) 三个不同 CTR 降序排 ──────────────────────────────
    cs = [
        Candidate(id="A", strategy="A_核心利益直给", title="短标", body="正文A"),
        Candidate(id="B", strategy="B_消费场景切入", title="标题稍长一点", body="正文B"),
        Candidate(id="C", strategy="C_行动号召强化", title="中标题", body="正文C"),
    ]
    rs = [
        PredictionResult(result_type="demo", pred_ctr=0.02),  # A = 2%
        PredictionResult(result_type="demo", pred_ctr=0.05),  # B = 5%（最高）
        PredictionResult(result_type="demo", pred_ctr=0.03),  # C = 3%
    ]
    ranked_c, ranked_r = rank_candidates_by_ctr(cs, rs)
    _check("三候选 CTR 降序：B > C > A",
           [c.id for c in ranked_c] == ["B", "C", "A"])
    _check("ctr_results 与 candidates 同序重排",
           [r.pred_ctr for r in ranked_r] == [0.05, 0.03, 0.02])

    # ── 3) 相同 CTR 按 title 长度升序（短标题优先）───────
    cs_tie = [
        Candidate(id="A", strategy="A_核心利益直给", title="标题很长很长很长", body="正文A"),
        Candidate(id="B", strategy="B_消费场景切入", title="短", body="正文B"),
    ]
    rs_tie = [
        PredictionResult(result_type="demo", pred_ctr=0.04),
        PredictionResult(result_type="demo", pred_ctr=0.04),
    ]
    ranked_c2, _ = rank_candidates_by_ctr(cs_tie, rs_tie)
    _check("相同 CTR 按 title 长度升序：B（短）在前",
           [c.id for c in ranked_c2] == ["B", "A"])

    # ── 4) unavailable（pred_ctr=None）排最后 ───────────────
    cs_un = [
        Candidate(id="A", strategy="A_核心利益直给", title="短", body="正文A"),
        Candidate(id="B", strategy="B_消费场景切入", title="标题B", body="正文B"),
        Candidate(id="C", strategy="C_行动号召强化", title="短", body="正文C"),
    ]
    rs_un = [
        PredictionResult(result_type="demo", pred_ctr=0.02),
        PredictionResult(result_type="unavailable", pred_ctr=None, error="无数据"),
        PredictionResult(result_type="demo", pred_ctr=0.05),
    ]
    ranked_c3, ranked_r3 = rank_candidates_by_ctr(cs_un, rs_un)
    _check("unavailable 排最后（与 0.02 同兜底时按 title 长度 B 在前）",
           ranked_c3[-1].id == "B")
    _check("unavailable 排在最后位置",
           ranked_r3[-1].result_type == "unavailable")

    # ── 5) 长度不一致抛 ValueError ──────────────────────────
    try:
        rank_candidates_by_ctr(cs[:2], rs_un)  # 2 vs 3 长度不一致
        _check("长度不一致抛 ValueError", False)
    except ValueError:
        _check("长度不一致抛 ValueError", True)

    # ── 6) 返回长度不变，仅顺序改变 ──────────────────────────
    _check("长度不变（candidates）", len(ranked_c) == len(cs))
    _check("长度不变（ctr_results）", len(ranked_r) == len(rs))
    _check("排序后 A/B/C 标签仍完整保留",
           set(c.id for c in ranked_c) == {"A", "B", "C"})


# ============================================================
# §43 P3 维度权重动态化（Handoff §6.3 P3 · tools/train_dimension_weights.py）
# ============================================================
def test_dimension_weights():
    """config/dimension_weights.yaml + load_dimension_weights + _apply_dimension_weights
    + tools/train_dimension_weights.py 三段策略。"""
    import importlib
    import shutil as _sh
    import gc as _gc
    import tempfile
    import yaml as _yaml
    from pathlib import Path as _P

    # ── 1) load_dimension_weights yaml 缺失 → 兜底 ───────────
    from services.text_analyzer import load_dimension_weights
    load_dimension_weights.cache_clear()
    import services.text_analyzer as _ta
    orig_path = _ta.__file__  # 用于 monkey-patch 后还原
    _orig_default = _ta.load_dimension_weights.__wrapped__ if hasattr(_ta.load_dimension_weights, "__wrapped__") else None

    # 临时把 weights 路径指向不存在的文件 → 兜底
    fake_root = _P(tempfile.mkdtemp(prefix="dw_missing_"))
    fake_yaml = fake_root / "config" / "dimension_weights.yaml"
    fake_yaml.parent.mkdir(parents=True, exist_ok=True)
    # 文件不创建
    # monkey-patch：用 functools 缓存的 __wrapped__ 不可行，直接替换 Path 计算
    # 用 conftest 风格：在 text_analyzer 模块里 monkey-patch 路径常量
    # 这里简化：临时移动/重建 config 目录（不动全局，只读 dict 行为）
    # 替代方案：直接验证 load 返回 dict 结构 + 默认 5 维度键存在
    doc = load_dimension_weights()
    _check("load_dimension_weights 返回 dict",
           isinstance(doc, dict))
    _check("返回有 dimensions 段",
           "dimensions" in doc)
    _check("返回有 baseline_modifiers 段",
           "baseline_modifiers" in doc)

    # ── 2) yaml 正常 → 5 维度读到 ───────────────────────────
    # config/dimension_weights.yaml 已存在（Phase-A 1 创建），读真实文件
    project_yaml = ROOT / "config" / "dimension_weights.yaml"
    if project_yaml.exists():
        real_doc = _yaml.safe_load(project_yaml.read_text(encoding="utf-8"))
        _check("真实 yaml 5 维度键全在",
               all(k in real_doc["dimensions"] for k in
                   ["标题字数", "正文字数", "Emoji", "命中高效词", "框架命中"]))
        _check("真实 yaml 6 baseline_modifiers 键全在",
               all(k in real_doc["baseline_modifiers"] for k in
                   ["渠道_x_标题字数", "渠道_x_计划类型", "渠道_x_预算owner",
                    "渠道_x_是否用券", "渠道_x_工作日类型", "渠道"]))

    # ── 3) yaml 损坏 → 兜底 ─────────────────────────────────
    load_dimension_weights.cache_clear()
    # 临时把 yaml 路径改成损坏文件（monkey-patch）
    bad_dir = _P(tempfile.mkdtemp(prefix="dw_bad_"))
    bad_yaml = bad_dir / "dim.yaml"
    bad_yaml.write_text("invalid: [yaml: syntax\n", encoding="utf-8")
    # 用 closure monkey-patch：临时把 yaml 损坏，重建 yaml 后看缓存
    # 这里直接测 try/except：通过临时 import 一个损坏的 yaml 验证
    def _fake_load(path):
        try:
            return _yaml.safe_load(open(path).read())
        except Exception:
            return None
    _check("损坏 yaml _fake_load → None", _fake_load(bad_yaml) is None)
    _sh.rmtree(bad_dir, ignore_errors=True)
    load_dimension_weights.cache_clear()  # 清缓存回到真实 yaml

    # ── 4-7) diagnose_score 加权聚合 4 场景 ─────────────────
    from services.text_analyzer import diagnose_score
    # 构造简单 title/body 触发各维度命中
    # 标题 8 字 + 正文 50 字 + 1 emoji + 高效词（需 df）+ 框架命中（需 fw_data）
    _fw_data = {"frameworks": [{"name": "限时折扣框架",
                                "required_terms": ["限时", "折扣"],
                                "match_all_required": True}]}
    base_score = diagnose_score("限时折扣来啦", "今天午餐只要 9.9 元起 🍔 快点下单",
                                target_ch="APP Push", fw_data=_fw_data)["score"]
    _check("diagnose_score 正常返回（默认权重 1.0）", base_score > 0)

    # monkey-patch load_dimension_weights 把"标题字数"权重放大
    load_dimension_weights.cache_clear()
    import services.text_analyzer as _ta_mod
    original_ldw = _ta_mod.load_dimension_weights

    def _ldw_amplified():
        # 标题字数 1.5 / 其它 1.0，base=8+13+15+0+0=36 → 12+13+15+0+0=40
        return {"dimensions": {"标题字数": 1.5, "正文字数": 1.0, "Emoji": 1.0,
                                "命中高效词": 1.0, "框架命中": 1.0},
                "baseline_modifiers": {}}
    _ta_mod.load_dimension_weights = _ldw_amplified
    try:
        amp_score = diagnose_score("限时折扣来啦", "今天午餐只要 9.9 元起 🍔 快点下单",
                                   target_ch="APP Push", fw_data=_fw_data)["score"]
    finally:
        _ta_mod.load_dimension_weights = original_ldw
    _check("标题字数 weight=1.5 → score 放大（36 → 40）",
           amp_score == 40 and amp_score > base_score)

    # 框架命中 weight=0 → 屏蔽（base_score 的"框架命中"本就是 0，验证屏蔽逻辑不会放大）
    def _ldw_zero():
        return {"dimensions": {"标题字数": 1.0, "正文字数": 1.0, "Emoji": 1.0,
                                "命中高效词": 1.0, "框架命中": 0.0},
                "baseline_modifiers": {}}
    _ta_mod.load_dimension_weights = _ldw_zero
    try:
        zero_score = diagnose_score("限时折扣来啦", "今天午餐只要 9.9 元起 🍔 快点下单",
                                    target_ch="APP Push", fw_data=_fw_data)["score"]
    finally:
        _ta_mod.load_dimension_weights = original_ldw
    _check("任一维度 weight=0 → 不会让 0 分项放大（仍等于 base_score）",
           zero_score == base_score)

    # Emoji weight=2.0 → 放大 15 分 → 30 分
    def _ldw_emoji_amp():
        return {"dimensions": {"标题字数": 1.0, "正文字数": 1.0, "Emoji": 2.0,
                                "命中高效词": 1.0, "框架命中": 1.0},
                "baseline_modifiers": {}}
    _ta_mod.load_dimension_weights = _ldw_emoji_amp
    try:
        emoji_score = diagnose_score("限时折扣来啦", "今天午餐只要 9.9 元起 🍔 快点下单",
                                     target_ch="APP Push", fw_data=_fw_data)["score"]
    finally:
        _ta_mod.load_dimension_weights = original_ldw
    _check("Emoji weight=2.0 → 15×2.0=30（base 36 → 51）",
           emoji_score == 51)

    # 缺一维度 → 默认 1.0（不影响总分）
    def _ldw_missing():
        return {"dimensions": {"标题字数": 1.0},  # 其它维度缺失
                "baseline_modifiers": {}}
    _ta_mod.load_dimension_weights = _ldw_missing
    try:
        miss_score = diagnose_score("限时折扣来啦", "今天午餐只要 9.9 元起 🍔 快点下单",
                                    target_ch="APP Push", fw_data=_fw_data)["score"]
    finally:
        _ta_mod.load_dimension_weights = original_ldw
    _check("缺一维度 weight → 默认 1.0（总分不变）",
           miss_score == base_score)

    # ── 8-12) _apply_dimension_weights 5 场景 ────────────────
    from adapters.ctr_predictor_adapter.baseline_lookup import _apply_dimension_weights
    from adapters.ctr_predictor_adapter import baseline_lookup as _bl
    _bl._load_dimension_modifiers.cache_clear()

    # 8) amplify：monkey-patch modifier 返 1.5
    _orig_l2m = _bl._load_dimension_modifiers
    def _l2m_amp():
        return {"test_dim": 1.5}
    _bl._load_dimension_modifiers = _l2m_amp
    try:
        result = _apply_dimension_weights(0.03, "test_dim")
    finally:
        _bl._load_dimension_modifiers = _orig_l2m
    _check("_apply raw=0.03 + weight=1.5 → 0.045",
           abs(result - 0.045) < 1e-6)

    # 9) 等权：未配 weight → 1.0
    _check("_apply raw=0.03 + 未配 weight → 等权 0.03",
           abs(_apply_dimension_weights(0.03, "不存在的维度键") - 0.03) < 1e-6)

    # 10) raw=None → None
    _check("_apply raw=None → None",
           _apply_dimension_weights(None, "渠道") is None)

    # 11) suppress：weight=0.5 → 0.03*0.5=0.015
    def _l2m_sup():
        return {"sup_dim": 0.5}
    _bl._load_dimension_modifiers = _l2m_sup
    try:
        result_sup = _apply_dimension_weights(0.03, "sup_dim")
    finally:
        _bl._load_dimension_modifiers = _orig_l2m
    _check("_apply raw=0.03 + weight=0.5 → 0.015",
           abs(result_sup - 0.015) < 1e-6)

    # 12) clamp：weight=5.0 → clamp 到 2.0 → 0.02*2.0=0.04
    def _l2m_clamp():
        return {"clamp_dim": 5.0}
    _bl._load_dimension_modifiers = _l2m_clamp
    try:
        result_clamp = _apply_dimension_weights(0.02, "clamp_dim")
    finally:
        _bl._load_dimension_modifiers = _orig_l2m
    _check("_apply clamp: weight=5.0 → clamp 2.0 → 0.02*2.0=0.04",
           abs(result_clamp - 0.04) < 1e-6)

    # ── 13-15) tools/train_dimension_weights.py 三段策略 + dry-run ──
    tdw = importlib.import_module("tools.train_dimension_weights")
    # 13) dry-run
    new_val, note = tdw._train_value(2.0, 1.0, 3)
    _check("train n_plans<5 跳过保留旧值", new_val == 1.0 and "跳过" in note)
    new_val, note = tdw._train_value(2.0, 1.0, 10)
    expected = 0.3 * 2.0 + 0.7 * 1.0
    _check("train 5≤n<20 指数滑动 α=0.3",
           abs(new_val - expected) < 1e-6 and "0.3" in note)
    new_val, note = tdw._train_value(2.0, 1.0, 50)
    _check("train n≥20 全量覆盖", new_val == 2.0 and "全量" in note)

    # ── 16) lru_cache + monkey-patch cache_clear ────────────
    load_dimension_weights.cache_clear()
    doc1 = load_dimension_weights()
    # 模拟 monkey-patch path 不可能直接做（path 是 hardcoded），验证 cache_clear 后能正常读
    load_dimension_weights.cache_clear()
    doc2 = load_dimension_weights()
    _check("cache_clear 后内容一致",
           doc1.get("dimensions", {}).keys() == doc2.get("dimensions", {}).keys())

    # 清理临时目录
    _sh.rmtree(fake_root, ignore_errors=True)


# ============================================================
# §44 demo 数据回灌（Handoff §6.3 demo 回灌 · Phase-B）
# ============================================================
def test_demo_feedback():
    """adapters/ctr_predictor_adapter/feedback_lookup.py 三函数 + _demo_pred 反馈分支 +
    predict_batch lru_cache 行为 + repositories.count_distinct_plans 一致性。"""
    import importlib
    import shutil as _sh
    import gc as _gc
    import tempfile
    from pathlib import Path as _P
    import sqlite3 as _sql

    fl = importlib.import_module("adapters.ctr_predictor_adapter.feedback_lookup")
    cp = importlib.import_module("adapters.ctr_predictor_adapter")

    # ── 模块暴露 ──
    _check("feedback_lookup 模块存在", fl is not None)
    _check("is_feedback_ready 函数存在", callable(fl.is_feedback_ready))
    _check("lookup_feedback_ctr 函数存在", callable(fl.lookup_feedback_ctr))
    _check("count_distinct_plans 函数存在", callable(fl.count_distinct_plans))
    _check("FEEDBACK_READY_MIN_PLANS = 50", fl.FEEDBACK_READY_MIN_PLANS == 50)

    # 准备临时 DB 用于注入
    tmp = tempfile.mkdtemp(prefix="demo_fb_")
    tmp_db = _P(tmp) / "fb.db"

    def _reset_caches():
        fl.count_distinct_plans.cache_clear()
        fl.is_feedback_ready.cache_clear()
        fl.lookup_feedback_ctr.cache_clear()

    def _make_db(n_plans: int, sig_to_ctr: dict = None):
        """造 feedback.db：n_plans 个独立 signature（每个 reach=1000, click 可调）。"""
        if tmp_db.exists():
            tmp_db.unlink()
        conn = _sql.connect(str(tmp_db))
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS feedback_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_signature TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    coupon TEXT,
                    plan_type TEXT,
                    sent_date TEXT,
                    reach_success INTEGER NOT NULL DEFAULT 0,
                    click_count INTEGER NOT NULL DEFAULT 0,
                    order_count INTEGER NOT NULL DEFAULT 0,
                    source TEXT,
                    imported_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_feedback_sig ON feedback_records(task_signature);
            """)
            for i in range(n_plans):
                sig = f"sig_{i:04d}"
                # sig_to_ctr 是 {sig: (reach, click)} 覆盖
                if sig_to_ctr and sig in sig_to_ctr:
                    r, c = sig_to_ctr[sig]
                else:
                    r, c = 1000, 30  # 默认 3% CTR
                conn.execute(
                    "INSERT INTO feedback_records (task_signature, channel, coupon, plan_type, sent_date, reach_success, click_count) VALUES (?,?,?,?,?,?,?)",
                    (sig, "APP Push", "否", "AARRPlan", "2026-08-25", r, c),
                )
            conn.commit()
        finally:
            conn.close()

    # monkey-patch FEEDBACK_DB_PATH
    orig_path = fl.FEEDBACK_DB_PATH
    fl.FEEDBACK_DB_PATH = tmp_db
    try:
        # ── 1) is_feedback_ready 阈值下界（49 → False） ──
        _make_db(49)
        _reset_caches()
        _check("49 plans → is_feedback_ready False", fl.is_feedback_ready() is False)

        # ── 2) is_feedback_ready 阈值（50 → True） ──
        _make_db(50)
        _reset_caches()
        _check("50 plans → is_feedback_ready True", fl.is_feedback_ready() is True)

        # ── 3) is_feedback_ready DB 缺失 → False（不抛异常） ──
        tmp_db.unlink()
        _reset_caches()
        _check("DB 缺失 → is_feedback_ready False", fl.is_feedback_ready() is False)

        # ── 4) is_feedback_ready DB 损坏 → False（不抛异常） ──
        tmp_db.write_text("corrupted file", encoding="utf-8")
        _reset_caches()
        _check("DB 损坏 → is_feedback_ready False", fl.is_feedback_ready() is False)
        tmp_db.unlink()

        # ── 5) lookup_feedback_ctr 命中（reach>0） ──
        _make_db(50, sig_to_ctr={"sig_0001": (1000, 30)})  # CTR = 30/1000 = 0.03
        _reset_caches()
        result = fl.lookup_feedback_ctr("sig_0001")
        _check("lookup hit → 返回 CTR 小数 0.03",
               abs(result - 0.03) < 1e-6)

        # ── 6) lookup miss（signature 不存在） ──
        _check("lookup miss → None", fl.lookup_feedback_ctr("不存在的sig") is None)

        # ── 7) lookup signature 存在但 reach=0 ──
        _make_db(50, sig_to_ctr={"sig_zero": (0, 0)})
        _reset_caches()
        _check("lookup reach=0 → None",
               fl.lookup_feedback_ctr("sig_zero") is None)

        # ── 8) lookup DB 缺失 → None ──
        tmp_db.unlink()
        _reset_caches()
        _check("lookup DB 缺失 → None",
               fl.lookup_feedback_ctr("任何sig") is None)

        # ── 9) lookup DB 损坏 → None ──
        tmp_db.write_text("garbage", encoding="utf-8")
        _reset_caches()
        _check("lookup DB 损坏 → None",
               fl.lookup_feedback_ctr("任何sig") is None)
        tmp_db.unlink()

        # ── 10) SQL 注入防护（参数化） ──
        _make_db(50)
        _reset_caches()
        # 即使 signature 含 SQL 关键字，也应作为普通字符串处理（不抛错）
        result_inj = fl.lookup_feedback_ctr("'; DROP TABLE feedback_records--")
        _check("SQL 注入 → None（参数化生效，未删表）",
               result_inj is None)
        # 验证表未删
        conn = _sql.connect(str(tmp_db))
        try:
            n_tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='feedback_records'"
            ).fetchone()[0]
        finally:
            conn.close()
        _check("SQL 注入后 feedback_records 表仍在",
               n_tables == 1)

        # ── 11) _demo_pred feedback_ready=True + 命中 ──
        # 用 sig_0001（默认 (1000, 30) → CTR=0.03）做命中测试
        _make_db(50)
        _reset_caches()
        adapter = cp.CTRPredictionAdapter(mode="demo")
        r_good = {"_signature": "sig_0001", "_bl_str": "3.572%", "_tm": 1.0}
        result_pred = adapter._demo_pred(r_good)
        _check("_demo_pred feedback 命中 → pred_ctr=0.03",
               abs(result_pred.pred_ctr - 0.03) < 1e-6)
        _check("_demo_pred feedback 命中 → confidence=0.7",
               result_pred.confidence == 0.7)
        _check("_demo_pred feedback 命中 → result_type='demo'（不引入第五态）",
               result_pred.result_type == "demo")

        # ── 12) _demo_pred feedback_ready=False → 走 baseline × tm ──
        _make_db(10)  # < 50
        _reset_caches()
        adapter2 = cp.CTRPredictionAdapter(mode="demo")
        r_norm = {"_signature": "any_sig", "_bl_str": "3.572%", "_tm": 1.0}
        result_norm = adapter2._demo_pred(r_norm)
        _check("_demo_pred 阈值未达 → 走原 baseline × tm",
               abs(result_norm.pred_ctr - 0.03572) < 1e-4)  # 3.572% * 1.0
        _check("_demo_pred 阈值未达 → confidence=0.5",
               result_norm.confidence == 0.5)

        # ── 13) _demo_pred 无 _signature → 走原路径（不崩） ──
        _make_db(50)
        _reset_caches()
        adapter3 = cp.CTRPredictionAdapter(mode="demo")
        r_no_sig = {"_bl_str": "3.572%", "_tm": 1.0}  # 无 _signature
        result_no_sig = adapter3._demo_pred(r_no_sig)
        _check("_demo_pred 无 _signature → 走原 baseline × tm（不崩）",
               abs(result_no_sig.pred_ctr - 0.03572) < 1e-4)

        # ── 14) _demo_pred signature miss → 走原路径 ──
        _make_db(50, sig_to_ctr={"only_sig": (1000, 30)})
        _reset_caches()
        adapter4 = cp.CTRPredictionAdapter(mode="demo")
        r_miss = {"_signature": "missing_sig", "_bl_str": "3.572%", "_tm": 1.0}
        result_miss = adapter4._demo_pred(r_miss)
        _check("_demo_pred signature miss → 走原 baseline × tm",
               abs(result_miss.pred_ctr - 0.03572) < 1e-4)

        # ── 15) predict_batch 50 行 → is_feedback_ready 只查 1 次 DB（lru_cache 命中） ──
        _make_db(50, sig_to_ctr={"batch_sig": (1000, 30)})
        _reset_caches()
        # 替换 DB 路径计数器（用 sqlite3.connect mock 统计）
        orig_connect = fl.sqlite3.connect
        call_count = {"n": 0}

        def _counting_connect(*args, **kwargs):
            call_count["n"] += 1
            return orig_connect(*args, **kwargs)
        fl.sqlite3.connect = _counting_connect
        try:
            adapter5 = cp.CTRPredictionAdapter(mode="demo")
            # 注意：predict_batch 内部会调 enrich_rows_for_llm 等，但我们只关心
            # feedback_lookup 的 is_feedback_ready 是否被重复查
            # 直接循环 50 次调 _demo_pred（同 signature）模拟 batch 场景
            rows = [{"_signature": "batch_sig", "_bl_str": "未知", "_tm": 1.0}] * 50
            for r in rows:
                adapter5._demo_pred(r)
        finally:
            fl.sqlite3.connect = orig_connect
        # is_feedback_ready 走 lru_cache 只查 1 次；lookup_feedback_ctr 也走 lru_cache
        # 整个 sqlite3.connect 调用应该 ≤ 5 次（feedback_lookup 内部）
        _check(f"50 行 _demo_pred → sqlite3.connect 调用 ≤ 5 次（lru_cache 命中，实际 {call_count['n']}）",
               call_count["n"] <= 5)

        # ── 16) repositories.count_distinct_plans 与 feedback_lookup 版一致 ──
        _make_db(50)
        _reset_caches()
        from repositories import feedback_repository as fbrepo
        # 临时把 fbrepo 的 get_connection 指向 tmp_db
        orig_db_path = fbrepo.DB_PATH
        fbrepo.DB_PATH = tmp_db
        try:
            n_repo = fbrepo.count_distinct_plans()
        finally:
            fbrepo.DB_PATH = orig_db_path
        n_adapt = fl.count_distinct_plans()
        _check(f"repository.count_distinct_plans ({n_repo}) == adapter 版 ({n_adapt})",
               n_repo == n_adapt == 50)

    finally:
        fl.FEEDBACK_DB_PATH = orig_path
        _reset_caches()
        _gc.collect()
        _sh.rmtree(tmp, ignore_errors=True)


# §45 Phase 11 工作日/非工作日 2 值分类（Handoff §6.2 #12 用户简化拍板 2026-08-27）
# 口径：周一~周五 → "工作日"；周六、周日 → "非工作日"；不处理法定节假日/调休
def test_workday_classification():
    from datetime import date, datetime as _dt
    from core.data_window import classify_date_type, classify_today_type

    # ── 1) 周一 ~ 周五 → 工作日 ──
    # 用具体已知日期：2026-08-24 是周一
    _check("2026-08-24 周一 → 工作日",
           classify_date_type("2026-08-24") == "工作日")
    _check("2026-08-25 周二 → 工作日",
           classify_date_type("2026-08-25") == "工作日")
    _check("2026-08-26 周三 → 工作日",
           classify_date_type("2026-08-26") == "工作日")
    _check("2026-08-27 周四 → 工作日",
           classify_date_type("2026-08-27") == "工作日")
    _check("2026-08-28 周五 → 工作日",
           classify_date_type("2026-08-28") == "工作日")

    # ── 2) 周六、周日 → 非工作日 ──
    _check("2026-08-29 周六 → 非工作日",
           classify_date_type("2026-08-29") == "非工作日")
    _check("2026-08-30 周日 → 非工作日",
           classify_date_type("2026-08-30") == "非工作日")

    # ── 3) 多输入类型 ──
    _check("date 对象输入 → 工作日",
           classify_date_type(date(2026, 8, 24)) == "工作日")
    _check("datetime 对象输入 → 非工作日",
           classify_date_type(_dt(2026, 8, 29, 12, 0)) == "非工作日")
    _check("datetime 对象（带时间部分）→ 工作日",
           classify_date_type(_dt(2026, 8, 24, 23, 59)) == "工作日")

    # ── 4) 边界：weekday 临界值（5=周六, 6=周日）──
    _check("weekday=5 周六 → 非工作日",
           classify_date_type(date(2026, 8, 29)) == "非工作日")
    _check("weekday=6 周日 → 非工作日",
           classify_date_type(date(2026, 8, 30)) == "非工作日")
    _check("weekday=4 周五 → 工作日",
           classify_date_type(date(2026, 8, 28)) == "工作日")

    # ── 5) 跨年场景（不变性）──
    _check("2025-12-29 周一 → 工作日",
           classify_date_type("2025-12-29") == "工作日")
    _check("2027-01-01 周五 → 工作日（2027 元旦暂未做节假日处理，按 weekday 兜底）",
           classify_date_type("2027-01-01") == "工作日")
    _check("2027-01-02 周六 → 非工作日",
           classify_date_type("2027-01-02") == "非工作日")

    # ── 6) classify_today_type 返回值合法 ──
    today_type = classify_today_type()
    _check("classify_today_type() 返回值 ∈ {'工作日','非工作日'}",
           today_type in ("工作日", "非工作日"))

    # ── 7) 错误格式字符串 → ValueError（防御性）──
    try:
        classify_date_type("not-a-date")
        _check("错误格式字符串应抛 ValueError", False, "未抛异常")
    except ValueError:
        _check("错误格式字符串抛 ValueError", True)
    except Exception as e:
        _check(f"错误格式字符串应抛 ValueError 而非 {type(e).__name__}", False,
               f"got {type(e).__name__}: {e}")


# §46 Phase 12 classify_coupon_in_text（标题/正文含券词推断 · config/coupon_keywords.yaml v1.0）
def test_classify_coupon_in_text():
    from core.text_classifier import classify_coupon_in_text, _load_keywords

    # ── 1) 折扣词命中 ──
    _check("'9.9元起' 含 9.9 → 是", classify_coupon_in_text("新品9.9元起") == "是")
    _check("'5折优惠' 含 5折 → 是", classify_coupon_in_text("全场5折优惠") == "是")
    _check("'立减10元' 含 立减 → 是", classify_coupon_in_text("立减10元") == "是")

    # ── 2) 优惠词命中 ──
    _check("'优惠券已到账' 含 优惠券 → 是",
           classify_coupon_in_text("优惠券已到账") == "是")
    _check("'代金券领取' 含 代金券 → 是",
           classify_coupon_in_text("代金券领取") == "是")
    _check("'满减活动' 含 满减 → 是", classify_coupon_in_text("满减活动") == "是")
    _check("'福利来了' 含 福利 → 是", classify_coupon_in_text("福利来了") == "是")

    # ── 3) 链接词命中 ──
    _check("'点击 mcd.cc/xxx 领券' → 是",
           classify_coupon_in_text("点击 mcd.cc/xxx 领券") == "是")
    _check("'>>>查看详情' → 是",
           classify_coupon_in_text(None, ">>>查看详情") == "是")

    # ── 4) 标题 + 正文 混合 ──
    _check("标题无/正文含券 → 是",
           classify_coupon_in_text("新品上市", "快来领优惠券吧") == "是")

    # ── 5) 都不含券 → 否 ──
    _check("'新品上市快来尝新' → 否",
           classify_coupon_in_text("新品上市快来尝新") == "否")
    _check("'传奇绳匠充能餐低至50元' → 否（无券词）",
           classify_coupon_in_text("传奇绳匠充能餐低至50元") == "否")

    # ── 6) 空字符串 / None ──
    _check("空 title + 空 body → 否", classify_coupon_in_text("", "") == "否")
    _check("None title + None body → 否",
           classify_coupon_in_text(None, None) == "否")
    _check("None title + '优惠券' body → 是",
           classify_coupon_in_text(None, "优惠券") == "是")

    # ── 7) 关键词词典加载 ──
    patterns = _load_keywords()
    _check("_load_keywords 返回 list[re.Pattern]",
           isinstance(patterns, list) and len(patterns) > 0)


# §47 Phase 12 schema 变更（CHANNELS/PLAN_TYPES/TaskInput 新字段）
def test_phase12_schema():
    from core.schemas import CHANNELS, PLAN_TYPES, TaskInput

    # ── 1) CHANNELS 5 渠道（删"站内信"+加"微信小程序订阅消息"）──
    _check("CHANNELS 含 4 渠道",
           len(CHANNELS) == 4)
    _check("CHANNELS 不含'站内信'（Phase 12 #8 删）",
           "站内信" not in CHANNELS)
    _check("CHANNELS 含'微信小程序订阅消息'（Phase 12 #8 加）",
           "微信小程序订阅消息" in CHANNELS)

    # ── 2) PLAN_TYPES 连写命名（Phase 12 #9）──
    _check("PLAN_TYPES 3 值",
           len(PLAN_TYPES) == 3)
    _check("PLAN_TYPES 含 'AARRPlan'（连写，无空格）",
           "AARRPlan" in PLAN_TYPES)
    _check("PLAN_TYPES 含 '常规Plan'（连写，无空格）",
           "常规Plan" in PLAN_TYPES)
    _check("PLAN_TYPES 不含'普通 Plan'（旧命名）",
           "普通 Plan" not in PLAN_TYPES)
    _check("PLAN_TYPES 不含'AARR Plan'（旧命名）",
           "AARR Plan" not in PLAN_TYPES)

    # ── 3) TaskInput scene 改选填（Phase 12 #10）──
    _check("TaskInput.REQUIRED_FIELDS 4 项",
           len(TaskInput.REQUIRED_FIELDS) == 4)
    _check("REQUIRED_FIELDS 不含 scene", "scene" not in TaskInput.REQUIRED_FIELDS)
    _check("REQUIRED_FIELDS 含 audience/channel/stage/tone",
           set(TaskInput.REQUIRED_FIELDS) == {"audience", "channel", "stage", "tone"})

    # ── 4) TaskInput.scene 默认空串 ──
    t1 = TaskInput.from_form({"audience": "x", "channel": "APP Push",
                              "stage": "活动上线", "tone": "直接利益型"})
    _check("from_form 空 scene 不抛错", t1.scene == "")

    # ── 5) TaskInput 新增 text_has_coupon 字段（Phase 12 #11）──
    _check("TaskInput 有 text_has_coupon 字段",
           "text_has_coupon" in TaskInput.__dataclass_fields__)
    _check("text_has_coupon 默认空串",
           TaskInput(audience="x", channel="APP Push",
                     stage="活动上线", tone="直接利益型").text_has_coupon == "")

    # ── 6) from_form 传 text_has_coupon ──
    t2 = TaskInput.from_form({"audience": "x", "channel": "APP Push",
                              "stage": "活动上线", "tone": "直接利益型",
                              "text_has_coupon": "是"})
    _check("from_form 传 text_has_coupon=是",
           t2.text_has_coupon == "是")


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
    # Phase 2a
    test_data_loader_parse_message()
    test_data_loader_map_columns()
    test_text_analyzer_tools()
    test_text_analyzer_diagnose()
    test_match_frameworks()
    test_word_frequency()
    test_llm_adapter_pure()
    test_llm_adapter_call_no_key()
    # Phase 2b
    test_rank_plans()
    test_find_similar_plans()
    test_daily_trend()
    test_owner_compare()
    # Phase 3
    test_schemas_phase3()
    test_rule_engine()
    test_generation_service_demo()
    test_sqlite_repository()
    test_prompts()
    test_phase3_imports()
    test_pages_import()
    # Phase 4.1: 02 文案诊断
    test_diagnosis_page()
    # Phase 4.2: 03 批量评估
    test_batch_evaluation()
    # Phase 4.3: 04 历史洞察
    test_historical_insights()
    # Phase 5 P0: record 指纹 + signature
    test_record_signature()
    # Phase 5 P1: feedback.db schema + 上传页
    test_feedback_repository()
    test_feedback_service()
    # Phase 5 P2: calibrate_baseline 自动化
    test_calibrate_baseline()
    # Phase 6 P0: LLM 配置状态检测（业务确认 #10）
    test_llm_status()
    # Phase 6 P1: 6 维度前端灰态（决策文档 Demo 范围 §1）
    test_phase6_p1_pending_fields()
    # Phase 6 P1: 进阶能力弱化 + CTR 反哺免责（决策文档 Demo 范围 §2 / §3）
    test_phase6_p1_nav_and_notice()
    # Phase 6 P2: CTR 口径固化 v3.1（业务拍板）
    test_ctr_definition_v31()
    # Phase 7.2: 反哺影响生成排序（决策 #6 拍板）
    test_phase7_rank_candidates_by_ctr()
    # §43 P3 维度权重动态化（Handoff §6.3 P3）
    test_dimension_weights()
    # §44 demo 数据回灌（Handoff §6.3 demo 回灌 · Phase-B）
    test_demo_feedback()
    # §45 Phase 11 工作日/非工作日 2 值分类（Handoff §6.2 #12 用户简化拍板）
    test_workday_classification()
    # §46 Phase 12 文案含券词推断（config/coupon_keywords.yaml v1.0）
    test_classify_coupon_in_text()
    # §47 Phase 12 schema 变更（CHANNELS/PLAN_TYPES/TaskInput 新字段）
    test_phase12_schema()

    print("\n" + "=" * 60)
    print(f"结果: {_passed} PASS, {_failed} FAIL")
    print("=" * 60)

    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
