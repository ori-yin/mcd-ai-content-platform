# mcd-ai-content-platform — 教训（避坑全集）

> **何时读我**：写代码踩了坑 / 准备做新模块前，按关键词搜这里。
> **本文件已压缩**（2026-08-31）：从 18 条精简到 8 条核心教训；删阶段性 bug + git log 已有的细节。

---

## 8 条核心教训

### 1. dataclass 字段顺序铁律（Phase 6 P1）

Python dataclass：**所有带默认值的字段必须在所有无默认值的字段之后**。
- 坑：`product_benefit` 改 `str = ""` 但忘了挪位置 → `TypeError: non-default argument 'audience' follows default argument 'product_benefit'`
- 铁律：改默认值前 (1) 看字段顺序、(2) 不要默认空串和 no-default 混、(3) 跑全套 verify.py 别靠肉眼

### 2. Streamlit widget 灰态 4 件套（Phase 6 P1）

决策要求"整体降透明度 + 右上角小角标 + hover tooltip"，Streamlit 没暴露 widget 级 opacity 钩子。**实用近似**：
1. `disabled=True`（控件灰化）
2. label 加「待开发·二期接入」（文字角标）
3. `help="后续开放..."`（hover tooltip）
4. 顶部 banner（`.advanced-notice`）+ 00_home 卡片分组

覆盖 > 90% 场景，剩下 10% 视觉差没必要追 100% CSS 还原。

### 3. `@lru_cache` + 测试 monkey-patch 陷阱（Phase 6 P3）

`_load_yaml()` 加 `@lru_cache(maxsize=1)` 后，测试改路径但 cache 仍命中旧路径 → 3 个 `_check` 全 FAIL。
- 修：测试 monkey-patch `CONFIG_PATH` 后必调 `ls._load_yaml.cache_clear()`
- 铁律：`lru_cache` 按参数 hash，**闭包内全局变量不在 hash key 里**

### 4. 手写 yaml 解析器 vs PyYAML（Phase 6 P3）

`ui/llm_status.py` v1 用 30 行手写解析（整行注释/行内注释/引号/空串 4 类边界）→ `yaml.safe_load` 1 行替（PyYAML 已在 requirements.txt）。
- 铁律：项目里已有 yaml 用法就别造轮子；新模块加载 yaml 前先 grep `yaml.safe_load` 是否有先例

### 5. GitHub secret scanning 阻断 push（Phase 5）

`tools/push_via_api.py` 硬编码 GitHub PAT 触发 secret scanning → push 被 `remote rejected`。
- 修：token 读环境变量 `GITHUB_TOKEN`/`GH_TOKEN` 或 `--token` CLI；amend commit + force-with-lease
- 铁律：工具脚本里**不要硬编码 token / API key / 私有证书**

### 6. CTR 学习 ≠ 复杂模型 · 务实主义（§5.5 衍生）

场景硬约束：结构化表格 + 中样本 + 可解释是刚需 → **LightGBM/XGBoost 几乎无悬念**；DeepFM/DIN/Transformer 全是过度设计。
- 铁律：加新模型前问三句——(1) 这是结构化还是非结构化？(2) 样本量级够哪个量级？(3) 可解释是不是刚需？三句里 2 句答"结构化/中样本/是"，**别上深度**

### 7. st.Page("app.py") 自引用递归（Phase 3.2）

`app.py` 用 `st.navigation([st.Page("app.py")])` + `pg.run()` → `RecursionError: maximum recursion depth exceeded`。
- 修：app.py 只保留入口配置（`set_page_config` + `inject_base_css`），首页挪 `pages/00_home.py`，用 `pages/` 自动发现（Streamlit 默认行为）

### 8. bat 文件必须 CRLF（Phase 3.2 第 6 次闪退）

cmd 严格要 CRLF；Write 工具默认 LF。
- 检测：`grep -c $'\r' 文件.bat` ≥ 1 才是 CRLF，= 0 是 LF-only 闪退风险
- 修：一次性 Python 脚本 `b'\n' → b'\r\n'`
- 铁律：所有 Windows bat 必须 CRLF；新建 bat 后立刻验证

---

## 已删（详见 git log 早期 commit / memory）

| 类别 | 删节项 |
|---|---|
| setup_and_run.bat 闪退 | v1-v5 各版详细失败原因 |
| analyzer → text_analyzer 脱 Streamlit | @st.cache_data → lru_cache / frozenset 替代 set 的细节 |
| 小 bug | diagnose_problems 参数陷阱 / Candidate.id=A/B/C 校验 / Candidate.title 允许为空 / CTR Adapter _demo_pred bl=None 兜底 / verify.py CSV bytes literal 限制 |
| 工具 | PowerShell 编码（WriteAllText+UTF8Encoding($false)）/ OneDrive + git 恢复（按 memory `feedback-onedrive-git`）/ github 推送（直连 github.com，分叉用 `--force-with-lease`）/ Python 字符串嵌套双引号（用中文「」替） |
| 极简 yaml 解析 | 行内 # 注释陷阱——已被第 4 条 PyYAML 替覆盖 |
| 决策文档驱动开发 | 接活前 grep `/c/Users/a952462/Downloads/` 找决策 md（已写入 Handoff.md §9 新 Session 第一步） |
| verify.py 用例数演进 | 82→152→...→854（简化为 Handoff.md §6.0 速查） |
