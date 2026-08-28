# mcd-ai-content-platform — 决策记录（详）

> **何时读我**：新 session 想了解"为什么 Phase X 这样设计"时，按 Phase 编号搜这里。
> 速查表在 `Handoff.md` §6.1。

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
- **2026-08-26**：Phase 6 P3 simplify 清理（`/simplify` 4 agent 并行 review）—— 净减 56 行（-122 / +66），9 文件改动，verify 421 → 418 PASS：
  - **修 A `ui/llm_status.py`**：30 行手写 yaml 解析 → 1 行 `yaml.safe_load`（PyYAML 已在 `services/rule_engine.py` 用，无新依赖）；`_load_yaml()` 加 `@functools.lru_cache(maxsize=1)`，3 个入口共用单次读盘；测试 monkey-patch `CONFIG_PATH` 后需 `_load_yaml.cache_clear()`（4 处，见 §7 新增教训）
  - **修 B 4 处 v3.1 docstring 缩成 1 行**：`baseline_lookup.py` / `ctr_prediction_service.py` / `feedback_repository.py` / `calibrate_baseline.py`——关键词保留（满足 §41 tests 守护），详细复述只留 `data/ctr_baseline.json:_definition_note` 一处 ground truth
  - **修 C 删 `PENDING_FIELDS` 死元组**：schemas.py + tests/verify.py 删 3 个 `_check` 用例；`pages/01_content_studio` 控件逻辑不动（直接硬编码灰态字段名）
  - **修 D `core/data_window.py`**：删 `_to_local` aware datetime 死分支 + `DEFAULT_TZ_OFFSET_HOURS` 常量 + `tz_offset_hours` 参数（从来不被调用）；`SNAPSHOT_CUTOFF_HOUR` 保留为 `cutoff_hour` 默认值
  - **修 E `ui/notice.py`**：抽 `render_notice(prefix, body, css_class)`，2 个 wrapper (`render_advanced_notice` / `render_ctr_feedback_notice`) 调它；保留外部 API 不破坏 pages 调用方
  - **跳过**：建 `core/ctr_definition.py`（altitude F1+F2，改动太大 ROI 不足）/ `CONFIG_DIR` 集中（reuse F3）/ 3 套 CSS 合并（reuse F6）/ banner 路由表（altitude F3）/ JSON 4 字段去重（被 §41 测试守护）/ `00_home` 跳转（Phase 7 候选）
  - working tree clean，9 文件改动未 commit
- **2026-08-26**：Phase 7 业务拍板落地——第一梯队 #3 + #6 全部 ✅ 拍板；verify 418 → 428 PASS（新增 §42 10 用例）：
  - **#3 触发条件**：每周一上午手动跑 `tools/weekly_calibrate.bat` → `tools/calibrate_baseline.py --db data/feedback.db`；新文档 `docs/ctr-feedback-schedule.md`（节奏 / 跳过 / 漏周策略 / 看什么）；bat 文件 CRLF 转换走 §7 铁律
  - ⏸️ **Phase 16.5 用户拍板延后自动调度**：`weekly_calibrate.bat` 仅落档不调度；真回流数据进来时手动跑脚本即可；自动定时等下次业务拍板再启动
  - **#6 反哺影响排序**：新加 `services/generation_service.rank_candidates_by_ctr(candidates, ctr_results)` 纯函数（pred_ctr 降序 + title 长度兜底 + unavailable 排末尾）；`pages/01_content_studio` 在 `predict_for_candidates` 后调一次，默认 `selected_id` 改 `candidates[0].id`（CTR 最高那条）；`_render_recommendation` 文案加"按 CTR 降序展示（演示口径）"措辞
  - **顺手清理**：删 `tools/phase6_p1_push.py` + `phase6_p2_push.py`（Handoff §10 self-check "临时文件全清" 闭环）
  - 12 文件改动未 commit，等推送
- **2026-08-26**：Phase 8 pytest 迁移——CLAUDE.md §4.4 工程债完成（双路运行，按 `feedback-concise-replies` 紧凑）：
  - **新文件 `pytest.ini`**：testpaths=tests / python_files=verify.py+test_*.py / markers 按 Phase 划分（phase1~phase7 7 个 marker，待用）/ `-ra --strict-markers --tb=short` addopts
  - **verify.py 改造**：顶部加 `_RUNNING_UNDER_PYTEST = "pytest" in sys.modules`（模块加载时检测）；`_check` 失败时 pytest 模式 `raise AssertionError(msg)` / CLI 模式静默累计（保留旧行为 428 PASS）
  - **requirements.txt 早列** `pytest>=7.4.0` + `pytest-cov>=4.1.0`，本轮无依赖变更（pip 装的是 pytest 9.1.1）
  - **反向验证**：注入 `_check(..., False, ...)` → pytest 立刻报 `1 failed, AssertionError: ...`；恢复后 43 passed
  - **双路一致性**：`pytest tests/verify.py` → 43 passed in 6.20s；`python tests/verify.py` → 428 PASS, 0 FAIL（无回归）
  - **顺手发现**：本地 `06425eb` Handoff commit 与远端 `8102185` 内容字节相同、commit hash 不同（autocrlf=true CRLF vs LF 存 blob）—— `git reset --hard origin/main` 对齐，无内容损失
  - 推送走 Contents API（github.com 被墙），3 commit：本地 `0709f04` (pytest.ini + verify.py) + 本地 `6002e6c` (push_via_api.py FILES 切) + Contents API 合并推 → 远端 HEAD `1a7a2c3`
- **2026-08-26**：Phase 6 P4 完成——**Handoff §6.3 纯工程候选 2 项扫掉**（业务拍板项不动）：
  - **P3 维度权重动态**：`config/dimension_weights.yaml`（5 维度权重 + 6 baseline_modifiers + 元信息）+ `tools/train_dimension_weights.py`（仿 calibrate_baseline.py 结构，argparse + 三段策略 5/20 + .bak 备份；v0.1 占位不接真实数据，等业务确认）；`services/text_analyzer.diagnose_score:557` 加权聚合替等权 + 新增 `load_dimension_weights()` lru_cache(1) helper；`adapters/ctr_predictor_adapter/baseline_lookup.py` 6 个 return 分支加 `_apply_dimension_weights()`（clamp [0.5, 2.0]）+ `_load_dimension_modifiers()` helper
  - **demo 数据回灌**：新建 `feedback_lookup.py`（`FEEDBACK_READY_MIN_PLANS=50` / `count_distinct_plans()` / `is_feedback_ready()` lru_cache(1) / `lookup_feedback_ctr(sig)` lru_cache(128) / 全 try-except + 参数化 SQL 防注入）；`repositories/feedback_repository.count_distinct_plans()` 对外暴露；`services/ctr_prediction_service._candidate_to_row` 末尾加 `_signature` 字段；`adapters/ctr_predictor_adapter/prompt_builder.enrich_rows_for_llm` 透传 `_signature`；`adapters/ctr_predictor_adapter/_demo_pred` 开头 9 行 feedback 分支（confidence=0.7，signature 命中后 `pred_ctr=fb_ctr`；DB 不就绪 / 无 signature / miss 三态全走原 baseline × tm 兜底）；**adapter 直接 sqlite3，不 import repository**（CLAUDE.md §4.1 红线）
  - **不动**：`core/schemas.PredictionResult`（`result_type` 仍 4 值）/ `services/rule_engine` / `services/analytics/*` / 6 维回退顺序 / `_score_*` 原始打分函数 / 不接真实 feedback
  - verify.py 428 → **473 PASS, 0 FAIL**（§43 dimension_weights 20 用例 + §44 demo_feedback 25 用例）/ pytest 43 → **45 passed**（双路一致）
  - 本地拆 2 commit（`c83981f` 代码 + `c616354` Handoff §6.3 checkbox），远端通过 Contents API 合并推（`538f00f` 一次性合并 commit）；CLI emoji 撞 GBK → ASCII `[OK] [SKIP]` 替 ✓

- **2026-08-27**：Phase 15 baseline v3.2 重算 + row key 修复（用户口径）：
  - **用户口径**：CTR 不响应 form 字段是设计/数据双因——① baseline JSON 没建"渠道_x_文案含券词"维度 key ② baseline_lookup.py 接受 7 维回退，但 row key 与 prompt_builder 读 key 不一致（plan_type/coupon/owner 3 字段读不到）
  - **新增一次性脚本 `tools/recalc_text_has_coupon.py`**：从 `data/cnn_backup_cleaned.xlsx`（48307 行）按指数衰减 λ=0.01 半衰期 69.3 天聚合"渠道 × 文案含券词"维度 8 keys，写入 baseline JSON v3.1.1 → v3.2：
    ```
    APP Push_是 / APP Push_否         (n_plans=1777/734, reach=76亿/28亿, CTR=0.16%/0.19%)
    企微1v1_是 / 企微1v1_否           (n_plans=640/364, reach=10亿/3亿, CTR=0.75%/0.57%)
    微信小程序订阅消息_是/_否           (n_plans=82/42, reach=1.2亿/0.9亿, CTR=3.33%/3.17%)
    短信_是 / 短信_否                  (n_plans=336/59, reach=3.5亿/0.1亿, CTR=0.38%/0.14%)
    ```
  - **关键发现**：文案含券词对 CTR 影响**渠道差异极大**——
    - APP Push 文案带券反而低（0.16% < 0.19%）→ 用户可能因文案"打折味"反感
    - 企微1v1/微信小程序订阅/短信 文案带券高 1.32x / 1.05x / 2.77x
    - 印证 Phase 12 #11 用户假设反转：文案含券词不是统一方向影响，每个渠道不同
  - **`baseline_lookup.py` row key 修复**（Phase 14）：
    - `_candidate_to_row` 同时输出中英文 key（`channel/coupon/plan_type` + `渠道/是否用券/计划类型`），避免 prompt_builder 读 key 不到
    - 新增 `workday` 字段透传（之前 TaskInput.planned_send_date 是孤儿字段）
    - `prompt_builder.py:101` 修 `"普通Plan"` → `"常规Plan"`（与 baseline_lookup.py:82 对齐）
  - **测试**：verify.py §48 row key 9 用例 + §49 baseline v3.2 验证 14 用例 + §50 baseline version 断言松绑
  - verify.py 525 → **557 PASS, 0 FAIL**（pytest 双路一致）
  - **baseline JSON 自动备份**：`ctr_baseline.bak.json`（Phase 15 跑前的 v3.1.1 版本）
  - **不动**：calibrate_baseline.py（仍只覆盖 2 个维度；feedback.db 是空的） / feedback_records 表 schema / 02/03/04 业务页
  - commit + push via Contents API（github.com 仍被墙）

- **2026-08-27**：Phase 14 CTR 不响应 form 字段排查（用户报告）：
  - 用户报"选了具体指标 CTR 没变"
  - 排查发现 2 类根因：
    1. **row key 不匹配**：`_candidate_to_row` 输出英文 key（`plan_type/coupon/owner`），但 `prompt_builder.py:95/98/99` 读中文 key（`是否用券/计划类型/预算Owner`）—— 3 字段永远读不到
    2. **workday 孤儿字段**：`TaskInput.planned_send_date` 是孤儿字段（Handoff §11 Phase 11 拍板时发现），下游 0 消费
  - 修复：`_candidate_to_row` 中英文 key 双输出 + workday 透传
  - 与 Phase 15 合并落地（同一组测试 §48）

- **2026-08-27**：Phase 13 工具定位重定义 · UI 3 按钮砍齐（用户口径）：
  - **用户重新定义工具定位**：CTR 评估**辅助决策**工具，不是选文案工作流
  - **流程重定义**：
    ```
    业务方看 3 候选 + CTR 估计 → 自己决定采纳哪条 → 不入库
                                                ↓
    业务方自己导入生产系统投放 → 一周后导出 Excel → 上传 pages/05_feedback
                                                ↓
    tools/calibrate_baseline.py 每周一手动跑一次 → 新 baseline JSON
                                                ↓
    下周 CTR 预测更准（指数滑动 α=0.3 / 1.0；详见 docs/ctr-feedback-schedule.md）
    ```
  - **3 按钮全砍**：
    - ❌ 编辑候选 A → 无人用文案（业务方看后自己导入），编辑后 CTR 不重跑（`pages/01_content_studio.py:334-340` 只重算规则，CTR `ctr_results` 永远是生成时那版）
    - ❌ 恢复 AI 原文 → 依赖"编辑过"才能恢复，编辑砍了没意义
    - ❌ 保存当前选择 → records.db 是死数据（grep 验证：pages/02/03/04 没人读，pages/05_feedback 走独立 feedback.db 链路）
  - **`records.db` 保留但 UI 不调用**：
    - `GenerationRecord` / `record_service` / `sqlite_repository` / `task_signature` 全部保留（`tools/train_dimension_weights.py:97` 未来会读 records.db 关联 feedback.db 做维度权重训练；Handoff §6.3 L3 轻量模型升级）
    - UI 不暴露"保存当前选择"入口，业务方不点击 → records.db 不增长
  - **`Candidate` 字段重构**：
    - 删除：`title_edited` / `body_edited` 字段 + `effective_title` / `effective_body` / `is_edited` 属性 + `reset_edit()` 方法
    - 引用方改：`ctr_prediction_service.py:35-36` + `generation_service.py:55` + `rule_engine.py:355,360` + `pages/01_content_studio.py:282-283,391-392,630` 全改 `effective_*` → `title/body`
    - `task_signature` 算 `c.title / c.body` 长度桶（line 405-406）
  - **`pages/01_content_studio.py` 改动**：
    - 删 `_render_edit_area()` 整段（line 304-341），新增轻量 `_render_rule_panel()`（保留 PRD §8.4 规则诊断）
    - 删 `_save_current()` 整段（line 553-571）+ 顶部 docstring 同步简化
    - 清 import：`build_record` / `save_generation`
  - **测试**：verify.py §17 effective_title/is_edited/reset_edit 7 用例 → 8 用例 `hasattr(c, "title_edited")` 校验（确保字段不再存在）
  - verify.py 522 → **525 PASS, 0 FAIL**（pytest 双路一致）
  - **不动**：baseline JSON / `services/record_service` / `services/generation_service.build_record` / `repositories/sqlite_repository` / `tools/train_dimension_weights.py` / `pages/05_feedback` / 反哺管道
  - commit + push via Contents API（github.com 仍被墙）

- **2026-08-27**：Phase 12 schema "未知"兜底字段拍板（用户口径）：
  - **PLAN_TYPES 保留"未知"**：schema `PLAN_TYPES = ("AARRPlan", "常规Plan", "未知")` 中"未知"是 **form 字段默认值兜底**，不是数据源枚举（数据源只有 2 值，distinct=2）；删它会导致 form 不填时抛错，UI 必须强制选——失去 UX 防御性
  - **COUPON_FLAGS 保留"未知"**：同上，schema 兜底；数据源"是否用券"也只有 2 值
  - **"未知" ≠ 0 系数**（baseline_lookup.py:86 接受 `("是", "否")`）："未知" 跳过 `渠道_x_是否用券` 维度分支 → 走 `渠道整体` 兜底（粗粒度值）；"是/否" 命中该维度 → 用具体 CTR 系数
  - **指数平滑衰减已实现**（baseline JSON v3.0+）：`calibration_lambda=0.01 / half_life_days=69.3 / weighted_method=exponential_decay`（`data/ctr_baseline.json:8-12`），所有维度 CTR 值都是加权后的；越靠近 `last_updated` 的数据权重越高（半衰期 69.3 天）
  - **用券细分维度暂不做**（按 mcd-analysis 务实主义）：业务侧 form "是否" 已是主驱动（#11 反转验证），细分 ROI 暂不明确；数据列也没有结构化"用券类型"字段（只有 `是否用券` 1 列），关键词推断准确度有限；等跑一阵 #11 双字段数据后看 CTR 离散度再决定
  - **不动代码**：纯 Handoff 文档同步

- **2026-08-27**：Phase 12 #8/#9/#11 三项落地 + **#11 用户假设反转 + 用券双字段保留**：
  - **#11 用户假设反转**：用户原假设"标题正文带券词 CTR 影响更大"，CNN0827 数据验证**反转**——form "实际是否用券"才是主驱动（企微 1v1 form 用券 2.56x vs 文案含券 1.32x；APP Push 文案含券反向 0.84x）。**保留 form 字段**，新增"标题正文是否带券"作为第二个选填字段（双字段并存）
  - **#8 渠道清洗**（用户拍板）：清洗脚本 `tools/clean_cnn_backup.py` 滤掉"无需渠道"(434) + "微信公众号推文"(19)；baseline JSON v3.1.1 删 14 个 key（微信公众号推文 / 微信订阅 全维度 + optimal_chars）；schema CHANNELS 删"站内信" + 加"微信小程序订阅消息"
  - **#9 Plan 命名统一**（用户拍板"按数据源来"）：schema PLAN_TYPES 改 `("AARRPlan", "常规Plan", "未知")`（连写，跟数据一致）；schema CHANNELS "企微 1v1" → "企微1v1"；CHANNELS 4 渠道
  - **#10 SCENES 改选填**（用户拍板"必填改选填"）：TaskInput.REQUIRED_FIELDS 从 5 → 4；scene 字段挪到 has-default 区（dataclass 字段顺序铁律）
  - **#11 用券双字段**：①保留 form `coupon`（实际是否用券，plan 维度）；②新增 `text_has_coupon`（标题正文是否带券，文案粒度，由 `classify_coupon_in_text` 推断）
  - **bug 修复顺手**：baseline_lookup.py:76 写错 "普通Plan" → 修 "常规Plan"（baseline JSON 实际用"常规Plan"，导致 *_常规Plan key 从未命中过；v3.0 → v3.1 一直有这个 bug）
  - 落地 9 文件：
    - `core/schemas.py`：CHANNELS 4 渠道（APP Push/企微1v1/短信/微信小程序订阅消息）/PLAN_TYPES 3 值（连写）/TaskInput 新增 `text_has_coupon: str = ""` + scene 改选填
    - `core/text_classifier.py`：新增 `classify_coupon_in_text(title, body) → "是"/"否"`（纯函数 + lru_cache 加载 yaml）
    - `config/coupon_keywords.yaml`：v1.0 关键词词典（discount/coupon/link 三类）
    - `adapters/ctr_predictor_adapter/baseline_lookup.py`：修 "普通Plan"→"常规Plan" bug + 新增 `text_has_coupon` 参数 + "渠道_x_文案含券词" 维度分支
    - `data/ctr_baseline.json`：v3.1 → v3.1.1（删 14 个 key + 元信息 _note 加 2026-08-27 渠道清理说明 + 备份 `ctr_baseline_v3.1.1.bak.json`）
    - `pages/01_content_studio.py`：form 加"标题正文是否带券" selectbox；已有 coupon label 改"实际是否用券"；form_dict 加 text_has_coupon
    - `tools/clean_cnn_backup.py`：新增清洗脚本（复用 日报清洗_new.py 解析 + 过滤 + 报告）
    - `data/cnn_backup_cleaned.xlsx`：清洗后产物（48307 行 / 3821 plan / 4 渠道 / 2024-10-15 ~ 2026-08-26）
    - `tests/verify.py`：§46 classify_coupon_in_text（14 用例）+ §47 schema 变更（12 用例）+ 5 个旧用例契约更新（CHANNELS 4/REQUIRED_FIELDS 4/v3.1.1）
  - verify.py 491 → **522 PASS, 0 FAIL**（新增 §46/§47 共 26 用例 + 5 个契约更新）
  - **待业务确认/补**：baseline 新增"渠道_x_文案含券词"维度 key（数据齐后建）/ SCENES 内容推断工具函数（等用户喂关键词词典）/ 字典维护 UI `pages/06_settings.py`

- **2026-08-27**：Phase 11 第三梯队 #12 简化落地（用户口径当天降级）：
  - **用户拍板反转**：第三梯队 #12 原拍板稿是 3 值（法定节假日/非工作日/工作日，需节假日字典），用户当天改口径——**不要日期选择器**，法定节假日暂搁，**只 selectbox 2 值（工作日/非工作日）**
  - 落地 4 文件：
    - `core/data_window.py`：加 `classify_date_type(target)` + `classify_today_type()`（纯 weekday 逻辑，`>=5`=非工作日；不依赖节假日字典、不处理调休）
    - `pages/01_content_studio.py:189`：`st.date_input` → `st.selectbox` 二选一；默认值按今日自动算
    - `core/schemas.py:187`：`TaskInput.planned_send_date` 字段名保留（孤儿字段，下游 baseline_lookup 走 `row["工作日类型"]` 不消费本字段），注释更新为"工作日/非工作日 标签"
    - `tests/verify.py §45`：18 个用例（5 工作日 + 2 非工作日 + 3 输入类型 + 3 边界 + 3 跨年 + 1 today 合法 + 1 错误抛错）
  - **baseline JSON 不动**——现有 `渠道_x_工作日类型` 2 值 key（`data/ctr_baseline.json:135-146`）正好对齐，无需新增 3 值维度；节假日日期被算进"非工作日"
  - **后续扩展路径**：要支持法定节假日时，建 `data/holidays.yaml` + `classify_date_type` 加节假日优先级分支，baseline 加 3 值 key
  - verify.py 473 → **491 PASS, 0 FAIL**（§45 新增 18 用例，CLI 与 pytest 双路一致）
  - **不动**：Handoff §6.2 第三梯队 #8/#9/#10/#11（仍等用户喂数据）/ 法定节假日字典 / baseline JSON / `pages/05_feedback` / 反哺管道
  - 完整变更记录在 `git log` 后续 commit 中

- **2026-08-26**：第二梯队 #1/#2 业务拍板落档（**不动代码，纯文档同步**）：
  - **#1 产品与权益**：单字段 `product_benefit` → 拆 `product_category` + `benefit_type` 两字段；枚举 10 产品 + 8 权益（含「自定义输入」兜底）；必填；参与生成；jieba 词典与 yaml 枚举解耦并行（jieba = 内容运营维护单品词典，yaml = 产品经理维护业务大类，自演化机制闭环）
  - **#2 投放目标**：PRD 6 值收敛到 4 值（品牌认知 / 点击驱动 / 转化促成 / 用户召回）；**支持多选**（逗号分隔，max 3，union 合并 tone_bias/must_avoid）；必填；参与生成 + 影响 strategy 优先级 + tone 词库；不约束 product（软引导）
  - **⚠️ 修正条目 1（拍板同日核对 baseline 实情）**：
    - Handoff §2 写"baseline 7 维 = channel/audience/coupon/stage/scene/plan_type/owner"**错**——baseline_lookup.py 实际是 1 基础 + 5 渠道交叉 + 1 时段 = 7 维（**无 objective 维度**）
    - objective 是 **新增** baseline 维度（7 → 8），不是"6→4 key 收敛"
    - PRD §9.1 例子 `"objective": "建立活动认知、提升点击"` 是字符串拼接，非多选；schema 单字符串维持
    - baseline 新增 `objective_x_渠道` = 4×6 = 24 key；当前 ~200 plan → 70% 兜底，等反馈 ≥ 1000 后切 L1 GBDT
  - **⚠️ 修正条目 2（拍板同日用户 Q1-Q3 揭示盲点 → 改多选）**：
    - 用户 Q1（新品 + 大促）+ Q2（召回 + 新品推荐）都是**多目标并存**——原"4 值单选"会强迫业务方简化信息
    - 修正为**4 值多选**：逗号分隔，max 3，tone_bias/must_avoid 取**并集**（最保守）
    - baseline 24 → **90 key**（2^4-1 × 6 = 90），7 级回退兜底（`baseline_lookup.py` 加 1 分支在 char_range 之前）
    - 修正记录：`Downloads/decision-objective-multiselect-correction-2026-08-26.md`
    - 修正后剧本：新品+大促 = `brand_awareness,conversion`（"全新 + 5折"）/ 召回+新品 = `user_recall,brand_awareness`（"想念 + 全新"）
  - 落地清单（未启动）：PRD §6.2/§9.1/§9.2 修订 + `config/product_benefit.yaml` 新 + `config/objective_strategy.yaml` 新（**含 combine_strategy: union + max_objectives: 3**）+ `core/schemas.py` 字段调整（注意 dataclass 字段顺序铁律）+ **8 维 baseline lookup**（含 90 key 算法，key 先 sort）+ **多选 prompt 拼装**（union 合并）+ `services/generation_service` strategy 投票合并；粗估 4-6 工作日
  - **暂搁**：字典维护 UI `pages/06_settings.py`（等 #7 拍板时一起决策，跟"附属页面范围"强相关）
  - 决策文档：`Downloads/decision-product-benefit-2026-08-26.md` + `Downloads/decision-objective-2026-08-26.md`（含 2 条修正记录）+ `Downloads/decision-objective-multiselect-correction-2026-08-26.md`（盲点修正）
  - 测试：未动代码 → 473 PASS / 0 FAIL 不变

- **2026-08-28**：Phase 22 B/C/D 完成（用户拍板节奏：B → C → D → A，A 最后做）：
  - **B 特征重要性月报脚本**（用户拍板：月报 + 自己看为主，不分享业务部）：
    - 新增 `tools/print_feature_importance.py`（217 行）：加载 lgbm_model_v1.pkl + lgbm_feature_meta.json，算 importance_type="gain"（支持 split），Top N 默认 10，与上次快照对比名次变化（±2 名算"涨/跌"，标 ↑/↓/新）；落档 `data/feature_importance_history/importance_YYYY-MM-DD_HHMMSS.json` + `data/reports/feature_importance_YYYY-MM-DD.txt`；Windows console 编码 fix（sys.stdout.reconfigure UTF-8 防 GBK 乱码）
    - humanizer 把内部列名翻成人话（`channel_APP_Push` → "渠道: APP Push"，`ch_x_wd_APP_Push_工作日` → "渠道×工作日: APP Push × 工作日"，`plan_type_te` → "计划类型 (target encoding)"）
    - 首次跑结果：Top 5 = 正文长度 35.19% / 标题长度 22.92% / 高效词命中数 14.59% / 渠道: 短信 8.63% / 计划类型 TE 6.48%（CTR 受文案长度主导，渠道影响排第 4，印证用户口径）
    - 测试：§58 新增 22 用例（humanizer 12 + compute_importance 5 + diff 5 + save/render/CLI 5）
    - 不动：L1 模型 / l1_predictor / baseline JSON / pages/01 sidebar（自己用的工具）
  - **C 漂移自动回退**（用户拍板：自动切回 L0，不让人介入）：
    - 新增 `core/active_mode.py`（read/write/clear 三态 + ALLOWED_MODES = {demo, baseline_only, l1_model}）
    - `tools/monitor_l1_drift.py` 加 `apply_auto_rollback(alert_level)`：ALERT → 写 demo / WARN → 写 baseline_only / OK → 清文件（恢复默认）；加 `--no-active-mode` CLI flag（默认开）
    - `pages/01_content_studio.py` 启动读 `data/active_mode.txt` → 覆盖 sidebar 默认 ctr_mode + 黄色 banner 提示"已被自动回退到 {mode}（漂移告警）"
    - 工作流：monitor 跑出告警 → 写文件 → 下次开 01 页面 sidebar 自动显示 demo + 红字提示；人工确认后手动删文件恢复
    - 测试：§59 新增 31 用例（active_mode 读写清 + 三档 ALERT/WARN/OK 端到端 + 01 sidebar 集成 + CLI 跑通）
    - 不动：l1_predictor / l1_drift 的 baseline / records.db schema / feedback.db
  - **D 批量预测自动落档 records.db**（用户口径：批量跑的预测一定会投出去，必须回收校准）：
    - `services/batch_evaluation_service.py` 加 `batch_signature(row)`（与 task_signature 同字段顺序：channel/coupon/plan_type/audience/stage/scene + 标题桶/正文桶，SHA1 截 12 位，batch 缺后 3 字段填空串）+ `save_predictions_to_records(rows, db_path)`（仅写 ctr_result_type 非空行，包成单候选 id="A" strategy="batch_eval" + ctr source 标 "batch_{result_type}"，单行失败不影响其他）
    - `pages/03_batch_evaluation.py` 加 checkbox「保存预测到 records.db（用于漂移监控 + 后续校准）」（默认关，按需开启）；评估完成自动调 save + 显示"已保存 N 条"
    - 闭环：03 上传 CSV → 勾选 → 跑评估 → 自动落档 → 后续 `pages/05_feedback` 上传真实 CTR 时 feedback_repository 自动 join signature 算 MAE/MAPE
    - 测试：§60 新增 24 用例（batch_signature 6 + save 端到端 10 + 边界 3 + 03 集成 5）
    - 不动：01 主流程 / 04 历史洞察 / pages/02/05 / baseline JSON / feedback_repository（不需改，自动 join）
  - 总用例：697 → **794 PASS / 0 FAIL**（pytest 双路一致）
  - **A 待启动**：用户口径"A 很重，最后做"——产品权益+投放目标维度扩展（Phase 9 已拍板），代码未动

- **2026-08-28**：Phase 22 A.1 产品权益维度扩展完成（用户口径：A 拆分，**A.1 先做 / A.2 投放目标待开发**）：
  - 拆字段：`core/schemas.py` `TaskInput.product_benefit` 单字段 → 拆 `product_category` + `benefit_type` 两字段（启用，**不参与 CTR baseline**——Phase 9 拍板 baseline 数据稀疏 ROI 低；只影响①AI prompt 注入 ②产品词典 jieba 词条扩展）
  - 数据源：新 `config/product_benefit.yaml`（10 产品：汉堡/小食/饮料/全餐/早餐/甜品/咖啡/麦满分/儿童餐/限定；8 权益：折扣/满减/赠品/会员专享/限时优惠/新品首发/活动促销/其他；`custom_label: 自定义`）+ `core/product_benefit.py` 加载模块（PyYAML + lru_cache + FALLBACK 兜底 + `options_with_custom()` 给 UI selectbox 加"自定义"末位）
  - dataclass 字段顺序铁律（no-default 在前）：audience/channel/stage/tone → expected_action/plan_type/coupon/planned_send_date/scene/extra_requirements（defaults） → **product_category / benefit_type（新启）** → objective（灰态） → text_has_coupon
  - prompt 拼接：`prompts/copy_generation.py` VERSION v1.0→v1.1，原「产品与权益：X」单行 → 拆「产品类别：X」「权益类型：Y」两行，任一空时不拼该行；SYSTEM_PROMPT 中 used_input_fields 同步
  - Demo 兜底：`services/generation_service._demo_candidates` 按"类别+权益"两值组装 benefit 短语（双非空 → "类别 权益"，单空 → "类别 优惠" / "权益"，双空 → 稳定兜底"新品限时优惠"）；短信/企微1v1/APP Push 三渠道 Demo 文案自动适应新组合
  - UI：`pages/01_content_studio.py` 2 列 selectbox（pc_a/pc_b 两列避免与原 c1-c5 命名冲突）+ 自定义文本框联动 disabled（选"自定义"才启用文本框，文本框值落最终字段）；保留 objective 灰态（**A.2 待开发 · UI 重构后启用**）
  - 测试：§39 旧 P1 灰态测试已重命名为 `test_phase_a1_product_benefit_split`，新增 29 用例覆盖（product_benefit 模块 8 + TaskInput 字段顺序 6 + prompt 拼装 4 + Demo 拼接 4 + 01 源码静态 7）；**总用例 794 → 823 PASS / 0 FAIL**（pytest 双路 61 passed）
  - **A.2 投放目标（PRD §9.1 4 值多选 + 8 维 baseline 90 key 算法）暂搁**：用户口径"投放目标可以写待开发，跟 L2 和 UI 坐一桌"；待 UI 重构 + L2 完成后启 A.2（粗估 4-6 工作日）
  - 同步：Handoff §2/§5/§5.5 数据维度列表（粗估：维度 5 → 7 启用 / 灰态 2 → 2 不变）+ PRD §9.1 字段定义（如有需要同步）

### §5.5 CTR 准确率学习 Roadmap（2026-08-26 · 重要背景）

**完整原文**：`Downloads\CTR准确率学习-Roadmap附录_2026-08-26.md`。**此处给执行摘要**。

**一句话**：把 CTR 从"查找表统计校准"升级到"会自我度量、会重训的回归模型"，让"**预测误差 vs 真实 CTR 曲线**"往下走。

#### Phase 16 维度扩展决策（2026-08-27 · 用户拍板）

口径：「**预算owner 不加，工作日类型从 sent_date 推算就行，标题正文是否带券加一下，其他不用**」。

- ✅ 加 `text_has_coupon`（Phase 15 已建维度，Phase 16 接入回流反馈聚合）
- ✅ 加 `工作日类型`（从 `sent_date` 推 `工作日`/`非工作日`，复用 `core/data_window.classify_date_type`）
- ❌ 不加 `预算Owner`（用户拍板"不加"）
- ❌ 不加 `title_len_range`（用户拍板"其他不用"）
- 落地：`tools/calibrate_baseline.py` 覆盖 4 维度（渠道 / 渠道×用券 / 渠道×文案含券词 / 渠道×工作日类型）；`baseline_lookup` 已支持（Phase 12 落）；`feedback_records` 表加 `text_has_coupon TEXT` 列 + ALTER 兼容老库

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
