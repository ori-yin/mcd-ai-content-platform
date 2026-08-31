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

> **新会话 AI 直接读这段 ↓**

### 6.0 当前快照（最快定位状态）

> **⚠️ 口径说明（2026-08-31 · 诚实性修正）**：以下能力为**演示/离线口径 / 架构预留**，**非线上生产已跑通**，业务确认后接入：
> - **05 真实结果回流**：演示口径，**未接真实投放数据**，feedback.db 当前为空
> - **existing_predictor CTR 模式**：灰态二期，**当前无 predictor 注入**（生产口径未接通）
> - **objective / coupon（TaskInput 字段）**：灰态字段，**二期接入**
> - **records.db / feedback.db**：**尚未回传真实投放数据**
> - **train_dimension_weights.py**：v0.1 占位 · **暂不可用**（等 records.db 充实；Handoff §6.1 Phase 6 P4 段已标）
> - **闭环状态**：依赖用户**每月手动跑** `tools/calibrate_baseline.py` + `tools/monitor_l1_drift.py`；**不跑 = 闭环静默失效（非自动运行）**
> - **L1 数字**：以下 §6.1 Phase 18 段用 baseline v3.2 同口径实测值（2026-08-31 复现）

- **阶段**：**Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep + Phase 25 死代码清理/L1 runbook/Handoff 压缩**（2026-08-28 → 2026-08-31）
- **用例**：**854 PASS / 0 FAIL**（`python tests/verify.py`，794 → 854，§61 sweep 新增 24 用例 + §11b Critical-1/2 回归 6 用例）= pytest 双路一致
- **已可用模块**：①内容创作（01 生成 3 候选 + CTR 评估 + 阈值生效）；②真实回流（04 上传 CSV/Excel → 入库 → 4 维度聚合 → 写 baseline）；③历史洞察（04 七 Tab）；④批量评估 CTR（03）
- **L1 静默双轨 + 切主流程**：admin 在 sidebar ①勾选"显示 L1 实验对比（仅管理员）"才显示 L1 预测列（默认关）；②selectbox 选 "CTR 主流程模式"（demo / baseline_only / l1_model，默认 demo）—— 用户主动切 L1 时改这里即可；模型缺失/渠道不在训练范围时静默降级 unavailable，主流程不受影响
- **L1 漂移监控**：`tools/monitor_l1_drift.py` —— records.db (l1_model 预测) join feedback.db (真 CTR) → 整体/分渠道 MAE；超 baseline × 1.3 → 红字告警 + 写 data/drift_log.csv 留档；空 DB 优雅降级（配对数 < 5 不评估防误报）
- **代码质量清理**：02 页面 bug 修复 / LLM call LRU cache / weighted_ctr 合并 / 注释对齐 / 死代码删除 / CSV reader 合并 / rule_engine 重构 / jieba 批量向量化 / Streamlit 页面缓存 / 5 处死代码清理 / L1 predictor 静默双轨
- **Phase 25 死代码清理 + L1 runbook（2026-08-31）**：`tools/push_*_via_api.py` ×9 → `tools/_archive/`；`ui/plotly_helpers.axis_rate()` 删；`pages/01/02` 各 1 个 unused import 删；`ui/styles.py` 加 .l1-pill/.l1-label/.l1-value/.l1-meta 4 类（之前 01 引用但未声明）；black 格式化 3 文件；`docs/l1-training-runbook.md` 落地（**5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报**）
- **Handoff 压缩（2026-08-31）**：4 文件总 ~103KB → ~32KB（Phase 1-10 早期决策压 1-2 行 + why；Phase 11+ 保留；L1 已落地段指向 runbook；P4 + UI 重设延后标记）
- **已拍板落档（2026-08-31 用户会话，详 §6.2/§6.3）**：①自动定时校准延后（`weekly_calibrate.bat` 仅落档不调度）；②CTR 校准频率从每周一上午（Phase 7.1）改为**每月一次手动**（建议每月 1 号上午跑，`docs/ctr-feedback-schedule.md` 已同步修订 + §3.5 加 L1 漂移监控步骤）；③02-05 附属页 + 字典维护 UI（`pages/06_settings.py`）纳入正式版，UI 重设阶段一起做；④L1 训练责任人 = 用户自己跑；⑤L1 特征重要性**月报** + 用户自己看（Phase 22 B 已落）
- **首要任务**：真回流数据进来时手动跑 `python tools/calibrate_baseline.py --db data/feedback.db` 重算 baseline；切 L1 后跑 `python tools/monitor_l1_drift.py` 监控漂移；**用户在 sidebar selectbox 主动切 l1_model**
- **下一阶段（候选待启动）**：UI 整体重设计（用户反馈太丑，整体架构 + 布局待重构）—— find-skills 已调研，详见 §6.3 UI 重设计段
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

> 详细 bullets 全部移入 §5 决策记录（按 commit hash 可追溯）。本表为速查。

### 6.2 待业务确认（按返工风险梯队）

> 详见 [`Handoff-todo.md` §6.2](Handoff-todo.md#62-待业务确认按返工风险梯队)。本文件 §6.4 是拍板落地状态。

### 6.3 候选（详 §5.5 CTR Roadmap）

> 详见 [`Handoff-todo.md` §6.3](Handoff-todo.md#63-候选详-55-ctr-roadmap)。

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
6. 当前是 **Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep + Phase 25 死代码清理/L1 runbook/Handoff 压缩**（2026-08-28 → 2026-08-31）

---

## 10. Self-check

- [x] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）— `tools/_push_phase6p4_once.py` 一次性脚本已删；`data/ctr_baseline_v3.1.1.bak.json` 是 baseline 版本备份非临时文件
- [x] `python tests/verify.py` 全过（**854 PASS / 0 FAIL**，Phase 22 §58/§59/§60 + Phase 23 §11b + Phase 24 §61 增量无回归）
- [x] `python -m py_compile $(git ls-files '*.py')` 全过
- [x] 关键改动进 commit（如 git 化）
- [x] UI 无 emoji，沟通全中文（Phase 21 清理 7 处 page_icon/inline emoji，CLAUDE.md §9 红线合规）
- [x] Phase 18-22 + Phase 23 + Phase 24 Handoff §5/§6.0/§6.1/§6.2/§8/§9/§10 同步（Critical-1/2 安全加固 + 3 处小修 + 全量 smoke sweep；L1 模型首次确认 live，l1_model mode 真能跑）
- [x] **Phase 25 Handoff 同步**（2026-08-31）：§6.0 加 Phase 25 + Handoff 压缩 2 行；§6.1 Phase 25 行；§7 lessons 文件大小更新；§8 加 l1-training-runbook.md + tools/_archive/ + ctr-feedback-schedule.md；§10 self-check 加 Phase 25；Handoff 4 文件总 ~103KB → ~32KB
