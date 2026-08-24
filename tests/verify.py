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
        TaskInput(product_benefit="", audience="常规大盘", channel="APP Push",
                  objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型")
        _check("TaskInput product_benefit 空 抛错", False, "未抛错")
    except ValueError:
        _check("TaskInput product_benefit 空 抛错", True)

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
    _check("CHANNELS 4 渠道", set(CHANNELS) == {"APP Push", "企微 1v1", "短信", "站内信"})


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

    # 必填字段缺失抛错（schema 层 ValueError 或 service 层 GenerationError 都算）
    try:
        bad_task = TaskInput(product_benefit="", audience="x", channel="APP Push",
                             objective="x", stage="x", scene="x", tone="x")
        generate(bad_task)
        _check("缺 product_benefit 抛错", False, "未抛错")
    except (GenerationError, ValueError):
        _check("缺 product_benefit 抛错", True)

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

    print("\n" + "=" * 60)
    print(f"结果: {_passed} PASS, {_failed} FAIL")
    print("=" * 60)

    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
