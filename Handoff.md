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
| 输入维度 | **5 必填 + 2 灰态**（audience/channel/stage/scene/tone 必填；objective 二期接入；**Phase A.1 已启用 product_category + benefit_type，10 产品 + 8 权益 + 自定义**） |

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
## 5. 决策记录

> Phase 1-22 详细决策 bullets 已拆分到 [](Handoff-decisions.md)（~285 行 / 40KB）。
> 本文件 §6.1 是速查表（最新 Phase 一句话）；要查"为什么 Phase X 这样设计"请跳 。

---


## 6. 待办

### 6.0 当前快照（最快定位状态）

> **⚠️ 口径说明（2026-08-31 · 诚实性修正）**：以下能力为**演示/离线口径 / 架构预留**，**非线上生产已跑通**，业务确认后接入：
> - **05 真实结果回流**：演示口径，**未接真实投放数据**，feedback.db 当前为空
> - **existing_predictor CTR 模式**：灰态二期，**当前无 predictor 注入**（生产口径未接通）
> - **objective / coupon（TaskInput 字段）**：灰态字段，**二期接入**
> - **records.db / feedback.db**：**尚未回传真实投放数据**
> - **train_dimension_weights.py**：v0.1 占位 · **暂不可用**（等 records.db 充实；Handoff §6.1 Phase 6 P4 段已标）
> - **闭环状态**：依赖用户**每月手动跑** `tools/calibrate_baseline.py` + `tools/monitor_l1_drift.py`；**不跑 = 闭环静默失效（非自动运行）**
> - **L1 数字**：以下 §6.1 Phase 18 段用 baseline v3.2 同口径实测值（2026-08-31 复现）

- **阶段**：**Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep + Phase 25 死代码清理/L1 runbook/Handoff 压缩 + Phase 26 Streamlit→FastAPI 全量 UI 迁移 + Phase 27 LLM 配置 UI 完整化 + URL 语义化 + Phase 36 滚动恢复 + Phase 37 UI 统一化 + Phase 38 5-agent BUG 审查 + 9 修复 + Phase 38 A1-mid 22 处 inline 收敛 + design.md §0.1 DNA/§12 避坑 + Phase 40-43 字典维护鉴权+3 个 BUG 修复 + Phase 44 _write_dict_file 4 重防御 + Phase 45 字典保存自动备份（每天首次）+ Phase 46 历史洞察 4 BUG 修复 + wf/ef/rank 3 Tab 查询增强 + Phase 47 字典维护 UI 重设 + smoke tmpdir 教训**（2026-08-28 → 2026-09-03）
- **用例**：**848 PASS / 0 FAIL**（`python tests/verify.py`，Phase 38 A1-mid 同步修 5 FAIL 断言 + 1 新增 = 847 → 848）
- **已可用模块**：①内容创作（01 生成 3 候选 + CTR 评估 + 阈值生效）；②真实回流（04 上传 CSV/Excel → 入库 → 4 维度聚合 → 写 baseline）；③历史洞察（04 七 Tab）；④内容预测 CTR（03）
- **L1 静默双轨 + 切主流程**：用户**主动切 XGBoost**（即原 l1_model），settings-bar `算法模型` selectbox 选 `XGBoost`（原 CTR 模式 → 算法模型 demo / baseline_only / xgboost，默认 **baseline_only**）；模型缺失/渠道不在训练范围时静默降级 unavailable，主流程不受影响。**L1 实验对比 checkbox 已删除**（Phase 27 — 普通用户不需要"对比"概念，多模型预测已合并到主流程 selectbox）
- **L1 漂移监控**：`tools/monitor_l1_drift.py` —— records.db (l1_model 预测) join feedback.db (真 CTR) → 整体/分渠道 MAE；超 baseline × 1.3 → 红字告警 + 写 data/drift_log.csv 留档；空 DB 优雅降级（配对数 < 5 不评估防误报）
- **代码质量清理**：02 页面 bug 修复 / LLM call LRU cache / weighted_ctr 合并 / 注释对齐 / 死代码删除 / CSV reader 合并 / rule_engine 重构 / jieba 批量向量化 / Streamlit 页面缓存 / 5 处死代码清理 / L1 predictor 静默双轨
- **LLM 配置 UI（Phase 27）**：右上角 pill 可点 → modal 弹出 → Provider 下拉 6 个预置（**MiniMax 走 Anthropic 协议，其他 5 个走 OpenAI 协议** + `自定义`）+ Base URL/Model 自动联动 + API Key `type=password`（打星号）；两个按钮 `测试连接`（openai/anthropic SDK 按 protocol 探测，`MiniMax` 自动走 `/v1/messages`）/ `应用配置`（不重复探测，直接写 yaml 到 **`~/.mcd-ai/llm_settings.yaml`**（**不进项目目录，git 历史不会被污染**）；pill 灰 → 绿 + pulse 动画
- **Phase 25 死代码清理 + L1 runbook（2026-08-31）**：`tools/push_*_via_api.py` ×9 → `tools/_archive/`；`ui/plotly_helpers.axis_rate()` 删；`pages/01/02` 各 1 个 unused import 删；`ui/styles.py` 加 .l1-pill/.l1-label/.l1-value/.l1-meta 4 类（之前 01 引用但未声明）；black 格式化 3 文件；`docs/l1-training-runbook.md` 落地（**5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报**）
- **Handoff 压缩（2026-08-31）**：4 文件总 ~103KB → ~32KB（Phase 1-10 早期决策压 1-2 行 + why；Phase 11+ 保留；L1 已落地段指向 runbook；P4 + UI 重设延后标记）
- **已拍板落档（2026-08-31 用户会话，详 §6.2/§6.3）**：①自动定时校准延后（`weekly_calibrate.bat` 仅落档不调度）；②CTR 校准频率从每周一上午（Phase 7.1）改为**每月一次手动**（建议每月 1 号上午跑，`docs/ctr-feedback-schedule.md` 已同步修订 + §3.5 加 L1 漂移监控步骤）；③02-05 附属页 + 字典维护 UI（`pages/06_settings.py`）纳入正式版，UI 重设阶段一起做；④L1 训练责任人 = 用户自己跑；⑤L1 特征重要性**月报** + 用户自己看（Phase 22 B 已落）
- **首要任务**：真回流数据进来时手动跑 `python tools/calibrate_baseline.py --db data/feedback.db` 重算 baseline；切 L1 后跑 `python tools/monitor_l1_drift.py` 监控漂移；**用户在 sidebar selectbox 主动切 l1_model**
- **Phase 36 滚动恢复强化（2026-09-01 用户拍板"页面还是会跳一下"）**：审计 5 页面 + 9 partial 所有 form，定位根因——JS 写在 body 末尾 + 浏览器 303 后默认自动滚顶 = 视觉"先跳顶再滚回"两步。**修复**：scroll restore JS 上提 `<head>` 同步执行 + `history.scrollRestoration='manual'`（关闭浏览器自动滚顶）+ rAF × 多时机重试；3 个 GET form `/04` 改 `/insights` 收尾。**记得硬刷一次 Ctrl+F5 让浏览器拿到新 base.html**（内联 JS 无法靠 CSS ?v=xxx 缓存破坏）
- **下一阶段（候选待启动）**：①**批量评估页面 UI 改进**（02/03/04/05 还没改，沿用 Phase 26 初始样式；用户反馈整体调性要跟 01 一致）；②**字典维护 UI（`pages/06_settings.py`）** 跟 LLM 配置一起做；③UI 重设阶段的整体收尾
- **当前迭代重点（Phase 27 用户反馈）**：①右上角 ☰ 删除；②LLM pill chev 改 SVG 对齐；③URL 全切语义化（`/00` `/01`...`/05` → `/` `/studio` `/diagnosis` `/batch` `/insights` `/feedback`，API 同步 `/api/01/*` → `/api/studio/*`）；④模板内 `<title>` 去数字前缀；⑤内容工坊副标题去冗；⑥CTR 模式 → 算法模型（demo/baseline_only/l1_model → 演示规则/渠道基线/XGBoost），默认 baseline_only；⑦L1 实验对比 checkbox + L1 hint 删除（产品感不需要"对比"概念）
- **Phase 28 必填口径改 3 项 + 「通用（不指定）」（2026-09-01 用户拍板）**：表单必填从 5 项砍到 3 项（投放渠道 / 目标人群 / 内容语气），其余 9 项全部可选；可选字段第一项加「通用（不指定）」默认选中，后端 prompt 拼装 + Demo 占位候选遇此值整行跳过（让 AI 自由发挥）。改 6 文件：core/schemas.py（5 enum + REQUIRED_FIELDS 改 3 项）+ tests/verify.py（必填测试同步）+ web/templates/pages/01_内容工坊.html（重排字段顺序 + selectbox 选项）+ prompts/copy_generation.py（v1.1→v1.2 通用跳过）+ services/generation_service.py（_demo_candidates 通用跳过）+ PRD.md（§6.2 字段表）
- **Phase 29 候选展示翻牌（2026-09-01 用户复盘反馈）**：推翻 #6 反哺影响排序拍板——候选固定 A→B→C 顺序（不再按 CTR 重排）+ 默认选中 A（不再 CTR 最高那条）。CTR 仍展示在右侧"参考结果"，但卡片顺序操作直觉优先。改 3 文件：web/app.py（删 rank_candidates_by_ctr 调用 + selected_id 写死 "A"）+ web/static/css/style.css（candidate-card 加 min-height:210px 让 3 卡等高；cand-body line-clamp 5 行 + cand-title line-clamp 2 行 避免长 body 折成多行挤压竖排感）+ Handoff-decisions.md 新增 Phase 29 段。保留 rank_candidates_by_ctr 函数（tests/verify.py §42 PASS）
- **Phase 31A L1 混合校准（2026-09-01 用户拍板"不重训"）**：L1 LightGBM 推理后叠加 baseline_lookup × tm 做混合校准，UI 即时生效。`final = 0.5 × l1_pred + 0.5 × (baseline × tm)`（baseline 有值时 50/50 平权），`final = l1_pred × tm`（baseline 缺失时仅 L1 + 时段修正）。why：L1 区分能力差（R²=0.08）但 absolute MAE=0.34% 尚可；baseline 6 维回退查表有数据基础但稀疏维度兜底；两边互补。改 2 文件：adapters/ctr_predictor_adapter/__init__.py（`_l1_model_pred` 加 L1_BLEND_ALPHA=0.5 + 双分支混合 + source 改 `l1_blended`）+ tests/verify.py（§57 source 断言 `l1_lightgbm` → `l1` 兼容）。不动 L1 booster、meta、baseline_lookup、train_lgbm.py
- **Phase 32 算法模型显示名纠正（2026-09-01 用户拍板）**：01_内容工坊.html 顶部 selectbox 显示名 3 行纠正——`演示规则` 保留 / `渠道基线` → `历史基准`（覆盖 6 维回退全维度）/ `XGBoost` → `LightGBM`（底层真实模型名，Phase 27 误称误导运营同事去查 XGBoost 文档发现对不上）。`value` 属性不动（后端 mode 值不变），0 回归风险。
- **决策文档**：`Downloads/decision-product-benefit-2026-08-26.md` + `Downloads/decision-objective-2026-08-26.md`
- **口径文档**：`docs/ctr-kpi-definition-proposal-v0.2.md`（v3.1 拍板稿；v3.1.1 渠道清理已落档）+ `docs/feedback-ctr.md`

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
| **Phase 6 P2** CTR 口径固化 v3.1 | Q1-Q6 拍板 / bi_dt 铁律 / 6 文件落地 / 反哺批量回灌机制 | 421 |
| **Phase 6 P3** simplify 清理（4 agent review） | yaml.safe_load 替手写解析 / v3.1 docstring 缩成 1 行 / 删 PENDING_FIELDS / _to_local 死分支 / notice.py 合并 helper | **418** |
| **Phase 7** 业务拍板落地（#3 触发 + #6 排序） | docs/ctr-feedback-schedule.md / weekly_calibrate.bat / rank_candidates_by_ctr / UI 调 + 文案微调 / 删 phase6_p1/p2_push.py | **428** |
| **Phase 8** pytest 迁移（CLAUDE.md §4.4 工程债） | pytest.ini / _RUNNING_UNDER_PYTEST 标志 / _check 失败抛 AssertionError / 双路一致（pytest 43 passed + CLI 428 PASS） | **428（CLI）/ 43（pytest）** |
| **Phase 6 P4** Handoff §6.3 纯工程候选扫掉 | config/dimension_weights.yaml + train_dimension_weights.py（v0.1 占位 · **暂不可用**，等 records.db 充实）/ feedback_lookup.py + 5 文件改动 / §43+§44 共 45 用例 | **473（CLI）/ 45（pytest）** |
| **Phase 9** 第二梯队 #1/#2 业务拍板落档 | `Downloads/decision-product-benefit-2026-08-26.md` + `Downloads/decision-objective-2026-08-26.md`；Handoff §5/§6.0/§6.1/§6.2 同步；**不动代码** | **473（不动）** |
| **Phase 10** 第三梯队 #8-#13 维度设计迭代（用户口径） | schema 与 baseline 错位修正（CHANNELS 缺微信小程序订阅 / Plan 类型命名三套混乱）+ 投放日期→工作日/非工作日/节假日下拉 + 场景/用券从 form 字段改内容关键词推断 + 指数衰减已实现（λ=0.01 半衰期 69.3 天）+ 下次迭代目标=写具体阈值 | **不动代码，待拍板** |
| **Phase 11** 第三梯队 #12 简化落地（用户口径 2026-08-27） | 用户当天把 #12 从 3 值拍板稿降级为 2 值（不要日期选择器，法定节假日暂搁）；core/data_window.py 加 classify_date_type/classify_today_type 纯 weekday 函数；pages/01_content_studio.py:189 date_input → selectbox 2 值；core/schemas.py 注释更新；tests/verify.py §45 加 18 用例（491 PASS） | **491（CLI）/ 46（pytest，双路一致）** |
| **Phase 12** 第三梯队 #8/#9/#10/#11 全部落地 + #11 用户假设反转 | 用户喂 CNN0827 后 4 项一拍板：①#8 渠道清洗（无需渠道+微信公众号推文）；②#9 Plan 命名连写；③#10 SCENES 必填改选填；④#11 用券双字段（保留 form + 新增文案推断）；baseline_lookup "普通Plan"→"常规Plan" bug 顺手修；9 文件落地含 text_classifier/coupon_keywords/clean_cnn_backup；verify 491 → 522 PASS | **522（CLI）/ 47（pytest，双路一致）** |
| **Phase 13** 工具定位重定义 · UI 3 按钮砍齐 | 用户拍板"工具只是 CTR 评估辅助决策，业务方看后自己导入生产系统，不会点保存" → 删除 编辑候选/恢复 AI 原文/保存当前选择 3 按钮 + Candidate.title_edited/body_edited 字段 + effective_*/is_edited/reset_edit 全删；引用方 4 文件（ctr_prediction_service/generation_service/rule_engine/01_content_studio）全改 effective_* → title/body；records.db 保留（train_dimension_weights.py 未来用），UI 不调用；verify 522 → 525 PASS | **525（CLI）/ 47（pytest，双路一致）** |
| **Phase 14+15** baseline v3.2 重算 + row key 修复（CTR 响应 form 字段） | 用户报告"选了具体指标 CTR 没变" → 排查发现 2 类根因：① _candidate_to_row 输出英文 key 但 prompt_builder 读中文 key（plan_type/coupon/owner 3 字段全 miss）+ workday 孤儿字段；② baseline JSON 没建"渠道_x_文案含券词"维度 key。修：① _candidate_to_row 中英文 key 双输出 + workday 透传 + prompt_builder.py:101 "普通Plan"→"常规Plan"；② 一次性脚本 tools/recalc_text_has_coupon.py 从 cnn_backup_cleaned.xlsx（48307 行）按指数衰减 λ=0.01 半衰期 69.3 天聚合 8 keys 写 baseline v3.2（APP Push_是/否 0.16%/0.19% 等）。文案含券词对 CTR 渠道差异极大，印证 Phase 12 #11 用户假设反转。verify 525 → 557 PASS | **557（CLI）/ 49（pytest，双路一致）** |
| **Phase 16** calibrate_baseline 扩 2 维度（text_has_coupon + workday） | 用户口径"预算owner 不加，工作日类型用 sent_date 推算就行，标题正文是否带券加一下，其他不用" → 扩 calibrate_baseline.py 覆盖 4 维度：渠道 / 渠道×用券 / 渠道×文案含券词（新增，读 text_has_coupon 列）/ 渠道×工作日类型（新增，从 sent_date 推 weekday）；feedback_repository.py 加 text_has_coupon 列 + get_connection 先 ALTER 再 executescript（兼容老库；SQLite CREATE INDEX 对缺失列报"no such column"）；feedback_service.to_records 用 classify_coupon_in_text 推断每行 text_has_coupon；不动 owner/title_len。verify 557 → 574 PASS | **574（CLI）/ 50（pytest，双路一致）** |
| **Phase 16.5** 上线声明 · 自动定时校准 + L1 模型延后 | 用户拍板"先上线再说"：①内容创作 / 真实回流 / 历史洞察 / 批量评估 CTR 四模块全链路可用；②`weekly_calibrate.bat` 仅落档不调度（用户没说要开发自动跑）；③L1 LightGBM 模型升级（§6.3）延期，待样本 ≥ 1000 plan 再启动。**不动代码** | **574（CLI）/ 50（pytest，双路一致，不动代码）** |
| **Phase 17** 代码质量清理 · 02 bug + LLM cache + weighted_ctr + 注释对齐 | 用户拍板"检查整体代码质量性能"：①02_copy_diagnosis.py 真 bug：`from core.config import settings` 模块不存在导致页面永远走 Demo → 改用 ui.llm_status.load_config() + ProviderRouter；②services/record_service.py 死代码整文件删除；③core/llm_gateway.ProviderRouter.call 加实例级 LRU cache（512 容量，仅缓存成功响应）；④core/analytics_utils.py 抽 weighted_ctr + weighted_ctr_series 替代 7 处 inline 公式；⑤app.py / pages/00_home.py / core/schemas.py / tools/recalc_text_has_coupon.py 注释对齐 Phase 16.5。verify 574 → 600 PASS（§51 §52 新增 26 用例） | **600（CLI）/ 51（pytest，双路一致）** |
| **Phase 17.5** 重构 · CSV reader / row dict / rule_engine / 批量分类 | 用户拍板"继续"：①core/csv_utils.read_table() 替代 services/feedback + batch_evaluation 两处重复 reader + 列别名 + 必填列填空；②services/ctr_prediction_service._build_row() 合并 _candidate_to_row + predict_one 重复 row dict；③services/rule_engine._run_term_check() 合并 _check_banned + _check_risk 90% 模板（required/format 因业务逻辑不同保留原样）；④core/text_classifier.classify_coupon_batch() 向量化替代 df.apply(axis=1)（批量场景 50-100x 加速），feedback_service.to_records + tools/recalc_text_has_coupon.infer_text_has_coupon 改调批量版。verify 600 → 618 PASS（§53 新增 18 用例） | **618（CLI）/ 52（pytest，双路一致）** |
| **Phase 17.6** Streamlit 缓存 + 死代码清理 | 用户拍板"按节奏继续"：①pages/04 删 `__import__("io").BytesIO` 黑魔法 + 加 `_cached_parse_insights_file` (sha1 key) + `_cached_generation_records_list` (TTL 60s)；②pages/05 加 `_cached_recent_feedback` (TTL 30s) + `_cached_generation_records_list` (TTL 60s)；③pages/01 删 Phase 13 残留 `"saved_id": None` 死 state；④ui/plotly_helpers.py 删 `apply_brand_theme` 死函数 + 配套 `import go`；⑤adapters/ctr_predictor_adapter/column_mapping.py 删 `from_optional()` NotImplementedError 死函数；⑥core/data_window.py 删 `SNAPSHOT_CUTOFF_HOUR` 常量（`resolve_bi_dt_window` 默认 cutoff=12 硬编码保留）。verify 618 → 630 PASS（§54 新增 12 用例） | **630（CLI）/ 53（pytest，双路一致）** |
| **Phase 18** L1 LightGBM PoC（剔除小程序 + 高效词 + 时间衰减） | 用户拍板"先试试看"。基于 cnn_backup_cleaned.xlsx 4.4 万行训练：①**剔除微信小程序订阅消息**（仅 7 Plan，统一模型被带偏）；②特征 14 维（5 数值 + 6 类别 one-hot + 1 高效词命中数 + 1 计划类型 target encoding + 1 工作日 one-hot）；③时间衰减权重 half_life=180 天；④logit(CTR) 目标。结果：L1 MAE 0.395%（vs L0 0.416% 降 5.2%），R² 0.0824（vs L0 0.0659）。**3 渠道 L1 全胜**：APP Push 0.273%（vs L0 0.309%）/ 企微1v1 0.682%（vs L0 0.740%）/ 短信 0.203%（vs L0 0.351%）。**关键发现**：A/B 对比验证渠道×工作日交叉特征为负向（LightGBM 自己能学，显式加 = 特征冗余）。`tools/train_lgbm.py` 训练 + `tools/evaluate_lgbm.py` L1 vs L0 同口径对比 + `data/lgbm_model_v1.pkl` 模型 + `data/effective_words.json` 高效词表（62 词来自 word_frequency 差值>0.5）+ `data/lgbm_feature_meta.json` 特征元信息。**待做**：`adapters/ctr_predictor_adapter/l1_predictor.py` 接入 + 4 态分明 + 误差监控 + 业务方拍"特征重要性 Top10 每周给业务看" / "切 L1 时点" / "误差告警阈值" / "训练责任人"（§6.3）。verify 630 → 631 PASS（§55 新增 1 用例：模型加载 + feature_columns 一致性） | **631（CLI）/ 53（pytest，双路一致）** |
| **Phase 19** L1 LightGBM 生产接入 + 静默双轨（§56 · 2026-08-28） | 用户拍板"接入生产，方案 B 静默双轨"。**接入**：新建 `adapters/ctr_predictor_adapter/l1_predictor.py`（predict_l1 / predict_l1_batch / predict_l1_status / L1_SUPPORTED_CHANNELS 四态分明，懒加载 + lru_cache 兜底）；`__init__.py` 导出 4 符号。**特征工程与 train_lgbm 严格对齐**：数值 6 维（title_len/content_len/has_emoji/has_digit/has_question/eff_word_count）+ channel/coupon/workday one-hot + ch_x_wd cross + plan_type_te。**静默双轨**：`pages/01_content_studio.py` sidebar 加"显示 L1 实验对比（仅管理员）"checkbox（默认关），开启时 `_render_ctr_card` 多渲染一行 L1 预测；模型缺失/渠道不在训练范围时静默降级 unavailable（小红字提示），主流程不受影响。**渠道校验**：L1_SUPPORTED_CHANNELS 仅含 APP Push / 企微1v1 / 短信（训练数据范围），其他渠道 → unavailable。**容错**：lru_cache(maxsize=1) 加载模型，异常路径返回 (None, "unavailable") 不抛错。verify 655 → 677 PASS（§56 新增 22 用例） | **677（CLI）/ 54（pytest，双路一致）** |
| **Phase 20** l1_model mode 主流程接入 + 漂移监控（§57 · 2026-08-28） | 用户拍板"切 L1 时点用户主动" + "误差大告警"。**l1_model mode**：`CTRPredictionAdapter.VALID_MODES` 加 `"l1_model"`（5 态）；新方法 `_l1_model_pred` 走 `predict_l1`，4 态透传（model→model_prediction/source=l1_lightgbm，baseline_only→baseline_only，unavailable→unavailable）。**UI 主动切**：`pages/01_content_studio.py` sidebar 新增 "CTR 主流程模式" selectbox（demo/baseline_only/l1_model，默认 demo，env CTR_MODE 可覆盖）；L1 模型缺失时 l1_model 不可选。**漂移监控**：`tools/monitor_l1_drift.py` records.db (source=l1_lightgbm) join feedback.db (按 task_signature 聚合真 CTR) → 整体/分渠道 MAE vs baseline（lgbm_feature_meta.json）→ 超 1.3 倍红字告警 + 写 data/drift_log.csv 留档；配对数 < 5 优雅跳过（防小样本误报）。**切 L1 时点 / 误差告警阈值（30%）**：业务拍板 2 项已落，详见 §6.3。verify 677 → 697 PASS（§57 新增 20 用例） | **697（CLI）/ 55（pytest，双路一致）** |
| **Phase 21** simplify pass · 文档漂移 + 死代码 + UI emoji 清理（§58 · 2026-08-28） | 用户拍板"谨慎点修复，怕你修坏整体了"。先 Explore agent 逐项 grep 验证为死代码/漂移才动手：(1) **CLAUDE.md 漂移**：§3 架构图删 `services/record_service`（Phase 17 已删）+ `adapters/cache_adapter`（从未实现）；§4.4 `pytest tests/test_ctr_adapter.py` 加注释（文件尚未拆分）；§6.2 加 `l1_model` 模式（Phase 20 已落地）。(2) **死代码**：pages/05 删 2 个未用 import（`Optional` / `rate_value`）；pages/03 删 `show_col_map` 死 dict（保留「`suggestion` → `建议`」映射逻辑 + 加 `not in display.columns` 防御）；services/generation_service `_validate()` 删 if-pass 死块（body 是 `pass`，whitespace-only title 会进但无副作用）。(3) **UI emoji 清理**（CLAUDE.md §9 红线合规）：5 个 pages `page_icon` → `None`；home.py 内嵌 `<h1>🍟</h1>` `<h2>🚀</h2>` 删。**不动**：P2 灰色地带（pages/02 自构造 ProviderRouter）+ P3 风格（04 空行/01 三栏比例）+ adapter 末尾 import 顺序（已 `# noqa: E402`，运行无问题）。**验证**：Explore agent 确认无 verify.py 用例拦截；py_compile 3 个 .py 干净；verify.py 仍 **697 PASS / 0 FAIL**（无回归）。**不在 Phase 21 范围**：emoji 用法 P0 决策（红线本身是否调整）；CLAUDE.md §3 架构图与 Handoff 同步方式长期治理 | **697（CLI）/ 55（pytest，双路一致）** |
| **Phase 22 B** 特征重要性月报脚本（§58 · 2026-08-28） | 用户拍板"自己看为主，月报"。**新增 `tools/print_feature_importance.py`**（217 行）：加载 lgbm_model_v1.pkl + lgbm_feature_meta.json，算 importance_type=gain（支持 split），Top N 默认 10，与上次快照对比名次变化（±2 名算涨/跌，标 ↑/↓/新）；落档 `data/feature_importance_history/importance_YYYY-MM-DD_HHMMSS.json` + `data/reports/feature_importance_YYYY-MM-DD.txt`；Windows console 编码 fix（sys.stdout.reconfigure UTF-8）。**humanizer** 把内部列名翻成人话（`channel_APP_Push` → "渠道: APP Push"）。**首次跑结果**：正文长度 35.19% / 标题长度 22.92% / 高效词命中数 14.59% / 渠道: 短信 8.63% / 计划类型 TE 6.48%。verify 697 → **719 PASS**（§58 新增 22 用例） | **719（CLI）/ 56（pytest）** |
| **Phase 22 C** 漂移自动回退（§59 · 2026-08-28） | 用户拍板"自动切回 L0，不让人介入"。**新增 `core/active_mode.py`**（read/write/clear 三态 + ALLOWED_MODES = {demo, baseline_only, l1_model}）。**`tools/monitor_l1_drift.py` 加 `apply_auto_rollback(alert_level)`**：ALERT → 写 demo / WARN → 写 baseline_only / OK → 清文件；加 `--no-active-mode` CLI flag（默认开）。**`pages/01_content_studio.py` 启动读 `data/active_mode.txt`** → 覆盖 sidebar 默认 ctr_mode + 黄色 banner 提示"已被自动回退到 {mode}（漂移告警）"。**工作流**：monitor 跑出告警 → 写文件 → 下次开 01 页面 sidebar 自动显示 demo + 红字提示；人工确认后手动删文件恢复。verify 719 → **750 PASS**（§59 新增 31 用例） | **750（CLI）/ 57（pytest）** |
| **Phase 22 D** 批量预测自动落档 records.db（§60 · 2026-08-28） | 用户口径"批量跑的预测一定会投出去，必须回收校准"。**`services/batch_evaluation_service.py` 加 `batch_signature(row)`**（与 task_signature 同字段顺序：channel/coupon/plan_type/audience/stage/scene + 标题桶/正文桶，SHA1 截 12 位，batch 缺后 3 字段填空串）+ **`save_predictions_to_records(rows, db_path)`**（仅写 ctr_result_type 非空行，包成单候选 id="A" strategy="batch_eval" + ctr source 标 "batch_{result_type}"，单行失败不影响其他）。**`pages/03_batch_evaluation.py` 加 checkbox「保存预测到 records.db」**（默认关，按需开启）；评估完成自动调 save + 显示"已保存 N 条"。**闭环**：03 上传 CSV → 勾选 → 跑评估 → 自动落档 → 后续 `pages/05_feedback` 上传真实 CTR 时 feedback_repository 自动 join signature 算 MAE/MAPE。verify 750 → **794 PASS**（§60 新增 24 用例） | **794（CLI）/ 59（pytest，双路一致）** |
| **Phase 23** 安全加固 · Critical-1/2 + 3 处小修（§11b · 2026-08-28） | 用户拍板"1改，2改，3改"（Critical-1 API key 泄漏 + Critical-2 XSS + Required-1 page→core 误判跳过）。**(1) Critical-1**：`core/llm_gateway.py` 加 `_KEY_PATTERNS = [sk-..., Bearer ...]` + `_sanitize_error()` 兜底 + `_classify_call_error()` 归类 6 种稳定错误码（Authentication/Permission/RateLimit/Timeout/Connection/BadRequest，未识别走 fallback "API异常: <cls>"）；3 处 `_call_openai / _call_anthropic / parse_json_response` 全替换 str(e)[:N] → 稳定错误码 + stderr 完整日志（仅服务端）。**(2) Critical-2 XSS**：pages/01/02 `_render_channel_preview` 用 `html.escape()` 包 title/body；短信段数按 escape 前原始长度算（防 body_len 算多）；删除 5 个 pages 的死 import。**(3) Required-1 误判**：经核查 services/feedback_service.py 已走 repository 抽象、pages 只 import services 不直 repository（CLAUDE.md §4.1 合规），**误判跳过**。**(4) 3 处小修**：`prompts/copy_rewrite.py:117` parse_response 用 `_sanitize_error(str(e))[:80]` 兜底（防御性，同 Critical-1 模式）；`tools/monitor_l1_drift.py` 统一 `sys.exit(1)` + 抽 `MIN_REAL_REACH=50` 常量 + 新增 `--min-real-reach` arg + `import sys` 移顶部。**(5) page_setup 模块**：抽 `ui/page_chrome.py` `page_setup(page_id, subtitle)` 消除 5 pages × 14 行 chrome 模板。verify 794 → **830 PASS**（§11b 新增 6 回归用例：4 helper-level + 1 call-site mock 测 ProviderRouter.call 不透漏 sk-，+1 copy_rewrite sanitize） | **830（CLI）/ 60（pytest，双路一致）** |
| **Phase 24** 全量 smoke sweep（防退化 · §61 · 2026-08-28） | 用户拍板"完整测试"。把 §17-19 跑的 sweep 固定下来防回归：**§38 test_smoke_sweep** 24 用例覆盖 ①31 模块 import（core/services/adapters/repositories/prompts/ui 全集）②SQLite tmp dir 隔离读写（**关键：必须用 db_path 参数，不能默认走 data/**）③rule_engine 4 边界（空/超长/4 渠道/未知渠道不 crash）④ctr 5 modes 全过（含 l1_model 真模型加载：pred=0.00116，模型已 live）⑤TaskInput 4 必填字段校验（audience/channel/stage/tone）⑥similarity_service 空 DB ⑦copy_analysis_service.diagnose 返回结构 ⑧read_recent limit 边界 ⑨import_feedback 空 CSV。**新发现**：l1_model mode 实际能跑（lgbm_model_v1.pkl 已存在并能加载），PRD/CLAUDE.md 仅说 capability，**首次确认 L1 模型 live**。verify 830 → **854 PASS**（§61 sweep 新增 24 用例） | **854（CLI）/ 61（pytest，双路一致）** |
| **Phase 25** 死代码清理 + L1 runbook + Handoff 压缩（2026-08-31） | 用户拍板"按节奏继续"：(1) `tools/push_via_api.py` + `tools/push_phase18-23_via_api.py` + `tools/push_simplify_a1_via_api.py` + `tools/push_phase22_a1_via_api.py` × 9 个历史 push 脚本 → `tools/_archive/`（untracked 用 `mv` 而非 `git mv`）；(2) `ui/plotly_helpers.axis_rate()` 0-caller 删；(3) `pages/01_content_studio.py` 删 `from core.text_classifier import classify_coupon_in_text`（line 43 unused）+ `pages/02_copy_diagnosis.py` 删 `from adapters.llm_adapter import call_llm`（line 40 unused，走 ProviderRouter）；(4) `ui/styles.py` 加 .l1-pill/.l1-label/.l1-value/.l1-meta 4 类 CSS（之前 01 引用但未声明）；(5) black 格式化 3 文件；(6) `docs/l1-training-runbook.md` 落地（5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报）；(7) `docs/ctr-feedback-schedule.md` 从"每周一上午"改为"每月 1 号上午手动"（用户拍板）+ §3.5 加 L1 漂移监控步骤；(8) **Handoff 4 文件压缩**（~103KB → ~32KB）。verify **854 PASS**（无回归） | **854（CLI）/ 61（pytest，双路一致）** |
| **Phase 26** Streamlit → FastAPI + Jinja2 + HTMX 全量 UI 迁移（§62 · 2026-08-31） | 用户拍板"全部完成后再找我 / 安心改"。**起点**：用户给参考 HTML `mcd_ai_content_platform_ui_v2.html`（中台风格）+ 另一 AI 评估"Streamlit 默认样式扁平，无法达成设计稿保真度"；CSS-only 方案试过 3 轮后定 FastAPI 路线。**完成**：5/5 页面（00 首页 / 01 内容工坊 / 02 文案诊断 / 03 批量评估 / 04 历史洞察 / 05 真实结果回流）从 `pages/0X_*.py` 迁到 `web/templates/pages/0X_*.html` + 9 个 partial；13 API（`/api/0X/...`）POST + 6 GET 页面 + `/health` + 静态资源（CSS / 金拱 SVG）。**业务层 0 行改动**：services / core / adapters / repositories / prompts 全部复用，sys.path 注入父目录。**设计稿还原**：参考 v2 HTML 整体风格 + 金拱 SVG 替换 M 字母 + LLM 状态 pill + 头像 topbar + 居中 primary button + 3 列 studio grid + 7 tab 切换 + 4 KPI 卡片 + 批量评估表格 + 下载 CSV。**state 管理**：模块级 dict（`web/state.py`：S_01..S_05 + df_registry），单用户 OK，生产换 Redis。**架构**：HTMX partial reload（`hx-post` / `hx-get`）+ Jinja2 模板继承（base.html）+ 表单 PRG（POST 303 → GET）；HTMX CDN `unpkg.com/htmx.org@1.9.10`。**入口**：`cd web && python -m uvicorn app:app --port 8530`（默认 FastAPI），旧 Streamlit 仍跑 8520 作对照。**验证**：curl 6 路由全 200 + 11 POST API 端到端通 + 静态资源 + 旧 `tests/verify.py` 仍 **854 PASS / 0 FAIL**（Streamlit 业务层 0 破坏）。**不动**：pages/0X_*.py 旧文件保留（Streamlit 作 fallback）；state 多用户限制注释标红；§6.3 P4（历史洞察签名关联）+ 字典维护 UI（`pages/06_settings.py`）依旧推后到二轮 UI 优化。 | **854（CLI）/ 61（pytest，0 回归）** |
| **Phase 27** LLM 配置 UI 完整化 + URL 语义化 + 产品观感清理（§63 · 2026-09-01） | 用户拍板"应用起来看着像个合格的产品"。分 4 块工作：<br>**① LLM 配置 UI**：右上角 pill 可点 → 弹 modal（4 字段 + 6 个 Provider 预置 + base_url/model 自动联动 + api_key `type=password` 打星号 + 测试连接/应用配置 2 按钮分离）；后端 `_probe_llm` 按 provider 协议选 SDK（**MiniMax 走 Anthropic**，其他 5 个走 OpenAI）；测试 endpoint 返回含 `providers` 避免 select swap 后丢 option；model 名自动清理 `[1m]` 等后缀；错误信息含请求 URL + HTTP status。**key 写到 `~/.mcd-ai/llm_settings.yaml`（不进项目目录，git 历史不被污染）**——`CONFIG_PATH` 从项目目录改到家目录。<br>**② URL 语义化**：`/00`/`/01`...`/05` 全部改成 `/`、`/studio`、`/diagnosis`、`/batch`、`/insights`、`/feedback`；API 路径 `/api/01/*`...`/api/05/*` 同步改成 `/api/studio/*`...`/api/feedback/*`；template 里 form action + HTMX URL 全部跟改。<br>**③ 内容工坊去技术裸露**：副标题"AI 文案生成 · CTR 预测 · 渠道预览 · 人工选择"→ 空；`CTR 模式` 标签 → `算法模型`；3 选项 `demo / baseline_only / l1_model` → `演示规则 / 渠道基线 / XGBoost`；默认模式 `demo` → `baseline_only`；删除 `L1 实验对比（仅管理员）` checkbox + `L1 状态：model；支持渠道：...` hint（**普通用户不该看到技术状态**）。<br>**④ UI 微调**：左上角 ☰ 删除；LLM pill chev 从 `⌄` 字符改 SVG（11×7，精准对齐）。<br>**不动**：旧 `pages/0X_*.py` 保留（Phase 26 fallback）；`l1_model` 后端逻辑保留（前端不展示而已，以后可重启用）。<br>**验证**：`python tests/verify.py` **847 PASS / 0 FAIL**（Phase 26 删 7 个 Streamlit 页面后从 854 → 847）；6 路由 `/`、`/studio`、`/diagnosis`、`/batch`、`/insights`、`/feedback` 全 200；旧 `/01` 返回 404（语义化生效）。<br>**Commit**：`8f5978e`（本地）→ `ea992d50c1`（远端 main）。 | **847（CLI）/ 0 回归** |
| **Phase 36** 滚动恢复强化 + URL /04 收尾（2026-09-01 用户拍板"页面还是会跳一下"） | 完整审计 5 页面 + 9 partial 所有 form/button，定位"跳一下"根因：**Phase 31B JS 写在 body 末尾**，恢复时机晚于浏览器首屏绘制，303 导航后浏览器**默认自动滚顶** = "先跳顶部 → 再 scrollTo 回原位"的视觉两步跳。**3 处修改**：(1) `web/templates/base.html` scroll restore JS 上提到 `<head>` 末尾同步执行 + 加 `history.scrollRestoration='manual'`（**关键**：关闭浏览器自动滚顶，由 JS 完全接管）+ `beforeunload` 兜底保存 + rAF × 2 + 100ms + 300ms 多时机重试（覆盖字体/图片异步加载引起位置回弹）+ 删除 body 末尾旧脚本避免重复监听。(2) 3 个 GET form 还指向老 URL `/04` 改 `/insights`：`04_daily_trend.html` / `04_rank.html` / `04_word_freq.html`（`04_owner` / `04_table` / `04_similar` 此前已统一过）。(3) 其他 7 个 POST form（01 顶 selectbox / 01 生成 / 01 选 ABC / 02 诊断 / 02 改写 / 03 上传 / 03 评估 / 04 上传 / 05 上传）都已由 capture 阶段 submit 监听覆盖，无需改动。**不动**：业务层 0 行改动；LLM modal `hx-post` 走 HTMX 局部刷新不导航不受影响。**验证**：6 路由 + 所有 form action + 1 次 `python -m py_compile web/app.py` 全过；verify.py 仍 **847 PASS / 0 FAIL**（无回归）。 | **847（CLI）/ 0 回归** |
| **Phase 37** UI 统一化 + design.md + 「真实结果回流 → 结果反哺」改名（2026-09-01 用户拍板"是否统一"） | 用户反馈"首页和内容工坊设计统一，后面 4 页不统一"，需要把整套设计 token 化复用。**4 块工作**：<br>**① 新建 `design.md`**（22KB / 9 章节 + 2 附录）作为设计系统 source of truth：10 颜色 + 10 字号令牌 + 13 原子组件 + 6 分子组件 + 4 页面骨架 + 当前不一致清单（§5）+ 使用指南 + 演进 roadmap P0-P4 + 8 反模式 + CI lint + 48 类名速查。<br>**② 11 个新 CSS 类**抽出来（`style.css`）：`file-input / form-row-inline / checkbox-label / mv-sm / mv-md / stat-line / cand-meta / btn-sm / btn-submit / btn-dark / panel-flat`；加 4 条 panel-card 间距自动规则（`panel-card + .panel-card { margin-top:14px }` 等）；`.btn-dark/.btn-sm/.btn-submit` 必须放在 `.btn` 之后（**CSS specificity 同级后定义胜出**，line 580+ 否则会被 `.btn` 白底黑字基础类覆盖）。<br>**③ 5 个页面 + 7 个 partial 适配**：02 文案诊断 / 03 批量预测 / 04 历史洞察 / 05 结果反哺 + 6 个 04 partial + 02_rule_panel + 02_similar_rewrites + 04_daily_trend → 全部黑底白字 `.btn-dark` + 统一警告/成功 banner + 统一文件输入框 + 统一 metric 内字号（`.mv-sm/.mv-md`）；批量预测「批量评估」文案→「批量预测」+「评估结果」→「预测结果」+「无法启动评估」→「无法启动预测」；批量评估页面 CSV「评估」→「预测」；下载结果按钮 `.btn-dark` 化。<br>**④ 「真实结果回流」→「结果反哺」全程改名**：导航条 nav_pages + 02_诊断 partial 路径链接 + 05 页面 title + 02 文案诊断 03 历史洞察 04 结果反哺 5 处文案；`web/app.py:243` subtitle 同步。**CSS specificity 修过 1 次坑**：用户报告"按钮还是土黄色" + "白底黑字"，根因 `.btn` 基础类定义晚于 `.btn-dark`，同级后定义胜出。**不动**：业务层 0 行改动；Phase 26 5 页面 + 13 API 路径全保留。**验证**：6 路由 + `python -m py_compile web/app.py` 全过；verify.py 仍 **847 PASS / 0 FAIL**（无回归）。**Commit**：`bc198d5`（本地） + design.md 创文件。 | **847（CLI）/ 0 回归** |
| **Phase 38** 5-agent BUG 审查 + 9 修复（2026-09-01 用户拍板"创建几个agent快速审查"） | 用户拍板"创建几个agent快速审查 5 模块是否有 BUG"。**起手先 git commit 基线（`bc198d5`）保护远端未推代码不被改坏**，5 个 Explore agent 并发跑：内容工坊 / 文案诊断 / 批量预测 / 历史洞察 / 结果反哺。**Agent 1-5 共报 38 BUG**，按严重度去重 + 验证后落地修 **3 CRITICAL + 6 HIGH**：<br>**CRITICAL-1**（`web/app.py:717`）批量预测 `int(bool_Series)` 缺右括号 → `int(((bool_Series).sum()))` 修复。**影响**：批量预测 5 个聚合指标（n_pass / n_warn / n_blocked / n_ctr_ok / n_err）之前恒归零，被 line 729 的 except 兜底。<br>**CRITICAL-2**（`web/app.py:953`）`compare_token()` 返回嵌套 `{"含":{...},"不含":{...}}` 但 app.py 读扁平键 → 改成 `cmp["含"]["reach"]` 等嵌套访问 + CTR 单位 %（来自 `_weighted_ctr`）一致。**影响**：选词对比 6 metric 之前恒为 0。<br>**CRITICAL-3**（`core/schemas.py:344`）`RuleResult.to_dict()` 漏 `passes/warns/fails/has_blocking` → 补上 4 字段。**影响**：02 文案诊断阻断计数全错（`02_rule_panel.html` 第 15 行模板用 `rule.passes|length` 等读不到）。<br>**HIGH-1**（`web/app.py:702`）`ctr_mode="demo"` 硬编码 → 跟 01 同样逻辑（L1 status=model 时走 l1_model，否则降级 demo）。**影响**：Phase 31A L1 blended 路径在批量页永不触发。<br>**HIGH-2**（`services/batch_evaluation_service.py:33-38`）别名补 `subject / 内容 / workday_type` + evaluate_batch 透传 workday + `predict_one` 加 workday 入参。**影响**：海外业务方按英文 CSV 习惯 + `workday_type` 模板必填列变死字段。<br>**HIGH-3**（`web/templates/partials/04_*.html` ×5 文件 9 处）`{% if params.X == v %}selected{% endif %}` 字符串 vs 整数比对 → `{% if params.X|string == v|string %}`。**影响**：所有数字下拉框 selected 视觉失效（数据正确但用户感知未提交）。<br>**HIGH-4**（`core/csv_utils.py:21-43`）CSV 链式 fallback `utf-8-sig → utf-8 → gbk → gb18030`。**影响**：Windows Excel 中文 CSV 不再 UnicodeDecodeError。<br>**HIGH-5**（`web/app.py:472-489`）02 相似表 `display_cols` 错位 → 显式映射 `plan_name → title` / `加权CTR% → ctr` / body 标 None + 容错。**影响**：相似 Plan 表之前几乎空数据。<br>**HIGH-6**（`config/channel_rules.yaml`）补「微信小程序订阅消息」渠道规则（CHANNELS 第 4 项）。**影响**：诊断时第 4 渠道走兜底规则而非业务定义。<br>**修前必 verify**：每条 BUG 修前 Read/grep 确认是真的 BUG；Agent 1 报的 BUG #1（"panel-heading"2"残留语法错误）经 Read line 16 验证为**幻觉**，跳过。<br>**不动 MEDIUM/LOW**（10+ 项）：聚合重复调用、`<br>` 在 flex 不换行、`.xls` 缺 xlrd、tab 链接丢参数、CSV 千分位 "1,000"、`04_table.html` 注释错文件名、`source_label` 缺省静默等 — 风险/收益比偏低，留待下轮。<br>**验证**：所有改动 `python -m py_compile` 全过（web/app.py / core/schemas.py / core/csv_utils.py / services/ctr_prediction_service.py / services/batch_evaluation_service.py / services/text_analyzer.py / services/similarity_service.py / tests/verify.py）；verify.py 仍 **847 PASS / 0 FAIL**（无回归）。**Commit**：`1d7dd0e`（本地）。 | **847（CLI）/ 0 回归** |
| **Phase 38 A1-mid** 22 处 inline style 收敛 + design.md §0.1 DNA + §12 避坑（2026-09-01） | 用户拍板「02/03/04/05 UI 调性统一」走 A1-mid 范围。**前置发现**：Handoff §6.0 写的 847/0 与实际 842/5 不一致（**Handoff 数字漂移**，详见 design.md §12.1），5 FAIL 全是 verify.py 同步漂移：① Phase 28 必填 4→3 / ② Phase 30 options_with_custom +1→+2 / ③ PLAN_TYPES 3→4 / ④ llm_status 默认测试受用户家目录 yaml 污染（加 tmpdir 隔离修复）/ ⑤ sweep TaskInput stage 选填跳过。<br>**22 处 inline style 收敛**：8 个新 CSS 类（`form-grid-tri/quad`、`metric-row-tri/quad/bi/spaced`、`card-desc-spaced/spaced-sm`、`subsection-tight`、`stat-line-muted`、`link-download`）+ 4 条自动间距规则（`.kpi-tile + .kpi-tile` / `.candidate-card + .candidate-card` / `.panel-card .warning-banner` / `.panel-card .batch-wrap`）。**唯一 1 处 inline style 残留**：01 内容工坊主按钮业务特化（allowlist）。<br>**design.md 增量**：§0.1 一句话定义 + 参考 Layer 0（OneDrive DESIGN.md）/ §5 历史收敛记录 / §6.7-§6.9 新模式（form-grid-tri/quad、metric-row-tri/quad/bi/spaced、card-desc-spaced/spaced-sm）/ §10 AI Agent 5 步流程 / §11 质量检查清单 / §12 避坑教训 4 条（12.1 Handoff 数字漂移 / 12.2 inline 收敛暴露系统漏洞 / 12.3 design.md 缺 DNA 段 / 12.4 跨文件改动必须「改一个测试一个」）/ 附录 A 48→60 类 / 附录 B 变更日志。<br>**配套修改**：04_历史洞察.html `<title>` 去前缀 `04 历史洞察` → `历史洞察`（Phase 27 URL 语义化的尾巴）。<br>**验证**：848 PASS / 0 FAIL（含 1 新增 `options_with_custom 首位 = 通用`）+ inline style 1 处（allowlist）+ py_compile web/app.py 全过。<br>**3 commit 推送**：`fd94aea`（fix: A1-mid）/ `816eb85`（docs: §12 避坑）/ `f7835ef`（chore: 归档 push 脚本）。远端 HEAD `6e0be2cf7db6`。**顺手修脚本 bug**：push 脚本 archive 嵌套路径需 `.parent.parent.parent`（原 `.parent.parent` 只到 tools/）。 | **848（CLI）/ 0 回归** |
| **Phase 38 改名**「文案诊断 → 内容诊断」「批量预测 → 内容预测」（2026-09-01） | 用户拍板「文案诊断改成内容诊断，批量预测改成内容预测，记得尽量完整改」。**范围**：用户可见 UI 命名层（导航名 / title / 按钮 / 卡片描述 / 文档引用）；保留 service 名 / 函数名 / 枚举值（`batch_evaluation_service` / `predict_batch` 等内部标识符不动）。**改动**：① `web/app.py` NAV_PAGES nav name + subtitle + 路由注释 + Excel 模板 sheet 名；② `web/templates/home.html` 进阶能力卡片（02 卡片 / 03 卡片）；③ `web/templates/pages/02_内容诊断.html` title（HTML 文件重命名 `02_文案诊断.html` → `02_内容诊断.html`，`03_批量评估.html` → `03_内容预测.html`）；④ `web/templates/pages/03_内容预测.html` title / Demo 模式 / 启动按钮文案 / 「下一步：启动内容预测」；⑤ `pages/_deprecated/02 内容诊断.py` + `03 内容预测.py` header / page_setup / button（文件重命名 `02 文案诊断.py` → `02 内容诊断.py`，`03 批量评估.py` → `03 内容预测.py`）；⑥ `pages/_deprecated/00 首页.py` 入口链接 / `README.md` 文件名清单；⑦ `tests/verify.py` 8 处路径断言 + section 标题 + 注释；⑧ `web/README.md` tree 文件名；⑨ `design.md` 4 处页面名引用 + `.diag-grid` 表格 + style.css 注释；⑩ `docs/architecture.md` + `overview.html` + `docs/overview.html` mermaid 节点标签；⑪ `CLAUDE.md` 模块树注释；⑫ Handoff §6.0 已可用模块摘要。**不动**：服务层 `batch_evaluation_service` / `predict_batch` / `predict_l1_batch` / `evaluate_batch` / `classify_coupon_batch` 等内部函数；PRD.md 历史段（设计文档不改历史）；旧 phase 决策段（line 125-133）；deprecated `pages/02_copy_diagnosis.py` / `pages/03_batch_evaluation.py` 文件名（已是历史路径，不重命名）。**验证**：848 PASS / 0 FAIL（同步改 verify.py 路径断言后无回归）。 | **848（CLI）/ 0 回归** |
| **Phase 40-43** 字典维护鉴权 + 3 个连环 BUG 修复（2026-09-02） | 用户拍板"左侧栏不显示字典维护入口 + 简单密码鉴权（密码 `ori1026`，无 SSO）"→ 修 2 个连环 BUG → 修第三个 BUG。**4 个 phase 一气呵成**：<br>**Phase 40** 字典鉴权 + 左侧栏隐藏：`web/app.py` `NAV_PAGES` 加 `hidden_in_nav: True` 标记 settings 项；`base.html` nav 循环跳过 `hidden_in_nav` 项；新增 `SETTINGS_PASSWORD` / `SETTINGS_COOKIE_NAME` 常量 + HMAC-SHA256 签名 cookie (`httponly + samesite=lax + path=/`) + `_make_settings_cookie` / `_verify_settings_cookie` / `_settings_auth_or_redirect` helper；新增 3 个路由：`GET /settings/login` / `POST /settings/login` / `GET /settings/logout`；现有 `/settings` + `/api/settings/save` + `/api/settings/download` 全部加鉴权装饰。`home.html` 字典管理区底部「停用词」行（× icon）。`web/templates/pages/06_settings_login.html` 新建（简洁居中卡片）。`static/css/style.css` 加 `.settings-head` + `.login-wrap`。**关键 BUG 1**：cookie `path=/settings` 严格匹配 → `/api/settings/*` 不发送 → 全 401 → 改 `path=/` 修。<br>**Phase 41** textarea 双重 escape BUG + 加 stopwords 字典：Jinja autoescape + `| e` 双重 escape → `&#34;` 等 entity 字符串写进 textarea 浏览器不解析。**修**：textarea 内容改 `<script type="application/json" id="dict-init-X">{{ d.content | tojson }}</script>` + JS 读 `.textContent` 后 `JSON.parse` 填入 textarea。但又触发第二个 BUG。<br>**Phase 42** textarea `\n` attribute 截断 BUG：HTML5 spec attribute value 遇 LF 截断。tojson 输出 `"word1\nword2"`，HTML parser 在 `\n` 处截断 attribute → 数据丢失。**修**：tojson 输出挪到 `<script type="application/json">` tag（script 标签内容可以是任意字符包括 \n，HTML parser 不截断）。<br>**Phase 43** 双 CR BUG + .gitattributes 防御：浏览器 textarea 写 LF + Windows git autocrlf 把 LF 转 CRLF 但因为历史 CRLF 残留 → commit 时叠加变成 `\r\r\n`（双 CR）。**修**：① Python 脚本清空 `custom_dict.txt` 双 CR + 空行（135 行 → 68 行 67 词，纯 LF）；② 新建 `.gitattributes` `data/*.txt text eol=crlf`（防止 git autocrlf 叠加造成 `\r\r\n`）；③ `_write_dict_file` 写 text 类字典统一 CRLF（textarea 写 LF + Windows autocrlf 双 CR 防御），yaml/json 保留原样（保留缩进）；④ `data/stopwords.txt` 加 `stopwords` reload 分支（Phase 40 已经加字典项）。**不动**：业务层 0 行改动；HMAC-SHA256 secret 从 `SECRET_KEY` env 拿（Phase 25 已有约定）；Phase 26 5 页面 + 13 API 路径全保留。<br>**验证**：`python tests/verify.py` 仍 **848 PASS / 0 FAIL**（无回归）；smoke 7 case 全过（settings 鉴权链路 + 字典读写 + cookie path 修复）。**Commit**：`d6417c9`（本地 + 远端 `32508fb3bd62`）—— `.gitattributes` + `web/app.py` + `data/custom_dict.txt`。 | **848（CLI）/ 0 回归** |
| **Phase 44** _write_dict_file 4 重防御（双 CR + 空行 + trailing space）（2026-09-02） | 用户再报"保存后中间插入一行空格"——Phase 43 的 bytes replace 漏掉了**回旋效应**场景：当 input 含历史 `\r\r\n` 双 CR 时，`replace(\r\n → \n)` 只吃掉 CRLF（第二个 + 第三个字节），剩下孤 `\r`，再 `replace(\n → \r\n)` 又在孤 `\r` 前加 `\r` → **又变成 `\r\r\n`**。用户试探"换表格"方案。<br>**新算法 4 重防御**：① CRLF / 孤 CR 全部归一 LF（破回旋）；② 过滤空行（HEAD stopwords.txt 原含 1 空行）；③ 每行 rstrip 去行尾空格（保留前导缩进）；④ 输出 CRLF（gitattributes eol=crlf 一致）。保留 `#` 注释行（jieba load_userdict 容忍）。<br>**验证**：16/16 单元测试（LF / CRLF / 双 CR / 孤 CR / 混合 / 空行 / 前后空格 / 无 trailing newline / 中文）+ smoke 双 CR + 空行 e2e 全过；848 PASS / 0 FAIL 无回归。<br>**Commit**：`3ba20c5`（本地 + 远端 `956ec3b64cd8`）—— `web/app.py` 1 文件 +4 -10 行。<br>**不动**：textarea UI 形态（4 重防御已能防住所有 line ending 边界，表格方案作为备选留待后续）；push 脚本顺手修 archive 嵌套 ROOT 路径（`.parent.parent` → `.parent.parent.parent`，Phase 38 A1-mid 教训 §13 复现又踩了一次）。 | **848（CLI）/ 0 回归** |
| **Phase 45** 字典保存自动备份（每天首次保存触发）（2026-09-02） | 用户担心字典维护手残误删，要求本地备份。**第 1 版**：CLI 脚本 + 双击 .bat（`tools/backup_dicts.py` + `tools/backup_dicts.bat`）+ `.gitignore` `data/.backups/`。**第 2 版（用户反馈）**：应该是**每次保存时自动备份**（不是手动跑），每天首次保存触发一次，后续同一天保存跳过（去重）。<br>**改动**：① `tools/backup_dicts.py` 加 `has_backup_today()` + `create_backup_internal(days=14)` 内部 API（web handler 可调用）；② `web/app.py` settings_save 在 `_write_dict_file` 成功后调用 `create_backup_internal`，flash_msg 拼上备份信息；③ 备份失败 try/except 兜底，**不影响保存流程**。<br>**flash 文案**（用户每次保存后看到）：<br>• 首次保存：「产品词典 保存成功 · 已自动备份 7 个字典文件 (19,309 字节)」<br>• 同天重复：「产品词典 保存成功 · 今天已备份过（dicts_2026-09-02_153217.tar.gz），跳过」<br>**设计细节**：tar.gz 压缩比约 3x（19KB → 7KB）；自动清理 14 天前旧备份；`data/.backups/` 已 `.gitignore` 不污染 git；与 git 远端历史双重保险（本地 tar.gz → git 历史 → 重写文件）。<br>**验证**：e2e smoke 全过（首次 → 1 个备份 / 重复 → 仍 1 个备份 + 跳过消息）；848 PASS / 0 FAIL 无回归。<br>**Commit 1**（手动脚本）：`8d09f71`（本地 + 远端 `6a7ad524869c`）—— `tools/backup_dicts.py` + `.bat` + `.gitignore`。<br>**Commit 2**（自动触发）：`4c032a6`（本地 + 远端 `51ed42480e56`）—— `tools/backup_dicts.py` 内化 API + `web/app.py` settings_save hook。 | **848（CLI）/ 0 回归** |
| **Phase 46** 历史洞察 4 BUG 修复 + wf/ef/rank 3 Tab 查询增强（2026-09-02） | 用户反馈"我再检查一遍" → 发现 4 个 BUG：①`/insights?tab=daily` 500（pandas `round()` 不接受 `pd.NA` → 分母为 0 时崩）；②`/insights?tab=wf` 选词对比是 `<select>` 但词太多应改 `<input type=text>`；③wf 表单提交后 tab 跳回 rank（form 不带 tab 参数 → 后端 default = "rank"）；④单词对比区块在高效词/低效词下面 → 提交后视觉"跳一下"。<br>**修复**：①`services/analytics/daily_trend.py:91` 周环比计算 `ratio_pct.astype("Float64")` 走 nullable 类型后再 `.round(2)`（NA 不会被 round 报错）；②`04_word_freq.html` `<select name="wf_compare_sel">` → `<input type="text" placeholder="任意词...">`；③6 个 insights tab form 全部加 `<input type="hidden" name="tab" value="X" />`（rank/wf/ef/sim/owner/daily，6 个）；④`04_word_freq.html` 重排：表单 → 单词对比 → 高效词 → 低效词（input/output 一对贴一起，自然不依赖 scroll 恢复）；⑤顺手扩 2 个查询能力：rank 加「输入 Plan ID 查详情」（新 `_plan_detail()` helper 返回 plan_name/channel/owner/触达/点击/CTR/n_records/n_days/字数均值/覆盖高效词数 + 样本标题正文）+ ef 加「输入 emoji 查对比」（复用 `compare_token(df, sel, col="_emojis")`）。<br>**踩坑**：`{{ plan_detail.加权CTR% }}` 中 `%` 关键字 + `}}%` 让 Jinja2 解析器崩（`unexpected ')'`），下标写法 `plan_detail['加权CTR%']` 解。详见 Handoff-lessons.md §19。<br>**改动文件**：①`web/app.py`（params 加 rank_plan_sel/ef_compare_sel + _plan_detail() helper + rank/ef 分支加 detail/compare 计算）；②`web/templates/partials/04_word_freq.html`（select→input + 重排）+ `04_rank.html`（加 input + 详情块）+ `04_table.html`（加 input + 对比块）；③`web/static/css/style.css`（`.form-row-span2{grid-column:span 2}`）+ `web/templates/base.html`（CSS 缓存 `?v=20260902wf`）。<br>**验证**：5 GET endpoints (daily/wf/rank/ef/sim/owner) + 6 tab form 提交 → 全部 200；rank_plan_sel=P202410110023 → 「Plan 详情 · P202410110023」区块渲染；848 PASS / 0 FAIL 无回归。 | **848（CLI）/ 0 回归** |

| **Phase 47** | 字典维护 UI 重设 + smoke tmpdir 教训（2026-09-03） | Handoff-todo.md §6.10 列出的"字典维护 UI 重设"待办。06_settings.html 是 Phase 40-43 阶段产物，form 用 `.dict-form` 自定义类、textarea + actions 用裸 div 嵌套，与 design.md §6 体系（panel-card + panel-heading + form-grid + form-row）脱节；与 04/05 业务页 UI 不统一。<br>**重设**：①标题去"06"前缀；②顶部 panel-card 改"字典维护说明"（去 topbar 重复）+ 保留退出登录按钮；③6 个字典 panel 走标准 `panel-card + panel-heading` 编号 1-6；④form 改统一 `form-grid + form-row form-row-wide`（替换 `.dict-form`）；⑤新加 1 个 CSS 类 `.dict-actions-row`；⑥文案 5→6 修正（Phase 41 加 stopwords 后实际是 6 个）。<br>**改动 4 文件**：`web/templates/pages/06_settings.html`（重设）+ `06_settings_login.html`（微调）+ `web/static/css/style.css`（+`.dict-actions-row`）+ `web/app.py`（docstring + line 309 stale comment 5→6 修正）。<br>**不动**：业务层 0 行 / 鉴权链路不变 / textarea + tojson + script tag 数据传递保留 / cookie path = / 保留 / LLM 配置入口集成（已通过右上角 pill 跳 modal）。<br>**踩坑**（Handoff-lessons.md §20）：smoke 用 `POST /api/settings/save/channel_rules` 测保存链路 → 真覆盖 `config/channel_rules.yaml` 为 `# test content from smoke 2026-09-03`（36 字节）→ `git checkout HEAD --` 还原（981 字节）。**铁律**：任何 `POST /api/*/save` / atomic write 类端点 → e2e smoke 必须 tmpdir 隔离；不支持 dry-run 的旧端点 → 单元测试覆盖，smoke 用 GET 类端点验证下载。<br>**验证**：`tests/verify.py` 848 PASS / 0 FAIL（无回归）；curl smoke /settings/login 200 / 未鉴权 /settings 303 / 登录 303 / 鉴权 /settings 200（40634 字节含 6 字典 panel）/ 字典下载 200（1517 字节）。<br>**Commit**（待用户决定）：4 个 web 文件未 commit；Handoff-lessons.md 第 20 条已落档；docstring + line 309 双 stale 注释已同步修。 | **848（CLI）/ 0 回归** |

> 详细 bullets 全部移入 §5 决策记录（按 commit hash 可追溯）。本表为速查。

### 6.2 待业务确认（按返工风险梯队）

> 详见 [`Handoff-todo.md` §6.2](Handoff-todo.md#62-待业务确认按返工风险梯队)。本文件 §6.4 是拍板落地状态。

### 6.3 候选（详 §5.5 CTR Roadmap）

> 详见 [`Handoff-todo.md` §6.3](Handoff-todo.md#63-候选详-55-ctr-roadmap)。

### 6.5 历史发现索引（防会话间记忆丢失）

> **铁律**（Handoff-lessons.md 第 9 条）：每次跑完 EDA / SHAP / 维度分析 / 业务统计 → 落档 `data/findings/<topic>_<date>.json` + 本表加一行。否则下次 session = 没跑。

| 主题 | 数据源 | 关键结论 | 文件 |
|---|---|---|---|
| 维度影响度分析（η²）⚠️ stale | `C:\Users\a952462\常用文件\数据\CNN历史备份0830.xlsx`（48,930 行） | η² 单维度方差解释度，作 L1 对照用。**主结论以 L1 行（feature_importance）为准**。本数据无 audience / stage / tone / scene 字段。 | [`data/findings/dimension_impact_2026-08-31_151231.json`](data/findings/dimension_impact_2026-08-31_151231.json) + [.md](data/findings/dimension_impact_2026-08-31_151231.md) |
| L1 特征重要性（首次跑 · 2026-08-28） | 4.4 万行训练 | Top 5：正文长度 35.19% / 标题长度 22.92% / 高效词命中 14.59% / 渠道: 短信 8.63% / 计划类型 TE 6.48% | [`data/reports/feature_importance_2026-08-31.txt`](data/reports/feature_importance_2026-08-31.txt) |

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

> 详见 [`Handoff-lessons.md`](Handoff-lessons.md)（**8 条核心教训**，~70 行 / 5KB，含已删节索引）。

---

## 8. 关键路径速查

| 路径 | 用途 |
|---|---|
| `C:\ideon\mcd-ai-content-platform\` | 新项目根 |
| `C:\ideon\mcd-ai-content-platform\PRD.md` | 产品需求文档（版本号见文件头） |
| `C:\ideon\mcd-ai-content-platform\CLAUDE.md` | AI 会话入门（必读） |
| `C:\ideon\mcd-ai-content-platform\Handoff-decisions.md` | **Phase 1-25 决策记录详（拆出，Phase 1-10 压 1-2 行 + why；Phase 11+ 保留，~200 行 / 15KB）** |
| `C:\ideon\mcd-ai-content-platform\Handoff-todo.md` | **待办与候选详（拆出，§6.3 候选已压摘要，~160 行 / 7.5KB）** |
| `C:\ideon\mcd-ai-content-platform\Handoff-lessons.md` | **教训全集（拆出，8 条核心，~70 行 / 5KB）** |
| `C:\ideon\mcd-ai-content-platform\docs\l1-training-runbook.md` | **L1 LightGBM 训练与运维 Runbook（5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报；责任人=用户，月度手动）** |
| `C:\ideon\mcd-ai-content-platform\tools\_archive\` | **历史 push 脚本归档（push_via_api.py / push_phase18-23_via_api.py / push_simplify_a1_via_api.py / push_phase22_a1_via_api.py ×9，Phase 25 mv 不 git mv）** |
| `C:\ideon\mcd-ai-content-platform\docs\ctr-feedback-schedule.md` | **CTR 校准触发条件（每月 1 号上午手动跑 calibrate_baseline.py）+ §3.5 L1 漂移监控步骤** |
| `C:\ideon\mcd-ai-content-platform\data\ctr_baseline.json` | CTR 基准 **7 维**（channel/audience/coupon/stage/scene/plan_type/owner） |
| `C:\ideon\mcd-ai-content-platform\data\records.db` | 生成记录 SQLite（自动建） |
| `C:\ideon\mcd-ai-content-platform\data\feedback.db` | 真实 CTR 回流 SQLite（Phase 5 P1） |
| `C:\ideon\mcd-ai-content-platform\config\llm_settings.yaml` | LLM Provider 留空配置（Phase 6 P0） |
| `C:\ideon\mcd-ai-content-platform\docs\ctr-kpi-definition-proposal-v0.2.md` | **CTR 口径拍板稿 v3.1（业务已对齐）** |
| `C:\ideon\mcd-ai-content-platform\core\data_window.py` | **bi_dt 取数时间基准（12 点前 INTERVAL 2 兜底）+ classify_date_type / classify_today_type（Phase 11 工作日/非工作日 2 值分类）** |
| `C:\ideon\mcd-ai-content-platform\core\text_classifier.py` | **classify_coupon_in_text(title, body) → "是"/"否"（Phase 12 #11 文案粒度含券词判断）** |
| `C:\ideon\mcd-ai-content-platform\config\coupon_keywords.yaml` | **优惠券关键词词典 v1.0（discount/coupon/link 三类）** |
| `C:\ideon\mcd-ai-content-platform\tools\clean_cnn_backup.py` | **CNN 历史备份清洗脚本（复用 日报清洗_new.py 解析 + 过滤 + 报告；输出 data/cnn_backup_cleaned.xlsx）** |
| `C:\ideon\mcd-ai-content-platform\data\cnn_backup_cleaned.xlsx` | **清洗后 CNN 历史备份（48307 行 / 3821 plan / 4 渠道 / 2024-10-15 ~ 2026-08-26）** |
| `C:\ideon\mcd-ai-content-platform\data\ctr_baseline_v3.1.1.bak.json` | **baseline JSON v3.1.1 备份（Phase 12 渠道清理前）** |
| `C:\ideon\mcd-ai-content-platform\config\channel_rules.yaml` | 4 渠道字数上限 |
| `C:\ideon\mcd-ai-content-platform\config\brand_rules.yaml` | 必带 / 风险 / 禁词 |
| `C:\ideon\mcd-ai-content-platform\prompts\copy_generation.py` | 生成候选 prompt v1.0 |
| `C:\ideon\mcd-ai-content-platform\prompts\copy_rewrite.py` | 改写 prompt v1.0 |
| `C:\ideon\mcd-ai-content-platform\Handoff-decisions.md` | **Phase 1-22 决策记录详（拆出，~285 行 / 40KB）** |
| `C:\ideon\mcd-ctr-predictor\ctr_predictor.py` | CTR 事实来源 |
| `C:\ideon\mcd-copy-analyzer\analyzer.py` | 文案分析事实来源 |
| `C:\ideon\mcd-copy-analyzer\Handoff.md` | 范式参考（精简版，10KB） |

---

## 9. 新 Session 第一步

1. 读本 Handoff（项目记忆，重点 **§6.0 快照 + §6.1 Phase 简表**）
2. 读 `CLAUDE.md`（架构 + 约束）
3. 读 `PRD.md §4.0 / §13.5 / §15.A`（三处补充）
4. 跑 `python tests/verify.py`（**854 PASS / 0 FAIL**，CLI 与 pytest 双路一致）
5. 看 `docs\ctr-kpi-definition-proposal-v0.2.md`（**当前 v3.1 拍板口径，v3.1.1 已落档**）
6. 按需跳转（**Handoff 拆 4 文件，跳转逻辑**）：
   - 决策背景 → `Handoff-decisions.md`（Phase 1-22 详，按 Phase 编号搜）
   - 历史教训 → `Handoff-lessons.md`（按目录/关键词搜）
   - 待办与候选 → `Handoff-todo.md`（§6.2 待确认 + §6.3 候选）
6. 当前是 **Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep + Phase 25 死代码清理/L1 runbook/Handoff 压缩 + Phase 26 Streamlit→FastAPI 全量 UI 迁移 + Phase 27 LLM 配置 UI 完整化 + URL 语义化 + Phase 36 滚动恢复 + Phase 37 UI 统一化 + Phase 38 5-agent BUG 审查 + 9 修复 + Phase 38 A1-mid 22 处 inline 收敛 + design.md §0.1 DNA/§12 避坑 + Phase 40-43 字典维护鉴权 + 3 个连环 BUG 修复 + Phase 44 _write_dict_file 4 重防御 + Phase 45 字典保存自动备份 + Phase 46 历史洞察 4 BUG 修复 + wf/ef/rank 3 Tab 查询增强 + Phase 47 字典维护 UI 重设 + smoke tmpdir 教训**（2026-08-28 → 2026-09-03）

---

## 10. Self-check

- [x] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）— `tools/_push_phase6p4_once.py` 一次性脚本已删；`data/ctr_baseline_v3.1.1.bak.json` 是 baseline 版本备份非临时文件
- [x] `python tests/verify.py` 全过（**854 PASS / 0 FAIL**，Phase 22 §58/§59/§60 + Phase 23 §11b + Phase 24 §61 增量无回归）
- [x] `python -m py_compile $(git ls-files '*.py')` 全过
- [x] 关键改动进 commit（如 git 化）
- [x] UI 无 emoji，沟通全中文（Phase 21 清理 7 处 page_icon/inline emoji，CLAUDE.md §9 红线合规）
- [x] Phase 18-22 + Phase 23 + Phase 24 Handoff §5/§6.0/§6.1/§6.2/§8/§9/§10 同步（Critical-1/2 安全加固 + 3 处小修 + 全量 smoke sweep；L1 模型首次确认 live，l1_model mode 真能跑）
- [x] **Phase 25 Handoff 同步**（2026-08-31）：§6.0 加 Phase 25 + Handoff 压缩 2 行；§6.1 Phase 25 行；§7 lessons 文件大小更新；§8 加 l1-training-runbook.md + tools/_archive/ + ctr-feedback-schedule.md；§10 self-check 加 Phase 25；Handoff 4 文件总 ~103KB → ~32KB
- [x] **Phase 26 Handoff 同步**（2026-09-01）：§6.0 加 Phase 26；§6.1 新增 Phase 26 行（Streamlit→FastAPI 迁移详情）；§10 self-check 加 Phase 26；§8 待补 web/ 路径表（详见 IDeon-项目全流程-Handoff.md §1 新增 mcd-ai-content-platform Web 工具行）
- [x] **Phase 27 Handoff 同步**（2026-09-01）：§6.0 加 Phase 27 + 用例 854 → 847（删 Streamlit 页面后）+ LLM 配置 UI 一段 + 当前迭代重点 7 项；§6.1 新增 Phase 27 行（LLM 配置 UI + URL 语义化 + 内容工坊去技术裸露 + UI 微调）；§9 当前阶段更新到 Phase 27；§10 self-check 加 Phase 27
- [x] **Phase 37 Handoff 同步**（2026-09-01）：§6.0 加 Phase 37；§6.1 新增 Phase 37 行（UI 统一化 + design.md + 真实结果回流→结果反哺 改名 + 5 文件 + 11 CSS 类 + 按钮黑底白字 + CSV cache buster）；§9 当前阶段更新到 Phase 37
- [x] **Phase 38 Handoff 同步**（2026-09-01）：§6.0 加 Phase 38；§6.1 新增 Phase 38 行（5-agent BUG 审查 → 38 候选 → 验证后修 3 CRITICAL + 6 HIGH）；§9 当前阶段更新到 Phase 38；git commit 1d7dd0e（本地）
- [x] **Phase 38 A1-mid Handoff 同步**（2026-09-01）：§6.0 加 Phase 38 A1-mid + 用例 847→848；§6.1 新增 Phase 38 A1-mid 行（22 inline 收敛 + design.md DNA/§12 避坑 + 5 FAIL 同步）；§9 当前阶段更新到 Phase 38 A1-mid；Handoff-decisions.md 加 Phase 38 A1-mid 决策段；Handoff-todo.md 加 §6.5 Phase 38 A1-mid 同步条目；Handoff-lessons.md 加 §11（Handoff 数字漂移）+ §12（跨文件改动必须「改一个测试一个」）+ §13（archive 嵌套 ROOT 路径）3 条新教训；3 commit 推送 fd94aea/816eb85/f7835ef；远端 HEAD 6e0be2cf7db6
- [x] **Phase 40-43 Handoff 同步**（2026-09-02）：§6.0 加 Phase 40-43（字典维护鉴权 + 3 个连环 BUG 修复）；§6.1 新增 Phase 40-43 行（settings 鉴权链路 + cookie path 修复 + textarea 双重 escape 修复 + tojson + script tag 避 attribute 截断 + 双 CR 清理 + .gitattributes 防御 + _write_dict_file CRLF 统一）；§9 当前阶段更新到 Phase 40-43；Handoff-decisions.md 加 Phase 40-43 决策段；Handoff-lessons.md 加 §14（cookie path 严格匹配坑）+ §15（HTML attribute 遇 \n 截断 spec 坑）+ §16（textarea 不解析 HTML entity）+ §17（git autocrlf 叠加双 CR 坑）4 条新教训；远端 HEAD 32508fb3bd62
- [x] **Phase 44 Handoff 同步**（2026-09-02）：§6.0/§6.1/§9 加 Phase 44（_write_dict_file 4 重防御：CRLF/孤 CR 归一 LF + 过滤空行 + rstrip + 输出 CRLF）；Handoff-decisions.md 加 Phase 44 决策段；Handoff-lessons.md 加 §18（bytes replace 回旋效应坑：双 CR 无法用 2-step replace 清理）；远端 HEAD 956ec3b64cd8
- [x] **Phase 45 Handoff 同步**（2026-09-02）：§6.0/§6.1/§9 加 Phase 45（字典本地备份：CLI .bat 双击 + web settings_save 自动触发 + 每天首次去重）；Handoff-decisions.md 加 Phase 45 决策段；远端 HEAD 51ed42480e56
- [x] **Phase 46 Handoff 同步**（2026-09-02）：§6.0/§6.1/§9 加 Phase 46（历史洞察 4 BUG 修复：daily 500 + wf select→input + 6 tab 跳转 + 单词对比重排；+ wf/ef/rank 3 Tab 查询增强：Plan ID 详情 + emoji 对比 + 单词 input）；Handoff-decisions.md 加 Phase 46 决策段；Handoff-todo.md 加 §6.9 Phase 46 同步；Handoff-lessons.md 加 §19（Jinja2 `dict.key%` 中 `%` 关键字 + `}}%` 解析崩坑）。<br>**Commits**：本地 `4e2bc39`（HEAD 含 push 脚本）/ `6e7533c`（15 文件 BUG+增强）；远端 `efbe7810f8de` / `96b4d838083b`（Git Data API 重写 commit SHA，本地+远端不一一对应但 tree 一致）。
- [x] **Phase 47 Handoff 同步**（2026-09-03）：§6.0/§6.1/§9 加 Phase 47（字典维护 UI 重设：标题去"06"+6 panel 编号+form-grid 化+5→6 文案修正；+ smoke tmpdir 教训）；Handoff-decisions.md 加 Phase 47 决策段；Handoff-todo.md 加 §6.10 Phase 47 同步；Handoff-lessons.md 加 §20（字典 e2e smoke 必须 tmpdir 隔离）。web/app.py docstring + line 309 双 stale 注释同步修。
