# -*- coding: utf-8 -*-
"""push_phase48.py — 用 Git Data API 把本地 9a07a8f+c36e082 合并成 1 个干净 commit 推到远端

按 memory `feedback-github-push-via-api` 的 Git Data API 4 步流程：
1. POST blobs (每个文件一个)
2. POST tree (base_tree + 9 个 path:blob 改动)
3. POST commit (parent = base_commit)
4. PATCH ref (heads/main → new commit)

为什么不用 Contents API：会生成 9 个 commit object 链式 commit，
git log 会一片 Phase 48 part 1/9 ... 9/9 很难看。
Git Data API 单次提交，所有改动在 1 个 commit 里。
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or ""
OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"

ROOT = Path(r"C:\ideon\mcd-ai-content-platform")
BASE_COMMIT = "3cce17607defd8347e573153fc84e5765468a45e"

# Phase 48 两个 commit 改动文件（合并成 1 个 commit 推送）
FILES = [
    "Handoff.md",
    "Handoff-decisions.md",
    "Handoff-todo.md",
    "Handoff-lessons.md",
    "design.md",
    "web/static/css/style.css",
    "web/templates/pages/04_历史洞察.html",
    "web/templates/pages/05_真实结果回流.html",
    "web/app.py",
]

COMMIT_MSG = (
    "docs+style+perf: Phase 48 — 02/03/04/05 UI 一致化微调 + 性能诊断 + 启动预热\n\n"
    "UI 5 项（A1 banner + A2 batch table + B1 metric-row + B2 code 去框 + B3 句式统一）\n"
    "性能诊断：实测启动预热无效（ASGI+业务层+浏览器全量加载占大头），保留代码无害\n"
    "Handoff 4 文件全量同步（Handoff.md §6.0/§6.1/§10 + decisions/todo/lessons 各自新段）\n\n"
    "验证：848 PASS / 0 FAIL + py_compile + 6 routes 200 + grep 句式一致\n"
    "Phase 48 后续：性能走 HTMX hx-boost / P4 反哺效果待用户拍板 / 反哺自动化待方案"
)


def api(method: str, path: str, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-push-phase48")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main():
    if not TOKEN:
        sys.exit("缺 GITHUB_TOKEN")

    # Step 0: 拿 base_commit 的 base_tree_sha
    print(f"[0/4] GET base commit {BASE_COMMIT[:10]} ...")
    status, commit = api("GET", f"git/commits/{BASE_COMMIT}")
    if status != 200:
        sys.exit(f"GET commit failed: {status} {commit}")
    base_tree = commit["tree"]["sha"]
    print(f"      base_tree = {base_tree[:10]}")

    # Step 1: POST blobs ×9
    print(f"[1/4] POST {len(FILES)} blobs ...")
    blob_shas = {}
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            sys.exit(f"本地文件不存在: {rel}")
        content_bytes = local.read_bytes()
        # utf-8 中文用 base64 编码，GitHub blob 支持 utf-8 直接传
        # 但保险起见用 base64，跨编码稳
        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        status, resp = api("POST", "git/blobs", {
            "encoding": "base64",
            "content": content_b64,
        })
        if status != 201:
            sys.exit(f"POST blob {rel} failed: {status} {resp}")
        blob_shas[rel] = resp["sha"]
        print(f"      [OK] {rel} -> blob {resp['sha'][:10]}")

    # Step 2: POST tree (基于 base_tree)
    print("[2/4] POST tree ...")
    tree_body = {
        "base_tree": base_tree,
        "tree": [
            {"path": rel, "mode": "100644", "type": "blob", "sha": blob_shas[rel]}
            for rel in FILES
        ],
    }
    status, tree = api("POST", "git/trees", tree_body)
    if status != 201:
        sys.exit(f"POST tree failed: {status} {tree}")
    new_tree_sha = tree["sha"]
    print(f"      new_tree = {new_tree_sha[:10]}")

    # Step 3: POST commit
    print("[3/4] POST commit ...")
    commit_body = {
        "message": COMMIT_MSG,
        "parents": [BASE_COMMIT],
        "tree": new_tree_sha,
    }
    status, new_commit = api("POST", "git/commits", commit_body)
    if status != 201:
        sys.exit(f"POST commit failed: {status} {new_commit}")
    new_commit_sha = new_commit["sha"]
    print(f"      new_commit = {new_commit_sha}")

    # Step 4: PATCH ref
    print("[4/4] PATCH ref heads/main ...")
    status, ref = api("PATCH", f"git/refs/heads/{BRANCH}", {
        "sha": new_commit_sha,
        "force": False,
    })
    if status != 200:
        sys.exit(f"PATCH ref failed: {status} {ref}")
    print(f"      main → {ref['object']['sha']}")

    print(f"\n[Phase 48 PUSH OK] {new_commit_sha[:10]}")
    print(f"   9 files merged into 1 commit on top of {BASE_COMMIT[:10]}")


if __name__ == "__main__":
    main()
