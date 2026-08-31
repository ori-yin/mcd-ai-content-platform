# -*- coding: utf-8 -*-
"""push_phase22_a1_via_api.py — Phase 22 A.1 产品权益维度扩展 推送（Contents API）

按 memory `feedback-github-push-via-api` 模板：牺牲 commit 历史换可达性。
6 文件一次合推：
- config/product_benefit.yaml（新）
- core/product_benefit.py（新）
- core/schemas.py（改：product_benefit 拆 2 字段）
- prompts/copy_generation.py（改：v1.0→v1.1，2 行拼接）
- services/generation_service.py（改：_demo_candidates 拼接逻辑）
- pages/01_content_studio.py（改：2 selectbox + 自定义）
- tests/verify.py（改：新增 §A.1 测试段）
- Handoff.md（改：§5 A.1 完成条目 + §2 维度列表）

运行：
  set GITHUB_TOKEN=ghp_<YOUR-TOKEN>
  python tools/push_phase22_a1_via_api.py
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
if not TOKEN:
    print("[FAIL] 未设 GITHUB_TOKEN/GH_TOKEN 环境变量", file=sys.stderr)
    sys.exit(1)

OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "config/product_benefit.yaml",
    "core/product_benefit.py",
    "core/schemas.py",
    "prompts/copy_generation.py",
    "services/generation_service.py",
    "pages/01_content_studio.py",
    "tests/verify.py",
    "Handoff.md",
]

COMMIT_MSG = (
    "feat(Phase 22 A.1): 产品权益维度扩展（product_category + benefit_type）\n\n"
    "- 拆字段：TaskInput.product_benefit 单字段 -> product_category + benefit_type 两字段\n"
    "- 数据源：config/product_benefit.yaml（新）+ core/product_benefit.py 加载模块\n"
    "  （10 产品 + 8 权益 + 自定义，PyYAML + lru_cache + FALLBACK 兜底）\n"
    "- dataclass 字段顺序铁律：no-default 在前，灰态字段在尾\n"
    "- prompt 拼接：copy_generation v1.0 -> v1.1，2 行（产品类别/权益类型）任一空不拼\n"
    "- Demo 拼接：_demo_candidates 按\"类别+权益\"两值组装 benefit 短语\n"
    "- UI：pages/01 2 selectbox + 自定义文本框联动 disabled\n"
    "- 测试：§39 test_phase_a1_product_benefit_split 新增 29 用例（794 -> 823 PASS / 0 FAIL）\n"
    "- A.2 投放目标暂搁（待 UI 重构 + L2 后启）\n"
    "- Handoff §2 维度列表 + §5 A.1 完成条目同步"
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
        body = e.read().decode("utf-8", errors="replace")[:300]
        return e.code, {"error": body}


def get_file_sha(path: str) -> str | None:
    status, body = api("GET", f"contents/{path}?ref={BRANCH}")
    if status == 200 and isinstance(body, dict):
        return body.get("sha")
    return None


def push_file(rel_path: str) -> bool:
    abs_path = ROOT / rel_path
    if not abs_path.exists():
        print(f"  [skip] 不存在：{rel_path}")
        return True
    try:
        content = abs_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = abs_path.read_bytes()
        content_b64 = base64.b64encode(content).decode("ascii")
        print(f"  [warn] {rel_path} 二进制，按 base64 上传")
    else:
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")

    sha = get_file_sha(rel_path)
    body = {
        "message": COMMIT_MSG,
        "branch": BRANCH,
        "content": content_b64,
    }
    if sha:
        body["sha"] = sha

    status, resp = api("PUT", f"contents/{rel_path}", body)
    if status in (200, 201):
        commit_url = (resp.get("commit") or {}).get("html_url", "")
        print(f"  [OK] {rel_path} (sha={sha[:8] if sha else 'new'})  {commit_url}")
        return True
    print(f"  [FAIL] {rel_path}  status={status}  {str(resp)[:200]}")
    return False


def main():
    print(f"[push] Phase 22 A.1 -> {OWNER}/{REPO}@{BRANCH}")
    print(f"[push] 共 {len(FILES)} 个文件")
    n_ok = 0
    for f in FILES:
        if push_file(f):
            n_ok += 1
    print(f"\n[done] 成功 {n_ok}/{len(FILES)}")


if __name__ == "__main__":
    main()