# -*- coding: utf-8 -*-
r"""
core/llm_gateway.py — 统一 LLM 调用网关

CLAUDE.md §3 架构：模型调用统一通过本模块，adapters/ 不得直接 import openai/anthropic SDK。

Phase 1b 范围：
- ProviderRouter: 按 provider 协议分流（openai / anthropic）+ JSON 解析 + 错误降级
- lazy import SDK（避免 import 时强制装 SDK）
- 不依赖 .env 配置（由调用方注入），便于测试

Provider 白名单：
- OpenAI 协议: openai / siliconflow / qianfan
- Anthropic 协议: minimax

错误降级策略：
- SDK 未装 → 返回 {"_error": "请安装 xxx SDK"}
- API 异常 → 返回 {"_error": "API错误: ..."}
- JSON 解析失败 → 返回 {"_error": "JSON失败: ..."}
- 由 CTRPredictionAdapter 标 unavailable，不在 gateway 抛异常（greeting-flow）
"""

from __future__ import annotations
import json
import re
from typing import Optional


# ── Provider 协议分类 ──────────────────────────────────────────────────
ANTHROPIC_PROVIDERS = {"minimax"}
OPENAI_PROVIDERS = {"openai", "siliconflow", "qianfan"}
ALL_PROVIDERS = ANTHROPIC_PROVIDERS | OPENAI_PROVIDERS

# ── 各 provider 的 base_url ────────────────────────────────────────────
OPENAI_BASE_URLS = {
    "openai":      None,                       # 用 SDK 默认
    "siliconflow": "https://api.siliconflow.cn/v1",
    "qianfan":     "https://qianfan.baidubce.com/v2/coding",
}


class ProviderRouter:
    """统一 LLM 调用路由。

    用法：
        router = ProviderRouter(provider="siliconflow", api_key="xxx", model="yyy")
        raw = router.call(prompt)  # str
        rows = ProviderRouter.parse_json_response(raw, expected_count=10)
    """

    def __init__(
        self,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        if provider not in ALL_PROVIDERS:
            raise ValueError(
                f"provider must be one of {sorted(ALL_PROVIDERS)}, got {provider!r}"
            )
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Phase 17 加实例级 LRU cache：同 prompt + model 命中直接返回，省 API 成本
        # 容量 512；超出按 LRU 淘汰；测试需要重置时调 self.clear_cache()
        self._cache: dict = {}

    # ── 主入口 ─────────────────────────────────────────────────────────
    def call(self, prompt: str, model: Optional[str] = None) -> str:
        """调用 LLM，返回原始文本（不解析 JSON）。

        错误时返回带 _error 标记的 dict 字符串（容错设计，由调用方处理）。
        """
        model = model or self.model
        if not self.api_key:
            return json.dumps({"_error": "请先填写API Key"}, ensure_ascii=False)

        # Phase 17 LRU cache：key = (prompt, model)
        cache_key = (prompt, model)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.provider in ANTHROPIC_PROVIDERS:
            raw = self._call_anthropic(prompt, model)
        else:
            raw = self._call_openai(prompt, model)

        # 仅缓存成功响应（不带 _error 的）
        if '"_error"' not in raw:
            self._cache[cache_key] = raw
            # 容量保护（LRU 简化版：超过 512 砍最旧一半）
            if len(self._cache) > 512:
                # dict 保留插入顺序；pop 老 key
                for k in list(self._cache.keys())[:256]:
                    self._cache.pop(k, None)
        return raw

    def clear_cache(self) -> None:
        """清空缓存（测试用 / 配置改后刷新用）。"""
        self._cache.clear()

    # ── OpenAI 协议 ────────────────────────────────────────────────────
    def _call_openai(self, prompt: str, model: str) -> str:
        try:
            import openai  # lazy import
        except ImportError:
            return json.dumps({"_error": "请安装 openai: pip install openai"}, ensure_ascii=False)
        base_url = OPENAI_BASE_URLS.get(self.provider)
        try:
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=base_url,
                timeout=self.timeout,
            ) if base_url else openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return json.dumps({"_error": f"API错误: {str(e)[:50]}"}, ensure_ascii=False)

    # ── Anthropic 协议 ─────────────────────────────────────────────────
    def _call_anthropic(self, prompt: str, model: str) -> str:
        try:
            import anthropic  # lazy import
        except ImportError:
            return json.dumps({"_error": "请安装 anthropic: pip install anthropic"}, ensure_ascii=False)
        try:
            client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url="https://api.minimaxi.com/anthropic",
                timeout=self.timeout,
            )
            resp = client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            # 过滤 text block（跳过 thinking 块）
            text_parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
            return "\n".join(text_parts).strip()
        except Exception as e:
            return json.dumps({"_error": f"API错误: {str(e)[:50]}"}, ensure_ascii=False)

    # ── JSON 解析（两个协议共用） ───────────────────────────────────────
    @staticmethod
    def parse_json_response(raw: str, expected_count: int, default_suggestion: str = "解析异常") -> list:
        """从 LLM 原始响应解析 JSON 数组。

        兼容：
        - markdown ```json ... ``` 包裹
        - 多余前缀/后缀文字
        - 长度不匹配（截断或补空）
        - 顶层 dict（非数组，自动包成 list）
        - 解析失败：返回全部 [{pred_ctr: None, confidence: None, suggestion: "JSON失败: ..."}]

        返回：list[dict]，长度 == expected_count
        """
        if not raw:
            return [_empty_row(f"空响应")] * expected_count

        # 解析为 dict（错误降级标记）
        try:
            d = json.loads(raw)
        except Exception:
            d = None
        if isinstance(d, dict) and "_error" in d:
            return [_empty_row(d["_error"])] * expected_count

        # 去 markdown 包裹
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        m = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(0)

        try:
            results = json.loads(cleaned)
            if not isinstance(results, list):
                results = [results]
            # 长度对齐
            if len(results) != expected_count:
                results = (results + [{}] * expected_count)[:expected_count]
            # 字段补全
            for r in results:
                r.setdefault("pred_ctr", None)
                r.setdefault("confidence", None)
                r.setdefault("suggestion", default_suggestion)
            return results
        except json.JSONDecodeError as e:
            return [_empty_row(f"JSON失败: {str(e)[:50]}")] * expected_count


def _empty_row(error: str) -> dict:
    return {"pred_ctr": None, "confidence": None, "suggestion": error}