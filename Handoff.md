# mcd-ai-content-platform — Handoff

> 新会话第一步：读 `Handoff.md` + `CLAUDE.md` + `PRD.md` §4.0 / §13.5 / §15.A。
> 范式：`C:\ideon\mcd-copy-analyzer\Handoff.md`（精简版）。

---

## 1. 一句话

整合 `mcd-copy-analyzer`（文案分析）+ `mcd-ctr-predictor`（CTR）+ PRD（AI 生成）的 Streamlit 内网工作台。`C:\ideon\mcd-ai-content-platform\`，端口 **8510**。

---

## 2. 决策与约束

| 维度 | 决策 |
|---|---|
| 复用策略 | Adapter 模式：import 旧项目纯函数 + thin wrapper + 配置复一份 |
| 旧项目 | `mcd-copy-analyzer` / `mcd-ctr-predictor` 保持独立运行，不修改源 |
| Provider | 内网 LLM（OpenAI 兼容）；无 Key 降级 Demo |
| CTR 模式 | `existing_predictor` / `baseline_only` / `demo` / `unavailable` |
| 数据契约 | `data/ctr_baseline.json`（v3.0，7 维度）+ 词典 + frameworks |

**红线**：页面层不得 import 旧项目；CTR 四态分明；不复制整个旧文件到新项目；UI 不放 emoji。

---

## 3. 复用清单

### 3.1 mcd-copy-analyzer

| 原模块 | 处理 | 新位置 | 状态 |
|---|---|---|---|
| `data.py` parse_message / _map_columns | 直接复用 | `services/data_loader.py` | ✅ Phase 2 |
| `analyzer.py` tokenize / diagnose_score | 抽纯函数 + 替 cache | `services/text_analyzer.py` | ✅ Phase 2 |
| `ai_service.py` provider + JSON 解析 | thin wrapper | `adapters/llm_adapter.py` | ✅ Phase 2 |
| `config.py` 颜色 token + axis_rate | 直接复用 | `ui/theme_tokens.py` / `ui/plotly_helpers.py` | ✅ Phase 0 |
| `advanced.py` 缺的 4 分析 | **从零实现** | `services/analytics/*.py` | ✅ Phase 2 |
| `app.py` / `inject_css` | **不复用** | 重写为 `pages/` + `ui/styles.py` | ⏳ Phase 3 |

### 3.2 mcd-ctr-predictor

| 原函数 | 行号 | 新位置 |
|---|---|---|
| `get_baseline_ctr` | 54-85 | `adapters/ctr_predictor_adapter/baseline_lookup.py` |
| `get_time_multiplier` | 88-120 | 同上 |
| `build_context_for_llm` | 205-251 | `adapters/ctr_predictor_adapter/prompt_builder.py` |
| `call_llm_batch` | 255-365 | 拆 `enrich_rows_for_llm` + `ProviderRouter` |
| `auto_detect*` + 8 组别名 | 449-477 | `adapters/ctr_predictor_adapter/column_mapping.py` |
| `get_char_range` + `count_chars` + `suggest_char_range` | 159-201 | `adapters/ctr_predictor_adapter/char_utils.py` |
| `OPTIMAL_CHARS` / `CHANNEL_KEYS` | 40-49 | `adapters/ctr_predictor_adapter/constants.py` |
| `calibrate_baseline.py` | 整体 | `tools/calibrate_baseline.py` |
| `tests/verify.py` 模式 | 整体 | 升级为解耦版 |

---

## 4. 设计原则

1. Adapter 隔离旧项目（业务层只依赖 `adapters/` 和 `services/`）
2. 配置化优于硬编码（渠道规则/禁用词/Prompt 在 `config/` 和 `prompts/`）
3. Demo 模式零依赖（`APP_MODE=demo` 必须能跑通完整流程）
4. CTR 四态分明（model_prediction / baseline_only / demo / unavailable）
5. 本地能做的全做（没 API Key 也能用 80%）
6. AI 只生成候选（人工最终决定，PRD §3.3）

---

## 5. 决策记录

- **2026-08-24**：项目立项，PRD v2.0 + 3 处补充（§4.0 CTR 三入口 / §13.5 Adapter 策略 / §15.A 工程化配套）
- **2026-08-24**：端口 8501 → 8510（避让旧项目）；setup_and_run.bat 多次重写（v1 chcp 闪退 → v2 netstat 闪退 → v3 activate.bat 损坏 → v4 GBK 编码 → **v5 跳过 venv，用系统 Python**）
- **2026-08-24**：Phase 1 完成（commit `dc831b0` Phase 1a + `bf1db9b` Phase 1b）；82 verify.py 用例全过；GitHub ori-yin/mcd-ai-content-platform 公开仓库
- **2026-08-24**：修复 setup_and_run.bat 双标签 bug——删除 `explorer.exe` 行，让 Streamlit `--server.headless=false` 自动开浏览器
- **2026-08-24**：Phase 2 完成（commit `99ee282` 抽 copy-analyzer Adapter + `b44d85d` verify.py 152 用例）；新增 services/ + services/analytics/ + adapters/llm_adapter.py；Handoff §3.1 复用清单加状态列（✅/⏳）
- **2026-08-24**：修复 setup_and_run.bat 第 6 次闪退——LF 换行改 CRLF（commit `25b1a30`）；新铁律：所有 Windows bat 必须 CRLF（Write 工具默认 LF 是陷阱）
- **2026-08-24**：Phase 3.1 基础设施——6 service + 2 prompt + 1 repository + 2 yaml + core/schemas 增补 + ui/styles 增 6 class；`tests/verify.py` 152 → 222 PASS
- **2026-08-24**：Phase 3.2 页面 + 多页——`pages/01_content_studio.py` 三栏主流程 + `pages/02-04_*.py` Phase 4 占位 + `app.py` 改 pages/ 自动发现入口（修复 st.Page 自引用递归 bug）；`tests/verify.py` 222 → 230 PASS
- **2026-08-26**：Phase 4 完成——`pages/02_copy_diagnosis.py`（入口 B 单条诊断 + 规则/词语/相似/CTR/AI 改写五位一体）+ `pages/03_batch_evaluation.py`（入口 C CSV/Excel 批量评估 + 结果导出）+ `pages/04_historical_insights.py`（七 Tab 洞察：高效 Plan/高低词/Emoji/字数/相似/趋势/Owner）+ `services/batch_evaluation_service.py` 新建；01 渠道预览从占位升级到高保真（加品牌头部 + 渠道特征）；`tests/verify.py` 230 → 290 PASS（新增 §31/§32/§33 共 60 用例）；额外产出 `docs/feedback-ctr.md`（CTR 反哺闭环思考笔记）+ 评审并改写 `Downloads/PRD-content-gen-demo.md` v0.1 → v0.2
- **2026-08-26**：CTR Adapter bug 修复——`adapters/ctr_predictor_adapter/_demo_pred` 在 `_bl_str="未知"` 时 `bl*100` 抛 TypeError，新增 bl=None 兜底分支；`services/ctr_prediction_service.predict_one` 重写，不构造 Candidate（避免 id=A/B/C 限制），直接走 row dict 路径；`services/copy_analysis_service.diagnose` 补 problems/suggestions 字段（调 diagnose_problems 拼装）
- **2026-08-26**：Phase 5 完成——CTR 反哺闭环最小三件套 P0+P1+P2：
  - **P0 record 指纹**：`core/schemas.task_signature()` SHA1 截 12 位（channel/coupon/plan_type/audience/stage/scene + 标题桶/正文桶）；`generation_service.build_record` 自动算；`sqlite_repository` 老库自动 `ALTER TABLE ADD COLUMN signature` + 建索引（PRAGMA table_info 检查）
  - **P1 feedback 库**：`repositories/feedback_repository`（SQLite `data/feedback.db`）+ `services/feedback_service`（CSV/Excel 解析 + 列名别名 + 兜底签名）+ `pages/05_feedback`（上传 + 汇总 + 与 generation_records join 检查）
  - **P2 baseline 校准自动化**：`tools/calibrate_baseline.py` 三段策略——`n_plans<5` 跳过 / `5≤n_plans<20` 指数滑动 α=0.3 / `n_plans≥20` 全量覆盖；输出 `data/ctr_baseline_v3.x.json` + `.bak` 备份；`--dry-run / --min-reach / --db / --baseline` CLI
  - **token 教训**：`tools/push_via_api.py` 硬编码 GitHub token 触发 secret scanning 阻断 push，改成读环境变量 `GITHUB_TOKEN` / `GH_TOKEN` + `--token` 命令行参数；force-with-lease 推上去（远端 6 个重复 Phase 4 commit 被覆盖）
  - verify.py 290 → **339 PASS, 0 FAIL**（新增 §34 record指纹 11 + §35/§36 feedback_repository + feedback_service 20 + §37 calibrate_baseline 16）
- **下一步**：Phase 6（按 docs/feedback-ctr.md §5 待办：维度权重 yaml / 端到端流程串联 / 历史洞察签名关联）

---

## 6. 待办

### Phase 1 — CTR Adapter（核心复用层） ✅ 已完成
- [x] 抽 `get_baseline_ctr` / `get_time_multiplier` / `build_context_for_llm` 等到 `adapters/ctr_predictor_adapter/`
- [x] 拆 `call_llm_batch` 为 `enrich_rows_for_llm` + `ProviderRouter`
- [x] 写 `PredictionResult` dataclass + `CTRPredictionAdapter` 接口
- [x] `tests/test_ctr_adapter.py` + verify.py 用例（verify.py 82 用例全过；pytest 版按 CLAUDE.md §4.4 留待 Phase 2/3 接服务层一起补）

### Phase 2 — copy-analyzer Adapter + 缺失分析 ✅ 已完成
- [x] 抽 `data.py` 纯函数 → `services/data_loader.py`（load_sheet / map_columns / parse_message / build）
- [x] 抽 `analyzer.py` 纯函数 + 替 `@st.cache_data` → `services/text_analyzer.py`（@functools.lru_cache 仿 ctr_predictor_adapter 模式）
- [x] `dict_counts(staging_dict, staging_ban)` 改为参数注入（UI 层从 session_state 取出传入）
- [x] 抽 `ai_service.py` 纯函数 → `adapters/llm_adapter.py`（call_llm 接收 ProviderRouter，不直接 SDK）
- [x] 从零实现 4 个缺失分析 → `services/analytics/`（rank_plans / find_similar_plans / daily_aggregate / owner_compare）
- [x] verify.py 加 11 个测试函数（§13-23）共 70 用例；总计 **152 PASS, 0 FAIL**

### Phase 3 — 业务页面（进行中）
- [x] `services/rule_engine.py` — 字数 / 必带 / 禁词 / 风险词 / 格式 / 重复 6 类规则，Pass/Warn/Fail 三态
- [x] `services/generation_service.py` — Demo 模式稳定占位 + LLM 模式（router 注入）
- [x] `services/ctr_prediction_service.py` — 包 CTRPredictionAdapter
- [x] `services/similarity_service.py` — 包 find_similar_plans
- [x] `services/copy_analysis_service.py` — 包 diagnose_score
- [x] `services/record_service.py` + `repositories/sqlite_repository.py` — SQLite `data/records.db`
- [x] `prompts/copy_generation.py` + `prompts/copy_rewrite.py` — Prompt 版本管理 v1.0
- [x] `config/channel_rules.yaml` + `config/brand_rules.yaml` — 渠道字数 / 必带 / 风险 / 禁词
- [x] `core/schemas.py` 增补 — `TaskInput` / `Candidate` / `RuleItem` / `RuleResult` / `GenerationRecord`
- [x] `ui/styles.py` 增 6 class — candidate-card / rule-pass/rule-fail/rule-warn / preview-card / kpi-tile / warning-banner
- [x] `pages/01_content_studio.py` 三栏主流程（PRD §4.1）
- [x] `pages/02_copy_diagnosis.py` + `03_batch_evaluation.py` + `04_historical_insights.py` Phase 4 占位
- [x] `app.py` 改 `pages/` 自动发现入口（避 st.Page 自引用递归 bug）

### Phase 4 — 三个业务页面实现 ✅ 已完成（2026-08-26）
- [x] `pages/02_copy_diagnosis.py` — 输入 title/body/channel → 规则 + 词语 + 相似 + CTR 入口 B + AI 改写
- [x] `services/batch_evaluation_service.py` — CSV/Excel 解析 + 批量评估（rule + CTR + 建议）+ CSV 导出
- [x] `pages/03_batch_evaluation.py` — 上传 → 预览 → 进度条评估 → 结果表 + 汇总 + 下载
- [x] `pages/04_historical_insights.py` — 七 Tab 洞察（rank_plans / word_frequency / emoji_frequency / title_len / find_similar_plans / daily_aggregate / owner_compare）
- [x] 01_content_studio 渠道预览升级：APP Push 加 McDonald's + 时间戳头；企微加品牌头；短信加发件人号；站内信加品牌头
- [x] CTR Adapter bug 修复：`_demo_pred` 在 `_bl_str="未知"` 时 bl=None 兜底；`predict_one` 重写不走 Candidate
- [x] `services/copy_analysis_service.diagnose` 补 problems/suggestions 字段
- [x] verify.py 290 PASS（新增 §31/§32/§33 共 60 用例）
- [ ] pytest 版测试（CLAUDE.md §4.4 留待 Phase 5 接 feedback.db 一起补）

### Phase 5 — CTR 反哺闭环（最小闭环 P0+P1+P2）✅ 已完成（2026-08-26）
- [x] **P0 record 指纹**：`core/schemas.task_signature()` + `GenerationRecord.signature` + sqlite_repository 自动迁移加列 + 索引
- [x] **P1 feedback 库**：`repositories/feedback_repository` + `services/feedback_service` + `pages/05_feedback.py`
- [x] **P2 baseline 校准自动化**：`tools/calibrate_baseline.py` 三段策略 + `data/ctr_baseline_v3.x.json` 多版本化 + .bak 备份
- [x] `tools/push_via_api.py` 修 token 泄露（改读环境变量）
- [x] verify.py 339 PASS, 0 FAIL（新增 §34/§35/§36/§37 共 47 用例）
- [ ] `config/dimension_weights.yaml`（留 Phase 6）
- [ ] 历史洞察页签 signature 关联展示（留 Phase 6）

### 待业务确认（PRD §26，12 项）
第一场 Demo 主渠道 / 人群-阶段-场景枚举值 / 字数上限 / 禁用词清单 / 校准状态 / 内网 LLM 接口 / 企微 1v1 预览支持 / 完整文案存储

---

## 7. 教训（避坑）

### `setup_and_run.bat` 闪退 5 次迭代（2026-08-24 实战）

**最终方案 v5**：跳过 venv，用系统 Python（依赖已装好），`python -m streamlit run app.py`。

**失败历史**：
1. **v1 chcp 65001 闪退**：Win11 cmd 子系统切换 UTF-8 在某些环境崩
2. **v2 netstat -ano 找不到**：Win11 默认禁用 netstat
3. **v3 `call venv\Scripts\activate.bat` 损坏**：venv 损坏导致 cmd 把 activate.bat 内容当命令执行（`'form' / 'use' / 'ho' 不是内部命令`）
4. **v4 GBK 编码问题**：脚本含中文，cmd 用 GBK 解码乱码
5. **v5 跳过 venv**：系统 Python 已有依赖，直接 `python -m streamlit run`

**铁律**：bat 文件**只用 ASCII**（含 `setlocal enabledelayedexpansion` 支持 `!VAR!`）；每个 `exit /b` 前 `pause`；最后成功也 `pause`；不依赖 `where` / `netstat`，用 PowerShell 替代。

### bat 文件 LF vs CRLF 换行符（2026-08-24 实战第 6 次闪退）

**症状**：v5 bat 跑起来报 `'form' / 'dexpansion' / 'Platform' / 'k' 不是内部或外部命令`，cmd 把整段当一行命令执行。

**真因**：bat 文件用 LF（`\n`）换行，cmd **严格要求 CRLF**（`\r\n`）。Write 工具默认 UTF-8 LF，commit 时 git 还提醒 `LF will be replaced by CRLF`——但当时没人注意到这个 warning 已经把文件存成了 LF。

**检测**：`grep -c $'\r' setup_and_run.bat` ≥ 1 才是 CRLF，= 0 是 LF-only 闪退风险。

**修复**（一次性 Python 脚本）：
```python
p = 'setup_and_run.bat'
content = open(p, 'rb').read()
fixed = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
open(p, 'wb').write(fixed)
```

**铁律**：所有 Windows bat 必须 **CRLF**；新建 bat 后立刻 `grep -c $'\r' 文件.bat` 验证 ≥ 1，否则必闪退。

### OneDrive + git
`C:\ideon` 不是 OneDrive 同步目录，git 正常。搬 OneDrive 后按 memory `feedback-onedrive-git` 恢复。

### setup_and_run.bat 双标签（2026-08-24 实战）
`start "" explorer.exe "http://..."` + `streamlit --server.headless=false` → 各开一个浏览器 tab。
正确做法：删 explorer 行，让 Streamlit 自己用 webbrowser 模块开浏览器（headless=false 默认行为）。

### analyzer.py → text_analyzer.py 脱 Streamlit（2026-08-24 实战）
- `@st.cache_data` 全替 `@functools.lru_cache(maxsize=N)`，注意 frozenset 不能放 lru_cache（需 tuple 装返回）+ 字典读 file 时路径要 fallback（参数注入）
- `dict_counts()` 旧实现读 `st.session_state` 返回实时 staging 数。脱 Streamlit 后改成 `dict_counts(staging_dict=None, staging_ban=None)`，UI 层从 `st.session_state.get(...)` 取出传入——保持语义不变、不丢功能
- `frozenset` 替 `set`：放进 pandas `apply(axis=1)` 的 Series 时，**frozenset 比 set 安全**（避免 set 在 dataframe 操作中被冻结抛 Unhashable）

### diagnose_problems 参数陷阱（2026-08-24 实战）
`diagnose_score(...)` 返回 `{"diag": local_diagnose_dict, ...}`。调用 `diagnose_problems(title, body, diag)` 时 `diag` 必须是 **local_diagnose dict**（含 `len_title` / `len_body` / `emoji_count` / `hit_words` / `miss_top`），不是 score 顶层 dict。
- 正确写法：`diagnose_problems(t, b, score_result["diag"])`
- 错误写法：`diagnose_problems(t, b, score_result)` → `KeyError: 'len_title'`

### Candidate.id=A/B/C 校验（2026-08-26 实战）
`Candidate.__post_init__` 强制 id ∈ {"A","B","C"}（PRD §9.2 输出 schema）。所以 `predict_one` 之类的入口 B 不能走 Candidate 包装，必须直接构造 row dict 调 `adapter.predict_batch`：
- 错：`Candidate(id="X", strategy="diagnose", ...)` → `ValueError`
- 对：`adapter.predict_batch([{"channel":..., "title":..., "body":..., ...}])`

### CTR Adapter _demo_pred bl=None 兜底（2026-08-26 实战）
原 `_demo_pred` 第 184 行直接 `bl*100:.2f`，但 `baseline_lookup` 找不到维度组合时 `_safe_ctr("未知")` 返回 None，`None*100` 抛 TypeError。
- 入口 B 触发率 100%（无历史数据时必然 bl=None）
- 修复：bl=None 时显示"无基准"；pred_ctr 兜底 0.02

### verify.py CSV bytes literal 限制（2026-08-26 实战）
Python `b"..."` 字面量只能含 ASCII。中文字符串测试数据要 `.encode("utf-8")`：
- 错：`b"title,body,channel\n标题,内容,APP Push\n"` → `SyntaxError`
- 对：`"title,body,channel\n标题,内容,APP Push\n".encode("utf-8")`

### GitHub secret scanning 阻断 push（2026-08-26 实战）
`tools/push_via_api.py` 硬编码 GitHub PAT 触发了 GitHub 的 secret scanning 规则 → push 被 `remote rejected`。
- **症状**：`error: failed to push some refs ... (push declined due to repository rule violations)` + `path: tools/push_via_api.py:17` 提示"remove secret from commit(s)"
- **修复**：token 改成从环境变量 `GITHUB_TOKEN` / `GH_TOKEN` 读，或 `--token` CLI 参数；amend commit 覆盖后 force-with-lease 推上去
- **铁律**：任何工具脚本里**不要硬编码 token / API key / 私有证书**——既不安全也会被 GitHub 阻断 push

### verify.py 用例数从 82 → 152（2026-08-24 实战）
Phase 2 新增 11 个测试函数（§13-23，共 70 用例）。跑测试要 `PYTHONIOENCODING=utf-8`，否则 `_check()` 的 emoji 中文会撞 GBK codec（不是 bug，但中断 print 流导致用例数不准）。

### PowerShell 编码
Windows 上 WriteAllText+UTF8Encoding($false)。Claude Code Write 工具默认 UTF-8 无 BOM，OK。

### github 推送
直连 `github.com`，gh-proxy.com 反代已 403。本地分叉用 `--force-with-lease`。

### st.Page("app.py") 自引用递归（2026-08-24 实战）
`app.py` 用 `st.navigation([st.Page("app.py", ...), ...])` + `pg.run()` → `RecursionError: maximum recursion depth exceeded`。Streamlit 把 app.py 自己也当页面执行，每次 exec 都会再调 pg.run() → 无限递归。

**修法**：app.py 只保留入口配置（`set_page_config` + `inject_base_css`），首页内容挪到 `pages/00_home.py`，用 `pages/` 自动发现（Streamlit 默认行为），**不要在 app.py 调 st.navigation / st.Page**。

### Python 字符串嵌套双引号（2026-08-24 实战）
LLM prompt 字符串里要嵌"引用"，**别直接 `"...\"X\"..."` 配 `\"` 转义**，Claude Code Write 工具容易错位导致 SyntaxError。

**修法**：用中文「」替代英文双引号——`"突出「专属」+「福利」命中企微 1v1 必带词"`。可读性更好且无转义负担。涉及：`services/generation_service.py:70` + `prompts/copy_rewrite.py:29/33`。

### Candidate.title 允许为空（2026-08-24 实战）
短信 / 企微 1v1 无独立标题，PRD §8.2 显式允许。`core/schemas.py:265` 校验必须放：`if not self.body.strip()`，**不要带 title 校验**。验证测试也要相应改成"title 空不抛错"。

---

## 8. 关键路径速查

| 路径 | 用途 |
|---|---|
| `C:\ideon\mcd-ai-content-platform\` | 新项目根 |
| `C:\ideon\mcd-ai-content-platform\PRD.md` | v2.1（1410 行） |
| `C:\ideon\mcd-ai-content-platform\CLAUDE.md` | 给 AI 看的项目说明 |
| `C:\ideon\mcd-ai-content-platform\data\ctr_baseline.json` | 7 维度基准（v3.0） |
| `C:\ideon\mcd-ai-content-platform\data\records.db` | 生成记录 SQLite（自动建） |
| `C:\ideon\mcd-ai-content-platform\config\channel_rules.yaml` | 4 渠道字数上限 |
| `C:\ideon\mcd-ai-content-platform\config\brand_rules.yaml` | 必带 / 风险 / 禁词 |
| `C:\ideon\mcd-ai-content-platform\prompts\copy_generation.py` | 生成候选 prompt v1.0 |
| `C:\ideon\mcd-ai-content-platform\prompts\copy_rewrite.py` | 改写 prompt v1.0 |
| `C:\ideon\mcd-ctr-predictor\ctr_predictor.py` | CTR 事实来源 |
| `C:\ideon\mcd-copy-analyzer\analyzer.py` | 文案分析事实来源 |
| `C:\ideon\mcd-copy-analyzer\Handoff.md` | 范式参考 |

---

## 9. 新 Session 第一步

1. 读本 Handoff（项目记忆）
2. 读 `CLAUDE.md`（架构 + 约束）
3. 读 `PRD.md §4.0 / §13.5 / §15.A`（三处补充）
4. 跑 `python tests/verify.py`（82 用例）
5. 看 `.claude/agents/` 3 个 sub-agent
6. 当前是 **Phase 1 已完成，Phase 2 待开始**

---

## 10. Self-check

- [ ] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）
- [ ] `python tests/verify.py` 全过
- [ ] `python -m py_compile $(git ls-files '*.py')` 全过
- [ ] 关键改动进 commit（如 git 化）
- [ ] UI 无 emoji，沟通全中文
