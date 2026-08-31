# -*- coding: utf-8 -*-
"""push_phase23_via_api.py — Phase 22 A.1 + 23 + 24 批量推送（Git Data API）

按 memory `feedback-github-push-via-api`：
- github.com 直连 SSL EOF，用 Contents API 一次推 20 文件 = 20 个 commit（污染历史）
- Git Data API 4 步：blob × N → tree → commit → ref update = 1 个 commit 保历史

用法：
    export GITHUB_TOKEN=ghp_<YOUR-TOKEN>
    python tools/push_phase23_via_api.py

文件清单从 git diff HEAD~1..HEAD 读（保证本地 commit 与远端 commit 一致）。
"""

import base64
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def api(method: str, path: str, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-git-data-api")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return e.code, body_text


def get_changed_files() -> list:
    """从 git diff HEAD~1..HEAD 读本次 commit 改的文件。"""
    out = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=str(ROOT),
    ).decode("utf-8").strip()
    return [l for l in out.splitlines() if l]


def get_commit_message() -> str:
    return subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"], cwd=str(ROOT),
    ).decode("utf-8").strip()


def main():
    global TOKEN
    # 优先级：--token 命令行 > 环境变量
    if "--token" in sys.argv:
        i = sys.argv.index("--token")
        if i + 1 < len(sys.argv):
            TOKEN = sys.argv[i + 1]
    if not TOKEN:
        sys.exit("缺少 token：请用 --token ghp_<YOUR-TOKEN> 或设 GITHUB_TOKEN / GH_TOKEN 环境变量")

    files = get_changed_files()
    msg = get_commit_message()
    print(f"待推 {len(files)} 个文件 / commit msg: {msg.splitlines()[0][:60]}...")

    # 1) 拿 parent commit
    status, ref = api("GET", f"git/ref/heads/{BRANCH}")
    if status != 200:
        sys.exit(f"GET ref 失败: {status} {ref}")
    parent_sha = ref["object"]["sha"]
    print(f"parent commit: {parent_sha[:12]}")

    # 2) 拿 parent tree
    status, parent_commit = api("GET", f"git/commits/{parent_sha}")
    if status != 200:
        sys.exit(f"GET parent commit 失败: {status} {parent_commit}")
    base_tree_sha = parent_commit["tree"]["sha"]
    print(f"base tree: {base_tree_sha[:12]}")

    # 3) 逐文件创建 blob
    tree_entries = []
    for rel in files:
        local = ROOT / rel
        if not local.exists():
            print(f"  ! 跳过（本地不存在）: {rel}")
            continue
        content_bytes = local.read_bytes()
        # 检测 binary（含 NUL）
        if b"\x00" in content_bytes[:8192]:
            content_b64 = base64.b64encode(content_bytes).decode("ascii")
            encoding = "base64"
        else:
            # text：utf-8 encode 后 base64
            content_b64 = base64.b64encode(content_bytes).decode("ascii")
            encoding = "base64"

        status, blob = api("POST", "git/blobs", {
            "content": content_b64,
            "encoding": encoding,
        })
        if status != 201:
            sys.exit(f"POST blob {rel} 失败: {status} {blob}")
        tree_entries.append({
            "path": rel,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"  ✓ blob {rel} ({len(content_bytes):,} bytes)")

    # 4) 创建新 tree（基于 parent tree，加我们的 entries）
    status, new_tree = api("POST", "git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_entries,
    })
    if status != 201:
        sys.exit(f"POST tree 失败: {status} {new_tree}")
    print(f"new tree: {new_tree['sha'][:12]}")

    # 5) 创建 commit
    status, new_commit = api("POST", "git/commits", {
        "message": msg,
        "tree": new_tree["sha"],
        "parents": [parent_sha],
    })
    if status != 201:
        sys.exit(f"POST commit 失败: {status} {new_commit}")
    print(f"new commit: {new_commit['sha'][:12]}")

    # 6) 更新 ref
    status, ref_resp = api("PATCH", f"git/refs/heads/{BRANCH}", {
        "sha": new_commit["sha"],
    })
    if status != 200:
        sys.exit(f"PATCH ref 失败: {status} {ref_resp}")

    print(f"\n✅ 推送完成。新 HEAD: {new_commit['sha'][:12]}")


if __name__ == "__main__":
    main()