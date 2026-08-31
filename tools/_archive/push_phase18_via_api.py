# -*- coding: utf-8 -*-
r"""push_phase18_via_api.py — Contents API 推 Phase 18（更新已存在文件自动拿 sha）。"""

import base64
import json
from pathlib import Path

import urllib.request
import urllib.error

TOKEN = "ghp_<YOUR-TOKEN>"
REPO = "ori-yin/mcd-ai-content-platform"
ROOT = Path(r"C:\ideon\mcd-ai-content-platform")

FILES = [
    ".gitignore",
    "Handoff.md",
    "data/effective_words.json",
    "data/lgbm_feature_meta.json",
    "tests/verify.py",
    "tools/evaluate_lgbm.py",
    "tools/train_lgbm.py",
]

COMMIT_MSG = "Phase 18: L1 LightGBM PoC（剔除小程序 + 高效词 + 时间衰减）"


def api_get_sha(path: str) -> str | None:
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-phase18-push",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8")).get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def api_put(path: str, content_bytes: bytes, msg: str, sha: str | None) -> tuple:
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    body = {
        "message": msg,
        "content": base64.b64encode(content_bytes).decode("ascii"),
    }
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="PUT",
        headers={
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-phase18-push",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    ok, fail, skip = 0, 0, 0
    for rel in FILES:
        full = ROOT / rel
        if not full.exists():
            print(f"[SKIP] {rel} 不存在")
            skip += 1
            continue
        content = full.read_bytes()
        # 检查远端 sha
        sha = api_get_sha(rel)
        status, data = api_put(rel, content, COMMIT_MSG, sha)
        if status in (200, 201):
            new_sha = data.get("content", {}).get("sha", "?")[:10]
            op = "update" if sha else "create"
            print(f"[OK {status}] {rel}  ({op}, sha={new_sha})")
            ok += 1
        else:
            msg = data.get("message", str(data))[:120]
            print(f"[FAIL {status}] {rel}: {msg}")
            fail += 1
    print(f"\n=== 推送完成: {ok} OK / {fail} FAIL / {skip} SKIP ===")


if __name__ == "__main__":
    main()
