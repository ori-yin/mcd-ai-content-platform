# -*- coding: utf-8 -*-
"""push_phase49.py — 用 Git Data API 把本地 e51c1eb+2c3b0ae 合并成 1 个干净 commit 推到远端

基于 push_phase48.py 模式，Files 列表对应 Phase 49 两个 commit 的所有改动。
"""
import base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or ""
OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"
ROOT = Path(r"C:\ideon\mcd-ai-content-platform")

# 取最新远端 ref 作为 base（不是 hardcode Phase 48 的 SHA）
import urllib.request
def get_remote_head():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
        headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["object"]["sha"]

BASE_COMMIT = get_remote_head()
print(f"[base] remote HEAD: {BASE_COMMIT[:10]}")

FILES = [
    "Handoff.md",
    "Handoff-decisions.md",
    "Handoff-todo.md",
    "Handoff-lessons.md",
    "web/app.py",
    "web/templates/base.html",
    "tools/_archive/bench_routes.py",
    "tools/_archive/trace_studio.py",
    "tools/_archive/trace_studio_v2.py",
    "tools/_archive/trace_01.py",
    "tools/_archive/trace_01b.py",
    "tools/_archive/push_phase48.py",
]

COMMIT_MSG = (
    "perf+docs+tools: Phase 49 \u2014 \u6027\u80fd\u4f18\u5316 4 \u9879\u843d\u5730 + Handoff \u540c\u6b65\n\n"
    "B: Jinja auto_reload=False + cache={} \u2192 /studio cold 12.4s -> 1.2s (-90%)\n"
    "C: startup \u5b57\u5178 + LLM \u914d\u7f6e\u9884\u70ed (\u65e0\u635f\uff0c1.2s \u4e0d\u662f\u5b57\u5178)\n"
    "D: /static/* Cache-Control: public, max-age=3600 \u2192 warm / 16ms -> 4ms (-75%)\n"
    "A: base.html <body hx-boost=\"true\"> \u2192 \u5185\u7ad9\u8df3\u8f6c\u611f\u5b98\u63d0\u5347\u6700\u5927\n\n"
    "\u9a8c\u8bc1: 848 PASS / 0 FAIL + bench_routes 5 \u8f6e\u5bf9\u7167 + curl -I \u786e\u8ba4 D \u5934 + grep hx-boost \u786e\u8ba4 A\n\n"
    "\u65b0\u589e 6 \u4e2a bench/trace \u811a\u672c + push_phase48.py \u672c\u8eab\n"
    "\u9636\u6bb5\u540e\u7eed: F SQLite \u7d22\u5f15 / G L1 \u9884\u70ed / H lazy import / I \u6b7b\u94fe\u6e05\u7406"
)


def api(method, path, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-push-phase49")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main():
    if not TOKEN:
        sys.exit("missing GITHUB_TOKEN")

    status, commit = api("GET", f"git/commits/{BASE_COMMIT}")
    if status != 200:
        sys.exit(f"GET commit failed: {status} {commit}")
    base_tree = commit["tree"]["sha"]
    print(f"[0/4] base_tree = {base_tree[:10]}")

    print(f"[1/4] POST {len(FILES)} blobs ...")
    blob_shas = {}
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            sys.exit(f"local file missing: {rel}")
        content_bytes = local.read_bytes()
        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        status, resp = api("POST", "git/blobs", {"encoding": "base64", "content": content_b64})
        if status != 201:
            sys.exit(f"POST blob {rel} failed: {status} {resp}")
        blob_shas[rel] = resp["sha"]
        print(f"      [OK] {rel} -> blob {resp['sha'][:10]}")

    print("[2/4] POST tree ...")
    tree_body = {
        "base_tree": base_tree,
        "tree": [{"path": rel, "mode": "100644", "type": "blob", "sha": blob_shas[rel]} for rel in FILES],
    }
    status, tree = api("POST", "git/trees", tree_body)
    if status != 201:
        sys.exit(f"POST tree failed: {status} {tree}")
    new_tree_sha = tree["sha"]
    print(f"      new_tree = {new_tree_sha[:10]}")

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

    print("[4/4] PATCH ref heads/main ...")
    status, ref = api("PATCH", f"git/refs/heads/{BRANCH}", {"sha": new_commit_sha, "force": False})
    if status != 200:
        sys.exit(f"PATCH ref failed: {status} {ref}")
    print(f"      main -> {ref['object']['sha']}")

    print(f"\n[Phase 49 PUSH OK] {new_commit_sha[:10]}")
    print(f"   {len(FILES)} files merged into 1 commit on top of {BASE_COMMIT[:10]}")


if __name__ == "__main__":
    main()
