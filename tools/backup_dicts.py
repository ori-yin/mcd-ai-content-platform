# -*- coding: utf-8 -*-
"""backup_dicts.py — 字典文件本地备份（防手残误删）

用法：
    python tools/backup_dicts.py                # 默认保留 14 天
    python tools/backup_dicts.py --days 30      # 保留 30 天
    python tools/backup_dicts.py --list          # 列出已有备份（不创建新备份）

备份内容（7 个文件 / 字典维护 UI 能改的全部）：
    data/custom_dict.txt       产品词典
    data/stopwords.txt         停用词
    data/ctr_baseline.json     CTR 基准
    config/channel_rules.yaml  渠道规则
    config/dimension_weights.yaml 维度权重
    config/coupon_keywords.yaml  含券关键词
    config/brand_rules.yaml    品牌规则

输出：
    data/.backups/dicts_YYYY-MM-DD_HHMMSS.tar.gz
    保留最近 N 天（默认 14），超出自动清理

可选：自动每天定时备份（Windows 任务计划）：
    schtasks /Create /SC DAILY /TN "mcd-dict-backup" /TR "python C:\\ideon\\mcd-ai-content-platform\\tools\\backup_dicts.py" /ST 18:00
    schtasks /Run /TN "mcd-dict-backup"          # 立即跑一次测试

Why:
    用户担心字典维护误删，本地每天备份；不污染 git（data/.backups/ 入 .gitignore）。
    同时 git 远端有完整版本，可双重恢复：本地 tar.gz → git 历史 → 重写文件。
"""

import argparse
import os
import re
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "data" / ".backups"

# 字典维护 UI 能改的全部文件（settings page NAV dicts）
DICT_FILES = [
    "data/custom_dict.txt",
    "data/stopwords.txt",
    "data/ctr_baseline.json",
    "config/channel_rules.yaml",
    "config/dimension_weights.yaml",
    "config/coupon_keywords.yaml",
    "config/brand_rules.yaml",
]


def list_backups() -> list[Path]:
    """列出已有备份（按时间排序，最新在前）。"""
    if not BACKUP_DIR.exists():
        return []
    return sorted(BACKUP_DIR.glob("dicts_*.tar.gz"), reverse=True)


def has_backup_today() -> bool:
    """今天是否已有备份？用于 settings 保存时的去重。"""
    if not BACKUP_DIR.exists():
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    return any(f.name.startswith(f"dicts_{today}_") for f in BACKUP_DIR.glob("dicts_*.tar.gz"))


def cleanup_old(days: int) -> int:
    """清理 N 天前的备份，返回删除数量。"""
    if not BACKUP_DIR.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    pattern = re.compile(r"dicts_(\d{4}-\d{2}-\d{2})_(\d{6})\.tar\.gz")
    removed = 0
    for f in BACKUP_DIR.glob("dicts_*.tar.gz"):
        m = pattern.match(f.name)
        if not m:
            continue
        try:
            ts = datetime.strptime(f"{m.group(1)}_{m.group(2)}", "%Y-%m-%d_%H%M%S")
        except ValueError:
            continue
        if ts < cutoff:
            f.unlink()
            removed += 1
    return removed


def create_backup_internal(days: int = 14, verbose: bool = False) -> tuple[Path | None, str]:
    """内部 API：创建新备份（被 web/settings_save handler 调用）。

    返回 (backup_path_or_None, info_message)。
    - backup_path_or_None: 备份文件路径；None 表示今天已备份过（跳过）
    - info_message: 人类可读的描述

    注意：失败不抛异常（web handler 必须容错，备份失败不影响保存）。
    """
    try:
        # 去重：今天已备份过则跳过
        if has_backup_today():
            latest = list_backups()[0] if list_backups() else None
            return None, f"今天已备份过（{latest.name if latest else '?'}），跳过"

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out = BACKUP_DIR / f"dicts_{ts}.tar.gz"

        # 检查所有源文件存在
        missing = [f for f in DICT_FILES if not (ROOT / f).exists()]
        if missing and len(missing) == len(DICT_FILES):
            return None, f"所有字典文件都不存在，跳过备份"

        # 写 tar.gz
        total_bytes = 0
        written_count = 0
        with tarfile.open(out, "w:gz") as tar:
            for rel in DICT_FILES:
                src = ROOT / rel
                if not src.exists():
                    continue
                tar.add(src, arcname=rel)
                total_bytes += src.stat().st_size
                written_count += 1

        # 清理旧备份
        cleanup_old(days)

        msg = f"已自动备份 {written_count} 个字典文件 ({total_bytes:,} 字节)"
        if verbose:
            print(f"✅ 自动备份：{out.name} ({written_count} files, {total_bytes:,} bytes)")
        return out, msg
    except Exception as e:
        return None, f"备份失败：{e}"


def create_backup() -> Path:
    """CLI API：创建新备份（CLI 命令调用）。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = BACKUP_DIR / f"dicts_{ts}.tar.gz"

    # 检查所有源文件存在
    missing = [f for f in DICT_FILES if not (ROOT / f).exists()]
    if missing:
        print(f"⚠️  以下字典文件不存在，跳过备份：")
        for f in missing:
            print(f"   - {f}")
        if len(missing) == len(DICT_FILES):
            sys.exit(1)

    # 写 tar.gz
    total_bytes = 0
    written = []
    with tarfile.open(out, "w:gz") as tar:
        for rel in DICT_FILES:
            src = ROOT / rel
            if not src.exists():
                continue
            tar.add(src, arcname=rel)
            size = src.stat().st_size
            total_bytes += size
            written.append((rel, size))

    return out, written, total_bytes


def cmd_list():
    """列出所有备份（最新在最上）。"""
    backups = list_backups()
    if not backups:
        print(f"📂 {BACKUP_DIR} 下暂无备份")
        print(f"   跑 `python tools/backup_dicts.py` 创建第一个备份")
        return
    print(f"📂 {BACKUP_DIR}（共 {len(backups)} 个备份）")
    print(f"{'备份文件':<40} {'大小':>10}  {'备份时间'}")
    print("-" * 80)
    for b in backups:
        size = b.stat().st_size
        # 从文件名提取时间
        m = re.search(r"dicts_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})\.tar\.gz", b.name)
        if m:
            ts = f"{m.group(1)} {m.group(2)}:{m.group(3)}:{m.group(4)}"
        else:
            ts = "?"
        print(f"{b.name:<40} {size:>10,}  {ts}")


def cmd_backup(days: int):
    """创建新备份 + 清理旧备份。"""
    print(f"🔧 字典备份（保留 {days} 天）")
    print(f"   备份目录：{BACKUP_DIR}")
    print()

    out, written, total = create_backup()
    print(f"✅ 备份成功：{out.name}")
    print(f"   文件数：{len(written)}")
    print(f"   原始大小：{total:,} 字节")
    print(f"   压缩后：{out.stat().st_size:,} 字节")
    print()
    print("   包含文件：")
    for rel, size in written:
        print(f"   - {rel:<40} {size:>10,} 字节")

    # 清理
    removed = cleanup_old(days)
    if removed:
        print(f"\n🗑️  清理了 {removed} 个超过 {days} 天的旧备份")
    remaining = len(list_backups())
    print(f"📦 当前共 {remaining} 个备份（最近 {days} 天内）")


def main():
    ap = argparse.ArgumentParser(
        description="字典文件本地备份（防手残误删）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--days", type=int, default=14, help="保留天数（默认 14）")
    ap.add_argument("--list", action="store_true", help="列出已有备份（不创建新备份）")
    args = ap.parse_args()

    if args.list:
        cmd_list()
    else:
        cmd_backup(args.days)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
