# -*- coding: utf-8 -*-
"""push_cleanup_2026-08-31.py — 一次性 push 脚本（口径清理 + stale 标记）

按 memory `feedback-github-push-via-api` 模板（Contents API + Git Trees API 拿 sha）：
- 空仓库 /contents 端点 404；但 PUT .../contents/{path} 仍能用
- content 始终 base64
- 更新现有文件 PUT 必须带 sha（用 Git Trees API 拿）
- push 前后各 GET 一次远端 HEAD sha，验证改动是叠加而不是冲突
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "Handoff.md",
    "Handoff-lessons.md",
    "tools/dimension_impact_analysis.py",
    "data/findings/dimension_impact_2026-08-31_151231.json",
    "data/findings/dimension_impact_2026-08-31_151231.md",
]
COMMIT_MSG = (
    "chore(handoff): η² 落档加 stale 标记 + 口径声明（Handoff / Handoff-lessons / script）\n\n"
    "- Handoff.md §6.5: 维度影响度分析行加 ⚠️ stale 标，主结论指向 L1 feature_importance 行\n"
    "- Handoff-lessons.md #9: 删具体案例（audience 显著影响），只留通用铁律\n"
    "- tools/dimension_impact_analysis.py: 输出顶部加口径声明；follow_up 删强表述\n"
    "- data/findings/dimension_impact_2026-08-31_151231.{json,md}: 加 _stale_notice / ⚠️ 块\n"
    "- 不动其它文件，避免污染下个 session\n"
)


def api(method, path, body=None):
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


def get_head_sha():
    status, ref = api("GET", f"git/ref/heads/{BRANCH}")
    if status != 200:
        sys.exit(f"GET ref failed: {status} {ref}")
    return ref["object"]["sha"]


def get_existing_shas():
    tree_sha = get_head_sha()
    status, tree = api("GET", f"git/trees/{tree_sha}?recursive=1")
    if status != 200:
        sys.exit(f"GET tree failed: {status} {tree}")
    return {item["path"]: item["sha"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def main():
    if not TOKEN:
        for i, arg in enumerate(sys.argv):
            if arg == "--token" and i + 1 < len(sys.argv):
                globals()["TOKEN"] = sys.argv[i + 1]
                break
    if not TOKEN:
        sys.exit("缺少 GitHub token。请通过 --token 或环境变量 GITHUB_TOKEN / GH_TOKEN 传入")

    before_sha = get_head_sha()
    print(f"[before] 远端 main HEAD: {before_sha}")

    shas = get_existing_shas()
    print(f"[info] 远端已有 {len(shas)} 个文件")

    for rel_path in FILES:
        local = ROOT / rel_path
        if not local.exists():
            print(f"  ! skip (not found): {rel_path}")
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
            print(f"  OK {rel_path} (status={status})")
        else:
            err_text = str(resp)[:300] if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)[:300]
            print(f"  FAIL {rel_path} (status={status}): {err_text}")
            sys.exit(1)

    after_sha = get_head_sha()
    print(f"\n[after] 远端 main HEAD: {after_sha}")
    if after_sha == before_sha:
        print("[WARN] HEAD sha 没变，push 可能失败")
        sys.exit(1)
    print("[OK] HEAD 已推进，push 成功")


if __name__ == "__main__":
    main()
