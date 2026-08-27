# -*- coding: utf-8 -*-
r"""
tools/clean_cnn_backup.py — CNN 历史备份清洗工具（Phase 12 · 2026-08-27）

功能：
1. 调用 日报清洗_new.py 解析 CNN 历史备份 xlsx（解析 title/content JSON 字段）
2. 过滤掉"无需渠道"（434 行，标题恒为 [NULL] 占位符）+ "微信公众号推文"（19 行，
   数据稀疏，baseline 已删）
3. 输出到 data/cnn_backup_cleaned.xlsx + 报告（行数/plan数/渠道分布/时间区间）

用法：
    python tools/clean_cnn_backup.py                    # 用默认路径
    python tools/clean_cnn_backup.py --input X.xlsx     # 指定输入
    python tools/clean_cnn_backup.py --skip-parse       # 跳过 json 解析（已清洗）

前置：
- 日报清洗_new.py 在 常用文件/代码/ 目录，路径写死在 SCRIPT_DIR
- 输出到 data/cnn_backup_cleaned.xlsx（保留原 CNN历史备份0827.xlsx 作审计源）
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

# 项目根（tools/clean_cnn_backup.py → ../）
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# 日报清洗_new.py 路径（用户外部脚本，不在项目内）
SCRIPT_DIR = Path(r"C:\Users\a952462\常用文件\代码")
PARSE_SCRIPT = SCRIPT_DIR / "日报清洗_new.py"
PARSE_INPUT = SCRIPT_DIR / "全量推送明细.xlsx"   # 日报清洗_new.py 写死读这个
PARSE_OUTPUT = SCRIPT_DIR / "全量推送明细2.xlsx"  # 日报清洗_new.py 写死输出这个

# 默认输入 / 输出
DEFAULT_INPUT = Path(r"C:\Users\a952462\常用文件\数据\CNN历史备份0827.xlsx")
DEFAULT_OUTPUT = DATA_DIR / "cnn_backup_cleaned.xlsx"

# 过滤掉的目标渠道（#8 渠道清洗 · 用户拍板 2026-08-27）
EXCLUDED_CHANNELS = ("无需渠道", "微信公众号推文")


def run_parse_script(input_xlsx: Path) -> Path:
    """调用 日报清洗_new.py 解析 xlsx，返回中间产物路径（PARSE_OUTPUT）。"""
    if not PARSE_SCRIPT.exists():
        sys.exit(f"找不到解析脚本: {PARSE_SCRIPT}")
    if not input_xlsx.exists():
        sys.exit(f"找不到输入文件: {input_xlsx}")

    # 复制 input → 日报清洗_new.py 写死的 PARSE_INPUT
    shutil.copy2(input_xlsx, PARSE_INPUT)
    print(f"[1/3] 复制 {input_xlsx.name} -> {PARSE_INPUT.name}")

    # 跑 日报清洗_new.py
    print(f"[2/3] 跑 日报清洗_new.py 解析 json 字段...")
    result = subprocess.run(
        [sys.executable, str(PARSE_SCRIPT)],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        sys.exit(f"解析脚本失败:\n{result.stderr}")
    print(f"      {result.stdout.strip().split(chr(10))[-2]}")
    return PARSE_OUTPUT


def clean_and_save(parsed_xlsx: Path, output_xlsx: Path) -> dict:
    """读已解析的 xlsx，过滤 + 输出 + 报告。"""
    print(f"[3/3] 过滤 + 写入 {output_xlsx.name}...")
    df = pd.read_excel(parsed_xlsx, dtype=str, engine="openpyxl").fillna("")
    n_raw = len(df)

    # 过滤
    df_clean = df[~df["渠道"].isin(EXCLUDED_CHANNELS)].copy()
    n_clean = len(df_clean)
    n_excluded = n_raw - n_clean

    # 输出
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_excel(output_xlsx, index=False, engine="openpyxl")

    # 报告
    channel_dist = df_clean["渠道"].value_counts().to_dict()
    plan_count = df_clean["Plan ID"].nunique()
    date_min = str(df_clean["发送日期"].min())[:10]
    date_max = str(df_clean["发送日期"].max())[:10]

    report = {
        "n_raw": n_raw,
        "n_excluded": n_excluded,
        "n_clean": n_clean,
        "n_plans": plan_count,
        "date_range": (date_min, date_max),
        "channel_dist": channel_dist,
        "excluded_channels": list(EXCLUDED_CHANNELS),
    }
    return report


def cleanup_intermediate() -> None:
    """清理中间产物（PARSE_INPUT / PARSE_OUTPUT 在用户 常用文件 目录，不主动删；
    PARSE_INPUT 是用户目录，写了等于污染；用 PARSE_INPUT.unlink 兜底）。"""
    try:
        if PARSE_INPUT.exists():
            PARSE_INPUT.unlink()
    except Exception as e:
        print(f"[warn] 清理中间产物失败: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CNN 历史备份清洗")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help=f"输入 xlsx 路径（默认：{DEFAULT_INPUT.name}）")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"输出 xlsx 路径（默认：{DEFAULT_OUTPUT}）")
    parser.add_argument("--skip-parse", action="store_true",
                        help="跳过 json 解析（输入已是 全量推送明细2.xlsx 格式）")
    parser.add_argument("--keep-intermediate", action="store_true",
                        help="保留 常用文件/代码/全量推送明细*.xlsx 中间产物")
    args = parser.parse_args()

    if args.skip_parse:
        parsed = PARSE_OUTPUT
        if not parsed.exists():
            sys.exit(f"--skip-parse 模式需要 {parsed} 存在")
        print(f"[1/3] 跳过解析，直接读 {parsed.name}")
        print(f"[2/3] （跳过）")
    else:
        parsed = run_parse_script(args.input)

    report = clean_and_save(parsed, args.output)

    if not args.keep_intermediate:
        cleanup_intermediate()

    # 报告
    print()
    print("=" * 60)
    print("清洗报告")
    print("=" * 60)
    print(f"  原始行数:      {report['n_raw']}")
    print(f"  过滤行数:      {report['n_excluded']} "
          f"（{', '.join(report['excluded_channels'])}）")
    print(f"  清洗后行数:    {report['n_clean']}")
    print(f"  独立 plan 数:  {report['n_plans']}")
    print(f"  时间区间:      {report['date_range'][0]} ~ {report['date_range'][1]}")
    print(f"  渠道分布:")
    for ch, n in sorted(report["channel_dist"].items(), key=lambda x: -x[1]):
        pct = n / report["n_clean"] * 100
        print(f"    [{n:6d}] {pct:5.1f}%  {ch}")
    print()
    print(f"  输出文件:      {args.output}")


if __name__ == "__main__":
    main()
