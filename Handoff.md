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
| 数据契约 | `data/ctr_baseline.json`（v3.0，CTR 基准 **7 维**）+ 词典 + frameworks |
| 输入维度 | **5 必填 + 2 灰态**（audience/channel/stage/scene/tone 必填；product_benefit/objective 二期接入） |

**红线**：页面层不得 import 旧项目；CTR 四态分明；不复制整个旧文件到新项目；UI 不放 emoji。

---

## 3. 复用清单

旧项目 → 新项目映射**已全部完成**（Phase 1-2，✅✅）。详细映射见 `CLAUDE.md §5`；这里只保留索引。

**mcd-copy-analyzer**（6 模块全部 ✅）— data / analyzer / ai_service / config / advanced 4 分析 / app 重写  
**mcd-ctr-predictor**（9 项全部 ✅）— baseline_lookup / prompt_builder / column_mapping / char_utils / constants / calibrate 工具 / verify 模式升级，全部落到 `adapters/ctr_predictor_adapter/` 与 `tools/calibrate_baseline.py`

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
- **2026-08-26**：Phase 6 P0 完成——**业务确认 12 项过完 + 企微 1v1 聊天气泡预览 + LLM 留空 banner**：
  - **业务确认**：PRD §26 12 项全部拍板（详见 `docs/architecture.md §五` 表格）——Demo 主渠道 APP Push + 企微 1v1 同期；枚举值/字数/词表复用 yaml 配置；predictor 走 main 版；CTR 状态"未校准 / 机制就绪"；加 `confidence` 字段（PRD v0.2 §5.3 口径 A）；内网 LLM 暂留空；不存完整文案（合规稳）
  - **企微 1v1 预览**：`ui/styles.py` 新增 `.wechat-bubble-wrap`（40×40 红底 M 头像 + 白色气泡卡片 + 时间戳"今天 HH:MM · 已送达"），`pages/01_content_studio` 替换占位实现
  - **LLM 留空 banner**：新增 `config/llm_settings.yaml`（provider/base_url/model/api_key 4 字段全空占位）+ `ui/llm_status.py` 检测器（极简 yaml 解析，无 PyYAML 依赖）+ `.llm-warning` 样式（黄色左边框 banner），00_home/01/02/03 入口全加；banner 文案分两态（全空"未配置" vs 部分空"缺字段"）
  - 验证：verify.py 339 → **349 PASS, 0 FAIL**（新增 §38 llm_status 10 用例）
- **2026-08-26**：Phase 6 P1 完成——按 `Downloads/Demo范围决策与待确认_2026-08-26.md` 三件事：
  - **决策 1（6 维度前端灰态）**：`core/schemas.py` `TaskInput` 必填 7→5，把 `product_benefit` / `objective` 加默认空串挪到所有无默认字段之后（dataclass 排序铁律，见 §7 教训），加 `PENDING_FIELDS` 元组；`pages/01_content_studio` 两控件 `disabled=True` + label 加「待开发·二期接入」+ `help=` tooltip；`prompts/copy_generation.build_user_prompt` 空时不拼这两行（避免 prompt 里出现空值"产品与权益："）
  - **决策 2（4 附属页面弱化）**：新建 `ui/notice.py`（`render_advanced_notice` / `render_ctr_feedback_notice` 两个 helper）；`ui/styles.py` 加 `.advanced-notice` / `.home-section-core` / `.home-section-advanced` 三个 CSS 类；02/03 顶部仅 advanced banner；04/05 顶部 advanced + ctr 双 banner；`pages/00_home.py` 重排分组入口卡（核心大卡红底链 01 + 进阶小卡灰底链 02-05）
  - **决策 3（CTR 反哺免责）**：`render_ctr_feedback_notice` 顶部 04/05 + 00_home 进阶区明示"演示口径·业务确认前不接真实数据"；01 推荐结论原有"不代表正式投放承诺"免责话术保留（Handoff §7 教训录过）
  - **不动**：app.py（避开 st.Page 自引用递归铁律）；后端反哺逻辑（baseline 校准 / fingerprint / feedback.db 保持演示口径，等业务确认）；任何页面删除（02-05 弱化不剔除）
  - verify.py 349 → **395 PASS, 0 FAIL**（新增 §39 决策1 灰态 17 用例 + §40 决策2/3 综合 29 用例）
- **2026-08-26**：Phase 6 P2 完成——**CTR 口径固化 v3.1（业务拍板）**：
  - **Q1-Q6 拍板**：Q1 去重点击人次 / Q2 触达成功 / Q3 plan 全周期不截断 / Q4 不跨渠道聚合 / Q5 暂回退 B（min_reach>=1000 兜底，等业务标注机制就位再切 A）/ Q6 业务确认前不接真实数据
  - **取数时间基准铁律**：bi_dt T-1 快照，12 点前用 INTERVAL 2（前天），新增 `core/data_window.py` 的 `resolve_bi_dt_window()` 函数
  - **落地 6 文件**：`data/ctr_baseline.json`（v3.0 → v3.1 + `_definition_note` / `_min_reach_threshold` / `_definition_version` / `_definition_ref`）+ `adapters/ctr_predictor_adapter/baseline_lookup.py`（顶部口径注释）+ `services/ctr_prediction_service.py`（同步口径）+ `repositories/feedback_repository.py`（标注 Q1/Q2 + bi_dt）+ `tools/calibrate_baseline.py`（加 `--definition` flag 默认 v3.1，写出 `_definition_version`）+ `docs/ctr-kpi-definition-proposal-v0.2.md`（拍板稿，v0.1 保留作历史）
  - **反哺批量回灌机制**：沿用 Phase 5 管道，不做实时对接；pages/05_feedback 上传 CSV/Excel → feedback.db → signature 配对算 MAE/MAPE → calibrate_baseline 重算（L0 EMA）；样本 ≥ 1000 后切 L1 GBDT
  - **关键前提**（写入 v0.2 §5）：导出表口径必须与 Q1-Q6 完全一致，否则"真实值"是另一套定义，模型越学越歪
  - verify.py 395 → **421 PASS, 0 FAIL**（新增 §41 v3.1 口径 26 用例：basline 元数据 + 5 文件注释 + calibrate --definition + plan/record/median 三种聚合数值对比 + 4 个 bi_dt 边界场景）
  - commit `f942765`（9 文件 / +411 行 / -18 行；working tree clean）
  - **下一步**：第一梯队还剩 #3 / #6 待业务拍板；走完启 P0/P1 反哺 demo 数据回灌（业务确认前仅 demo 走通流程）
- **2026-08-26**：推送 GitHub — commit `f942765` 推到 ori-yin/mcd-ai-content-platform（公开仓库，按 memory 直连 github.com）

### §5.5 CTR 准确率学习 Roadmap（2026-08-26 · 重要背景）

**完整原文**：`Downloads\CTR准确率学习-Roadmap附录_2026-08-26.md`。**此处给执行摘要**。

**一句话**：把 CTR 从"查找表统计校准"升级到"会自我度量、会重训的回归模型"，让"**预测误差 vs 真实 CTR 曲线**"往下走。

#### 三台阶

| 台阶 | 做法 | 触发 |
|---|---|---|
| **L0（现状）** | baseline 查找表 + `calibrate_baseline.py` EMA | ✅ 已建（Phase 5 P2） |
| **L1** | LightGBM 回归替查找表（6 维 + 字数 + emoji + 命中词） | feedback 样本 ≥ ~千条 |
| **L2** | 增量重训 + 上线前回测门禁 + 误差监控 | L1 稳定后 |

#### 当前断点

```
①生成 → ②预测 → ③投放 → ④回收真实 CTR
                                ↓
                          ⑤ 重训模型（断点）
```

①②③④ Phase 5 管道已搭（P0 signature + P1 feedback + P2 calibrate），**断点在 ⑤**。

#### 落地机制（核心）

1. **存每次预测**：已用 `signature` + `confidence`
2. **回流后自动算误差**：预测 vs 真实 MAE / MAPE
3. **画误差曲线**：往下 = 在学；平/往上 = 漂移，触发重训
4. **达阈值自动重训 + 离线回测门禁**：准确率没退化才上线

**第 2、3 步（误差算 + 曲线）**L0 阶段就能做、不需要多少数据，是地基。

#### 选型铁律 · 为什么是 GBDT 不是深度学习

- 输入是**结构化表格特征** + **中样本** → LightGBM 几乎必然赢神经网络
- GBDT 出**特征重要性**（能回答"哪个维度影响 CTR"）—— 麦当劳场景可解释是刚需
- 深度 CTR 模型（DeepFM/DIN）要**亿级样本**才回本，本项目喂不饱，别上

#### 务实节奏（防过拟合）

- **短期（< 几百条）**：维持 L0 EMA；先把 §3 第 2、3 步（误差曲线）搭起来
- **中期（~ 千条）**：切 L1；现有 demo 回灌门槛 ≥ 50 plan 对 EMA 够，**训 GBDT 偏少易过拟合**
- **长期**：L2 增量重训 + 回测门禁 + 曲线监控常态化

#### 与决策文档联动

CTR 学习 ≠ 复杂模型，但**首先得有"准确率"可量化的指标**——这要先定**口径**（决策文档 #5）。口径不定，**算不出误差** → L1 全免谈。

---

## 6. 待办

> **新会话 AI 直接读这段 ↓**

### 6.0 当前快照（最快定位状态）

- **阶段**：Phase 6 P2 完成（CTR 口径固化 v3.1 拍板完成）
- **用例**：421 PASS / 0 FAIL（`python tests/verify.py`）
- **首要任务**：第一梯队剩 #3 反哺触发条件 / #6 反哺是否影响生成排序 — 详 §6.2
- **口径文档**：`docs/ctr-kpi-definition-proposal-v0.2.md`（v3.1 拍板稿）+ `docs/feedback-ctr.md`
- **不动**：业务确认前不接真实反馈数据；不启用灰态字段（product_benefit/objective）
- 详情：§5 决策记录 / §6.1 Phase 历史 / §6.2 待业务确认 / §6.3 候选

### 6.1 Phase 历史（已完成）

| Phase | 关键产出 | 用例 |
|---|---|---|
| **Phase 1** CTR Adapter 核心层 | baseline/prompt/column/char 4 模块 + `PredictionResult` | 82 |
| **Phase 2** copy-analyzer Adapter + 4 分析 | data_loader / text_analyzer / analytics（rank/similar/daily/owner） | 152 |
| **Phase 3** 业务页基础设施 + 01 主流程 | 6 service + 2 prompt + 2 yaml + sqlite repo | 222 |
| **Phase 4** 02/03/04 三业务页 | 02 单条诊断 / 03 批量评估 / 04 七 Tab 历史洞察 + 01 预览升级 + CTR Adapter bug 修 | 290 |
| **Phase 5** CTR 反哺闭环 P0+P1+P2 | record signature 指纹 / feedback 库 / baseline 自动校准 | 339 |
| **Phase 6 P0** 业务确认 + 企微 1v1 + LLM 留空 | PRD §26 12 项拍板 / wechat-bubble-wrap / llm_status.yaml + banner | 349 |
| **Phase 6 P1** 灰态 + 进阶弱化 + CTR 免责 | 6 维度前端灰态 / 4 附属页 banner / ui/notice + render_ctr_feedback_notice | **395** |
| **Phase 6 P2** CTR 口径固化 v3.1 | Q1-Q6 拍板 / bi_dt 铁律 / 6 文件落地 / 反哺批量回灌机制 | **421** |

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

### Phase 6 P0 — 业务确认 + 企微 1v1 + LLM 留空 ✅ 已完成（2026-08-26）
- [x] PRD §26 12 项业务确认全部拍板（详见 `docs/architecture.md §五` 表格）
- [x] **企微 1v1 聊天气泡预览**：`ui/styles.py` 加 `.wechat-bubble-wrap`（40×40 红底 M 头像 + 白色气泡卡片 + 时间戳），`pages/01_content_studio` 替换占位实现
- [x] **LLM 配置留空**：`config/llm_settings.yaml`（provider/base_url/model/api_key 全空占位）+ `ui/llm_status.py` 检测器 + `.llm-warning` 样式，00_home/01/02/03 入口全加 banner
- [x] verify.py 349 PASS, 0 FAIL（新增 §38 llm_status 10 用例）

### Phase 6 P1 — 6 维度灰态 + 进阶弱化 + CTR 反哺免责 ✅ 已完成（2026-08-26）
- [x] **决策 1**：6 维度前端灰态 — `product_benefit` + `objective` 控件 `disabled=True` + label「待开发·二期接入」+ help tooltip；TaskInput 必填 7→5（+ `PENDING_FIELDS`）；prompt 空时不拼这两行
- [x] **决策 2**：4 附属页面弱化 — `ui/notice.render_advanced_notice` + `.advanced-notice` CSS；02/03/04/05 顶部 banner；`00_home` 重排核心/进阶两组卡片
- [x] **决策 3**：CTR 反哺免责 — `ui/notice.render_ctr_feedback_notice` + 04/05 顶部 + 00_home 进阶区"演示口径"文案
- [x] **不动**：app.py（避 st.Page 递归铁律）/ 后端反哺逻辑 / 任何页面删除（02-05 全弱化不剔除）
- [x] verify.py 395 PASS, 0 FAIL（新增 §39 灰态 17 用例 + §40 弱化+免责 29 用例）

### Phase 6 P2 — CTR 口径固化 v3.1（业务拍板） ✅ 已完成（2026-08-26）
- [x] **Q1-Q6 拍板** — 详 `docs/ctr-kpi-definition-proposal-v0.2.md` §2
- [x] **取数铁律** — `core/data_window.resolve_bi_dt_window()` 12 点前 INTERVAL 2 兜底
- [x] **6 文件落地**：`ctr_baseline.json`（v3.0 → v3.1 + definition 注释）/ `baseline_lookup.py` / `ctr_prediction_service.py` / `feedback_repository.py` / `calibrate_baseline.py`（加 `--definition` flag）/ `docs/ctr-kpi-definition-proposal-v0.2.md`（新写，v0.1 保留作历史）
- [x] **反哺批量回灌机制** — 沿用 Phase 5 管道，详 v0.2 §5
- [x] verify.py 395 → **421 PASS, 0 FAIL**（新增 §41 口径固化 26 用例）

### 6.2 待业务确认（按返工风险梯队）

> 防返工背景见 `Downloads\Demo范围决策与待确认_2026-08-26.md`。**拍板前不动后端反哺 / 不启用灰态字段**。

**第一梯队（高返工 · 现在就该确认）**
- [x] **#5** CTR **口径定义**（哪个 CTR / 去重规则）—— ✅ Phase 6 P2 已拍板，详 `docs/ctr-kpi-definition-proposal-v0.2.md`
- [ ] **#6** 反哺是否**影响生成排序**（A/B/C 候选排序）—— 影响主流程逻辑
- [ ] **#3** CTR 反哺**触发条件**（累计多少 plan / 定时？）

**第二梯队（中低返工 · 可后置）**
- [ ] **#1** 产品与权益 维度枚举 + 是否参与生成
- [ ] **#2** 投放目标 维度枚举 + 是否参与生成
- [ ] **#4** CTR 校准频率（手动 / T+1 / 周）
- [ ] **#7** 02-05 附属页面**是否纳入正式版**

### 6.3 候选（详 §5.5 CTR Roadmap）

**业务确认后启动**：
- [ ] **L1** LightGBM 回归替 baseline 查找表（结构化特征 + 中样本，详 §5.5）
- [ ] **P3** 维度权重动态 `config/dimension_weights.yaml` + `train_dimension_weights.py`
- [ ] **P4** 历史洞察签名关联（04 七 Tab 加 signature 视角：回流 CTR / 相似文案均值）
- [ ] **demo 数据回灌**（feedback.db ≥ 50 plan 后 `_demo_pred` 优先本地聚合）
- [ ] **pytest 迁移**（CLAUDE.md §4.4 工程债）

### 6.4 PRD §26 12 项已拍板 ✅ 2026-08-26
详见 `docs/architecture.md §五`。按议题：

| 议题 | 拍板 |
|---|---|
| #1 主渠道 / #11 企微 1v1 | APP Push + 企微 1v1 同期 |
| #2-4 枚举值 / #12 文案存储 | 复用 copy-analyzer 既有 4 值；只存摘要+signature+task_json |
| #5-6 字数+词表 / #8 校准 | 复用 yaml；CTR "未校准 / 机制就绪" |
| #7 predictor / #9 置信 | 走 main 版；加 `confidence` 字段 |
| #10 内网 LLM | 暂留空 → Phase 6 已加 `llm_settings.yaml` + banner |

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

### 极简 yaml 解析行内注释陷阱（2026-08-26 实战）
`ui/llm_status._read_yaml` 第一版只 `partition(":")` + `strip`，没处理**行内 # 注释**。当 yaml 写 `provider: ""  # 例: "openai"` 时，注释文字被当成 value，结果 `is_configured()` 误判 True。
- **症状**：默认全空状态 is_configured() 返回 True，missing_fields() 返回空
- **修复**：value 端要先 `split("#", 1)[0]` 砍注释，再 strip + 去引号
- **铁律**：手写 yaml 解析必须处理 4 类边界——整行 `#` 注释 / 行内 `#` 注释 / 引号包裹 / 空字符串

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

### CTR 学习 ≠ 复杂模型 · 务实主义（2026-08-26 · §5.5 衍生教训）
第一直觉是"加神经网络预测 CTR"，但本场景 4 个硬约束直接排除：
- 输入特征是**结构化表格**（渠道/人群/阶段/场景 + 字数 + emoji + 命中词），不是文本/图像
- 样本量是**几千到几万**（麦当劳业务体量），不是亿级
- **可解释是刚需**——业务要能问"为什么这个 Plan CTR 高"，GBDT 给特征重要性，DNN 给一堆注意力
- LLM 在旁主攻**生成**，CTR 模型只替**预测**这一层，两个职责清

→ **L1 选 LightGBM/XGBoost 几乎无悬念**；L2 增量重训也走这套路。DeepFM/DIN/Transformer 全上都是过度设计。

**铁律**：加新模型前先问三句——(1) 这是结构化还是非结构化？(2) 样本量级够哪个量级？(3) 可解释是不是刚需？三句里如果有 2 句答"结构化/中样本/是"，**别上深度**。

### dataclass 字段顺序铁律（2026-08-26 实战 · Phase 6 P1）
Python dataclass 强约束：**所有带默认值的字段必须在所有无默认值的字段之后**。
Phase 6 P1 把 `product_benefit` 切灰态改成 `str = ""`，但忘了挪位置，结果 `raise TypeError: non-default argument 'audience' follows default argument 'product_benefit'`，整页报错回不去。
- **修法**：`TaskInput` 改为 `[audience/channel/stage/scene/tone (no-default) + expected_action/plan_type/coupon/planned_send_date/extra_requirements (有默认) + product_benefit/objective (灰态有默认)]`——所有灰态字段挪到末尾
- **副作用 1**：`from_form` 仍然按 dict 关键字传，**参数顺序不影响**（只影响位置传参）
- **副作用 2**：用 `try TaskInput.from_form(空 form) except ValueError` 校验必填——直接抛错就够，不必绕一圈
- **铁律**：改 dataclass 字段默认值前 (1) 看字段顺序、(2) 不要默认空串和 no-default 混、(3) 改完跑全套 verify.py 别靠肉眼

### Streamlit widget 灰态实战（2026-08-26 · Phase 6 P1）
决策文档说视觉："整体降透明度（如 opacity 0.5）+ 右上角小角标 + hover tooltip"——Streamlit 没暴露 widget 级 opacity 钩子。
**实用近似**：
1. `disabled=True`（Streamlit 自己会灰化控件，符合预期）
2. label 加「待开发·二期接入」（文字角标代替 CSS 角标）
3. `help="后续开放，敬请期待"`（自动 hover tooltip）

三层叠加视觉差异足够清晰。剩下 10% 视觉差用顶部 banner（`.advanced-notice`）+ 00_home 卡片分组补。
**铁律**：Streamlit 控件别追 100% CSS 还原；用 disabled / label / help / banner 四件套覆盖 > 90% 场景。

### 决策文档驱动开发（2026-08-26 · Phase 6 P1）
另一个 AI 提醒的 `Downloads\Demo范围决策与待确认_2026-08-26.md` 定义了"本轮只动 6 维度灰态 + 4 页面弱化 + CTR 反哺免责，不动后端反哺 / 不删任何页面 / 不接真实数据"。
**严格按文档边界执行**——本轮没碰 P3/P4/demo 回灌/pytest 候选（虽然看着诱人），等业务确认 7 项清单再说。
**启示**：用户或另一个 AI 留的"范围/边界/决策"文档 = 当前轮的 scope-control，**不要按"全局规划"自己加码**。
**铁律**：接活前先 grep `/c/Users/a952462/Downloads/` 找决策/范围/边界 md 文件；找到了就以它为准，无就走 PRD / Handoff 默认。

---

## 8. 关键路径速查

| 路径 | 用途 |
|---|---|
| `C:\ideon\mcd-ai-content-platform\` | 新项目根 |
| `C:\ideon\mcd-ai-content-platform\PRD.md` | 产品需求文档（版本号见文件头） |
| `C:\ideon\mcd-ai-content-platform\CLAUDE.md` | AI 会话入门（必读） |
| `C:\ideon\mcd-ai-content-platform\data\ctr_baseline.json` | CTR 基准 **7 维**（channel/audience/coupon/stage/scene/plan_type/owner） |
| `C:\ideon\mcd-ai-content-platform\data\records.db` | 生成记录 SQLite（自动建） |
| `C:\ideon\mcd-ai-content-platform\data\feedback.db` | 真实 CTR 回流 SQLite（Phase 5 P1） |
| `C:\ideon\mcd-ai-content-platform\config\llm_settings.yaml` | LLM Provider 留空配置（Phase 6 P0） |
| `C:\ideon\mcd-ai-content-platform\docs\ctr-kpi-definition-proposal-v0.2.md` | **CTR 口径拍板稿 v3.1（业务已对齐）** |
| `C:\ideon\mcd-ai-content-platform\core\data_window.py` | **bi_dt 取数时间基准（12 点前 INTERVAL 2 兜底）** |
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
4. 跑 `python tests/verify.py`（**421 PASS / 0 FAIL**）
5. 看 `docs\ctr-kpi-definition-proposal-v0.2.md`（**当前 v3.1 拍板口径**）
6. 当前是 **Phase 6 P2 完成 · 等第一梯队剩 #3 / #6 拍板**

---

## 10. Self-check

- [ ] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）
- [ ] `python tests/verify.py` 全过
- [ ] `python -m py_compile $(git ls-files '*.py')` 全过
- [ ] 关键改动进 commit（如 git 化）
- [ ] UI 无 emoji，沟通全中文
