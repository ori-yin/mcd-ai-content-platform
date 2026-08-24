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

| 原模块 | 处理 | 新位置 |
|---|---|---|
| `data.py` parse_message / _map_columns | 直接复用 | `services/data_loader.py` |
| `analyzer.py` tokenize / diagnose_score | 抽纯函数 + 替 cache | `services/text_analyzer.py` |
| `ai_service.py` provider + JSON 解析 | thin wrapper | `adapters/llm_adapter.py` |
| `config.py` 颜色 token + axis_rate | 直接复用 | `ui/theme_tokens.py` |
| `advanced.py` 缺的 4 分析 | **从零实现** | `services/analytics/*.py` |
| `app.py` / `inject_css` | **不复用** | 重写为 `pages/` + `ui/styles.py` |

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
- **下一步**：Phase 2（copy-analyzer Adapter抽离 + 4 个缺失分析从零实现）

---

## 6. 待办

### Phase 1 — CTR Adapter（核心复用层） ✅ 已完成
- [x] 抽 `get_baseline_ctr` / `get_time_multiplier` / `build_context_for_llm` 等到 `adapters/ctr_predictor_adapter/`
- [x] 拆 `call_llm_batch` 为 `enrich_rows_for_llm` + `ProviderRouter`
- [x] 写 `PredictionResult` dataclass + `CTRPredictionAdapter` 接口
- [x] `tests/test_ctr_adapter.py` + verify.py 用例（verify.py 82 用例全过；pytest 版按 CLAUDE.md §4.4 留待 Phase 2/3 接服务层一起补）

### Phase 2 — copy-analyzer Adapter（待开始）
- [ ] 抽 `data.py` / `analyzer.py` / `ai_service.py` 纯函数
- [ ] 从零实现 4 个缺失分析（高效 plan / 相似 plan / 每日趋势 / Owner 对比）

### Phase 3 — 业务页面
- [ ] `pages/01_content_studio.py` 三栏主流程
- [ ] `pages/02_copy_diagnosis.py` 文案诊断（CTR 入口 B）
- [ ] `pages/03_batch_evaluation.py` 批量评估（CTR 入口 C）
- [ ] `pages/04_historical_insights.py` 历史洞察
- [ ] `services/rule_engine.py` + `services/generation_service.py` + SQLite

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

### OneDrive + git
`C:\ideon` 不是 OneDrive 同步目录，git 正常。搬 OneDrive 后按 memory `feedback-onedrive-git` 恢复。

### setup_and_run.bat 双标签（2026-08-24 实战）
`start "" explorer.exe "http://..."` + `streamlit --server.headless=false` → 各开一个浏览器 tab。
正确做法：删 explorer 行，让 Streamlit 自己用 webbrowser 模块开浏览器（headless=false 默认行为）。

### PowerShell 编码
Windows 上 WriteAllText+UTF8Encoding($false)。Claude Code Write 工具默认 UTF-8 无 BOM，OK。

### github 推送
直连 `github.com`，gh-proxy.com 反代已 403。本地分叉用 `--force-with-lease`。

---

## 8. 关键路径速查

| 路径 | 用途 |
|---|---|
| `C:\ideon\mcd-ai-content-platform\` | 新项目根 |
| `C:\ideon\mcd-ai-content-platform\PRD.md` | v2.1（1410 行） |
| `C:\ideon\mcd-ai-content-platform\CLAUDE.md` | 给 AI 看的项目说明 |
| `C:\ideon\mcd-ai-content-platform\data\ctr_baseline.json` | 7 维度基准（v3.0） |
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
