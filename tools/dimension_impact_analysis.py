# -*- coding: utf-8 -*-
r"""
tools/dimension_impact_analysis.py — 维度对 CTR 影响度分析（2026-08-31 · 补回丢失分析）

目的：
  之前 session 跑过维度影响分析但没写 Handoff → 这次必须落档。
  数据：CNN历史备份0830.xlsx（48,930 行 × 17 列）
  目标：哪些维度对 CTR 影响程度大（η² = SS_between / SS_total）

约束（CLAUDE.md §4 / Handoff-lessons.md 第 9 条）：
  - 80/20 train/test split（如果时间允许，加时间切分），防数据泄漏
  - 输出落 data/findings/（新建目录），不放 tmpdir
  - Handoff.md §6.5 加历史发现索引
  - json + md 双落档（机器读 + 人读）

影响度（eta 平方 η²）：
  0.01 = 小效应
  0.06 = 中效应
  0.14 = 大效应
"""
from __future__ import annotations

import ast
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Windows console UTF-8 (CLAUDE.md §4)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ============== 路径 / 常量 ==============
SRC_XLSX = Path(r"C:\Users\a952462\常用文件\数据\CNN历史备份0830.xlsx")
PROJECT_DIR = Path(r"C:\ideon\mcd-ai-content-platform")
FINDINGS_DIR = PROJECT_DIR / "data" / "findings"
FINDINGS_DIR.mkdir(parents=True, exist_ok=True)

DATE_TAG = datetime.now().strftime("%Y-%m-%d_%H%M%S")
JSON_OUT = FINDINGS_DIR / f"dimension_impact_{DATE_TAG}.json"
MD_OUT = FINDINGS_DIR / f"dimension_impact_{DATE_TAG}.md"

RANDOM_SEED = 42
TEST_RATIO = 0.2

# ============== 复用 日报清洗_new.py 的 parse_message ==============
# 解析第 17 列（消息内容）JSON 格式，提取真正的标题 + 内容
def _clean_text(value):
    if value is None or pd.isna(value):
        return ""
    s = str(value).strip()
    if not s:
        return ""
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _load_json_safely(raw):
    """日报清洗_new.py:load_json_safely 的等价实现（多层 fallback 解析 JSON）。"""
    if raw is None or pd.isna(raw):
        return None
    if isinstance(raw, dict):
        return raw
    s = str(raw).strip()
    if not s:
        return None
    candidates = [s]
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        candidates.append(s[1:-1])
    candidates.append(s.replace('""', '"'))
    candidates.append(s.replace('\\"', '"'))
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        inner = s[1:-1]
        candidates.append(inner.replace('""', '"'))
        candidates.append(inner.replace('\\"', '"'))
    unique = []
    seen = set()
    for item in candidates:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    for item in unique:
        try:
            result = json.loads(item)
            if isinstance(result, str):
                try:
                    r2 = json.loads(result)
                    if isinstance(r2, dict):
                        return r2
                except Exception:
                    pass
            if isinstance(result, dict):
                return result
        except Exception:
            pass
    for item in unique:
        try:
            r = ast.literal_eval(item)
            if isinstance(r, dict):
                return r
        except Exception:
            pass
    return None


def _regex_extract_json_value(raw, key):
    if raw is None or pd.isna(raw):
        return ""
    s = str(raw)
    pattern = rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"'
    m = re.search(pattern, s, flags=re.S)
    if not m:
        return ""
    v = m.group(1)
    try:
        v = json.loads(f'"{v}"')
    except Exception:
        v = v.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
    return _clean_text(v)


def _extract_title_from_forms(forms):
    if not isinstance(forms, list):
        return ""
    for item in forms:
        if isinstance(item, dict) and item.get("code") == "thing1" and item.get("value"):
            return _clean_text(item["value"])
    for item in forms:
        if isinstance(item, dict):
            code = str(item.get("code", ""))
            value = item.get("value")
            if code.startswith("thing") and value:
                return _clean_text(value)
    for item in forms:
        if isinstance(item, dict):
            code = str(item.get("code", ""))
            value = item.get("value")
            if not code.startswith("time") and value:
                return _clean_text(value)
    return ""


def _extract_text_from_forms(forms):
    if not isinstance(forms, list):
        return ""
    for item in forms:
        if isinstance(item, dict):
            code = str(item.get("code", ""))
            value = item.get("value")
            if code in ("thing5", "short_thing5") and value:
                return _clean_text(value)
    for item in forms:
        if isinstance(item, dict):
            code = str(item.get("code", ""))
            value = item.get("value")
            if code.startswith("thing") and code != "thing1" and value:
                return _clean_text(value)
    return ""


def _extract_title_from_attachments(data):
    attachments = data.get("attachments")
    if not isinstance(attachments, list):
        return ""
    for att in attachments:
        if isinstance(att, dict) and att.get("name"):
            return _clean_text(att["name"])
    return ""


def parse_message(raw, backup_title=""):
    """日报清洗_new.py:parse_message 等价实现。返回 Series('标题', '内容')。"""
    title = ""
    content = ""
    data = _load_json_safely(raw)
    if isinstance(data, dict):
        if data.get("title"):
            title = _clean_text(data["title"])
        if data.get("text"):
            content = _clean_text(data["text"])
        if not title:
            att_title = _extract_title_from_attachments(data)
            if att_title:
                title = att_title
        forms = data.get("forms")
        if isinstance(forms, list):
            if not title:
                title = _extract_title_from_forms(forms)
            if not content:
                content = _extract_text_from_forms(forms)
        if not content:
            for key in ("content", "description", "desc", "message"):
                if data.get(key):
                    content = _clean_text(data[key])
                    break
    else:
        title = _regex_extract_json_value(raw, "title")
        content = _regex_extract_json_value(raw, "text")
    if not title and backup_title:
        title = _clean_text(backup_title)
    return pd.Series({"标题": title, "内容": content})


# ============== 加载 + 清洗 ==============
def load_and_clean():
    df = pd.read_excel(SRC_XLSX)
    print(f"[load] {len(df):,} 行 × {df.shape[1]} 列")

    # 过滤有效渠道（Phase 12 #8：剔除"无需渠道"+"微信公众号推文"）
    df = df[~df["渠道"].isin(["无需渠道", "微信公众号推文"])].copy()
    print(f"[filter 渠道] 剩 {len(df):,} 行 ({df['渠道'].nunique()} 渠道: {sorted(df['渠道'].unique())})")

    # 过滤触达成功 > 0（CTR 计算前提）
    df = df[df["触达成功"] > 0].copy()
    print(f"[filter 触达成功>0] 剩 {len(df):,} 行")

    # 计算 CTR
    df["ctr"] = df["点击人次"] / df["触达成功"]
    # 过滤极端值（CTR > 100% 是异常 — 应剔除）
    df = df[df["ctr"] <= 1.0].copy()
    print(f"[filter CTR<=1] 剩 {len(df):,} 行")

    # 工作日类型
    df["发送日期"] = pd.to_datetime(df["发送日期"])
    df["weekday"] = df["发送日期"].dt.weekday  # 0=Mon
    df["workday_type"] = df["weekday"].apply(lambda x: "工作日" if x < 5 else "非工作日")
    df.drop(columns=["weekday"], inplace=True)

    # 文本特征（消息标题 + 消息内容）
    # 复用 C:\Users\a952462\常用文件\代码\日报清洗_new.py 的 parse_message 函数
    # 第 17 列（消息内容）可能是 JSON 格式，需要解析出真正的标题 + 内容
    df["_backup_title"] = df["消息标题"].fillna("").astype(str)
    df["_raw_content"] = df["消息内容"].fillna("").astype(str)

    parsed = df.apply(
        lambda r: parse_message(r["_raw_content"], r["_backup_title"]),
        axis=1,
    )
    df["parsed_title"] = parsed["标题"].astype(str)
    df["parsed_body"] = parsed["内容"].astype(str)
    df["full_text"] = (df["parsed_title"] + " " + df["parsed_body"]).str.strip()
    df["text_len"] = df["full_text"].str.len()

    # 含券词推断（复用 core/text_classifier）
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from core.text_classifier import classify_coupon_in_text
        df["text_has_coupon"] = df.apply(
            lambda r: classify_coupon_in_text(r["parsed_title"], r["parsed_body"]),
            axis=1,
        )
    except Exception as e:
        print(f"[warn] classify_coupon_in_text 失败: {e} → text_has_coupon 全填'未知'")
        df["text_has_coupon"] = "未知"

    # 清理临时列
    df.drop(columns=["_backup_title", "_raw_content"], inplace=True)

    return df


# ============== eta 平方（η²）— 维度对 CTR 方差的解释比例 ==============
def eta_squared(df: pd.DataFrame, dim_col: str, target: str = "ctr") -> dict:
    """单维度 eta 平方：SS_between / SS_total。越大说明该维度对 CTR 方差解释越多。

    返回: {"dim": ..., "eta2": float, "n_groups": int, "groups": {value: {"ctr": float, "n": int}}}
    """
    grouped = df.groupby(dim_col)[target].agg(["mean", "count", "sum"])
    grand_mean = df[target].mean()
    ss_total = ((df[target] - grand_mean) ** 2).sum()
    if ss_total == 0:
        return {"dim": dim_col, "eta2": 0.0, "n_groups": 0, "groups": {}}
    ss_between = (grouped["count"] * (grouped["mean"] - grand_mean) ** 2).sum()
    eta2 = float(ss_between / ss_total)

    # 加权 CTR（按触达成功加权）— 更接近真实基线
    df_weighted = df.copy()
    df_weighted["weighted_ctr"] = df_weighted[target]  # 等价
    weighted = df.groupby(dim_col).apply(
        lambda g: g["点击人次"].sum() / g["触达成功"].sum() if g["触达成功"].sum() > 0 else 0,
        include_groups=False,
    )

    groups = {}
    for v in grouped.index:
        n = int(grouped.loc[v, "count"])
        mean_ctr = float(grouped.loc[v, "mean"])
        weighted_ctr = float(weighted.loc[v])
        groups[str(v)] = {"n": n, "mean_ctr": mean_ctr, "weighted_ctr": weighted_ctr}

    return {
        "dim": dim_col,
        "eta2": round(eta2, 4),
        "n_groups": len(grouped),
        "groups": groups,
    }


# ============== 80/20 train/test split ==============
def split_train_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """80/20 random split（RANDOM_SEED=42）。如果是时间序列更应该按时间切，但 L1 是 random split，按 L1 来。"""
    rng = np.random.default_rng(RANDOM_SEED)
    mask = rng.random(len(df)) < (1 - TEST_RATIO)
    return df[mask].copy(), df[~mask].copy()


# ============== 主流程 ==============
def main():
    print(f"=== Dimension Impact Analysis · {DATE_TAG} ===")
    print(f"源: {SRC_XLSX}")
    print(f"输出: {JSON_OUT} + {MD_OUT}")

    df = load_and_clean()
    print(f"\n整体加权 CTR: {df['点击人次'].sum() / df['触达成功'].sum() * 100:.4f}%\n")

    df_train, df_test = split_train_test(df)
    print(f"[split] train={len(df_train):,}, test={len(df_test):,}\n")

    # 维度列
    dims_categorical = ["渠道", "计划类型", "是否用券", "预算owner", "workday_type", "text_has_coupon"]
    dims_numeric = ["text_len", "触达成功"]  # 数值维度用 eta 也行（视为 binning）

    print("=== 维度影响度 (η² · train 集) ===")
    results = {"train": {}, "test": {}}
    for dim in dims_categorical:
        r_train = eta_squared(df_train, dim)
        r_test = eta_squared(df_test, dim)
        results["train"][dim] = r_train
        results["test"][dim] = r_test
        print(f"  {dim:<20} η²={r_train['eta2']:.4f}  ({r_train['n_groups']} 值, train) | test η²={r_test['eta2']:.4f}")

    # 排序输出（按 η² 降序）
    sorted_train = sorted(results["train"].items(), key=lambda x: x[1]["eta2"], reverse=True)
    print(f"\n=== 维度影响度排名 (train η²) ===")
    for rank, (dim, r) in enumerate(sorted_train, 1):
        effect = "大效应" if r["eta2"] >= 0.14 else "中效应" if r["eta2"] >= 0.06 else "小效应" if r["eta2"] >= 0.01 else "极小效应"
        print(f"  #{rank}  {dim:<20} η²={r['eta2']:.4f}  {effect}")

    # ===== JSON 落档 =====
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_xlsx": str(SRC_XLSX),
        "n_rows_total": len(df),
        "n_rows_train": len(df_train),
        "n_rows_test": len(df_test),
        "random_seed": RANDOM_SEED,
        "test_ratio": TEST_RATIO,
        "overall_weighted_ctr_pct": round(df["点击人次"].sum() / df["触达成功"].sum() * 100, 4),
        "overall_mean_ctr_pct": round(df["ctr"].mean() * 100, 4),
        "dimensions": sorted_train[0][0] + " (最大影响维度)",
        "eta2_ranking": [
            {
                "rank": rank,
                "dim": dim,
                "eta2": r["eta2"],
                "effect_size": "大" if r["eta2"] >= 0.14 else "中" if r["eta2"] >= 0.06 else "小" if r["eta2"] >= 0.01 else "极小",
                "n_groups": r["n_groups"],
                "train_groups": r["groups"],
                "test_eta2": results["test"][dim]["eta2"],
                "test_groups": results["test"][dim]["groups"],
            }
            for rank, (dim, r) in enumerate(sorted_train, 1)
        ],
        "limitations": [
            "η² 是单维度方差解释度（SS_between/SS_total），与 L1 feature_importance（gain 占比）口径不同；主结论以 Handoff.md §6.5 L1 行为准",
            "本数据无 audience / stage / tone / scene 字段",
            "数据时间跨度 684 天（2024-10-15 ~ 2026-08-30），早期 baseline 已校准",
            "80/20 random split 与 L1 训练一致，但时间序列场景建议加时间切分作对照",
        ],
        "parser": {
            "source_script": r"C:\Users\a952462\常用文件\代码\日报清洗_new.py",
            "parsed_column": "消息内容 (第 17 列, JSON 格式)",
            "parser_logic": "复用日报清洗_new.py:parse_message 5 层 fallback（标准JSON → CSV转义 → 嵌套字符串JSON → Python dict → 正则提取）",
        },
        "follow_up": [
            "对照 L1 feature_importance（当前 Top 5：正文长度 35% / 标题长度 23% / 高效词 15% / 短信渠道 9% / 计划类型 6%）",
            "预算owner 31 值 → 数据稀疏，单维度统计可能不稳定，需后续 EDA",
        ],
    }
    JSON_OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[json] 落档: {JSON_OUT}")

    # ===== MD 落档 =====
    md_lines = [
        f"# 维度影响度分析 — {DATE_TAG}",
        "",
        "> ⚠️ **口径声明**：η² 是单维度方差解释度（SS_between/SS_total），**与 L1 feature_importance（gain 占比）口径不同**。**主结论以 Handoff.md §6.5 L1 行为准**（tools/print_feature_importance.py 输出）。本输出保留作对照/复盘用。",
        "",
        f"- **数据源**: `{SRC_XLSX}`（{len(df):,} 行有效数据）",
        f"- **目标**: 单维度对 CTR 数值方差的解释比例（η² = SS_between / SS_total）",
        f"- **80/20 split**: train={len(df_train):,} / test={len(df_test):,} (RANDOM_SEED={RANDOM_SEED})",
        f"- **整体加权 CTR**: {output['overall_weighted_ctr_pct']:.4f}%",
        f"- **整体算术平均 CTR**: {output['overall_mean_ctr_pct']:.4f}%",
        "",
        "## 维度影响度排名",
        "",
        "| 排名 | 维度 | η² (train) | 效应大小 | n_groups | test η² |",
        "|---:|---|---:|---|---:|---:|",
    ]
    for entry in output["eta2_ranking"]:
        md_lines.append(
            f"| {entry['rank']} | {entry['dim']} | {entry['eta2']:.4f} | {entry['effect_size']} | {entry['n_groups']} | {entry['test_eta2']:.4f} |"
        )

    md_lines += ["", "## 各维度 CTR 分布 (train)", ""]
    for entry in output["eta2_ranking"]:
        dim = entry["dim"]
        groups = entry["train_groups"]
        md_lines.append(f"### {dim} (η² = {entry['eta2']:.4f})")
        md_lines.append("")
        md_lines.append("| 值 | n | 平均 CTR% | 加权 CTR% |")
        md_lines.append("|---|---:|---:|---:|")
        # 按加权 CTR 降序
        sorted_groups = sorted(groups.items(), key=lambda x: x[1]["weighted_ctr"], reverse=True)
        for v, g in sorted_groups[:15]:  # 限制 15 行（owner 31 值截断）
            md_lines.append(
                f"| {v} | {g['n']:,} | {g['mean_ctr']*100:.4f} | {g['weighted_ctr']*100:.4f} |"
            )
        if len(sorted_groups) > 15:
            md_lines.append(f"| ... (余 {len(sorted_groups)-15} 值省略) | | | |")
        md_lines.append("")

    md_lines += [
        "## 局限与待办",
        "",
        "- **本数据无 audience / stage / tone / scene 字段** → 这几个维度在本分析中无法评估",
        "- η² 是单维度方差解释度（与 L1 gain 占比不同），不捕捉交叉维度（如 channel × coupon 交叉效应可能大）",
        "- 预算owner 31 值，数据稀疏，单维度统计可能不稳定",
        "- 80/20 random split 与 L1 训练一致；时间序列场景建议加时间切分作对照",
        "",
        "## 文案解析",
        "",
        "- 解析脚本：`C:\\Users\\a952462\\常用文件\\代码\\日报清洗_new.py:parse_message`",
        "- 第 17 列（消息内容）JSON 格式，5 层 fallback 解析（标准JSON → CSV转义 → 嵌套字符串JSON → Python dict → 正则提取）",
        "- 解析后字段：`parsed_title` / `parsed_body` / `full_text` / `text_len`",
        "",
        "## 配套",
        "",
        "- JSON 落档: `" + str(JSON_OUT.relative_to(PROJECT_DIR)) + "`",
        "- Handoff.md §6.5 加索引（本文件）",
        "- Handoff-lessons.md 加第 9 条教训（防丢失）",
        "",
    ]
    MD_OUT.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[md] 落档: {MD_OUT}")

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
