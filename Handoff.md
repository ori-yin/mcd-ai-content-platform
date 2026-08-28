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

- **阶段**：**Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep**（2026-08-28）
- **用例**：**854 PASS / 0 FAIL**（`python tests/verify.py`，794 → 854，§61 sweep 新增 24 用例 + §11b Critical-1/2 回归 6 用例）= pytest 双路一致
- **已可用模块**：①内容创作（01 生成 3 候选 + CTR 评估 + 阈值生效）；②真实回流（04 上传 CSV/Excel → 入库 → 4 维度聚合 → 写 baseline）；③历史洞察（04 七 Tab）；④批量评估 CTR（03）
- **L1 静默双轨 + 切主流程**：admin 在 sidebar ①勾选"显示 L1 实验对比（仅管理员）"才显示 L1 预测列（默认关）；②selectbox 选 "CTR 主流程模式"（demo / baseline_only / l1_model，默认 demo）—— 用户主动切 L1 时改这里即可；模型缺失/渠道不在训练范围时静默降级 unavailable，主流程不受影响
- **L1 漂移监控**：`tools/monitor_l1_drift.py` —— records.db (l1_model 预测) join feedback.db (真 CTR) → 整体/分渠道 MAE；超 baseline × 1.3 → 红字告警 + 写 data/drift_log.csv 留档；空 DB 优雅降级（配对数 < 5 不评估防误报）
- **代码质量清理**：02 页面 bug 修复 / LLM call LRU cache / weighted_ctr 合并 / 注释对齐 / 死代码删除 / CSV reader 合并 / rule_engine 重构 / jieba 批量向量化 / Streamlit 页面缓存 / 5 处死代码清理 / L1 predictor 静默双轨
- **未做（用户拍板延后）**：自动定时校准（`weekly_calibrate.bat` 仅落档不调度）/ 训练责任人 + 特征重要性周报（详 §6.3）
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
| **Phase 6 P4** Handoff §6.3 纯工程候选扫掉 | config/dimension_weights.yaml + train_dimension_weights.py / feedback_lookup.py + 5 文件改动 / §43+§44 共 45 用例 | **473（CLI）/ 45（pytest）** |
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
| **Phase 18** L1 LightGBM PoC（剔除小程序 + 高效词 + 时间衰减） | 用户拍板"先试试看"。基于 cnn_backup_cleaned.xlsx 4.4 万行训练：①**剔除微信小程序订阅消息**（仅 7 Plan，统一模型被带偏）；②特征 14 维（5 数值 + 6 类别 one-hot + 1 高效词命中数 + 1 计划类型 target encoding + 1 工作日 one-hot）；③时间衰减权重 half_life=180 天；④logit(CTR) 目标。结果：L1 MAE 0.353%（vs L0 0.414% 降 14.8%），R² 0.136（vs L0 -0.005）。**3 渠道 L1 全胜**：APP Push 0.272%（vs L0 0.309%）/ 企微1v1 0.631%（vs L0 0.740%）/ 短信 0.215%（vs L0 0.351%）。**关键发现**：A/B 对比验证渠道×工作日交叉特征为负向（LightGBM 自己能学，显式加 = 特征冗余）。`tools/train_lgbm.py` 训练 + `tools/evaluate_lgbm.py` L1 vs L0 同口径对比 + `data/lgbm_model_v1.pkl` 模型 + `data/effective_words.json` 高效词表（62 词来自 word_frequency 差值>0.5）+ `data/lgbm_feature_meta.json` 特征元信息。**待做**：`adapters/ctr_predictor_adapter/l1_predictor.py` 接入 + 4 态分明 + 误差监控 + 业务方拍"特征重要性 Top10 每周给业务看" / "切 L1 时点" / "误差告警阈值" / "训练责任人"（§6.3）。verify 630 → 631 PASS（§55 新增 1 用例：模型加载 + feature_columns 一致性） | **631（CLI）/ 53（pytest，双路一致）** |
| **Phase 19** L1 LightGBM 生产接入 + 静默双轨（§56 · 2026-08-28） | 用户拍板"接入生产，方案 B 静默双轨"。**接入**：新建 `adapters/ctr_predictor_adapter/l1_predictor.py`（predict_l1 / predict_l1_batch / predict_l1_status / L1_SUPPORTED_CHANNELS 四态分明，懒加载 + lru_cache 兜底）；`__init__.py` 导出 4 符号。**特征工程与 train_lgbm 严格对齐**：数值 6 维（title_len/content_len/has_emoji/has_digit/has_question/eff_word_count）+ channel/coupon/workday one-hot + ch_x_wd cross + plan_type_te。**静默双轨**：`pages/01_content_studio.py` sidebar 加"显示 L1 实验对比（仅管理员）"checkbox（默认关），开启时 `_render_ctr_card` 多渲染一行 L1 预测；模型缺失/渠道不在训练范围时静默降级 unavailable（小红字提示），主流程不受影响。**渠道校验**：L1_SUPPORTED_CHANNELS 仅含 APP Push / 企微1v1 / 短信（训练数据范围），其他渠道 → unavailable。**容错**：lru_cache(maxsize=1) 加载模型，异常路径返回 (None, "unavailable") 不抛错。verify 655 → 677 PASS（§56 新增 22 用例） | **677（CLI）/ 54（pytest，双路一致）** |
| **Phase 20** l1_model mode 主流程接入 + 漂移监控（§57 · 2026-08-28） | 用户拍板"切 L1 时点用户主动" + "误差大告警"。**l1_model mode**：`CTRPredictionAdapter.VALID_MODES` 加 `"l1_model"`（5 态）；新方法 `_l1_model_pred` 走 `predict_l1`，4 态透传（model→model_prediction/source=l1_lightgbm，baseline_only→baseline_only，unavailable→unavailable）。**UI 主动切**：`pages/01_content_studio.py` sidebar 新增 "CTR 主流程模式" selectbox（demo/baseline_only/l1_model，默认 demo，env CTR_MODE 可覆盖）；L1 模型缺失时 l1_model 不可选。**漂移监控**：`tools/monitor_l1_drift.py` records.db (source=l1_lightgbm) join feedback.db (按 task_signature 聚合真 CTR) → 整体/分渠道 MAE vs baseline（lgbm_feature_meta.json）→ 超 1.3 倍红字告警 + 写 data/drift_log.csv 留档；配对数 < 5 优雅跳过（防小样本误报）。**切 L1 时点 / 误差告警阈值（30%）**：业务拍板 2 项已落，详见 §6.3。verify 677 → 697 PASS（§57 新增 20 用例） | **697（CLI）/ 55（pytest，双路一致）** |
| **Phase 21** simplify pass · 文档漂移 + 死代码 + UI emoji 清理（§58 · 2026-08-28） | 用户拍板"谨慎点修复，怕你修坏整体了"。先 Explore agent 逐项 grep 验证为死代码/漂移才动手：(1) **CLAUDE.md 漂移**：§3 架构图删 `services/record_service`（Phase 17 已删）+ `adapters/cache_adapter`（从未实现）；§4.4 `pytest tests/test_ctr_adapter.py` 加注释（文件尚未拆分）；§6.2 加 `l1_model` 模式（Phase 20 已落地）。(2) **死代码**：pages/05 删 2 个未用 import（`Optional` / `rate_value`）；pages/03 删 `show_col_map` 死 dict（保留「`suggestion` → `建议`」映射逻辑 + 加 `not in display.columns` 防御）；services/generation_service `_validate()` 删 if-pass 死块（body 是 `pass`，whitespace-only title 会进但无副作用）。(3) **UI emoji 清理**（CLAUDE.md §9 红线合规）：5 个 pages `page_icon` → `None`；home.py 内嵌 `<h1>🍟</h1>` `<h2>🚀</h2>` 删。**不动**：P2 灰色地带（pages/02 自构造 ProviderRouter）+ P3 风格（04 空行/01 三栏比例）+ adapter 末尾 import 顺序（已 `# noqa: E402`，运行无问题）。**验证**：Explore agent 确认无 verify.py 用例拦截；py_compile 3 个 .py 干净；verify.py 仍 **697 PASS / 0 FAIL**（无回归）。**不在 Phase 21 范围**：emoji 用法 P0 决策（红线本身是否调整）；CLAUDE.md §3 架构图与 Handoff 同步方式长期治理 | **697（CLI）/ 55（pytest，双路一致）** |
| **Phase 22 B** 特征重要性月报脚本（§58 · 2026-08-28） | 用户拍板"自己看为主，月报"。**新增 `tools/print_feature_importance.py`**（217 行）：加载 lgbm_model_v1.pkl + lgbm_feature_meta.json，算 importance_type=gain（支持 split），Top N 默认 10，与上次快照对比名次变化（±2 名算涨/跌，标 ↑/↓/新）；落档 `data/feature_importance_history/importance_YYYY-MM-DD_HHMMSS.json` + `data/reports/feature_importance_YYYY-MM-DD.txt`；Windows console 编码 fix（sys.stdout.reconfigure UTF-8）。**humanizer** 把内部列名翻成人话（`channel_APP_Push` → "渠道: APP Push"）。**首次跑结果**：正文长度 35.19% / 标题长度 22.92% / 高效词命中数 14.59% / 渠道: 短信 8.63% / 计划类型 TE 6.48%。verify 697 → **719 PASS**（§58 新增 22 用例） | **719（CLI）/ 56（pytest）** |
| **Phase 22 C** 漂移自动回退（§59 · 2026-08-28） | 用户拍板"自动切回 L0，不让人介入"。**新增 `core/active_mode.py`**（read/write/clear 三态 + ALLOWED_MODES = {demo, baseline_only, l1_model}）。**`tools/monitor_l1_drift.py` 加 `apply_auto_rollback(alert_level)`**：ALERT → 写 demo / WARN → 写 baseline_only / OK → 清文件；加 `--no-active-mode` CLI flag（默认开）。**`pages/01_content_studio.py` 启动读 `data/active_mode.txt`** → 覆盖 sidebar 默认 ctr_mode + 黄色 banner 提示"已被自动回退到 {mode}（漂移告警）"。**工作流**：monitor 跑出告警 → 写文件 → 下次开 01 页面 sidebar 自动显示 demo + 红字提示；人工确认后手动删文件恢复。verify 719 → **750 PASS**（§59 新增 31 用例） | **750（CLI）/ 57（pytest）** |
| **Phase 22 D** 批量预测自动落档 records.db（§60 · 2026-08-28） | 用户口径"批量跑的预测一定会投出去，必须回收校准"。**`services/batch_evaluation_service.py` 加 `batch_signature(row)`**（与 task_signature 同字段顺序：channel/coupon/plan_type/audience/stage/scene + 标题桶/正文桶，SHA1 截 12 位，batch 缺后 3 字段填空串）+ **`save_predictions_to_records(rows, db_path)`**（仅写 ctr_result_type 非空行，包成单候选 id="A" strategy="batch_eval" + ctr source 标 "batch_{result_type}"，单行失败不影响其他）。**`pages/03_batch_evaluation.py` 加 checkbox「保存预测到 records.db」**（默认关，按需开启）；评估完成自动调 save + 显示"已保存 N 条"。**闭环**：03 上传 CSV → 勾选 → 跑评估 → 自动落档 → 后续 `pages/05_feedback` 上传真实 CTR 时 feedback_repository 自动 join signature 算 MAE/MAPE。verify 750 → **794 PASS**（§60 新增 24 用例） | **794（CLI）/ 59（pytest，双路一致）** |
| **Phase 23** 安全加固 · Critical-1/2 + 3 处小修（§11b · 2026-08-28） | 用户拍板"1改，2改，3改"（Critical-1 API key 泄漏 + Critical-2 XSS + Required-1 page→core 误判跳过）。**(1) Critical-1**：`core/llm_gateway.py` 加 `_KEY_PATTERNS = [sk-..., Bearer ...]` + `_sanitize_error()` 兜底 + `_classify_call_error()` 归类 6 种稳定错误码（Authentication/Permission/RateLimit/Timeout/Connection/BadRequest，未识别走 fallback "API异常: <cls>"）；3 处 `_call_openai / _call_anthropic / parse_json_response` 全替换 str(e)[:N] → 稳定错误码 + stderr 完整日志（仅服务端）。**(2) Critical-2 XSS**：pages/01/02 `_render_channel_preview` 用 `html.escape()` 包 title/body；短信段数按 escape 前原始长度算（防 body_len 算多）；删除 5 个 pages 的死 import。**(3) Required-1 误判**：经核查 services/feedback_service.py 已走 repository 抽象、pages 只 import services 不直 repository（CLAUDE.md §4.1 合规），**误判跳过**。**(4) 3 处小修**：`prompts/copy_rewrite.py:117` parse_response 用 `_sanitize_error(str(e))[:80]` 兜底（防御性，同 Critical-1 模式）；`tools/monitor_l1_drift.py` 统一 `sys.exit(1)` + 抽 `MIN_REAL_REACH=50` 常量 + 新增 `--min-real-reach` arg + `import sys` 移顶部。**(5) page_setup 模块**：抽 `ui/page_chrome.py` `page_setup(page_id, subtitle)` 消除 5 pages × 14 行 chrome 模板。verify 794 → **830 PASS**（§11b 新增 6 回归用例：4 helper-level + 1 call-site mock 测 ProviderRouter.call 不透漏 sk-，+1 copy_rewrite sanitize） | **830（CLI）/ 60（pytest，双路一致）** |
| **Phase 24** 全量 smoke sweep（防退化 · §61 · 2026-08-28） | 用户拍板"完整测试"。把 §17-19 跑的 sweep 固定下来防回归：**§38 test_smoke_sweep** 24 用例覆盖 ①31 模块 import（core/services/adapters/repositories/prompts/ui 全集）②SQLite tmp dir 隔离读写（**关键：必须用 db_path 参数，不能默认走 data/**）③rule_engine 4 边界（空/超长/4 渠道/未知渠道不 crash）④ctr 5 modes 全过（含 l1_model 真模型加载：pred=0.00116，模型已 live）⑤TaskInput 4 必填字段校验（audience/channel/stage/tone）⑥similarity_service 空 DB ⑦copy_analysis_service.diagnose 返回结构 ⑧read_recent limit 边界 ⑨import_feedback 空 CSV。**新发现**：l1_model mode 实际能跑（lgbm_model_v1.pkl 已存在并能加载），PRD/CLAUDE.md 仅说 capability，**首次确认 L1 模型 live**。verify 830 → **854 PASS**（§61 sweep 新增 24 用例） | **854（CLI）/ 61（pytest，双路一致）** |

> 详细 bullets 全部移入 §5 决策记录（按 commit hash 可追溯）。本表为速查。

### 6.2 待业务确认（按返工风险梯队）

> 防返工背景见 `Downloads\Demo范围决策与待确认_2026-08-26.md`。**拍板前不动后端反哺 / 不启用灰态字段**。

**第一梯队（高返工 · 现在就该确认）**
- [x] **#5** CTR **口径定义**（哪个 CTR / 去重规则）—— ✅ Phase 6 P2 已拍板，详 `docs/ctr-kpi-definition-proposal-v0.2.md`
- [x] **#6** 反哺是否**影响生成排序**（A/B/C 候选排序）—— ✅ Phase 7.2 拍板：同意，rank_candidates_by_ctr 已实现（pred_ctr 降序 + title 长度兜底）
- [x] **#3** CTR 反哺**触发条件**（累计多少 plan / 定时？）—— ✅ Phase 7.1 拍板：每周一上午手动跑一次，详 `docs/ctr-feedback-schedule.md`

**第二梯队（中低返工 · 可后置）**
- [x] **#1** 产品与权益 维度枚举 + 是否参与生成 —— ✅ **Phase 9 已拍板**，详 `Downloads/decision-product-benefit-2026-08-26.md`（拆 `product_category` + `benefit_type` 两字段；10 产品 + 8 权益枚举 +「自定义」输入兜底；必填 + 参与生成；jieba 词典与 yaml 枚举解耦并行）
- [x] **#2** 投放目标 维度枚举 + 是否参与生成 —— ✅ **Phase 9 已拍板**，详 `Downloads/decision-objective-2026-08-26.md`（6 值 → 4 值收敛：品牌认知 / 点击驱动 / 转化促成 / 用户召回；**支持多选，逗号分隔，max 3，union 合并**；必填 + 参与生成 + 影响 strategy+tone，不约束 product；baseline 新增 objective_x_渠道 = 90 key，7 级回退兜底）
- [ ] **#4** CTR 校准频率（手动 / T+1 / 周）
- [ ] **#7** 02-05 附属页面**是否纳入正式版**（含字典维护 UI `pages/06_settings.py` 议题）

**第三梯队（用户口径 · Phase 10 拍板稿 · 2026-08-27 用户会话提）**

> 用户视角：维度设计需贴近业务实际，不是 form 字段堆积。**核心观点**：CTR 真实影响因子在**文案内容**（标题/正文是否带券、含场景关键词）而不是 form 字段值；投放日期影响系数靠工作日类型推算，不需要具体日期。

#### 已拍板（已落地 Phase 11 · 2026-08-27）

- [x] **#12 工作日/非工作日 2 值（用户简化拍板 2026-08-27 · Phase 11 已落地）**
  - **原始拍板稿是 3 值（法定节假日/非工作日/工作日），用户当天简化成 2 值**——不要日期选择器，法定节假日暂不做
  - 替换 date_input → selectbox 二选一：**工作日 / 非工作日**
  - 默认值按今天自动算（`classify_today_type()` 走 weekday 逻辑，周一~周五=工作日，周六周日=非工作日）
  - baseline JSON **不动**——现有 "渠道_x_工作日类型" 2 值 key（`data/ctr_baseline.json:135-146`）正好对齐，无需新增 3 值维度
  - 落地文件：
    - `core/data_window.py` 加 `classify_date_type(target) → "工作日"|"非工作日"` + `classify_today_type()` 工具函数（纯 weekday 逻辑，不依赖节假日字典）
    - `pages/01_content_studio.py:189` date_input → selectbox 2 值；默认按今日自动算
    - `core/schemas.py:187` `TaskInput.planned_send_date` 字段名保留（孤儿字段，下游 0 消费），注释更新为"工作日/非工作日 标签"
    - `tests/verify.py §45` 加 18 个用例（5 工作日 + 2 非工作日 + 3 输入类型 + 3 边界 + 3 跨年 + 1 today 合法 + 1 错误抛错）
  - 法定节假日 / 调休 暂不支持；baseline_lookup.py 现有 2 值 key 仍按"工作日/非工作日"统计（节假日日期会被算进"非工作日"）

#### 已落地（Phase 12 · 2026-08-27 · 用户喂 CNN0827 数据后一拍板）

- [x] **#8 渠道枚举清洗 + 对齐** —— 用户拍板："公众号推文删除"
  - 清洗脚本 `tools/clean_cnn_backup.py` 滤掉"无需渠道"(434) + "微信公众号推文"(19)，输出 `data/cnn_backup_cleaned.xlsx`（48307 行 / 3821 plan / 4 渠道）
  - baseline JSON v3.1 → **v3.1.1**：删 14 个 key（微信公众号推文 12 维度 + 微信订阅 2 维度 + optimal_chars 2 项）
  - schema `CHANNELS` 删"站内信" + 加"微信小程序订阅消息" + "企微 1v1" → "企微1v1"（跟数据源连写）；最终 4 渠道：`APP Push / 企微1v1 / 短信 / 微信小程序订阅消息`
- [x] **#9 Plan 命名统一** —— 用户拍板："按我的数据源来"
  - schema `PLAN_TYPES` 改 `("AARRPlan", "常规Plan", "未知")`（连写，跟数据一致）
  - baseline_lookup.py:76 顺手修 bug：原 `("AARRPlan", "普通Plan")` → 修 `("AARRPlan", "常规Plan")`（baseline JSON 实际用"常规Plan"，导致 *_常规Plan key 从未命中过；v3.0 → v3.1 一直有这个 bug）
- [x] **#10 场景字段改选填 + 内容推断** —— 用户拍板："必填改选填呗"
  - `TaskInput.REQUIRED_FIELDS` 从 5 → 4（去掉 scene）；scene 字段挪到 has-default 区（dataclass 字段顺序铁律）
  - 内容推断工具函数（`classify_scene_in_text`）**未做**——等用户喂场景关键词词典（`config/scene_keywords.yaml`）后再实现；baseline 新增"渠道_x_文案场景"维度同理等数据
- [x] **#11 用券双字段保留** —— 用户拍板："保留 form 字段，但是不是要加两个"
  - **用户假设反转**：CNN0827 数据验证 form "实际是否用券"才是主驱动（企微 1v1 form 用券 2.56x vs 文案含券 1.32x；APP Push 文案含券反向 0.84x）；用户拍板保留 form 字段
  - 新增第二个字段 `text_has_coupon: str = ""`（标题正文是否带券，由 `classify_coupon_in_text(title, body)` 推断）
  - `core/text_classifier.py` + `config/coupon_keywords.yaml` v1.0（discount/coupon/link 三类；删 `\d+元` 太宽）
  - `pages/01_content_studio.py` 加 selectbox；已有 coupon label 改"实际是否用券"
  - baseline_lookup.py 新增 `text_has_coupon` 参数 + "渠道_x_文案含券词" 维度分支（baseline JSON 暂无 key 走兜底；等用户重算 baseline）

#### Schema 兜底字段决策（Phase 12 · 2026-08-27 · 用户拍板）

- [x] **PLAN_TYPES / COUPON_FLAGS 保留"未知"** —— schema 兜底字段，非数据源枚举
  - 数据源枚举：计划类型只 2 值（AARRPlan 93.3% + 常规Plan 6.7%，distinct=2）；是否用券只 2 值（是 67.2% + 否 32.8%，distinct=2）
  - "未知"在 baseline_lookup 里的实际行为：`baseline_lookup.py:86` 接受 `("是", "否")` → "未知" 跳过 `渠道_x_是否用券` 维度分支 → 走 `渠道整体` 兜底（**粗粒度 fallback，不是 0 系数**）
  - 不删"未知"原因：form 字段不填时需要 UI 兜底；删了强制 form 必填损失 UX 防御性
- [x] **指数平滑衰减已实现** —— baseline JSON `calibration_lambda=0.01 / half_life_days=69.3 / weighted_method=exponential_decay`（`data/ctr_baseline.json:8-12`），所有维度 CTR 都是加权后的（越靠近 `last_updated` 权重越高，半衰期 69.3 天；2024-10 老数据权重 ≈ 0.0014）
- [x] **用券细分维度暂不做** —— 业务侧 form "是否" 已确认是主驱动（#11 反转）；数据列无结构化"用券类型"字段；关键词推断 ROI 不明确；等跑一阵 #11 双字段数据后看 CTR 离散度再决定

#### 已确认无需动

- [x] **#13 指数衰减（EMA）已实现** —— baseline JSON（`data/ctr_baseline.json:8-12`）已含 `calibration_lambda=0.01 / half_life_days=69.3 / weighted_method=exponential_decay`；`_note` 写"越靠近 2026-08-16 的数据权重越高"

#### 第三梯队 · 下次迭代目标

- 用户口径：**下次 session 喂数据 → 写入具体阈值**
- 落地路径：①用户给数据（Plan × CTR × 触达）→ ②按第三梯队已拍板项对齐 schema/baseline → ③`pages/05_feedback` 上传 / 直接走 `tools/calibrate_baseline.py --db data/feedback.db` → ④重算 `data/ctr_baseline.json` → ⑤下次 demo/真实预测就用新值
- 已落地前置：#12 工作日/非工作日 2 值（Phase 11）

### 6.3 候选（详 §5.5 CTR Roadmap）

**业务确认后启动**（下方 2 项候选 L1 + P4 待业务拍板；§6.3 原 P3 维度权重动态 + demo 数据回灌已在 Phase 6 P4 完成，见 §5）。

#### L1 · LightGBM 回归替 baseline 查找表（详 §5.5）✅ **Phase 18 已落地（2026-08-28）**

> **用户拍板"先试试看"**（2026-08-28），基于历史 CNN 4.4 万行数据直接训练。详见下方"Phase 18 L1 LightGBM PoC"段。下方为原 §5.5 设计稿，实际落地配置按 PoC 结果（剔除小程序 + 高效词 + 时间衰减）。

**一句话**：用 LightGBM 回归替 baseline 7 维查表，**结构化特征 + 中样本 + 可解释**三场景适配 GBDT，DNN 是过度设计。

**为什么是 GBDT 不是 DNN**：
- 输入 = 结构化表格（7 维 + 字数 + emoji + 命中词），不是文本/图像
- 样本 = 几千到几万（麦当劳业务体量），不是亿级
- 可解释 = 刚需——业务问"为什么这个 Plan CTR 高"，GBDT 出特征重要性，DNN 给一堆注意力
- DeepFM/DIN/Transformer 要亿级样本回本，喂不饱

**关键设计点**：
- **特征 X**：7 维基础 + 文本衍生（title_len/body_len/emoji_count/命中词数）+ 历史衍生（past_ctr_similar）+ 时段衍生（dayofweek/hour/is_holiday）
- **训练集**：feedback.db（真实 CTR）按 signature join records.db → 每个 plan 一行 (X, y)
- **样本阈值**：< 50 plan 走 baseline / 50-500 走 L0 EMA / **~ 1000 切 L1**（< 1000 易过拟合，叶节点多 + 噪声大）
- **离线回测门禁**：L1 MAE > L0 × 1.05 → 拒绝上线，回退 L0
- **冷启动兜底**：新维度组合 L1 也查不到，走 baseline 兜底（4 态分明不变）
- **误差曲线**（必备）：预测 vs 真实 MAE/MAPE 散点 + 时间趋势图；曲线往下 = 在学，平/往上 = 漂移触发告警

**落地步骤**（粗估 10 工作日）：
1. `tools/train_l1_model.py`（~150 行：加载 feedback.db → join → 训练集 → LightGBM 训练 → 保存 .pkl）
2. `adapters/ctr_predictor_adapter/l1_predictor.py`（~50 行：加载 .pkl + predict）
3. `CTRPredictionAdapter` mode 加 `"l1_model"`（~30 行）
4. `tools/plot_error_curve.py`（~80 行：每周预测 vs 真实 MAE 散点图）
5. `tests/verify.py §43` L1 模块（~10 用例）
6. 业务反馈：误差曲线图、特征重要性 Top10、模型切换门禁报告

**风险**：
1. **过拟合**：< 千条样本时 GBDT 不如 L0 EMA
2. **冷启动**：新维度组合必须走 baseline 兜底
3. **误差曲线不一定往下走**——可能持平或上漂，这是诊断信号（"在学" vs "漂移"）
4. **责任划分**：谁负责训练 / 谁负责监控 / 谁有权批准上线

**业务要拍 4 项**：
1. ✅ **切 L1 时点**：用户主动（sidebar selectbox 切到 l1_model 即可）—— Phase 20 已落地
2. ⏳ **谁来训练**：业务方跑 / 平台自动 / 数据团队跑？ → 待业务拍板
3. ✅ **误差告警阈值**：MAE 涨到 baseline × 1.3 触发告警 —— Phase 20 `tools/monitor_l1_drift.py` 已落地（建议 30%，工具参数可调 `--alert-ratio`）
4. ⏳ **可解释输出**：要不要把"特征重要性 Top10 维度"每周给业务看？ → 待业务拍板

**Phase 19 完成项（2026-08-28）**：
- ✅ `adapters/ctr_predictor_adapter/l1_predictor.py` 接入生产（predict_l1 / predict_l1_batch / predict_l1_status）
- ✅ `__init__.py` 导出 4 符号
- ✅ 静默双轨：`pages/01_content_studio.py` sidebar admin 开关，默认关
- ✅ 4 态分明：model / baseline_only（模型缺）/ unavailable（渠道不在训练范围 + 特征构造失败）
- ✅ 渠道校验：L1_SUPPORTED_CHANNELS = (APP Push, 企微1v1, 短信)
- ✅ 容错：lru_cache 加载 + 异常路径静默降级（不抛错影响主流程）
- ✅ 验证：verify 655 → 677 PASS（§56 新增 22 用例）

**Phase 20 完成项（2026-08-28）**：
- ✅ `CTRPredictionAdapter.VALID_MODES` 加 `"l1_model"`（5 态：existing_predictor/baseline_only/demo/l1_model/unavailable）
- ✅ `_l1_model_pred` 走 predict_l1 → 4 态透传（model→model_prediction/source=l1_lightgbm，baseline_only→baseline_only，unavailable→unavailable）
- ✅ `pages/01_content_studio.py` sidebar "CTR 主流程模式" selectbox（demo/baseline_only/l1_model，默认 demo，env CTR_MODE 可覆盖）；L1 模型缺失时 l1_model 不可选
- ✅ `tools/monitor_l1_drift.py` records.db join feedback.db → MAE vs baseline → 1.3x 告警 + drift_log.csv 留档
- ✅ 验证：verify 677 → 697 PASS（§57 新增 20 用例）

**Phase 19+20 未做（留给后续 Phase）**：
- ⏳ 训练责任人 + 重训调度机制
- ⏳ `tools/print_feature_importance.py` 特征重要性 Top10 周报
- ⏳ CTRPredictionAdapter mode 切主流程的回滚机制（万一 L1 漂移自动回退 demo）

---

#### P4 · 历史洞察签名关联（04 七 Tab 加 signature 视角）

**一句话**：把"哪条 Plan 后来效果如何"接进洞察 Tab，让业务闭环"看"反哺。

**当前状态**：`pages/04_historical_insights.py` 七 Tab 按 plan / 文案维度统计，没有"采纳后真实效果"视角。P4 加 signature 视角 = 新增第 8 Tab"签名关联"。

**为什么重要**：
- 闭环到"看"——业务验证"我推荐的文案投出去后真有人点吗"
- 反哺闭环可视化——哪些文案被采纳 → 投出去 → 真实 CTR 多高
- 找高效 Plan 模板——相似文案 vs 真实 CTR 找规律

**Tab 内容**：
- 表格按 signature 分组聚合：`signature` / `采纳数` / `预测 CTR 平均` / **feedback 接入后**加 `真实 CTR 中位数/P90` / `预测 vs 真实 diff`
- 散点图：预测 CTR (x) vs 真实 CTR (y)，每点一个 plan
- Top10 复用模板：采纳数最多的 signature

**数据来源**：
```
records.db    feedback.db
   ↓              ↓
   selected_id ←─signature─→ 真实 CTR（按 signature join）
```

没有 feedback 数据时只能看"采纳数"，无法做 CTR 对比——这正是当前状态。

**风险**：
1. **没数据时空着**——业务确认前不接真实数据，Tab 加了但只能看采纳数，可能觉得"没用"
2. **数据稀疏**——单 signature 可能只 1-2 个 plan，"中位数 CTR"无意义；加阈值保护（≥ N 才显示 CTR 列）
3. **混淆"采纳"和"成功"**——selected_id ≠ 投放成功，只是"运营最终选的那条"
4. **CTR 散点少时画不出**——feedback 样本 < 50 时散点只有几个点，无诊断价值
5. **与 L1 联动**——L1 训练数据正是"signature + 真实 CTR"，P4 是 L1 的"查看界面"

**落地步骤**（粗估 3 工作日）：
1. `services/signature_insight_service.py`（~100 行）
   - `summarize_signatures(records, feedback)` → `list[{signature, count, pred_ctr_avg, real_ctr_median}]`
   - 空数据兜底：`feedback is None` → 只返回采纳数维度
2. `pages/04_historical_insights.py` 加第 8 Tab（~80 行 + plotly 散点）
3. `tests/verify.py §43`（~6 用例：聚合、join、空数据兜底、稀疏过滤）
4. **联动 L1**：`signature_insight_service` 直接给 `train_l1_model.py` 提供训练数据

**业务要拍 4 项**：
1. **要不要加这个 Tab**：业务确认前不接真实数据，Tab 加了只能看采纳数——值不值得？
2. **CTR 列显示阈值**：feedback 样本 ≥ 多少才显示 CTR 列？建议 ≥ 50
3. **展示粒度**：signature（细 12 位指纹）vs strategy（A_核心利益直给 3 选 1）？
4. **与 L1 联动**：要不要 P4 先于 L1 做（先有"看"再有"用"）？

**建议节奏**：P4 先做（3 天）→ L1 后做（10 天）。先有"看"的能力，再上"用"的模型。

---

#### UI · 整体重设计（候选 · 2026-08-28 find-skills 调研）

**用户反馈（2026-08-28）**：核心逻辑（Phase 19-21 L1 主流程 + simplify 清理）已完成，**UI 太丑，整体架构 + 布局都有大问题**。下一步计划整体重构，不是修修补补。

**find-skills 调研结论**（2026-08-28）：

**已装可直接用**（`~\.claude\skills\`）：
- `developing-with-streamlit` —— **最对口**，Streamlit 官方，覆盖 dashboards / themes / layouts / 自定义组件 / 美化主题 / 性能
- `frontend-design` —— 通用前端设计
- `designing-beautiful-websites` —— 通用网站美化

**skills.sh 命中度高**（待评估装不装）：
| Skill | installs | 备注 |
|---|---|---|
| `vercel-labs/agent-skills@web-design-guidelines` | **584.6K** ⭐ | 通用 web 设计准则（Vercel/Next 背景） |
| `nextlevelbuilder/ui-ux-pro-max-skill@ckm:design-system` | 32.8K | UI/UX 设计系统（通用） |
| `firecrawl/firecrawl-workflows@firecrawl-dashboard-reporting` | 31.1K | dashboard 报告 |
| `wshobson/agents@kpi-dashboard-design` | 13.3K | KPI dashboard 设计 |

**SkillHub 国内源**：`skillhub: command not found`（CLI 未装），按 memory `install_skills.md` 应补装后同步搜国内源。

**下一步行动**：
1. 先跑 `python "C:/Users/a952462/.claude/skills/developing-with-streamlit/scripts/discover.py" --project-dir "C:/ideon/mcd-ai-content-platform"` 拿项目级 recommendations
2. 按 discover.py 输出决定要不要补装 `vercel-labs/agent-skills@web-design-guidelines`（设计规范通用补充）或 `ui-ux-pro-max-skill@design-system`（设计系统）
3. 选定 skill 后整体重构（CLAUDE.md §9 红线 + 走 skill 流水线，不自己糊 CSS）
4. Streamlit UI 改动注意 `feedback-streamlit-ui-iteration` 4 个常见坑（清理列表冲突、类名冲突、注入 DOM 不归 React 管、CSS 时序）

**作用域**：当前页面 6 个（app + 00-05）+ 顶部 banner 系统 + sidebar 主题；**不动后端逻辑**（已稳定，Phase 19-21 验证 697 PASS）。

---

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

### `@lru_cache` + 测试 monkey-patch 陷阱（2026-08-26 · Phase 6 P3）
`_load_yaml()` 加 `@functools.lru_cache(maxsize=1)` 后，测试 `ls.CONFIG_PATH = type(...)(新路径)` 改路径但 cache 仍命中首次调用的旧路径内容。
- **症状**：3 个 `_check` 全 FAIL——"全填 is_configured() == True" / "全填 missing_fields() == []" / "部分空 missing_fields 2 字段"
- **修法**：测试在每次 monkey-patch `CONFIG_PATH` 后调 `ls._load_yaml.cache_clear()`（4 处），让下次读取走新路径
- **铁律**：测试里改任何被 `lru_cache` 捕获的依赖（路径 / env / module-level dict），改完必 `cache_clear()`——`@lru_cache` 是按参数 hash 的，**闭包内全局变量不在 hash key 里**

### 手写 yaml 解析器 vs PyYAML（2026-08-26 · Phase 6 P3）
`ui/llm_status.py` v1 用 30 行手写解析（4 类边界：整行注释 / 行内注释 / 引号包裹 / 空串）。Handoff §7 已录"行内 # 注释陷阱"教训——**那本身就是过度设计的代价**。
- **现状**：`services/rule_engine.py:54-56` 已用 `yaml.safe_load` 加载 `channel_rules.yaml` / `brand_rules.yaml`，PyYAML 在 `requirements.txt` 已是依赖
- **修法**：删 30 行手写解析，1 行 `yaml.safe_load` 替——4 类边界 PyYAML 自动处理，教训条目同时作废
- **铁律**：项目里已有 yaml 用法就别自己造轮子；新模块加载 yaml 前先 grep `yaml.safe_load` 是否有先例

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
6. 按需跳转：
   - 决策背景 → `Handoff-decisions.md`（Phase 1-22 详，按 Phase 编号搜）
   - 历史教训 → 见本文件 §7
   - 待办清单 → 见本文件 §6.2
6. 当前是 **Phase 22 B/C/D 完成 + Phase 23 安全加固 + Phase 24 全量 sweep**（2026-08-28）

---

## 10. Self-check

- [x] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）— `tools/_push_phase6p4_once.py` 一次性脚本已删；`data/ctr_baseline_v3.1.1.bak.json` 是 baseline 版本备份非临时文件
- [x] `python tests/verify.py` 全过（**854 PASS / 0 FAIL**，Phase 22 §58/§59/§60 + Phase 23 §11b + Phase 24 §61 增量无回归）
- [x] `python -m py_compile $(git ls-files '*.py')` 全过
- [x] 关键改动进 commit（如 git 化）
- [x] UI 无 emoji，沟通全中文（Phase 21 清理 7 处 page_icon/inline emoji，CLAUDE.md §9 红线合规）
- [x] Phase 18-22 + Phase 23 + Phase 24 Handoff §5/§6.0/§6.1/§6.2/§8/§9/§10 同步（Critical-1/2 安全加固 + 3 处小修 + 全量 smoke sweep；L1 模型首次确认 live，l1_model mode 真能跑）
