# -*- coding: utf-8 -*-
"""push_phase38_a1mid_via_api.py — Phase 38 A1-mid 推送（Git Data API · 2 commits 依次推）

按 memory `feedback-github-push-via-api`：
- github.com 直连 SSL EOF，用 Contents API 一次推 30 文件 = 30 commit（污染历史）
- Git Data API 4 步：blob × N → tree → commit → ref update

本脚本特殊处理：
- 2 个本地 commit 依次推（保留 history）：fd94aea (22 inline 收敛 + design.md DNA) → 816eb85 (设计规范 §12 避坑教训)
- 每次推完，parent = 上次创建的 commit（不是远端 HEAD）
- 删除文件走 tree entry sha: null（Contents API 不能删）

用法：
    python tools/push_phase38_a1mid_via_api.py --token ghp_xxx
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent.parent.parent  # 适配 archive 嵌套（tools/_archive/ → repo root）
TOKEN = ""

# 要推的 commits（按从旧到新的顺序；本地 HEAD = f7835ef → ahead 远端 1 commit）
COMMITS_TO_PUSH = ["f7835ef"]


def api(method: str, path: str, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-phase26-push")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _git_env() -> dict:
    """Git on Windows: subprocess 默认 GBK，输出中文文件名是 octal escape。
    加 LC_ALL=C.UTF-8 + -c core.quotepath=false 让 git 用真 UTF-8 输出文件名。"""
    env = os.environ.copy()
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    return env


def get_commit_files(commit_sha: str) -> list:
    out = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "diff-tree",
         "--no-commit-id", "--name-only", "-r", commit_sha],
        cwd=str(ROOT), env=_git_env(),
    ).decode("utf-8").strip()
    return [l for l in out.splitlines() if l]


def get_commit_message(commit_sha: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "log",
         "-1", "--pretty=%B", commit_sha],
        cwd=str(ROOT), env=_git_env(),
    ).decode("utf-8").strip()


def push_one_commit(commit_sha: str, parent_sha: str) -> str:
    files = get_commit_files(commit_sha)
    msg = get_commit_message(commit_sha)
    print(f"\n===== 推 commit {commit_sha[:12]} =====")
    print(f"  文件数: {len(files)}, message: {msg.splitlines()[0][:60]}...")

    # 拿 parent tree
    status, parent_commit = api("GET", f"git/commits/{parent_sha}")
    if status != 200:
        sys.exit(f"GET parent commit 失败: {status} {parent_commit}")
    base_tree_sha = parent_commit["tree"]["sha"]
    print(f"  parent tree: {base_tree_sha[:12]}")

    # 创建 blob（含删除检测）
    tree_entries = []
    for rel in files:
        local = ROOT / rel
        if not local.exists():
            # 删除
            tree_entries.append({
                "path": rel,
                "mode": "100644",
                "type": "blob",
                "sha": None,
            })
            print(f"  - delete {rel}")
            continue
        content_bytes = local.read_bytes()
        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        status, blob = api("POST", "git/blobs", {
            "content": content_b64,
            "encoding": "base64",
        })
        if status != 201:
            sys.exit(f"POST blob {rel} 失败: {status} {blob}")
        tree_entries.append({
            "path": rel,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"  + blob {rel} ({len(content_bytes):,} bytes)")

    # 创建 tree
    status, new_tree = api("POST", "git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_entries,
    })
    if status != 201:
        # 等 3 秒重试（memory 坑 #2：parent tree 还没 fully indexed）
        print(f"  ! POST tree {status}，等 3 秒重试...")
        time.sleep(3)
        status, new_tree = api("POST", "git/trees", {
            "base_tree": base_tree_sha,
            "tree": tree_entries,
        })
        if status != 201:
            sys.exit(f"POST tree 失败: {status} {new_tree}")
    print(f"  new tree: {new_tree['sha'][:12]}")

    # 创建 commit
    status, new_commit = api("POST", "git/commits", {
        "message": msg,
        "tree": new_tree["sha"],
        "parents": [parent_sha],
    })
    if status != 201:
        sys.exit(f"POST commit 失败: {status} {new_commit}")
    print(f"  new commit: {new_commit['sha'][:12]}")

    # 更新 ref
    status, ref_resp = api("PATCH", f"git/refs/heads/{BRANCH}", {
        "sha": new_commit["sha"],
    })
    if status != 200:
        sys.exit(f"PATCH ref 失败: {status} {ref_resp}")

    return new_commit["sha"]


def main():
    global TOKEN
    if "--token" in sys.argv:
        i = sys.argv.index("--token")
        TOKEN = sys.argv[i + 1]
    elif os.environ.get("GITHUB_TOKEN"):
        TOKEN = os.environ["GITHUB_TOKEN"]
    if not TOKEN:
        sys.exit("缺少 token：--token ghp_xxx 或 GITHUB_TOKEN env")

    # 拿当前远端 HEAD
    status, ref = api("GET", f"git/ref/heads/{BRANCH}")
    if status != 200:
        sys.exit(f"GET ref 失败: {status} {ref}")
    parent_sha = ref["object"]["sha"]
    print(f"远端 HEAD: {parent_sha[:12]}")

    # 依次推
    for commit_sha in COMMITS_TO_PUSH:
        parent_sha = push_one_commit(commit_sha, parent_sha)

    # memory 坑 #4：最后 print 失败但 PATCH 已成功，必须 verify HEAD
    print(f"\n推送流程完成。verify 远端 HEAD...")
    status, ref_after = api("GET", f"git/ref/heads/{BRANCH}")
    if status != 200:
        sys.exit(f"verify ref 失败: {status} {ref_after}")
    actual_head = ref_after["object"]["sha"]
    if actual_head != parent_sha:
        sys.exit(f"⚠️ HEAD 不一致: 期望 {parent_sha[:12]} / 实际 {actual_head[:12]}")
    print(f"✅ 推送完成。远端 HEAD: {actual_head[:12]}")


if __name__ == "__main__":
    # Windows Git Bash 默认 GBK stdout，print 中文 message 触发 UnicodeEncodeError（memory 坑 #4）
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()