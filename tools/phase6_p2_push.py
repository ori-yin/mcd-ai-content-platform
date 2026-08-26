# -*- coding: utf-8 -*-
"""phase6_p2_push.py — Phase 6 P2 Contents API 推送（仅 4 文件）

github.com 被墙时改走 api.github.com（按 memory feedback-github-push-via-api）。
复刻 tools/push_via_api.py 结构但 FILES 只列本次变更的 4 个文件。
Token 不进文件：从 --token 或 env GITHUB_TOKEN 读。
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "CLAUDE.md",
    "Handoff.md",
    "docs/ctr-kpi-definition-proposal-v0.1.md",
    "tools/phase6_p2_push.py",   # 自身
]
COMMIT_MSG = (
    "chore(Phase 6 P2): Handoff/CLAUDE.md 同步 + CTR 口径倾向稿 + 压缩 Handoff 冗余\n\n"
    "1. Handoff 入口信息同步（§2 维度 / §6 快照 / §8 路径 / §9 阶段 / §5.5 / §7）\n"
    "2. CLAUDE.md §8 Self-check 自动化（Phase 收尾必同步 Handoff）\n"
    "3. 新增 docs/ctr-kpi-definition-proposal-v0.1.md（plan 加权 CTR + 6 业务选择题）\n"
    "4. 压缩 Handoff 冗余（§3 27→4 行；§6 加 6.0 快照 / 6.1 总览表）\n\n"
    "verify.py 不动 -> 395 PASS 不变"
)


def _resolve_token() -> str:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not tok:
        for i, arg in enumerate(sys.argv):
            if arg == "--token" and i + 1 < len(sys.argv):
                tok = sys.argv[i + 1]
                break
    if not tok:
        sys.exit("缺少 GitHub token")
    return tok


def api(method, path, token, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-push-api")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return e.code, body_text


def get_existing_shas(token):
    status, ref = api("GET", f"git/ref/heads/{BRANCH}", token)
    if status != 200:
        sys.exit(f"GET ref failed: {status} {ref}")
    tree_sha = ref["object"]["sha"]
    status, tree = api("GET", f"git/trees/{tree_sha}?recursive=1", token)
    if status != 200:
        sys.exit(f"GET tree failed: {status} {tree}")
    return {item["path"]: item["sha"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def main():
    token = _resolve_token()
    shas = get_existing_shas(token)
    print(f"远端已有 {len(shas)} 个文件")

    for rel_path in FILES:
        local = ROOT / rel_path
        if not local.exists():
            print(f"  ! 跳过（本地不存在）：{rel_path}")
            continue

        content_bytes = local.read_bytes()
        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        body = {
            "message": COMMIT_MSG,
            "branch": BRANCH,
            "content": content_b64,
        }
        if rel_path in shas:
            body["sha"] = shas[rel_path]
        status, resp = api("PUT", f"contents/{rel_path}", token, body)
        if status in (200, 201):
            print(f"  + {rel_path} (status={status})")
        else:
            print(f"  X {rel_path} (status={status}): {str(resp)[:300]}")
            sys.exit(1)

    status, ref = api("GET", f"git/ref/heads/{BRANCH}", token)
    new_sha = ref["object"]["sha"] if status == 200 else "?"
    print(f"\n推送完成。远端 main HEAD: {new_sha}")


if __name__ == "__main__":
    main()
