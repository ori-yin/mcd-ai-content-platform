# -*- coding: utf-8 -*-
"""push_via_api.py — github.com 被墙时改走 Contents API 推代码（一次性脚本）

按 memory `feedback-github-push-via-api` 模板：
- 空仓库 /contents 端点 404；但 PUT .../contents/{path} 仍能用
- content 始终 base64
- 更新现有文件 PUT 必须带 sha（用 Git Trees API 拿）
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Token 来源（按优先级）：
#   1) 命令行 --token
#   2) 环境变量 GITHUB_TOKEN / GH_TOKEN
# 不要把 token 硬编码进文件（会触发 GitHub secret scanning 阻断 push）
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "pytest.ini",
    "tests/verify.py",
]
COMMIT_MSG = (
    "feat(Phase 8): pytest 迁移 — 双路运行（pytest 43 passed + CLI 428 PASS）\n\n"
    "- pytest.ini: testpaths=tests / python_files=verify.py+test_*.py / markers 按 Phase 划分\n"
    "- tests/verify.py: _RUNNING_UNDER_PYTEST 标志 + _check 失败抛 AssertionError（pytest）/ 静默累计（CLI）\n"
    "- 保留 if __name__ == '__main__': 块，CLI 行为完全不变（428 PASS, 0 FAIL）\n"
    "- 反向验证：注入失败 _check → pytest 报 1 failed；恢复后 43 passed\n"
)


def api(method: str, path: str, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-push-api")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return e.code, body_text


def get_existing_shas():
    """用 Git Trees API 拿远端所有文件 sha。"""
    status, ref = api("GET", f"git/ref/heads/{BRANCH}")
    if status != 200:
        sys.exit(f"GET ref failed: {status} {ref}")
    tree_sha = ref["object"]["sha"]
    status, tree = api("GET", f"git/trees/{tree_sha}?recursive=1")
    if status != 200:
        sys.exit(f"GET tree failed: {status} {tree}")
    return {item["path"]: item["sha"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def main():
    # token 从 CLI / 环境变量获取，避免硬编码触发 secret scanning
    if not TOKEN:
        for i, arg in enumerate(sys.argv):
            if arg == "--token" and i + 1 < len(sys.argv):
                globals()["TOKEN"] = sys.argv[i + 1]
                break
    if not TOKEN:
        sys.exit("缺少 GitHub token。请通过 --token 或环境变量 GITHUB_TOKEN / GH_TOKEN 传入")

    shas = get_existing_shas()
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
        status, resp = api("PUT", f"contents/{rel_path}", body)
        if status in (200, 201):
            print(f"  ✓ {rel_path} (status={status})")
        else:
            print(f"  ✗ {rel_path} (status={status}): {str(resp)[:200]}")
            sys.exit(1)

    # 验证：拉远端 HEAD sha
    status, ref = api("GET", f"git/ref/heads/{BRANCH}")
    new_sha = ref["object"]["sha"] if status == 200 else "?"
    print(f"\n推送完成。远端 main HEAD: {new_sha}")


if __name__ == "__main__":
    main()