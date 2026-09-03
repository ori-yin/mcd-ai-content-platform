# -*- coding: utf-8 -*-
"""push_phase50.py — Phase 50 单 commit push（favicon + handoff）"""
import base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or ""
OWNER = "ori-yin"
REPO = "mcd-ai-content-platform"
BRANCH = "main"
ROOT = Path(r"C:\ideon\mcd-ai-content-platform")

FILES = [
    "web/templates/base.html",
    "Handoff.md",
]

COMMIT_MSG = (
    "feat(web): base.html 加 SVG favicon\n\n"
    "复用项目内已有 svg（与左上角 M 图同文件 358B），保证视觉一致\n"
    "现代浏览器全支持 SVG 不需要 .ico\n"
    "?v=20260903fv 主动破坏缓存\n\n"
    "Handoff.md 同步 Phase 50（§6.0 / §6.1 / §10）"
)


def get_remote_head():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}",
        headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["object"]["sha"]


def api(method, path, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-code-push-phase50")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main():
    if not TOKEN:
        sys.exit("missing GITHUB_TOKEN")

    BASE_COMMIT = get_remote_head()
    print(f"[base] remote HEAD: {BASE_COMMIT[:10]}")

    status, commit = api("GET", f"git/commits/{BASE_COMMIT}")
    if status != 200:
        sys.exit(f"GET commit failed: {status} {commit}")
    base_tree = commit["tree"]["sha"]
    print(f"[0/4] base_tree = {base_tree[:10]}")

    print(f"[1/4] POST {len(FILES)} blobs ...")
    blob_shas = {}
    for rel in FILES:
        content_bytes = (ROOT / rel).read_bytes()
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
    commit_body = {"message": COMMIT_MSG, "parents": [BASE_COMMIT], "tree": new_tree_sha}
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

    print(f"\n[Phase 50 PUSH OK] {new_commit_sha[:10]}")
    print(f"   {len(FILES)} files merged into 1 commit on top of {BASE_COMMIT[:10]}")


if __name__ == "__main__":
    main()
