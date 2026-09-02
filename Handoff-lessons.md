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

### 9. 会话间记忆丢失：跑分析不写 Handoff = 等于没跑（2026-08-31）

**防**：
- 每次跑完 EDA / SHAP / 维度统计 / 业务指标分析 → 强制落档 `data/findings/<topic>_<date>.json + .md`
- Handoff.md §6.5 维护一个**历史发现索引**（path + 一句话结论）
- 每次开新 session 第一步：grep §6.5 看有没有遗漏
- 工具脚本必须复用现有解析，不重新实现

**铁律**：跑完不写 Handoff = 没跑。落档路径必须有规律（`data/findings/` 不是 `tmp/`）。

### 10. UI 标签 vs selectbox value 分离（2026-09-01 · Phase 27 漏改）

**坑**：Phase 27 把 CTR 模式 UI 标签改成产品话术（`演示规则/渠道基线/XGBoost`）时，**selectbox 的 `value` 也跟着写成 `xgboost`**，但 `CTRPredictionAdapter.VALID_MODES = ('existing_predictor', 'baseline_only', 'demo', 'l1_model', 'unavailable')` 只认 `l1_model`。前端能选、后端拒收、用户看 500 Internal Server Error。

**表现**：`POST /api/studio/generate` 走 `api_01_generate` → `predict_for_candidates(..., mode=ctr_mode)` → `CTRPredictionAdapter(mode=ctr_mode)` 抛 `ValueError: mode must be one of ...`，冒到 FastAPI 默认 handler 返回 500。

**铁律**：
- UI 改标签（display text）时，**selectbox 的 `value=` 必须保持后端能识别的常量**（display 和 value 解耦）
- 改 UI 文案前后，**grep VALID_MODES / VALID_* 等后端枚举常量**，确认 selectbox value 没漏
- 涉及 `CTRPredictionAdapter` / `LLM_PROVIDERS` / `CHANNELS` / `PLAN_TYPES` 等枚举常量的 UI 修改，**改完必须 curl 跑一遍主路径**（不能只肉眼看 UI 标签对不对）

**副坑**：uvicorn `--reload` 在 Windows 上常失效，**改完代码必须手动重启 server** 才生效（setup_and_run.bat 默认不带 `--reload`，所以双击 bat 是最稳的方式）。

### 11. Handoff 数字漂移 =「schema 改 → verify.py 同步改」铁律失效（2026-09-01 · Phase 38 A1-mid 复盘）

**坑**：Handoff §6.0 写 `847 PASS / 0 FAIL`，实际跑是 `842 PASS / 5 FAIL`。Phase 28 / Phase 30 改 schema 时 verify.py 没同步 5 处断言（必填 4→3 / PLAN_TYPES 3→4 / options_with_custom +1→+2 / llm_status 默认测试用真实 yaml / sweep stage 必填 → 选填）。

**铁律**：
- **schema / enum / 必填字段改动 → verify.py 同步改是「改文件清单」的硬约束**，不是「下次再说」
- 改 `ui/llm_status.py` / `core/product_benefit.py` 等带 lru_cache 的模块 → 测试必须 monkey-patch + cache_clear，**闭包变量不入 hash key**
- Handoff §6.0 数字每次写必现场跑一次（**不引用旧数字**）

**避坑指引**：
- 改 `core/schemas.py` 任何字段、enum、默认值 → 必跑 `python tests/verify.py`，有 FAIL 就修
- design.md §12.1 写明此坑；新 session 第一步 grep Handoff §6.0 数字 + 现场跑 verify，数字对不上就查 lessons

### 12. 跨文件改动必须「改一个测试一个」（2026-09-01 · Phase 38 A1-mid 流程教训）

**坑**：本次 A1-mid 一开始想「先改 CSS 全部 → 一次性 verify」，结果中间出了 1 处遗漏 inline（03 line 41）。如果**改完一类就 grep lint + verify**，能立刻发现。

**铁律**：**每次 Edit 完一个文件 → 立刻跑针对该文件的小验证**（grep inline style / py_compile / verify §对应段），不要攒一批改完再测。

**避坑指引**：
- 改 HTML → grep `style="..."` 残留
- 改 Python → `python -m py_compile`
- 改 schema / enum / 必填 → 立刻跑 `python tests/verify.py`
- 全部改完 → 最后跑一次完整 verify.py + curl 6 路由

### 13. archive 嵌套的脚本 ROOT 路径需 `.parent.parent.parent`（2026-09-01 · Phase 38 A1-mid 顺手修）

**坑**：push_via_api.py 脚本从 `tools/_archive/` 跑时，`Path(__file__).resolve().parent.parent` 只到 `tools/`（不是 repo root），导致 `local.exists()` 检查错误，把"添加文件"分支走成"删除文件"分支，422 BadObjectState。

**铁律**：archive 里的脚本 `ROOT` 计算 = `.parent.parent.parent`（多一层）适配 archive 嵌套。

**避坑指引**：
- 新写 `_archive/` 下的工具脚本：直接用 `.parent.parent.parent`，不要 `.parent.parent`
- 跑 push 脚本前先 Read ROOT 计算那行，确认从 archive 跑不会走"删除"分支

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
