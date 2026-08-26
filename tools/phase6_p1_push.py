# -*- coding: utf-8 -*-
"""phase6_p1_push.py — Phase 6 P1 一次性 Contents API 推送脚本

github.com 被墙时用 Contents API 走 api.github.com 推（按 memory feedback-github-push-via-api）。
复刻 tools/push_via_api.py 结构但 FILES 改覆盖本次 12 个改动文件。
Token 不进文件：从 --token 或 env GITHUB_TOKEN 读（避 secret scanning）。
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
    "Handoff.md",
    "core/schemas.py",
    "pages/00_home.py",
    "pages/01_content_studio.py",
    "pages/02_copy_diagnosis.py",
    "pages/03_batch_evaluation.py",
    "pages/04_historical_insights.py",
    "pages/05_feedback.py",
    "prompts/copy_generation.py",
    "tests/verify.py",
    "ui/styles.py",
    "ui/notice.py",   # 新建
]
COMMIT_MSG = (
    "feat(Phase 6 P1): 6 维度前端灰态 + 4 附属页面弱化 + CTR 反哺免责\n\n"
    "按 Downloads/Demo范围决策与待确认_2026-08-26.md 三件事：\n\n"
    "- 决策 1（6 维度前端灰态）：\n"
    "  * core/schemas.TaskInput 必填 7→5，加 PENDING_FIELDS 元组；\n"
    "    product_benefit / objective 加默认空串挪到尾部（dataclass 字段顺序铁律）\n"
    "  * pages/01_content_studio.py 产品与权益 (text_area) + 投放目标 (selectbox)\n"
    "    disabled=True + label「待开发·二期接入」+ help tooltip；副标题「必填 5 项…」\n"
    "  * prompts/copy_generation.build_user_prompt 空时不拼这两行\n"
    "  * 01 推荐结论 + 投放理由 objective 空时兜底\n\n"
    "- 决策 2（4 附属页面弱化）：\n"
    "  * 新建 ui/notice.py：render_advanced_notice + render_ctr_feedback_notice 两个 helper\n"
    "  * ui/styles.py 加 .advanced-notice / .home-section-core / .home-section-advanced CSS\n"
    "  * 02/03 顶部仅 advanced banner；04/05 顶部 advanced + ctr 双 banner\n"
    "  * pages/00_home.py 重排：核心大卡（红底）→ 01；进阶小卡（灰底链列表）→ 02-05\n\n"
    "- 决策 3（CTR 反哺免责）：\n"
    "  * 04/05 顶部 call render_ctr_feedback_notice\n"
    "  * 00_home 进阶区明示「演示口径·业务确认前不接真实数据」\n"
    "  * 01 推荐结论保留原免责「不代表正式投放承诺」\n\n"
    "- 不动：app.py（避 st.Page 递归铁律）/ 后端反哺 / 删除任何页面（弱化不剔除）\n"
    "- tests/verify.py：新增 §39 灰态 17 + §40 弱化+免责 29 用例；349 → 395 PASS\n"
    "- Handoff.md：§5 加 P1 决策记录；§6 Phase 6 P1 标完成 + 加待业务确认 7 项；§7 补 3 教训"
)


def _resolve_token() -> str:
    """按优先级：CLI --token > 环境变量 GITHUB_TOKEN / GH_TOKEN"""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not tok:
        for i, arg in enumerate(sys.argv):
            if arg == "--token" and i + 1 < len(sys.argv):
                tok = sys.argv[i + 1]
                break
    if not tok:
        sys.exit("缺少 GitHub token。请通过 --token 或环境变量 GITHUB_TOKEN / GH_TOKEN 传入")
    return tok


def api(method: str, path: str, token: str, body=None):
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


def get_existing_shas(token: str):
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
