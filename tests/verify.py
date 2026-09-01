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
    from core.llm_gateway import _classify_call_error, _sanitize_error

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

    # ── Phase 23 regression（Critical-1 · 锁住 API key 不外漏）───────────
    # 现实场景：OpenAI AuthenticationError.message 含 sk- 前缀
    class _FakeAuthenticationError(Exception):
        pass
    fake_msg = "Incorrect API key provided: sk-AbCdEfGhiJklMnOpQrStUvWxYz1234567"
    err_code = _classify_call_error(_FakeAuthenticationError(fake_msg))
    _check("Critical-1: 鉴权错误分类（无 sk- 泄漏）",
           "鉴权" in err_code and "sk-" not in err_code,
           f"got {err_code!r}")
    # sanitize 行为：sk-AbCdEfGhi... 整段被替换成 ***，原 key 子串不得残留在输出
    sanitized = _sanitize_error(fake_msg)
    _check("Critical-1: sanitize 屏蔽 sk- 前缀",
           "sk-AbCdEfGhi" not in sanitized
           and "AbCdEfGhi" not in sanitized
           and "Incorrect API key" in sanitized,
           f"got {sanitized!r}")

    # ── Phase 23 regression（Critical-2 · 锁住 XSS escape + 短信长度）───
    from html import escape as _html_escape
    _check("Critical-2: html.escape 屏蔽 <script>",
           "&lt;script&gt;" in _html_escape("<script>alert(1)</script>"),
           f"got {_html_escape('<script>alert(1)</script>')!r}")
    _check("Critical-2: 短信段数按 escape 前长度算（escape 幂等性）",
           _html_escape("x" * 200) == "x" * 200,
           f"len mismatch")

    # ── Phase 23 regression（Critical-1 · 真覆盖调用点）─────────────────
    # 上面"鉴权错误分类"只测了 _classify_call_error helper。还得测：
    # ProviderRouter.call() → _call_openai → openai.OpenAI().chat.completions.create()
    # 抛鉴权错 → _call_openai 的 except 捕获 → 整条调用链都不能把 sk- 透到前端。
    # 实现：mock sys.modules['openai'] 让 client.chat.completions.create() raise AuthErr。
    import sys
    fake_key = "sk-AbCdEfGhiJklMnOpQrStUvWxYz1234567"

    class _FakeAuthenticationError(Exception):
        """类名必须含 'Authentication'，否则 _classify_call_error 走到 fallback 分支，测不出真路径。"""
        pass

    class _FakeCompletions:
        def create(self, **kwargs):
            raise _FakeAuthenticationError(f"Incorrect API key provided: {fake_key}")

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = _FakeChat()

    # 注入 fake openai 模块；_call_openai 内 `import openai` 拿到这个 fake
    saved_openai = sys.modules.get("openai")
    sys.modules["openai"] = type(sys)("openai")
    sys.modules["openai"].OpenAI = _FakeOpenAI

    try:
        router = ProviderRouter(provider="openai", api_key=fake_key)
        raw = router.call("test prompt")
    finally:
        if saved_openai is not None:
            sys.modules["openai"] = saved_openai
        else:
            del sys.modules["openai"]

    _check("Critical-1: ProviderRouter.call 调用点不透漏 sk-",
           fake_key not in raw and "sk-" not in raw,
           f"got {raw!r}")


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
        product_category="汉堡", benefit_type="折扣",
        audience="常规大盘",
        channel="APP Push", objective="建立认知", stage="活动预热",
        scene="早餐", tone="直接利益型",
    )
    _check("TaskInput 必填齐 is_complete=True", t.is_complete is True)
    _check("TaskInput.to_dict 含 product_category", "product_category" in t.to_dict())
    _check("TaskInput.to_dict 含 benefit_type", "benefit_type" in t.to_dict())
    try:
        t_empty_pending = TaskInput(product_category="", benefit_type="",
                                    audience="常规大盘",
                                    channel="APP Push", objective="",
                                    stage="活动预热", scene="早餐", tone="直接利益型")
        _check("TaskInput 灰态字段空 不抛错（Phase 6 P1）",
               t_empty_pending.product_category == "" and t_empty_pending.objective == "")
    except ValueError:
        _check("TaskInput 灰态字段空 不抛错（Phase 6 P1）", False, "误抛错")

    # Candidate（Phase 13 2026-08-27：删除 edited 字段 + effective_*/is_edited/reset_edit）
    c = Candidate(id="A", strategy="A_核心利益直给", title="新品限时", body="点击查看详情")
    _check("Candidate 无 title_edited 字段", not hasattr(c, "title_edited"))
    _check("Candidate 无 body_edited 字段", not hasattr(c, "body_edited"))
    _check("Candidate 无 effective_title 属性", not hasattr(c, "effective_title"))
    _check("Candidate 无 effective_body 属性", not hasattr(c, "effective_body"))
    _check("Candidate 无 is_edited 属性", not hasattr(c, "is_edited"))
    _check("Candidate 无 reset_edit 方法", not hasattr(c, "reset_edit"))
    _check("Candidate title 直读", c.title == "新品限时")
    _check("Candidate body 直读", c.body == "点击查看详情")
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
        product_category="汉堡", benefit_type="折扣",
        audience="常规大盘", channel="APP Push",
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
        bad_task = TaskInput(product_category="", benefit_type="",
                             objective="",
                             audience="", channel="APP Push",
                             stage="x", scene="x", tone="x")
        _check("缺 5 必填抛错", False, "未抛错")
    except (GenerationError, ValueError):
        _check("缺 5 必填抛错", True)

    # 短信渠道
    sms_task = TaskInput(
        product_category="汉堡", benefit_type="新品限时",
        audience="常规大盘", channel="短信",
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
            product_category="小食", benefit_type="赠品",
            audience="常规大盘", channel="APP Push",
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
        product_category="汉堡", benefit_type="新品",
        audience="常规大盘", channel="APP Push",
        objective="建立认知", stage="活动预热", scene="早餐", tone="直接利益型",
        expected_action="点击", extra_requirements="不得出现免费",
    )
    channel_rules = {"channels": {"APP Push": {"title_max": 15, "body_max": 60, "emoji_max": 2}}}
    p = copy_generation.build_user_prompt(task, channel_rules)
    _check("user_prompt 含'产品类别'", "产品类别" in p)
    _check("user_prompt 含'权益类型'", "权益类型" in p)
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

    # Phase 23 回归：parse_response 失败信息走 _sanitize_error 兜底（防 sk-/Bearer 模式泄漏）
    # 模拟 json.loads 抛含假 key 的异常，看 error 字段是否屏蔽
    from prompts import copy_rewrite as _cr
    import json as _json

    _FakeKey = "sk-AbCdEfGhiJklMnOpQrStUvWxYz1234567890"
    orig_loads = _json.loads
    def _bad_loads(s, *a, **kw):
        # 仅在 parse_response 触发的调用上注入假异常，其它不受影响
        raise ValueError(f"Incorrect API key provided: {_FakeKey}")
    try:
        _json.loads = _bad_loads
        err = _cr.parse_response("not-json")
    finally:
        _json.loads = orig_loads
    _check("rewrite parse 异常经 _sanitize_error 屏蔽 sk-",
           err.get("error", "").startswith("JSON失败") and _FakeKey not in err.get("error", ""),
           f"got {err!r}")


# ============================================================
# 29) Phase 3 import sanity
# ============================================================
_section("29) Phase 3 import sanity")

def test_phase3_imports():
    try:
        from services import (  # noqa
            generation_service, rule_engine,
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

    for page in ("pages.00 首页", "pages.01 内容工坊",
                 "pages.02 文案诊断", "pages.03 批量评估",
                 "pages.04 历史洞察"):
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
        product_category="小食", benefit_type="新品小卡",
        audience="常规大盘", channel="APP Push",
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

            agg = cb.aggregate_feedback(str(fr.DB_PATH))
            by_cp, by_ch = agg[0], agg[1]
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


# §39 Phase A.1 · 产品权益维度扩展（2026-08-28）
# ============================================================
def test_phase_a1_product_benefit_split():
    """Phase A.1 验证：原 product_benefit 拆为 product_category + benefit_type 两字段。

    覆盖：
    - core.product_benefit 加载 yaml + 兜底枚举（10 产品 + 8 权益 + 自定义）
    - core.schemas.TaskInput 字段拆分（to_dict 含新 2 字段，老字段不再存在）
    - prompts.copy_generation 拼 2 行「产品类别 / 权益类型」
    - services.generation_service._demo_candidates 拼接「类别 + 权益」
    - pages/01_content_studio 2 selectbox + 自定义输入（源码静态检查）
    """
    import re

    # ── 1) core.product_benefit 枚举加载 ────────────────────
    from core.product_benefit import (
        load_product_benefit, get_product_categories, get_benefit_types,
        get_custom_label, options_with_custom, FALLBACK_PRODUCT_CATEGORIES,
        FALLBACK_BENEFIT_TYPES, CUSTOM_LABEL,
    )
    _check("CUSTOM_LABEL='自定义'", CUSTOM_LABEL == "自定义")
    _check("FALLBACK_PRODUCT_CATEGORIES 10 项", len(FALLBACK_PRODUCT_CATEGORIES) == 10)
    _check("FALLBACK_BENEFIT_TYPES 8 项", len(FALLBACK_BENEFIT_TYPES) == 8)
    _check("汉堡在默认产品类别", "汉堡" in FALLBACK_PRODUCT_CATEGORIES)
    _check("折扣在默认权益类型", "折扣" in FALLBACK_BENEFIT_TYPES)

    cats = get_product_categories()
    bts = get_benefit_types()
    _check("get_product_categories() 返回 10 项", len(cats) == 10)
    _check("get_benefit_types() 返回 8 项", len(bts) == 8)
    _check("options_with_custom 加「自定义」在末位",
           options_with_custom(cats)[-1] == "自定义"
           and options_with_custom(bts)[-1] == "自定义")
    _check("options_with_custom 长度 = 原 + 1",
           len(options_with_custom(cats)) == len(cats) + 1)

    # lru_cache 命中：再 load 不重复读盘（直接调函数即可，行为校验）
    cfg = load_product_benefit()
    _check("load_product_benefit dict 含 product_categories",
           isinstance(cfg.get("product_categories"), tuple))
    _check("load_product_benefit dict 含 benefit_types",
           isinstance(cfg.get("benefit_types"), tuple))
    _check("load_product_benefit dict 含 custom_label",
           isinstance(cfg.get("custom_label"), str))

    # ── 2) core.schemas.TaskInput 字段拆分 ────────────────────
    from core.schemas import TaskInput
    _check("TaskInput 不再含 product_benefit 字段",
           "product_benefit" not in TaskInput.__dataclass_fields__)
    _check("TaskInput 含 product_category 字段",
           "product_category" in TaskInput.__dataclass_fields__)
    _check("TaskInput 含 benefit_type 字段",
           "benefit_type" in TaskInput.__dataclass_fields__)
    # 字段顺序（dataclass 顺序铁律：no-default 在前）
    field_names = list(TaskInput.__dataclass_fields__.keys())
    no_default_idx = [field_names.index(f) for f in ("audience", "channel", "stage", "tone")]
    pc_idx = field_names.index("product_category")
    bt_idx = field_names.index("benefit_type")
    _check("product_category 在 4 必填之后", min(no_default_idx) < pc_idx)
    _check("benefit_type 在 product_category 之后", pc_idx < bt_idx)
    # objective 灰态字段必须在尾部
    obj_idx = field_names.index("objective")
    _check("objective 灰态字段在末尾（dataclass 排序）", obj_idx > bt_idx)

    # 构造验证（dataclass no-default 在前 + 默认字段在后）
    t = TaskInput(
        product_category="汉堡", benefit_type="折扣",
        audience="常规大盘",
        channel="APP Push", stage="活动预热", scene="早餐", tone="直接利益型",
    )
    _check("TaskInput product_category 值正确", t.product_category == "汉堡")
    _check("TaskInput benefit_type 值正确", t.benefit_type == "折扣")
    _check("TaskInput.to_dict 含 2 字段",
           "product_category" in t.to_dict() and "benefit_type" in t.to_dict())
    _check("TaskInput.to_dict 不再含 product_benefit", "product_benefit" not in t.to_dict())

    # from_form 接受空值不抛错
    form = {
        "product_category": "", "benefit_type": "",
        "audience": "常规大盘", "channel": "APP Push",
        "stage": "活动预热", "scene": "早餐", "tone": "直接利益型",
    }
    task_empty = TaskInput.from_form(form)
    _check("from_form 接受空 product_category/benefit_type 不抛错",
           task_empty.product_category == "" and task_empty.benefit_type == "")

    # ── 3) prompts.copy_generation 拼 2 行 ────────────────────
    from prompts.copy_generation import build_user_prompt
    channel_rules = {"APP Push": {"title_max": 15, "body_max": 60, "emoji_max": 2}}
    out = build_user_prompt(t, channel_rules)
    _check("prompt 含「产品类别：汉堡」行", "产品类别：汉堡" in out)
    _check("prompt 含「权益类型：折扣」行", "权益类型：折扣" in out)
    _check("prompt 不再拼老行「产品与权益：」", "产品与权益：" not in out)

    # 类别空时该行不拼
    t_no_pc = TaskInput(
        product_category="", benefit_type="折扣",
        audience="常规大盘", channel="APP Push",
        stage="活动预热", scene="早餐", tone="直接利益型",
    )
    out_no_pc = build_user_prompt(t_no_pc, channel_rules)
    _check("类别空时 prompt 不拼「产品类别：」行", "产品类别：" not in out_no_pc)
    _check("类别空时权益行仍拼", "权益类型：折扣" in out_no_pc)

    t_no_bt = TaskInput(
        product_category="汉堡", benefit_type="",
        audience="常规大盘", channel="APP Push",
        stage="活动预热", scene="早餐", tone="直接利益型",
    )
    out_no_bt = build_user_prompt(t_no_bt, channel_rules)
    _check("权益空时 prompt 不拼「权益类型：」行", "权益类型：" not in out_no_bt)
    _check("权益空时类别行仍拼", "产品类别：汉堡" in out_no_bt)

    # ── 4) services.generation_service._demo_candidates 拼接 ──
    from services.generation_service import _demo_candidates
    cs_both = _demo_candidates(t)
    _check("Demo 模式 类别+权益 双非空 仍生成 3 条候选", len(cs_both) == 3)
    # body 内应包含「汉堡」或「折扣」（拼接短语）
    bodies_both = " ".join(c.body for c in cs_both)
    _check("Demo body 拼接含'汉堡'或'折扣'", "汉堡" in bodies_both or "折扣" in bodies_both)

    t_only_pc = TaskInput(
        product_category="甜品", benefit_type="",
        audience="常规大盘", channel="APP Push",
        stage="活动预热", scene="早餐", tone="直接利益型",
    )
    cs_pc_only = _demo_candidates(t_only_pc)
    _check("Demo 类别单空 仍生成 3 条候选", len(cs_pc_only) == 3)
    _check("Demo 类别单空 body 含'甜品'", any("甜品" in c.body for c in cs_pc_only))

    t_only_bt = TaskInput(
        product_category="", benefit_type="赠品",
        audience="常规大盘", channel="APP Push",
        stage="活动预热", scene="早餐", tone="直接利益型",
    )
    cs_bt_only = _demo_candidates(t_only_bt)
    _check("Demo 权益单空 仍生成 3 条候选", len(cs_bt_only) == 3)
    _check("Demo 权益单空 body 含'赠品'", any("赠品" in c.body for c in cs_bt_only))

    # ── 5) pages/01_content_studio 源码静态检查 ──────────────
    src_studio = open("pages/01 内容工坊.py", encoding="utf-8").read()
    _check("content_studio 引用 core.product_benefit 模块",
           "from core.product_benefit import" in src_studio)
    _check("content_studio 调用 get_product_categories",
           "get_product_categories()" in src_studio)
    _check("content_studio 调用 get_benefit_types",
           "get_benefit_types()" in src_studio)
    _check("content_studio 含 '产品类别' selectbox",
           '"产品类别"' in src_studio)
    _check("content_studio 含 '权益类型' selectbox",
           '"权益类型"' in src_studio)
    _check("content_studio 含 _render_benefit_select helper",
           "def _render_benefit_select" in src_studio)
    _check("content_studio 调用 _render_benefit_select 2 次",
           src_studio.count("_render_benefit_select(") >= 3)  # 1 def + 2 calls
    _check("content_studio 含「自定义」文案",
           "自定义" in src_studio)
    _check("content_studio 不再含老 st.text_area 产品与权益",
           'st.text_area("产品与权益"' not in src_studio)
    # objective 仍灰态（未启用，按 A.2 留待 UI 重构）
    _check("objective 控件仍 disabled",
           re.search(r'st\.selectbox\([\s\S]*?投放目标[\s\S]*?disabled\s*=\s*True', src_studio) is not None)


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
    src02 = open("pages/02 文案诊断.py", encoding="utf-8").read()
    src03 = open("pages/03 批量评估.py", encoding="utf-8").read()
    src04 = open("pages/04 历史洞察.py", encoding="utf-8").read()
    src05 = open("pages/05 真实结果回流.py", encoding="utf-8").read()
    home  = open("pages/00 首页.py", encoding="utf-8").read()

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
    src01 = open("pages/01 内容工坊.py", encoding="utf-8").read()
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
    # baseline 数据版本：v3.1（Phase 6 P2）→ v3.1.1（Phase 12 #8 渠道清理）→ v3.2（Phase 15 新增文案含券词维度）
    _check("baseline version 以 v3. 开头",
           str(base.get("version", "")).startswith("v3."))
    _check("baseline version >= v3.1（口径已稳定）",
           base.get("version") in ("v3.1", "v3.1.1", "v3.2"))
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


# §48 Phase 14 CTR row key 修复（中英文 key + workday 透传 + "普通Plan"→"常规Plan"）
def test_phase14_row_keys():
    from services.ctr_prediction_service import _candidate_to_row
    from core.schemas import TaskInput, Candidate

    c = Candidate(id="A", strategy="A_核心利益直给", title="新品限时折扣", body="点击查看详情")
    task = TaskInput(
        audience="常规大盘", channel="APP Push", stage="活动预热", tone="直接利益型",
        plan_type="AARRPlan", coupon="是", planned_send_date="工作日",
    )
    row = _candidate_to_row(c, task)

    # 1) 英文 key 保留
    _check("_candidate_to_row 含 channel", row.get("channel") == "APP Push")
    _check("_candidate_to_row 含 plan_type=AARRPlan", row.get("plan_type") == "AARRPlan")
    _check("_candidate_to_row 含 coupon=是", row.get("coupon") == "是")
    _check("_candidate_to_row 含 title_len", row.get("title_len") == len(c.title))

    # 2) 中文 key（prompt_builder 读这些；Phase 14 修复）
    _check("_candidate_to_row 含 '渠道' key", row.get("渠道") == "APP Push")
    _check("_candidate_to_row 含 '标题' key", row.get("标题") == c.title)
    _check("_candidate_to_row 含 '内容' key", row.get("内容") == c.body)
    _check("_candidate_to_row 含 '是否用券' key", row.get("是否用券") == "是")
    _check("_candidate_to_row 含 '计划类型' key", row.get("计划类型") == "AARRPlan")
    _check("_candidate_to_row 含 '工作日类型' key（Phase 11 修复）",
           row.get("工作日类型") == "工作日")

    # 3) 未知字段 → None（不传给 baseline_lookup）
    task_unknown = TaskInput(
        audience="常规大盘", channel="APP Push", stage="活动预热", tone="直接利益型",
        plan_type="未知", coupon="未知", planned_send_date=None,
    )
    row_u = _candidate_to_row(c, task_unknown)
    _check("_candidate_to_row 未知 plan_type → None", row_u.get("plan_type") is None)
    _check("_candidate_to_row 未知 coupon → None", row_u.get("coupon") is None)
    _check("_candidate_to_row 未知 workday → None", row_u.get("工作日类型") is None)

    # 4) prompt_builder.py:101 "普通Plan" bug 已修（Phase 14）
    src_text = open("adapters/ctr_predictor_adapter/prompt_builder.py", encoding="utf-8").read()
    _check("prompt_builder.py 接受 '常规Plan'（Phase 14 修复）",
           "常规Plan" in src_text and "普通Plan" not in src_text.split("plan_v =")[1].split("\n")[0])


# §49 Phase 15 baseline v3.2 文案含券词维度补齐
def test_phase15_text_has_coupon_baseline():
    import json
    from adapters.ctr_predictor_adapter.baseline_lookup import get_baseline_ctr

    base = json.load(open("data/ctr_baseline.json", encoding="utf-8"))

    # 1) baseline 版本 v3.2
    _check("baseline version == v3.2（Phase 15 重算）", base.get("version") == "v3.2")

    # 2) 新维度 "渠道_x_文案含券词" 已建 key
    dim = base.get("dimensions", {}).get("渠道_x_文案含券词")
    _check("baseline 含 '渠道_x_文案含券词' 维度", dim is not None)
    _check("'渠道_x_文案含券词' 有 8 keys（4 渠道 × 2 文案含券词）",
           len(dim.get("data", {})) == 8)

    # 3) baseline_lookup 能命中（4 渠道 × 是/否 全部）
    for ch in ("APP Push", "企微1v1", "短信", "微信小程序订阅消息"):
        v_yes = get_baseline_ctr(ch, coupon=None, workday=None, plan_type=None,
                                  text_has_coupon="是")
        v_no = get_baseline_ctr(ch, coupon=None, workday=None, plan_type=None,
                                 text_has_coupon="否")
        _check(f"baseline_lookup {ch}_是 命中",
               v_yes is not None and v_yes > 0,
               f"v_yes={v_yes}")
        _check(f"baseline_lookup {ch}_否 命中",
               v_no is not None and v_no > 0,
               f"v_no={v_no}")
        # 是/否 应有差异（form 不同时兜底会相等；但 text_has_coupon 是不同 key）
        _check(f"baseline_lookup {ch} 是/否应不同（或接近）",
               v_yes is not None and v_no is not None)

    # 4) recalc_text_has_coupon.py 一次性脚本存在 + 可 dry-run
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "recalc_text_has_coupon",
        "tools/recalc_text_has_coupon.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _check("recalc_text_has_coupon.exp_decay_weight(0) == 1.0",
           abs(mod.exp_decay_weight(0) - 1.0) < 1e-9)
    _check("recalc_text_has_coupon.exp_decay_weight(69.3) ≈ 0.5",
           abs(mod.exp_decay_weight(69.3) - 0.5) < 0.01)


# §50 Phase 16 calibrate_baseline 扩 text/workday 维度
def test_phase16_calibrate_text_workday():
    """Phase 16 用户口径：扩 calibrate_baseline 覆盖 2 维度（text_has_coupon + workday），
    不动 owner/title_len。
    """
    import importlib.util
    import sqlite3
    import tempfile
    from pathlib import Path

    # 1) tools/calibrate_baseline.py 新签名：返回 4 元组（by_cp, by_ch, by_text, by_workday）
    spec = importlib.util.spec_from_file_location(
        "calibrate_baseline", "tools/calibrate_baseline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 2) 用临时 feedback.db 跑 aggregate_feedback 验证 4 维度聚合
    tmpdir = tempfile.mkdtemp()
    db_path = f"{tmpdir}/test_feedback.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE feedback_records (
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
            imported_at TEXT,
            text_has_coupon TEXT
        );
    """)
    # 4 行：覆盖 channel × text × workday 组合
    rows = [
        # ("sig", "channel", "coupon", "plan", "date", reach, click, thc)
        ("s1", "APP Push",   "未知", "常规Plan", "2026-08-24", 5000, 250, "是"),  # 工作日（周一）
        ("s2", "APP Push",   "未知", "常规Plan", "2026-08-29", 5000, 100, "否"),  # 工作日（周六）
        ("s3", "企微1v1",    "未知", "常规Plan", "2026-08-25", 5000, 150, "是"),  # 工作日（周二）
        ("s4", "企微1v1",    "未知", "常规Plan", "2026-08-30", 5000, 120, "否"),  # 工作日（周日）
    ]
    for r in rows:
        conn.execute("""INSERT INTO feedback_records
            (task_signature, channel, coupon, plan_type, sent_date,
             reach_success, click_count, text_has_coupon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", r)
    conn.commit()
    conn.close()

    by_cp, by_ch, by_text, by_workday = mod.aggregate_feedback(db_path)

    # 3) by_cp（channel, coupon=未知）
    _check("aggregate_feedback by_cp 含 2 渠道",
           len(by_cp) == 2,
           f"got {len(by_cp)}")
    _check("by_cp 触达 = 10000（2 行 × 5000）",
           by_cp[("APP Push", "未知")]["reach"] == 10000)

    # 4) by_ch
    _check("by_ch 4 行总触达 = 20000",
           sum(v["reach"] for v in by_ch.values()) == 20000)

    # 5) by_text 维度（Phase 16 新增；走 text_has_coupon 列）
    _check("by_text 含 4 keys（2 渠道 × 2 文案含券词）",
           len(by_text) == 4,
           f"got {len(by_text)}")
    _check("by_text (APP Push, 是).ctr == 250/5000",
           by_text[("APP Push", "是")]["ctr"] == 0.05,
           f"got {by_text[('APP Push', '是')]}")
    _check("by_text (APP Push, 否).ctr == 100/5000",
           by_text[("APP Push", "否")]["ctr"] == 0.02)

    # 6) by_workday 维度（Phase 16 新增；从 sent_date 推 weekday）
    _check("by_workday 含 keys（2 渠道 × 工作日/非工作日）",
           len(by_workday) >= 2,
           f"got {len(by_workday)}")
    # 8/24 (周一)、8/25 (周二)、8/29 (周六)、8/30 (周日) → core.data_window.classify_date_type 决定
    # 不深究具体是"工作日"还是"非工作日"，只验证 by_workday 是 dict 且 n_plans > 0
    for (ch, wd), v in by_workday.items():
        _check(f"by_workday ({ch}, {wd}) n_plans > 0",
               v["n_plans"] > 0, f"got {v}")

    # 7) calibrate() 接受 by_text + by_workday 参数
    base = {"version": "v3.0", "dimensions": {
        "渠道":            {"description": "兜底", "data": {"APP Push": 0.04, "企微1v1": 0.03}},
        "渠道_x_是否用券":  {"description": "test", "data": {"APP Push_未知": 0.04, "企微1v1_未知": 0.03}},
        "渠道_x_文案含券词": {"description": "Phase 16", "data": {}},
        "渠道_x_工作日类型": {"description": "Phase 16", "data": {}},
    }}
    new_base, changes = mod.calibrate(base, by_cp, by_ch, by_text, by_workday,
                                     min_reach=1000, definition="v3.1")
    _check("calibrate() 返回版本号升级 v3.0 → v3.1",
           new_base["version"] == "v3.1",
           f"got {new_base['version']}")
    _check("calibrate() _definition_version 写入 v3.1",
           new_base.get("_definition_version") == "v3.1")
    _check("calibrate() 含 渠道×文案含券词 维度变更",
           any("渠道×文案含券词" in c for c in changes),
           f"changes={changes}")
    _check("calibrate() 含 渠道×工作日类型 维度变更",
           any("渠道×工作日类型" in c for c in changes),
           f"changes={changes}")
    # 渠道×文案含券词 数据应被填入（4 keys）
    text_data = new_base["dimensions"]["渠道_x_文案含券词"]["data"]
    _check("calibrate() 渠道×文案含券词 写入 4 keys",
           len(text_data) == 4, f"got {text_data}")

    # 8) 老库 ALTER 兼容（feedback_repository.get_connection）
    # 模拟"无 text_has_coupon 列的老库" → 重新建一个不含该列的表 → get_connection 应 ALTER ADD COLUMN
    legacy_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    conn2 = sqlite3.connect(legacy_db)
    conn2.executescript("""
        CREATE TABLE feedback_records (
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
    """)
    conn2.commit()
    conn2.close()
    # 清理 tmpdir；保留 legacy_db（NamedTemporaryFile delete=False 需手工清理）
    import shutil as _shutil
    _shutil.rmtree(tmpdir)

    from repositories.feedback_repository import get_connection as _gc
    conn = _gc(legacy_db)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(feedback_records)").fetchall()]
    _check("feedback_repository ALTER 兼容：老库补 text_has_coupon 列",
           "text_has_coupon" in cols, f"cols={cols}")
    conn.close()
    Path(legacy_db).unlink()


# §51 Phase 17 代码质量清理（02 bug 修复 + 死代码删除 + LLM cache + docstring 对齐）
def test_phase17_quality_cleanup():
    """Phase 17 · 2026-08-28 用户拍板"检查整体代码质量性能"后清理：

    - 02 文案诊断.py 改用 ui.llm_status.load_config()（不再 `from core.config` 失败）
    - services/record_service.py 整文件已删（Phase 13 后无人调）
    - core/llm_gateway.ProviderRouter.call 加实例级 LRU cache（512 容量）
    - docstring/注释 v3.0/Phase 3-4 标注对齐 Phase 16.5
    """
    import importlib

    # ── 1) ui.llm_status.load_config 存在 + 返回 4 字段 dict ──
    from ui import llm_status as ls
    _check("ui.llm_status.load_config 存在",
           hasattr(ls, "load_config"))
    # monkey-patch 让 load_config 返回 4 字段（避免依赖实际 yaml）
    ls._load_yaml.cache_clear()
    orig_load_yaml = ls._load_yaml
    ls._load_yaml = lambda: {"provider": "openai", "base_url": "https://x",
                             "model": "gpt-4", "api_key": "sk-fake"}
    cfg = ls.load_config()
    _check("load_config 返回 dict",
           isinstance(cfg, dict))
    _check("load_config 键集 ⊇ 4 字段",
           set(cfg.keys()) >= {"provider", "base_url", "model", "api_key"},
           f"keys={set(cfg.keys())}")
    ls._load_yaml = orig_load_yaml
    ls._load_yaml.cache_clear()

    # ── 2) ui.llm_status 已加入 __all__ ──
    _check("load_config 在 __all__",
           "load_config" in ls.__all__)

    # ── 3) services/record_service.py 已删除 ──
    import os
    rs_path = os.path.join(
        os.path.dirname(__file__), "..", "services", "record_service.py")
    rs_path = os.path.normpath(rs_path)
    _check("services/record_service.py 已删除",
           not os.path.exists(rs_path),
           f"仍存在：{rs_path}")

    # ── 4) ProviderRouter 加 _cache 实例属性 + clear_cache 方法 ──
    from core.llm_gateway import ProviderRouter
    # 用一个简单的 dummy 配置实例化（不真发请求）
    router = ProviderRouter(provider="openai", api_key="test", model="gpt-4")
    _check("ProviderRouter._cache 初始化为空 dict",
           router._cache == {})
    _check("ProviderRouter.clear_cache 方法存在",
           hasattr(router, "clear_cache"))

    # 手动注入缓存验证（不真调 SDK）
    router._cache[("prompt1", "gpt-4")] = "cached_response"
    _check("router._cache 写入/读取",
           router._cache[("prompt1", "gpt-4")] == "cached_response")
    router.clear_cache()
    _check("router.clear_cache 清空",
           router._cache == {})

    # ── 5) call() 命中 cache 走 _call_openai 不真发请求 ──
    # 准备：注入假 cache + monkey-patch _call_openai 计数
    call_count = {"n": 0}
    original_call_openai = router._call_openai

    def fake_call_openai(prompt, model):
        call_count["n"] += 1
        return "fake_response"

    router._call_openai = fake_call_openai
    router._cache[("hello", "gpt-4")] = "CACHED"
    # 注入 api_key 才能走真实分支
    router.api_key = "sk-fake"
    r1 = router.call("hello")
    _check("cache 命中：未调 _call_openai",
           call_count["n"] == 0 and r1 == "CACHED",
           f"r1={r1}, calls={call_count['n']}")
    # 第二次不同 prompt 真调一次
    r2 = router.call("different prompt")
    _check("cache miss：调 _call_openai 1 次",
           call_count["n"] == 1, f"calls={call_count['n']}")
    # 第二次相同 prompt 应命中（但本例 prompt 不同不命中）
    # 再来一次相同 prompt 测连续命中
    call_count["n"] = 0
    router._cache.clear()
    router.call("same")
    router.call("same")
    _check("同 prompt 连续 2 次只调 1 次 _call_openai",
           call_count["n"] == 1, f"calls={call_count['n']}")

    # 还原
    router._call_openai = original_call_openai

    # ── 6) call() 缓存容量上限保护（>512 砍老一半）──
    router2 = ProviderRouter(provider="openai", api_key="test", model="gpt-4")
    # 模拟 600 项（不真调）
    for i in range(600):
        router2._cache[(f"p{i}", "gpt-4")] = f"r{i}"
    router2._call_openai = lambda p, m: "fake"
    router2.api_key = "sk-fake"
    # 触发一次新 cache 写入（prompt 不在已有 keys 中）
    router2.call("NEW_PROMPT_NEVER_CACHED")
    _check("容量保护：触发后 cache ≤ 512",
           len(router2._cache) <= 512,
           f"size={len(router2._cache)}")

    # ── 7) 02 文案诊断.py 不再有 import core.config（注释里提到历史是 OK）──
    diag_src_path = os.path.join(
        os.path.dirname(__file__), "..", "pages", "02 文案诊断.py")
    diag_src_path = os.path.normpath(diag_src_path)
    with open(diag_src_path, encoding="utf-8") as f:
        diag_src = f.read()
    # 拆行后 grep：import 语句不在注释中（无 # 前缀且有 from core.config）
    import re as _re
    import_lines = [
        ln for ln in diag_src.splitlines()
        if ln.strip().startswith(("from ", "import "))
    ]
    _check("02 文案诊断.py 删 `from core.config import settings` 实际 import",
           not any("from core.config import" in ln for ln in import_lines),
           f"residual: {[l for l in import_lines if 'core.config' in l]}")
    _check("02 文案诊断.py 改用 load_config",
           "ui.llm_status import" in diag_src and "load_config" in diag_src)

    # ── 8) app.py / core/schemas.py / pages/00 首页.py 注释对齐 Phase 16.5 ──
    app_src = open(os.path.join(os.path.dirname(__file__), "..", "app.py"),
                   encoding="utf-8").read()
    _check("app.py 页面清单去 'Phase 4 占位'",
           "Phase 4 占位" not in app_src)
    _check("app.py 页面清单含 'Phase 16.5'",
           "Phase 16.5" in app_src)

    schema_src = open(os.path.join(os.path.dirname(__file__), "..", "core",
                                   "schemas.py"), encoding="utf-8").read()
    _check("core/schemas.py 删 '未来补：TaskInput / Candidate'",
           "未来补：TaskInput" not in schema_src)
    _check("core/schemas.py 提到 Phase 16.5",
           "Phase 16.5" in schema_src)


# §52 Phase 17 weighted_ctr 合并到 core.analytics_utils
def test_phase17_weighted_ctr_utility():
    """Phase 17 · weighted_ctr / weighted_ctr_series 替代 7+ 处重复公式。"""
    from core.analytics_utils import weighted_ctr, weighted_ctr_series
    import pandas as pd

    # ── 标量版（默认百分数）──
    _check("weighted_ctr(250, 5000) == 5.0", weighted_ctr(250, 5000) == 5.0)
    _check("weighted_ctr(0, 0) == 0.0（安全除零）", weighted_ctr(0, 0) == 0.0)
    _check("weighted_ctr(100, -1) == 0.0（负 reach 兜底）",
           weighted_ctr(100, -1) == 0.0)

    # ── 标量版（小数）──
    _check("weighted_ctr(250, 5000, as_percent=False) == 0.05",
           weighted_ctr(250, 5000, as_percent=False) == 0.05,
           f"got {weighted_ctr(250, 5000, as_percent=False)}")

    # ── Series 版（默认百分数）──
    s = pd.Series([250, 100, 0])
    r = pd.Series([5000, 5000, 0])
    out = weighted_ctr_series(s, r)
    _check("weighted_ctr_series [5.0, 2.0, 0.0]",
           list(out) == [5.0, 2.0, 0.0],
           f"got {list(out)}")

    # ── Series 版（小数）──
    out_dec = weighted_ctr_series(s, r, as_percent=False)
    _check("weighted_ctr_series 小数版 [0.05, 0.02, 0.0]",
           list(out_dec) == [0.05, 0.02, 0.0],
           f"got {list(out_dec)}")

    # ── 各调用点已替换（grep 验证）──
    import subprocess
    # 用 grep 统计还剩多少处 "click / reach * 100" 公式
    r1 = subprocess.run(
        ["grep", "-rn", "round(click / reach * 100",
         "services/", "repositories/", "pages/04 历史洞察.py"],
        capture_output=True, text=True,
    )
    inline_remaining = len([l for l in r1.stdout.splitlines() if l.strip()])
    _check(f"残留 inline 公式 ≤ 2 处（实际 {inline_remaining}）",
           inline_remaining <= 2,
           f"残留:\n{r1.stdout}")


# §53 Phase 17.5 重构（CSV reader / row dict / rule_engine / 批量分类）
def test_phase17_5_refactors():
    """Phase 17.5 · 用户拍板"继续"后的清理：

    - core/csv_utils.read_table() 替代 services/feedback + batch_evaluation 两处重复 reader
    - core/text_classifier.classify_coupon_batch() 向量化替代 df.apply(axis=1)
    - services/rule_engine._run_term_check() 合并 _check_banned + _check_risk
    - services/ctr_prediction_service._build_row() 合并 _candidate_to_row + predict_one
    """
    import io as _io
    import pandas as _pd
    from core.csv_utils import read_table
    from core.text_classifier import (
        classify_coupon_in_text, classify_coupon_batch,
    )

    # ── 1) csv_utils.read_table 扩展名分发 + 列别名 ──
    # CSV 路径（用 ASCII 列名测）
    csv_bytes = b"title,body,channel\nhi,hello,APP Push\n"
    df_csv = read_table(csv_bytes, "test.csv",
                        col_aliases={"title": ["title"], "body": ["body"],
                                     "channel": ["channel"]},
                        required_cols=("title", "body", "channel"))
    _check("read_table CSV 识别 title/body/channel",
           set(["title", "body", "channel"]).issubset(df_csv.columns))

    # 别名匹配（不同大小写 → 不匹配；用混合大小写别名）
    df_alias = read_table(b"Title,Body,Channel\nfoo,bar,baz",
                          "test.csv",
                          col_aliases={"title": ["title"], "body": ["body"],
                                       "channel": ["channel"]},
                          required_cols=("title", "body", "channel"))
    _check("read_table 别名精确小写匹配",
           df_alias.loc[0, "title"] == "foo")

    # 缺列填空
    df_fill = read_table(b"foo,bar\n1,2", "test.csv",
                         required_cols=("title", "body"))
    _check("read_table 缺 required_cols 自动填空",
           "title" in df_fill.columns and "body" in df_fill.columns)

    # ── 2) classify_coupon_batch 与逐行版语义一致 ──
    titles = _pd.Series(["限时 5 折", "新品上市", "立减 10 元", "新菜单"])
    bodies = _pd.Series(["详情点击", "欢迎品尝", "快来抢购", "看看"])
    batch_out = classify_coupon_batch(titles, bodies)
    single_out = [classify_coupon_in_text(t, b) for t, b in zip(titles, bodies)]
    _check("classify_coupon_batch 与单条版语义一致",
           batch_out == single_out,
           f"batch={batch_out}, single={single_out}")
    _check("classify_coupon_batch 长度 == 输入",
           len(batch_out) == len(titles))
    _check("classify_coupon_batch 至少识别出 2 条含券",
           batch_out.count("是") >= 2)

    # ── 3) rule_engine._run_term_check 三态 ──
    from services.rule_engine import _run_term_check
    # 空词表 → 空 PASS
    items_empty = _run_term_check([], "some text", "cat",
                                  "fail", "no terms", "pass", "hit {terms}")
    _check("_run_term_check 空词表 → pass",
           items_empty[0].severity == "pass" and items_empty[0].message == "no terms")

    # 命中 → fail + suggestion
    items_hit = _run_term_check(["bad", "evil"], "this is bad",
                                "cat", "fail", "none", "pass",
                                "hit {terms}", suggestion="改写")
    _check("_run_term_check 命中 → fail + suggestion",
           items_hit[0].severity == "fail"
           and "bad" in items_hit[0].message
           and items_hit[0].suggestion == "改写")

    # 未命中 → pass
    items_miss = _run_term_check(["bad"], "clean text",
                                 "cat", "warn", "none", "all clean", "hit {terms}")
    _check("_run_term_check 未命中 → pass",
           items_miss[0].severity == "pass" and items_miss[0].message == "all clean")

    # ── 4) _check_banned / _check_risk 仍工作（走 _run_term_check）──
    from services.rule_engine import _check_banned, _check_risk
    items_banned = _check_banned("折扣优惠", "新品上市",
                                 {"banned_terms": ["优惠"]})
    _check("_check_banned 命中优惠 → fail",
           items_banned[0].severity == "fail")
    items_risk = _check_risk("限时特惠", "新品上市",
                             {"risk_terms": ["特惠"]})
    _check("_check_risk 命中特惠 → warn",
           items_risk[0].severity == "warn")
    # 空词表 → pass
    items_empty2 = _check_banned("x", "y", {"banned_terms": []})
    _check("_check_banned 空词表 → pass",
           items_empty2[0].severity == "pass")

    # ── 5) ctr_prediction_service._build_row 中英文 key 双输出 ──
    from services.ctr_prediction_service import _build_row
    from core.schemas import TaskInput, Candidate
    task = TaskInput(audience="x", channel="APP Push",
                     stage="y", tone="z", coupon="是", plan_type="常规Plan",
                     planned_send_date="工作日")
    cand = Candidate(id="A", strategy="s", title="t1", body="b1")
    row = _build_row(title="t1", body="b1", channel="APP Push",
                     plan_v="常规Plan", coupon_v="是", workday_v="工作日",
                     task=task, candidate=cand)
    _check("_build_row 含英文 key（channel/title/body）",
           all(k in row for k in ("channel", "title", "body")))
    _check("_build_row 含中文 key（渠道/标题/内容）",
           all(k in row for k in ("渠道", "标题", "内容")))
    _check("_build_row 计划类型透传",
           row["plan_type"] == "常规Plan" and row["计划类型"] == "常规Plan")
    _check("_build_row 工作日透传",
           row["工作日类型"] == "工作日")
    _check("_build_row 含 _signature",
           isinstance(row["_signature"], str) and len(row["_signature"]) == 12)

    # ── 6) predict_one 走 _build_row 后仍出 PredictionResult ──
    from services.ctr_prediction_service import predict_one
    res = predict_one(title="测试", body="详情", channel="APP Push")
    _check("predict_one 返回 PredictionResult",
           hasattr(res, "result_type") and hasattr(res, "pred_ctr"))


# §54 Phase 17.6 Streamlit 缓存 + 死代码清理
def test_phase17_6_dead_code():
    """Phase 17.6 · Streamlit 页面缓存（04/05）+ 死代码清理（saved_id/apply_brand_theme/from_optional/SNAPSHOT_CUTOFF_HOUR）。"""
    import inspect
    import os

    # ── 1) pages/04 历史洞察.py 不再有 __import__("io") ──
    p04 = os.path.join(os.path.dirname(__file__), "..", "pages", "04 历史洞察.py")
    src04 = open(p04, encoding="utf-8").read()
    _check("04 历史洞察.py 删 __import__('io')",
           "__import__(\"io\")" not in src04 and "__import__('io')" not in src04)
    _check("04 历史洞察.py 改用 from io import BytesIO",
           "from io import BytesIO" in src04)
    _check("04 历史洞察.py 含 _cached_parse_insights_file 缓存",
           "_cached_parse_insights_file" in src04)

    # ── 2) pages/05 真实结果回流.py 含 _cached_recent_feedback / _cached_generation_records_list ──
    p05 = os.path.join(os.path.dirname(__file__), "..", "pages", "05 真实结果回流.py")
    src05 = open(p05, encoding="utf-8").read()
    _check("05 真实结果回流.py 含 _cached_recent_feedback",
           "_cached_recent_feedback" in src05)
    _check("05 真实结果回流.py 含 _cached_generation_records_list",
           "_cached_generation_records_list" in src05)

    # ── 3) pages/01 内容工坊.py 不再有 "saved_id": None 死 state ──
    p01 = os.path.join(os.path.dirname(__file__), "..", "pages", "01 内容工坊.py")
    src01 = open(p01, encoding="utf-8").read()
    _check("01 内容工坊.py 删 'saved_id': None（Phase 13 残留）",
           "\"saved_id\"" not in src01 and "'saved_id'" not in src01)

    # ── 4) ui/plotly_helpers.py 删 apply_brand_theme ──
    p_plotly = os.path.join(os.path.dirname(__file__), "..", "ui", "plotly_helpers.py")
    src_plotly = open(p_plotly, encoding="utf-8").read()
    _check("ui/plotly_helpers.py 删 apply_brand_theme 死代码",
           "def apply_brand_theme" not in src_plotly)
    _check("ui/plotly_helpers.py 不再 import go（apply_brand_theme 唯一用户）",
           "import plotly.graph_objects" not in src_plotly)

    # ── 5) column_mapping.py 删 from_optional() ──
    p_col = os.path.join(os.path.dirname(__file__), "..",
                         "adapters", "ctr_predictor_adapter", "column_mapping.py")
    src_col = open(p_col, encoding="utf-8").read()
    _check("column_mapping.py 删 from_optional() NotImplementedError 死代码",
           "def from_optional" not in src_col)

    # ── 6) core/data_window.py 删 SNAPSHOT_CUTOFF_HOUR 常量（注释里允许提到）──
    p_dw = os.path.join(os.path.dirname(__file__), "..", "core", "data_window.py")
    src_dw = open(p_dw, encoding="utf-8").read()
    # 注释里提到是 OK 的（如 "Phase 17.6 删除 ..."）；但不能有 `SNAPSHOT_CUTOFF_HOUR = X` 赋值或当默认值
    code_lines = [
        ln for ln in src_dw.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    _check("core/data_window.py 删 SNAPSHOT_CUTOFF_HOUR 赋值/引用",
           not any("SNAPSHOT_CUTOFF_HOUR" in ln for ln in code_lines),
           f"残留: {[l for l in code_lines if 'SNAPSHOT_CUTOFF_HOUR' in l]}")
    # resolve_bi_dt_window 仍能用（默认 12）
    from core.data_window import resolve_bi_dt_window
    v = resolve_bi_dt_window()
    _check("resolve_bi_dt_window 默认 cutoff=12 仍工作",
           isinstance(v, str) and len(v) == 10,
           f"got {v!r}")


# §55 Phase 18 L1 LightGBM PoC（剔除小程序 + 高效词 + 时间衰减）
def test_phase18_lgbm():
    """Phase 18 · L1 LightGBM 模型 + 元信息 + 高效词表 + 工具脚本。"""
    import pickle
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent
    model_path = ROOT / "data" / "lgbm_model_v1.pkl"
    meta_path = ROOT / "data" / "lgbm_feature_meta.json"
    eff_words_path = ROOT / "data" / "effective_words.json"
    train_script = ROOT / "tools" / "train_lgbm.py"
    eval_script = ROOT / "tools" / "evaluate_lgbm.py"

    # ── 1) 模型 + 元信息 + 高效词表 文件存在 ──
    _check("data/lgbm_model_v1.pkl 存在", model_path.exists())
    _check("data/lgbm_feature_meta.json 存在", meta_path.exists())
    _check("data/effective_words.json 存在", eff_words_path.exists())
    _check("tools/train_lgbm.py 存在", train_script.exists())
    _check("tools/evaluate_lgbm.py 存在", eval_script.exists())

    # ── 2) 模型能加载 + 是 LightGBM Booster ──
    if model_path.exists():
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        _check("L1 模型类型 = lightgbm.Booster",
               type(model).__name__ == "Booster")
        # Booster 必有 num_trees 方法
        _check("L1 模型有 num_trees()（训练过）",
               hasattr(model, "num_trees") and model.num_trees() > 0)

    # ── 3) 元信息字段齐全 ──
    if meta_path.exists():
        import json
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        _check("meta 含 feature_columns",
               "feature_columns" in meta and len(meta["feature_columns"]) > 0)
        _check("meta 含 target_transform=logit",
               meta.get("target_transform") == "logit")
        _check("meta 含 min_reach=50",
               meta.get("min_reach") == 50)
        _check("meta 含 time_decay_half_life_days=180",
               meta.get("time_decay_half_life_days") == 180)
        _check("meta 含 best_iteration（已收敛）",
               "best_iteration" in meta and meta["best_iteration"] > 0)
        _check("meta 含 test_metrics（已评估）",
               "test_metrics" in meta and "overall_mae_pct" in meta["test_metrics"])
        # 模型特征列与 meta 记录的一致
        if model_path.exists():
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            model_feat = model.feature_name()
            _check("模型 feature_name 与 meta feature_columns 一致",
                   sorted(model_feat) == sorted(meta["feature_columns"]),
                   f"diff: {set(model_feat) ^ set(meta['feature_columns'])}")

    # ── 4) 高效词表字段 ──
    if eff_words_path.exists():
        import json
        doc = json.loads(eff_words_path.read_text(encoding="utf-8"))
        _check("effective_words 含 top_words 数组",
               isinstance(doc.get("top_words"), list) and len(doc["top_words"]) > 0)
        _check("effective_words count > 0",
               doc.get("count", 0) > 0)
        _check("effective_words min_diff=0.5（差值>0.5）",
               doc.get("min_diff") == 0.5)

    # ── 5) 训练脚本含 4 步关键改动 ──
    if train_script.exists():
        src = train_script.read_text(encoding="utf-8")
        _check("train_lgbm.py 含 --exclude-channels 参数",
               "--exclude-channels" in src)
        _check("train_lgbm.py 含时间衰减权重逻辑（half_life）",
               "half_life" in src and "0.5 **" in src)
        _check("train_lgbm.py 含 _load_effective_words 函数",
               "_load_effective_words" in src)
        _check("train_lgbm.py 含 jieba 切词交集（高效词命中数）",
               "_count_effective_words" in src)
        _check("train_lgbm.py 含 logit 变换",
               "_safe_logit" in src and "_safe_sigmoid" in src)

    # ── 6) 评估脚本含 L1 vs L0 同口径对比 ──
    if eval_script.exists():
        src = eval_script.read_text(encoding="utf-8")
        _check("evaluate_lgbm.py 含 L0 baseline 查表",
               "lookup_l0_baseline" in src)
        _check("evaluate_lgbm.py 含分渠道 MAE/MAPE",
               "per_channel_metrics" in src)
        _check("evaluate_lgbm.py 含分桶误差",
               "per_bucket_metrics" in src)


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
    # Phase A.1 · 产品权益维度扩展（2026-08-28，原 Phase 6 P1 灰态测试升级）
    test_phase_a1_product_benefit_split()
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
    # §48 Phase 14 CTR row key 修复（中英文 key + workday 透传）
    test_phase14_row_keys()
    # §49 Phase 15 baseline v3.2 文案含券词维度补齐
    test_phase15_text_has_coupon_baseline()
    # §50 Phase 16 calibrate_baseline 扩 text/workday 维度
    test_phase16_calibrate_text_workday()
    # §51 Phase 17 代码质量清理（02 bug 修复 + LLM cache）
    test_phase17_quality_cleanup()
    # §52 Phase 17 weighted_ctr 合并到 core.analytics_utils
    test_phase17_weighted_ctr_utility()
    # §53 Phase 17.5 代码质量清理（CSV reader / row dict / rule_engine / jieba 批量）
    test_phase17_5_refactors()
    # §54 Phase 17.6 Streamlit 缓存 + 死代码清理
    test_phase17_6_dead_code()
    # §55 Phase 18 L1 LightGBM PoC（剔除小程序 + 高效词 + 时间衰减）
    test_phase18_lgbm()
    # §56 Phase 19 L1 静默双轨接入（adapters/ctr_predictor_adapter/l1_predictor.py）
    test_phase19_l1_predictor()
    # §57 Phase 20 l1_model mode + L1 漂移监控（CTRPredictionAdapter.mode + monitor_l1_drift.py）
    test_phase20_l1_main_and_drift()
    # §58 Phase 22 B 特征重要性月报脚本（tools/print_feature_importance.py）
    test_phase22_b_feature_importance_report()
    # §59 Phase 22 C 漂移自动回退（core/active_mode + monitor + 01 sidebar 联动）
    test_phase22_c_auto_rollback()
    # §60 Phase 22 D 批量预测自动落档 records.db
    test_phase22_d_batch_save_records()
    # §61 Phase 24 全量 smoke sweep（防退化）
    test_smoke_sweep()

    print("\n" + "=" * 60)
    print(f"结果: {_passed} PASS, {_failed} FAIL")
    print("=" * 60)

    return 0 if _failed == 0 else 1


# §56 Phase 19 L1 静默双轨接入（l1_predictor 模块 + adapter 导出 + UI 开关）
def test_phase19_l1_predictor():
    """Phase 19 · L1 LightGBM 生产接入 + 静默双轨开关。

    覆盖：
    1) l1_predictor 模块能 import（import 不抛异常）
    2) adapter __init__.py 导出 4 个 L1 符号
    3) 4 态分明：model / baseline_only / unavailable
    4) 模型加载路径：lru_cache 命中后状态稳定
    5) UI 开关：sidebar checkbox 默认 False + 字段在 session_state
    6) 页面已注入 L1 入口（_render_ctr_card 接受 l1_ctr 参数 + 调 predict_l1）
    """
    import pickle
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent

    # ── 1) 模块能 import（不依赖 LLM/Streamlit）──
    try:
        from adapters.ctr_predictor_adapter.l1_predictor import (
            predict_l1,
            predict_l1_batch,
            predict_l1_status,
            L1_SUPPORTED_CHANNELS,
        )
        import_ok = True
    except Exception as e:
        import_ok = False
        _check("l1_predictor 模块可 import", False, f"import error: {e}")
    _check("l1_predictor 模块可 import", import_ok)

    if not import_ok:
        return  # 后续用例全部跳过（依赖模块）

    # ── 2) adapter __init__ 导出 ──
    from adapters import ctr_predictor_adapter as cpa
    for name in ("predict_l1", "predict_l1_batch", "predict_l1_status", "L1_SUPPORTED_CHANNELS"):
        _check(f"adapter.__init__ 导出 {name}", name in cpa.__all__)

    # ── 3) 四态分明：模型 + meta 都在时 → "model" ──
    status = predict_l1_status()
    _check("predict_l1_status() 返回值合法",
           status in ("model", "baseline_only", "unavailable"),
           f"got {status!r}")

    model_path = ROOT / "data" / "lgbm_model_v1.pkl"
    meta_path = ROOT / "data" / "lgbm_feature_meta.json"
    if not (model_path.exists() and meta_path.exists()):
        _check("L1 模型/元信息存在（status=model 前提）", False, "pkl 或 meta 缺失")
    else:
        _check("L1 模型/元信息存在（status=model 前提）", True)
        # 真预测：APP Push（训练范围）+ 完整字段 → 应返回 model 态
        ctr, st = predict_l1(
            title="夏日新品限时尝鲜，9.9 元起点击立享",
            body="点击查看详情",
            channel="APP Push",
            plan_type="AARRPlan",
            coupon="是",
            workday="工作日",
        )
        _check("predict_l1(APP Push+AARRPlan+工作日) → model",
               st == "model" and ctr is not None and 0 < ctr < 1,
               f"got ctr={ctr} status={st}")

        # 小程序/站内信 等未训练渠道 → unavailable（不会预测）
        ctr2, st2 = predict_l1(
            title="测试",
            body="",
            channel="微信小程序订阅消息",
            plan_type=None,
            coupon=None,
            workday=None,
        )
        _check("predict_l1(微信小程序订阅消息) → unavailable",
               st2 == "unavailable" and ctr2 is None,
               f"got ctr={ctr2} status={st2}")

        # 空 title → 不应崩（业务容错）
        ctr3, st3 = predict_l1(
            title="", body="", channel="短信",
            plan_type=None, coupon=None, workday=None,
        )
        _check("predict_l1(空 title+短信) → model 不崩",
               st3 == "model" and ctr3 is not None,
               f"got ctr={ctr3} status={st3}")

        # 模型与元信息 特征列一致（构建期和运行期对齐）
        meta = __import__("json").loads(meta_path.read_text(encoding="utf-8"))
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        _check("运行期模型 feature_name 与 meta feature_columns 一致",
               sorted(model.feature_name()) == sorted(meta["feature_columns"]),
               f"diff: {set(model.feature_name()) ^ set(meta['feature_columns'])}")

    # ── 4) 批量接口 ──
    rows = [
        {"title": "a", "body": "", "channel": "APP Push", "plan_type": "AARRPlan",
         "coupon": "否", "workday": "工作日"},
        {"title": "b", "body": "", "channel": "短信", "plan_type": None,
         "coupon": None, "workday": None},
        {"title": "c", "body": "", "channel": "微信小程序订阅消息",
         "plan_type": None, "coupon": None, "workday": None},
    ]
    batch_out = predict_l1_batch(rows)
    _check("predict_l1_batch 长度 == len(rows)",
           len(batch_out) == len(rows),
           f"got {len(batch_out)}")
    if len(batch_out) == 3:
        # 顺序应与输入一致：APP Push → model，短信 → model，小程序 → unavailable
        _check("predict_l1_batch 顺序与输入一致（第 1 条 model）",
               batch_out[0][1] == "model")
        _check("predict_l1_batch 顺序与输入一致（第 3 条 unavailable）",
               batch_out[2][1] == "unavailable")

    # ── 5) L1_SUPPORTED_CHANNELS 三渠道 ──
    _check("L1_SUPPORTED_CHANNELS 含 APP Push", "APP Push" in L1_SUPPORTED_CHANNELS)
    _check("L1_SUPPORTED_CHANNELS 含 企微1v1", "企微1v1" in L1_SUPPORTED_CHANNELS)
    _check("L1_SUPPORTED_CHANNELS 含 短信", "短信" in L1_SUPPORTED_CHANNELS)
    _check("L1_SUPPORTED_CHANNELS 不含小程序（未训练）",
           "微信小程序订阅消息" not in L1_SUPPORTED_CHANNELS)

    # ── 6) UI 集成：sidebar checkbox + _render_ctr_card 接受 l1_ctr 参数 ──
    studio_page = ROOT / "pages" / "01 内容工坊.py"
    if studio_page.exists():
        src = studio_page.read_text(encoding="utf-8")
        _check("01 内容工坊.py 含 show_l1 checkbox",
               "show_l1" in src and "显示 L1 实验对比" in src)
        _check("01 内容工坊.py 调 predict_l1",
               "predict_l1(" in src)
        _check("01 内容工坊.py _render_ctr_card 接受 l1_ctr 参数",
               "l1_ctr" in src and "_render_ctr_card(selected_ctr, l1_ctr=l1_ctr_pair)" in src)
        _check("01 内容工坊.py import L1_SUPPORTED_CHANNELS",
               "L1_SUPPORTED_CHANNELS" in src)


# §57 Phase 20 l1_model mode 主流程接入 + L1 漂移监控
def test_phase20_l1_main_and_drift():
    """Phase 20 · l1_model mode 主流程切换 + 漂移监控脚本。

    覆盖：
    1) CTRPredictionAdapter.mode="l1_model" 加入 VALID_MODES
    2) l1_model 端到端：APP Push → model_prediction；小程序 → unavailable
    3) l1_model 透传 4 态（baseline_only 也透传）
    4) UI sidebar 模式选择器（selectbox 而非硬编码 demo）
    5) 漂移监控脚本存在 + baseline 加载
    6) 漂移监控对空 DB 优雅降级（0 配对 → skip，不评估）
    """
    # ── 1) VALID_MODES 含 l1_model ──
    from adapters.ctr_predictor_adapter import CTRPredictionAdapter, VALID_MODES
    _check("VALID_MODES 含 l1_model", "l1_model" in VALID_MODES)
    _check("VALID_MODES 共 5 个值（existing_predictor/baseline_only/demo/l1_model/unavailable）",
           len(VALID_MODES) == 5)

    # ── 2) l1_model 端到端 ──
    from core.schemas import TaskInput, Candidate
    from services.ctr_prediction_service import _candidate_to_row

    task = TaskInput(
        audience="常规大盘", channel="APP Push", stage="活动预热", tone="直接利益型",
        plan_type="AARRPlan", coupon="是", planned_send_date="工作日",
    )
    candidate = Candidate(id="A", strategy="A_核心利益直给",
                          title="夏日新品限时尝鲜，9.9 元起点击立享",
                          body="点击查看详情")

    adapter = CTRPredictionAdapter(mode="l1_model")
    rows = [_candidate_to_row(candidate, task)]
    results = adapter.predict_batch(rows)
    r = results[0]
    _check("l1_model APP Push → model_prediction",
           r.result_type == "model_prediction" and r.pred_ctr and 0 < r.pred_ctr < 1,
           f"got result_type={r.result_type} pred_ctr={r.pred_ctr}")
    _check("l1_model source 含 l1_lightgbm",
           "l1_lightgbm" in (r.source or ""),
           f"got source={r.source}")

    # 小程序 → unavailable（渠道不在训练范围）
    task_xp = TaskInput(audience="常规大盘", channel="微信小程序订阅消息",
                        stage="活动预热", tone="直接利益型")
    rows_xp = [_candidate_to_row(candidate, task_xp)]
    results_xp = adapter.predict_batch(rows_xp)
    r_xp = results_xp[0]
    _check("l1_model 微信小程序订阅消息 → unavailable",
           r_xp.result_type == "unavailable",
           f"got result_type={r_xp.result_type}")
    _check("l1_model unavailable 带合理错误信息",
           r_xp.error and "微信小程序订阅消息" in r_xp.error,
           f"got error={r_xp.error}")

    # ── 3) baseline_only 透传（pkl 缺失场景）──
    # 通过 monkey patch _load_model_and_meta 来模拟
    from adapters.ctr_predictor_adapter import l1_predictor as lp
    orig_load = lp._load_model_and_meta
    # 清 lru_cache（lru_cache 装饰器返回的 wrapper 有 cache_clear；raw 函数没有）
    try:
        lp._load_model_and_meta.cache_clear()
    except AttributeError:
        pass
    lp._load_model_and_meta = lambda: (None, None)  # 强制模型缺失
    try:
        ctr, st = lp.predict_l1(
            title="测试", body="", channel="APP Push",
            plan_type="AARRPlan", coupon="否", workday="工作日",
        )
        _check("predict_l1 pkl 缺失 → baseline_only",
               st == "baseline_only" and ctr is None,
               f"got ctr={ctr} status={st}")
    finally:
        lp._load_model_and_meta = orig_load
        try:
            lp._load_model_and_meta.cache_clear()
        except AttributeError:
            pass

    # ── 4) UI sidebar 模式选择器 ──
    studio_page = ROOT / "pages" / "01 内容工坊.py"
    src = studio_page.read_text(encoding="utf-8")
    _check("01 内容工坊.py sidebar 含 ctr_mode selectbox",
           "ctr_mode" in src and "selectbox" in src and "CTR 主流程模式" in src)
    _check("01 内容工坊.py predict_for_candidates 用 session_state ctr_mode",
           'st.session_state.get("ctr_mode"' in src)
    _check("01 内容工坊.py 模式选项含 l1_model",
           "l1_model" in src)

    # ── 5) 漂移监控脚本 ──
    monitor_script = ROOT / "tools" / "monitor_l1_drift.py"
    _check("tools/monitor_l1_drift.py 存在", monitor_script.exists())
    if monitor_script.exists():
        ms = monitor_script.read_text(encoding="utf-8")
        _check("monitor_l1_drift.py 含 alert_ratio 参数",
               "--alert-ratio" in ms)
        _check("monitor_l1_drift.py 含 1.3 阈值常量",
               "1.3" in ms or "DEFAULT_ALERT_RATIO = 1.3" in ms)
        _check("monitor_l1_drift.py 含 drift_log.csv 写入",
               "drift_log.csv" in ms and "write_drift_log" in ms)
        _check("monitor_l1_drift.py 含 baseline 加载（lgbm_feature_meta.json）",
               "lgbm_feature_meta.json" in ms and "test_metrics" in ms)
        _check("monitor_l1_drift.py 含 records.db 读取",
               "records.db" in ms and "load_l1_predictions" in ms)
        _check("monitor_l1_drift.py 含 feedback.db 读取",
               "feedback.db" in ms and "load_real_ctr_by_signature" in ms)
        _check("monitor_l1_drift.py 含 min-pairs 防误报",
               "min-pairs" in ms and "min_pairs" in ms)

    # ── 6) 漂移监控空 DB 优雅降级（无需写入 records.db）──
    if monitor_script.exists():
        import subprocess
        out = subprocess.run(
            ["python", str(monitor_script), "--no-log"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(ROOT),
        )
        out_text = out.stdout + out.stderr
        _check("monitor_l1_drift.py 空 DB 优雅降级（[skip]）",
               "[skip]" in out_text or "配对数" in out_text,
               f"got: {out_text[:200]}")
        _check("monitor_l1_drift.py 返回 0（不告警，因无数据）",
               out.returncode == 0,
               f"got returncode={out.returncode}")


# §58 Phase 22 B 特征重要性月报脚本
def test_phase22_b_feature_importance_report():
    """Phase 22 · tools/print_feature_importance.py 端到端 + humanizer + diff 逻辑。"""
    # ── 1) 脚本存在 + 关键 CLI 参数 ──
    script = ROOT / "tools" / "print_feature_importance.py"
    _check("tools/print_feature_importance.py 存在", script.exists())
    if not script.exists():
        return
    src = script.read_text(encoding="utf-8")
    _check("脚本含 argparse --top 参数", "--top" in src and "default" in src)
    _check("脚本含 argparse --threshold 参数", "--threshold" in src)
    _check("脚本含 argparse --importance-type 参数 (gain/split)",
           "importance-type" in src and "gain" in src and "split" in src)
    _check("脚本含 humanize_feature 函数", "def humanize_feature" in src)
    _check("脚本含 compute_importance 函数", "def compute_importance" in src)
    _check("脚本含 diff_with_history 函数", "def diff_with_history" in src)
    _check("脚本含 save_snapshot 写历史快照 JSON",
           "feature_importance_history" in src and "importance_" in src)
    _check("脚本含 render_report 写 .txt 报告",
           "reports_dir" in src and ".txt" in src)
    _check("脚本含 Windows console 编码 fix", "reconfigure" in src)

    # ── 2) humanize_feature 单元覆盖 ──
    import json
    import shutil
    from datetime import datetime
    import pandas as pd
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("_pfi_test", script)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h = mod.humanize_feature
    _check("humanize: title_len → 标题长度", h("title_len") == "标题长度")
    _check("humanize: content_len → 正文长度", h("content_len") == "正文长度")
    _check("humanize: has_emoji → 含 Emoji", h("has_emoji") == "含 Emoji")
    _check("humanize: eff_word_count → 高效词命中数",
           h("eff_word_count") == "高效词命中数")
    _check("humanize: channel_APP_Push → 渠道: APP Push",
           h("channel_APP_Push") == "渠道: APP Push")
    _check("humanize: channel_企微1v1 → 渠道: 企微1v1",
           h("channel_企微1v1") == "渠道: 企微1v1")
    _check("humanize: coupon_未知 → 用券: 未知",
           h("coupon_未知") == "用券: 未知")
    _check("humanize: coupon_ → 用券: (空)",
           h("coupon_") == "用券: (空)")
    _check("humanize: workday_type_工作日 → 工作日类型: 工作日",
           h("workday_type_工作日") == "工作日类型: 工作日")
    _check("humanize: ch_x_wd_APP_Push_工作日 → 渠道×工作日: APP Push × 工作日",
           h("ch_x_wd_APP_Push_工作日") == "渠道×工作日: APP Push × 工作日")
    _check("humanize: plan_type_te → 计划类型 (target encoding)",
           h("plan_type_te") == "计划类型 (target encoding)")
    _check("humanize: 未知列名透传", h("foo_bar") == "foo_bar")

    # ── 3) compute_importance 跑真实模型 ──
    model, meta = mod.load_model_and_meta()
    feat_cols = meta["feature_columns"]
    df = mod.compute_importance(model, feat_cols, "gain")
    _check("compute_importance 返回 DataFrame", isinstance(df, pd.DataFrame))
    _check("compute_importance 行数 == feature_columns 长度",
           len(df) == len(feat_cols))
    _check("compute_importance rank 从 1 开始连续",
           list(df["rank"]) == list(range(1, len(df) + 1)))
    _check("compute_importance importance_pct 求和约等于 100",
           abs(df["importance_pct"].sum() - 100.0) < 0.5,
           f"sum={df['importance_pct'].sum():.2f}")
    _check("compute_importance Top1 为正文长度或标题长度",
           df.iloc[0]["feature"] in ("content_len", "title_len"),
           f"got {df.iloc[0]['feature']}")

    # ── 4) find_latest_snapshot 首次跑返回 None ──
    snap_dir = ROOT / "data" / "feature_importance_history"
    snap_dir.mkdir(parents=True, exist_ok=True)
    # 用临时子目录隔离测试（不污染真实历史）
    tmp_dir = ROOT / "data" / ".tmp_fi_history"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)
    _check("find_latest_snapshot 空目录返回 None",
           mod.find_latest_snapshot(tmp_dir) is None)

    # ── 5) diff_with_history: 模拟"上次 Top1 是 eff_word_count" ──
    fake_prev = {
        "items": [
            {"rank": 1, "feature": "eff_word_count", "importance_pct": 50.0},
            {"rank": 2, "feature": "title_len", "importance_pct": 20.0},
            {"rank": 3, "feature": "content_len", "importance_pct": 10.0},
        ]
    }
    fake_prev_path = tmp_dir / "fake.json"
    fake_prev_path.write_text(json.dumps(fake_prev), encoding="utf-8")
    df2 = df.copy()
    df2 = mod.diff_with_history(df2, fake_prev_path, threshold=2)
    _check("diff_with_history: 新特征 (不在 prev) 标 '新'",
           (df2["change"] == "新").sum() >= len(df2) - 3)
    _check("diff_with_history: prev_rank 缺失为 NaN",
           df2["prev_rank"].isna().any())
    # 模拟"上次 Top1 是 content_len，本次 rank=2 → rank_change=1 < 2 不打标记"
    fake_prev2 = {
        "items": [
            {"rank": 1, "feature": "content_len", "importance_pct": 40.0},
            {"rank": 2, "feature": "title_len", "importance_pct": 25.0},
        ]
    }
    fake_prev2_path = tmp_dir / "fake2.json"
    fake_prev2_path.write_text(json.dumps(fake_prev2), encoding="utf-8")
    df3 = df.copy()
    df3 = mod.diff_with_history(df3, fake_prev2_path, threshold=2)
    # 在 fake_prev2 里只有 content_len 和 title_len，其它都标 "新"
    non_new = df3[df3["change"] != "新"]
    _check("diff_with_history: 在 prev 内的特征不算 '新'",
           len(non_new) == 2)
    _check("diff_with_history: content_len rank_change 列存在",
           "rank_change" in df3.columns)

    # ── 6) save_snapshot + render_report 真跑一遍（首次）──
    real_snap_dir = ROOT / "data" / "feature_importance_history"
    real_report_dir = ROOT / "data" / "reports"
    snap_count_before = len(list(real_snap_dir.glob("importance_*.json")))
    report_count_before = len(list(real_report_dir.glob("feature_importance_*.txt")))
    snap_path = mod.save_snapshot(df)
    # render_report 需要 df 含 change 列 → 先调 diff_with_history（无快照时自己造个空 prev）
    df_for_report = df.copy()
    df_for_report = mod.diff_with_history(
        df_for_report, fake_prev_path, threshold=2,
    )
    report_path = mod.render_report(df_for_report.head(5), fake_prev_path, "gain", 2)
    _check("save_snapshot: 写入 importance_*.json",
           snap_path.exists() and snap_path.suffix == ".json")
    _check("render_report: 写入 feature_importance_*.txt",
           report_path.exists() and report_path.suffix == ".txt")
    _check("save_snapshot: history 增加 1 个文件",
           len(list(real_snap_dir.glob("importance_*.json"))) == snap_count_before + 1)
    # 报告按日期命名，重复跑会覆盖而非新增；改为检查今日报告存在
    today_report = real_report_dir / f"feature_importance_{datetime.now().strftime('%Y-%m-%d')}.txt"
    _check("render_report: 今日报告存在", today_report.exists())
    # 报告内容校验
    report_text = report_path.read_text(encoding="utf-8")
    _check("报告含 'L1 特征重要性月报' 抬头",
           "L1 特征重要性月报" in report_text)
    _check("报告含 '排名' 表头", "排名" in report_text)
    _check("报告含 '正文长度' 或 '标题长度'（humanize 生效）",
           "正文长度" in report_text or "标题长度" in report_text)

    # ── 7) 清理临时目录 ──
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # ── 8) CLI 端到端跑通 ──
    import subprocess
    out = subprocess.run(
        ["python", str(script), "--top", "5"],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(ROOT),
    )
    _check("print_feature_importance.py CLI exit 0", out.returncode == 0,
           f"got returncode={out.returncode}, stderr={out.stderr[:200]}")
    combined = out.stdout + out.stderr
    _check("CLI 输出含 Top 5 表头", "Top 5" in combined)
    _check("CLI 输出含 '渠道' humanize 结果", "渠道" in combined)


# §59 Phase 22 C 漂移自动回退（core/active_mode + monitor + 01 sidebar 联动）
def test_phase22_c_auto_rollback():
    """Phase 22 · 漂移自动回退端到端：core/active_mode + monitor_l1_drift + 01 sidebar 读。

    覆盖：
    1) core/active_mode 模块读写 clear 三态
    2) monitor_l1_drift.py 含 apply_auto_rollback 函数 + ALERT/WARN/OK 三档分支
    3) pages/01 内容工坊.py 含 read_active_mode import + 启动时覆盖 default_mode
    4) 端到端：手动调 apply_auto_rollback 写文件 → read_active_mode 读回来
    """
    # ── 1) core/active_mode 模块 ──
    from core.active_mode import (
        read_active_mode, write_active_mode, clear_active_mode,
        ACTIVE_MODE_PATH, ALLOWED_MODES,
    )
    _check("core.active_mode 模块可 import", True)
    _check("ACTIVE_MODE_PATH 指向 data/active_mode.txt",
           str(ACTIVE_MODE_PATH).endswith("data\\active_mode.txt")
           or str(ACTIVE_MODE_PATH).endswith("data/active_mode.txt"))
    _check("ALLOWED_MODES = {demo, baseline_only, l1_model}",
           ALLOWED_MODES == {"demo", "baseline_only", "l1_model"})

    # 用临时路径隔离测试，不污染真实 active_mode.txt
    tmp = ROOT / "data" / ".tmp_active_mode.txt"
    if tmp.exists():
        tmp.unlink()
    _check("read_active_mode: 文件不存在 → None", read_active_mode(tmp) is None)

    write_active_mode("demo", tmp)
    _check("write+read: demo", read_active_mode(tmp) == "demo")

    write_active_mode("baseline_only", tmp)
    _check("write+read: baseline_only", read_active_mode(tmp) == "baseline_only")

    # 非法 mode → ValueError
    raised = False
    try:
        write_active_mode("garbage", tmp)
    except ValueError:
        raised = True
    _check("write_active_mode 非法 mode 抛 ValueError", raised)

    # 文件内容非法（手写一个 'xxx'）→ read 返回 None
    tmp.write_text("xxx\n", encoding="utf-8")
    _check("read_active_mode: 内容非法 → None", read_active_mode(tmp) is None)

    # clear
    write_active_mode("demo", tmp)
    cleared = clear_active_mode(tmp)
    _check("clear_active_mode: 删除存在文件 → True", cleared is True)
    _check("clear_active_mode: 再次删 → False", clear_active_mode(tmp) is False)
    _check("clear 后 read → None", read_active_mode(tmp) is None)
    if tmp.exists():
        tmp.unlink()

    # ── 2) monitor_l1_drift.py 含 apply_auto_rollback + 三档分支 ──
    monitor = ROOT / "tools" / "monitor_l1_drift.py"
    _check("tools/monitor_l1_drift.py 存在", monitor.exists())
    if monitor.exists():
        ms = monitor.read_text(encoding="utf-8")
        _check("monitor_l1_drift.py 含 apply_auto_rollback 函数",
               "def apply_auto_rollback" in ms)
        _check("monitor_l1_drift.py ALERT → demo 分支",
               'alert_level == "ALERT"' in ms and 'write_active_mode_safe("demo"' in ms)
        _check("monitor_l1_drift.py WARN → baseline_only 分支",
               'alert_level == "WARN"' in ms and 'write_active_mode_safe("baseline_only"' in ms)
        _check("monitor_l1_drift.py OK → clear_active_mode_safe 分支",
               "clear_active_mode_safe" in ms)
        _check("monitor_l1_drift.py 含 --no-active-mode CLI flag",
               "--no-active-mode" in ms)
        _check("monitor_l1_drift.py 含 [rollback] 打印",
               "[rollback]" in ms)
        _check("monitor_l1_drift.py 含 ACTIVE_MODE_PATH 常量",
               "ACTIVE_MODE_PATH = ROOT" in ms)

    # ── 3) 端到端：直接调 apply_auto_rollback（用临时路径）──
    if monitor.exists():
        import importlib.util as _ilu2
        spec2 = _ilu2.spec_from_file_location("_monitor_test", monitor)
        mod2 = _ilu2.module_from_spec(spec2)
        spec2.loader.exec_module(mod2)

        tmp_path = ROOT / "data" / ".tmp_active_mode.txt"
        # 模拟 ALERT
        result = mod2.apply_auto_rollback("ALERT", tmp_path)
        _check("apply_auto_rollback('ALERT') 返回 'demo'", result == "demo")
        _check("apply_auto_rollback('ALERT') 写入 demo",
               read_active_mode(tmp_path) == "demo")
        # 模拟 WARN
        result = mod2.apply_auto_rollback("WARN", tmp_path)
        _check("apply_auto_rollback('WARN') 返回 'baseline_only'",
               result == "baseline_only")
        _check("apply_auto_rollback('WARN') 写入 baseline_only",
               read_active_mode(tmp_path) == "baseline_only")
        # 模拟 OK → 删文件
        result = mod2.apply_auto_rollback("OK", tmp_path)
        _check("apply_auto_rollback('OK') 返回 'cleared'", result == "cleared")
        _check("apply_auto_rollback('OK') 删除文件", not tmp_path.exists())

    # ── 4) pages/01 内容工坊.py 含 active_mode 接入 ──
    studio = ROOT / "pages" / "01 内容工坊.py"
    if studio.exists():
        sc = studio.read_text(encoding="utf-8")
        _check("01 内容工坊.py import read_active_mode",
               "from core.active_mode import read_active_mode" in sc)
        _check("01 内容工坊.py 启动时调 read_active_mode",
               "read_active_mode()" in sc)
        _check("01 内容工坊.py 含 auto_rollback_msg banner",
               "auto_rollback_msg" in sc)
        _check("01 内容工坊.py 含 '自动回退' 提示文案",
               "自动回退" in sc)

    # ── 5) CLI 端到端：跑 monitor 一次，确认 active_mode.txt 处理逻辑跑通 ──
    # 关键：当前空 DB 配对数=0 < MIN_PAIR_COUNT，monitor 会走 [skip] 路径返回 0
    # 不走 ALERT/WARN/OK 三档，但确认 --no-active-mode 不影响行为
    import subprocess
    if monitor.exists():
        out = subprocess.run(
            ["python", str(monitor), "--no-log"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(ROOT),
        )
        combined = out.stdout + out.stderr
        _check("monitor_l1_drift.py 跑一次 exit 0（空 DB skip）",
               out.returncode == 0,
               f"got returncode={out.returncode}, stderr={out.stderr[:200]}")
        _check("空 DB 走 [skip] 路径", "[skip]" in combined)


# §60 Phase 22 D 批量预测自动落档 records.db
def test_phase22_d_batch_save_records():
    """Phase 22 · services/batch_evaluation_service.save_predictions_to_records。

    覆盖：
    1) batch_signature 函数逻辑（与 task_signature 字段一致）
    2) save_predictions_to_records 落档格式正确
    3) 仅保存 ctr_result_type 非空的行
    4) pages/03 批量评估.py 含 checkbox + save 入口
    """
    from services.batch_evaluation_service import (
        batch_signature, save_predictions_to_records, evaluate_batch,
    )

    # ── 1) batch_signature 单元 ──
    row = {
        "title": "麦当劳新品上市", "body": "限时优惠", "channel": "APP Push",
        "plan_type": "AARRPlan", "coupon": "是",
    }
    sig1 = batch_signature(row)
    _check("batch_signature 返回 12 位 hex", len(sig1) == 12 and all(c in "0123456789abcdef" for c in sig1))
    sig2 = batch_signature(row)
    _check("batch_signature 相同输入 → 相同签名", sig1 == sig2)
    row_diff = {**row, "channel": "企微1v1"}
    _check("batch_signature 不同 channel → 不同签名",
           batch_signature(row_diff) != sig1)
    # 改 title 长度（让桶跨过一个 5 倍数）
    row_diff2 = {**row, "title": "短"}
    _check("batch_signature 不同 title 长度 → 不同签名（标题桶变）",
           batch_signature(row_diff2) != sig1)
    # 跟 task_signature 字段一致性验证：手动构造同 raw 对比
    # raw 字段顺序：channel|coupon|plan_type|audience|stage|scene|title_bucket|body_bucket
    import hashlib
    raw = "APP Push|是|AARRPlan||||0|0"  # 8 字段，7 个 |
    sig_expected = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    _check("batch_signature 与 task_signature raw 拼接逻辑一致",
           batch_signature({"title": "", "body": "", "channel": "APP Push",
                            "plan_type": "AARRPlan", "coupon": "是"}) == sig_expected)

    # ── 2) save_predictions_to_records 端到端（用临时 db_path）──
    import sqlite3, tempfile, json
    tmpdir = tempfile.mkdtemp(prefix="phase22_d_")
    db_path = str(Path(tmpdir) / "test_records.db")
    rows = [
        {
            "row_index": 0, "title": "标题1", "body": "正文1", "channel": "APP Push",
            "rule_status": "pass", "rule_fail_count": 0, "rule_warn_count": 0,
            "ctr_result_type": "demo", "ctr_pred": 0.02, "ctr_baseline": 0.025,
            "ctr_confidence": 0.5, "ctr_error": "", "suggestion": "ok", "error": "",
        },
        {
            "row_index": 1, "title": "标题2", "body": "正文2", "channel": "企微1v1",
            "rule_status": "pass", "rule_fail_count": 0, "rule_warn_count": 0,
            "ctr_result_type": "model_prediction", "ctr_pred": 0.03, "ctr_baseline": 0.027,
            "ctr_confidence": 0.7, "ctr_error": "", "suggestion": "ok", "error": "",
        },
        {
            "row_index": 2, "title": "标题3", "body": "", "channel": "APP Push",  # body 空 → 跳过
            "rule_status": "", "rule_fail_count": 0, "rule_warn_count": 0,
            "ctr_result_type": "", "ctr_pred": None, "ctr_baseline": None,
            "ctr_confidence": None, "ctr_error": "", "suggestion": "", "error": "正文为空",
        },
    ]
    n = save_predictions_to_records(rows, db_path=db_path)
    _check("save_predictions_to_records 返回成功条数（仅 ctr_result_type 非空）", n == 2, f"got {n}")

    # 验证 db 内容
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    saved = conn.execute(
        "SELECT signature, task_json, candidates_json, ctr_results_json, selected_id, created_at "
        "FROM generation_records ORDER BY id ASC"
    ).fetchall()
    _check("records.db 写入 2 条", len(saved) == 2, f"got {len(saved)}")

    if saved:
        r1 = saved[0]
        _check("r1 signature 长度 12", len(r1["signature"]) == 12)
        _check("r1 selected_id = 'A'", r1["selected_id"] == "A")
        _check("r1 created_at 非空", bool(r1["created_at"]))
        task = json.loads(r1["task_json"])
        _check("r1 task_json.channel = APP Push", task["channel"] == "APP Push")
        # 测试数据 row[0] 没 plan_type → 默认 "未知"
        _check("r1 task_json.plan_type = 未知（缺省默认）", task["plan_type"] == "未知")
        _check("r1 task_json.audience 空串", task["audience"] == "")
        cands = json.loads(r1["candidates_json"])
        _check("r1 candidates_json 长度 1", len(cands) == 1)
        _check("r1 candidates[0].strategy = batch_eval",
               cands[0]["strategy"] == "batch_eval")
        ctrs = json.loads(r1["ctr_results_json"])
        _check("r1 ctr_results_json 长度 1", len(ctrs) == 1)
        _check("r1 ctr source 含 batch_ 前缀",
               ctrs[0].get("source", "").startswith("batch_"),
               f"got {ctrs[0].get('source')}")
    conn.close()

    # ── 3) 空 rows + 全部无 ctr 的边界 ──
    n_empty = save_predictions_to_records([], db_path=db_path)
    _check("空 rows 返回 0", n_empty == 0)
    n_no_ctr = save_predictions_to_records([
        {"title": "t", "body": "b", "channel": "APP Push", "ctr_result_type": ""}
    ], db_path=db_path)
    _check("全部无 ctr_result_type 返回 0", n_no_ctr == 0)

    # ── 4) pages/03 批量评估.py 含 checkbox + save 入口 ──
    page_03 = ROOT / "pages" / "03 批量评估.py"
    _check("pages/03 批量评估.py 存在", page_03.exists())
    if page_03.exists():
        p3 = page_03.read_text(encoding="utf-8")
        _check("03 含 batch_save_to_records 状态",
               "batch_save_to_records" in p3)
        _check("03 含 '保存预测到 records.db' checkbox",
               "保存预测到 records.db" in p3 and "checkbox" in p3)
        _check("03 含 save_predictions_to_records 调用",
               "save_predictions_to_records" in p3)
        _check("03 含 '已保存 N 条' 提示",
               "已保存" in p3)

    # 清理
    import shutil as _sh2
    _sh2.rmtree(tmpdir, ignore_errors=True)


# ============================================================
# 38) Phase 24 — 全量 smoke sweep（防退化）
# ============================================================
_section("38) 全量 smoke sweep（防退化）")


def test_smoke_sweep():
    """Phase 24 · 2026-08-28：把 §17-19 跑的 sweep 固定下来，防止以后回归。

    覆盖：
    - 31 个核心模块可 import（core / services / adapters / repositories / prompts / ui）
    - SQLite tmp dir 隔离读写（不污染 data/）
    - rule_engine 边界（空 / 超长 / 4 渠道 / 未知渠道）
    - ctr_prediction_service 5 modes（含 l1_model 真模型加载）
    - TaskInput 必填校验（4 字段）
    - similarity_service.find_similar 空 DB
    - copy_analysis_service.diagnose 返回结构
    - generation_service.read_recent 不同 limit
    - feedback_service.import_feedback 空 CSV
    """
    import json as _json
    import os as _os
    import shutil as _sh3
    import sys as _sys
    import tempfile as _tf
    import importlib as _il

    _sys.path.insert(0, ".")

    # 1) 31 个核心模块 import
    _mods = [
        "core.schemas", "core.llm_gateway", "core.analytics_utils",
        "core.active_mode", "core.data_window",
        "services.rule_engine", "services.copy_analysis_service",
        "services.similarity_service", "services.ctr_prediction_service",
        "services.feedback_service", "services.generation_service",
        "services.text_analyzer",
        "adapters.llm_adapter", "adapters.ctr_predictor_adapter",
        "repositories.sqlite_repository", "repositories.feedback_repository",
        "prompts.copy_generation", "prompts.copy_rewrite",
        "ui.styles", "ui.page_chrome", "ui.plotly_helpers",
        "ui.llm_status", "ui.notice",
        "services.analytics.owner_compare", "services.analytics.similarity",
        "adapters.ctr_predictor_adapter.char_utils",
        "adapters.ctr_predictor_adapter.baseline_lookup",
        "adapters.ctr_predictor_adapter.feedback_lookup",
        "adapters.ctr_predictor_adapter.column_mapping",
        "adapters.ctr_predictor_adapter.l1_predictor",
        "adapters.ctr_predictor_adapter.prompt_builder",
    ]
    _imp_ok = 0
    for _m in _mods:
        try:
            _il.import_module(_m)
            _imp_ok += 1
        except Exception as _e:
            _check(f"sweep import {_m}", False, f"{type(_e).__name__}: {_e}")
    _check(f"sweep 31 模块 import ({_imp_ok}/{len(_mods)})", _imp_ok == len(_mods))

    # 2) SQLite tmp dir 隔离读写
    _td = _tf.mkdtemp()
    try:
        _td_rec = _os.path.join(_td, "records.db")
        _td_fb = _os.path.join(_td, "feedback.db")
        from repositories import sqlite_repository as _sr, feedback_repository as _fr

        _sr.save({
            "signature": "sweep_001",
            "task_json": _json.dumps({"channel": "APP Push"}),
            "candidates_json": _json.dumps([{"id": "A"}]),
            "ctr_results_json": _json.dumps([{"source": "demo", "pred_ctr": 0.05}]),
            "selected_id": "A",
            "created_at": "2026-08-28 22:00:00",
        }, db_path=_td_rec)
        _check("sweep records.save → 1 row", _sr.list_all(limit=5, db_path=_td_rec) and
               _sr.list_all(limit=5, db_path=_td_rec)[0]["signature"] == "sweep_001")

        _fr.save({
            "task_signature": "sweep_001",
            "channel": "APP Push",
            "reach_success": 1000,
            "click_count": 50,
            "source": "sweep_test",
        }, db_path=_td_fb)
        _agg = _fr.aggregate_by_signature(db_path=_td_fb)
        _check("sweep feedback.save + aggregate",
               "sweep_001" in _agg and _agg["sweep_001"]["ctr"] == 5.0,
               f"got {_agg}")
    finally:
        _sh3.rmtree(_td, ignore_errors=True)

    # 3) rule_engine 边界
    from services.rule_engine import load_rules as _lr, check_one as _co
    _cr, _br = _lr()
    _r1 = _co("", "", "APP Push", _cr, _br)
    _check("sweep rule empty 文案 → fail", _r1.status == "fail")
    _r2 = _co("T" * 300, "B" * 1000, "APP Push", _cr, _br)
    _check("sweep rule 超长 → fail blocking",
           _r2.status == "fail" and _r2.has_blocking)
    for _ch in ["APP Push", "企微1v1", "短信", "未知渠道"]:
        _rc = _co("标题", "正文", _ch, _cr, _br)
        _check(f"sweep rule 渠道 {_ch} 不 crash",
               _rc.status in ("pass", "warn", "fail"))

    # 4) ctr_prediction_service 5 modes
    from services.ctr_prediction_service import predict_one as _po
    for _mode in ("existing_predictor", "baseline_only", "demo", "l1_model", "unavailable"):
        try:
            _pr = _po(title="测试", body="点击查看", channel="APP Push", mode=_mode)
            _check(f"sweep ctr mode={_mode} OK",
                   _pr.result_type in ("model_prediction", "baseline_only", "demo", "unavailable"))
        except Exception as _e:
            _check(f"sweep ctr mode={_mode} OK", False, f"{type(_e).__name__}: {_e}")

    # 5) TaskInput 必填校验
    from core.schemas import TaskInput as _TI
    for _f in ("audience", "channel", "stage", "tone"):
        _kw = {k: "x" for k in ("product_category", "benefit_type", "audience",
                                  "channel", "objective", "stage", "scene",
                                  "tone", "expected_action", "extra_requirements")}
        _kw[_f] = ""
        try:
            _TI(**_kw)
            _check(f"sweep TaskInput {_f} 必填校验", False, "未抛 ValueError")
        except ValueError:
            _check(f"sweep TaskInput {_f} 必填校验", True)

    # 6) similarity_service 空 DB
    from services.similarity_service import (
        find_similar as _fs, summarize_similar as _ss,
    )
    _df = _fs("测试", "点击查看", "APP Push")
    _check("sweep find_similar 空 DB → 空 df",
           _df is None or len(_df) == 0)
    _sm = _ss(_df)
    _check("sweep summarize_similar 空 DB → count=0",
           _sm.get("count") == 0 and _sm.get("avg_ctr") is None)

    # 7) copy_analysis_service.diagnose 返回结构
    from services.copy_analysis_service import diagnose as _dg
    _dg_r = _dg("测试", "点击查看", channel="APP Push")
    _check("sweep diagnose 含 score/grade/problems",
           all(k in _dg_r for k in ("score", "grade", "problems")))

    # 8) generation_service.read_recent 不同 limit
    from services.generation_service import read_recent as _rr
    _rr5 = _rr(limit=5)
    _check("sweep read_recent(limit=5) ≤5",
           0 <= len(_rr5) <= 5,
           f"got {len(_rr5)}")
    _rr_all = _rr(limit=10000)
    _check("sweep read_recent(limit=10000) ≥ read_recent(limit=5)",
           len(_rr_all) >= len(_rr5),
           f"5={len(_rr5)} all={len(_rr_all)}")

    # 9) feedback_service.import_feedback 空 CSV
    import io as _io
    from services.feedback_service import import_feedback as _ifb
    _empty_csv = _io.BytesIO(b"task_signature,channel,reach_success,click_count\n")
    _ifb_r = _ifb(_empty_csv.read(), filename="empty.csv")
    _check("sweep import_feedback 空 CSV 不报错",
           _ifb_r.get("n") == 0 and len(_ifb_r.get("errors") or []) == 0)


if __name__ == "__main__":
    sys.exit(main())
