# -*- coding: utf-8 -*-
"""push_simplify_a1_via_api.py — /simplify Phase A.1 清理推送

改动（5 文件）：
- core/product_benefit.py：提 _FALLBACK_CFG 常量，去 4 处 dict literal 重复
- services/generation_service.py：_demo_candidates 去掉" 优惠"凑字（只拼用户输入 token）
- pages/01_content_studio.py：
  - 提 _render_benefit_select helper（pc_a/pc_b 50 行去重）
  - form_dict 修 critical bug：product_benefit.strip() NameError → product_category/benefit_type
  - _task_signature keys 修：删 stale product_benefit，加新 2 字段
- tests/verify.py：更新 §39 静态断言（string-match 改为包含即可）+ 加 helper 存在检查
- config/product_benefit.yaml：加 ⚠️ 双源同步提示
"""
import base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
if not TOKEN:
    print("[FAIL] 未设 GITHUB_TOKEN/GH_TOKEN", file=sys.stderr); sys.exit(1)

OWNER, REPO, BRANCH = "ori-yin", "mcd-ai-content-platform", "main"
ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "core/product_benefit.py",
    "services/generation_service.py",
    "pages/01_content_studio.py",
    "tests/verify.py",
    "config/product_benefit.yaml",
]

COMMIT_MSG = (
    "refactor(Phase A.1 simplify): 修 critical bugs + 4 处清理\n\n"
    "Critical:\n"
    "- pages/01 form_dict 修 NameError（product_benefit 字段已删，submit 会崩）\n"
    "- pages/01 _task_signature keys 删 stale product_benefit，加新 2 字段\n\n"
    "Cleanup:\n"
    "- core/product_benefit.py: 提 _FALLBACK_CFG 常量（去 4 处 dict literal 重复）\n"
    "- services/_demo_candidates: 去掉\" 优惠\"凑字，只拼用户输入 token\n"
    "- pages/01_content_studio: 提 _render_benefit_select helper（pc_a/pc_b 50 行去重）\n"
    "- config yaml: 加 ⚠️ 双源同步提示\n"
    "- tests/verify: 静态断言更新 + 加 helper 存在检查\n\n"
    "测试: 823 → 825 PASS / 0 FAIL（pytest 双路 61 passed）"
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
        return e.code, {"error": e.read().decode("utf-8", errors="replace")[:300]}


def get_sha(path):
    s, b = api("GET", f"contents/{path}?ref={BRANCH}")
    return b.get("sha") if s == 200 and isinstance(b, dict) else None


def push(rel):
    abs_p = ROOT / rel
    if not abs_p.exists(): print(f"  [skip] {rel}"); return True
    b64 = base64.b64encode(abs_p.read_bytes()).decode("ascii")
    sha = get_sha(rel)
    body = {"message": COMMIT_MSG, "branch": BRANCH, "content": b64}
    if sha: body["sha"] = sha
    s, r = api("PUT", f"contents/{rel}", body)
    if s in (200, 201):
        url = (r.get("commit") or {}).get("html_url", "")
        print(f"  [OK] {rel}  {url}"); return True
    print(f"  [FAIL] {rel}  s={s}  {str(r)[:200]}"); return False


def main():
    print(f"[push] /simplify A.1 → {OWNER}/{REPO}@{BRANCH}")
    n = sum(1 for f in FILES if push(f))
    print(f"\n[done] 成功 {n}/{len(FILES)}")


if __name__ == "__main__":
    main()