# -*- coding: utf-8 -*-
"""push_phase22_via_api.py — Phase 22 B/C/D 推送（github.com 被墙，Contents API）

按 memory `feedback-github-push-via-api` 模板：牺牲 commit 历史换可达性。
9 文件一次合推：
- tools/print_feature_importance.py（新）
- core/active_mode.py（新）
- tools/monitor_l1_drift.py（改）
- pages/01_content_studio.py（改）
- services/batch_evaluation_service.py（改）
- pages/03_batch_evaluation.py（改）
- tests/verify.py（改）
- .gitignore（改）
- Handoff.md（改）

运行：
  set GITHUB_TOKEN=ghp_<YOUR-TOKEN>
  python tools/push_phase22_via_api.py
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
    "tools/print_feature_importance.py",
    "core/active_mode.py",
    "tools/monitor_l1_drift.py",
    "pages/01_content_studio.py",
    "services/batch_evaluation_service.py",
    "pages/03_batch_evaluation.py",
    "tests/verify.py",
    ".gitignore",
    "Handoff.md",
]

COMMIT_MSG = (
    "feat(Phase 22 B/C/D): 特征重要性月报 + 漂移自动回退 + 批量落档\n\n"
    "B: tools/print_feature_importance.py (217 行) — 加载 lgbm_model_v1.pkl 算 importance, "
    "Top 10 + 名次变化 + 落档 JSON/TXT, humanizer 翻列名\n"
    "C: core/active_mode.py + monitor_l1_drift apply_auto_rollback + 01 sidebar 启动读 "
    "active_mode.txt 覆盖默认 ctr_mode\n"
    "D: services/batch_evaluation_service.batch_signature + save_predictions_to_records + "
    "pages/03 checkbox「保存预测到 records.db」默认关\n"
    "tests/verify.py §58/§59/§60 共 77 用例 (697 -> 794 PASS)\n"
    "Handoff §5/§6.0/§6.1 同步\n"
    ".gitignore 加 drift_log/feature_importance_history/reports\n"
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
    """GET 现有文件拿 sha（更新用）；不存在返回 None。"""
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
    print(f"[push] Phase 22 B/C/D → {OWNER}/{REPO}@{BRANCH}")
    print(f"[push] 共 {len(FILES)} 个文件")
    n_ok = 0
    for f in FILES:
        if push_file(f):
            n_ok += 1
    print(f"\n[done] 成功 {n_ok}/{len(FILES)}")


if __name__ == "__main__":
    main()
