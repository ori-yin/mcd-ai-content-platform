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

## 6. 待办

> **新会话 AI 直接读这段 ↓**

### 6.0 当前快照（最快定位状态）

- **阶段**：**核心全链路完成 · 准备上线**（Phase 16.5 · 2026-08-27 用户拍板"先上线再说"）
- **用例**：574 PASS / 0 FAIL（`python tests/verify.py`，557 → 574）= pytest 双路一致
- **已可用模块**：①内容创作（01 生成 3 候选 + CTR 评估 + 阈值生效）；②真实回流（04 上传 CSV/Excel → 入库 → 4 维度聚合 → 写 baseline）；③历史洞察（04 七 Tab）；④批量评估 CTR（03）
- **未做（用户拍板延后）**：自动定时校准（`weekly_calibrate.bat` 仅落档不调度）/ L1 LightGBM 模型升级（Roadmap §5.5；等样本过千）
- **首要任务**：真回流数据进来时手动跑 `python tools/calibrate_baseline.py --db data/feedback.db` 重算 baseline
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

#### L1 · LightGBM 回归替 baseline 查找表（详 §5.5）⏸️ **延期（2026-08-27 用户拍板·Phase 16.5）**

> 用户口径："**L1 模型升级先不做，先上线**"。待样本 ≥ 1000 plan 再次启动。下方为原候选描述，待启动时直接复用。

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
1. **切 L1 时点**：样本 ≥ 多少 plan 时启动 L1？建议 ≥ 1000
2. **谁来训练**：业务方跑 / 平台自动 / 数据团队跑？
3. **误差告警阈值**：MAE 涨多少触发告警？建议 > 30%
4. **可解释输出**：要不要把"特征重要性 Top10 维度"每周给业务看？

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
| `C:\ideon\mcd-ctr-predictor\ctr_predictor.py` | CTR 事实来源 |
| `C:\ideon\mcd-copy-analyzer\analyzer.py` | 文案分析事实来源 |
| `C:\ideon\mcd-copy-analyzer\Handoff.md` | 范式参考 |

---

## 9. 新 Session 第一步

1. 读本 Handoff（项目记忆，重点 **§6.0 快照 + §6.2 第三梯队**）
2. 读 `CLAUDE.md`（架构 + 约束）
3. 读 `PRD.md §4.0 / §13.5 / §15.A`（三处补充）
4. 跑 `python tests/verify.py`（**522 PASS / 0 FAIL**，CLI 与 pytest 双路一致）
5. 看 `docs\ctr-kpi-definition-proposal-v0.2.md`（**当前 v3.1 拍板口径，v3.1.1 已落档**）
6. 当前是 **Phase 12 完成 · 第三梯队 #8/#9/#10/#11 全部落地 · #11 用户假设反转保留双字段**

---

## 10. Self-check

- [x] 临时文件全清（`_*.py / *.bak / *.log / *.pyc`）— `tools/_push_phase6p4_once.py` 一次性脚本已删；`data/ctr_baseline_v3.1.1.bak.json` 是 baseline 版本备份非临时文件
- [x] `python tests/verify.py` 全过（**522 PASS / 0 FAIL**，Phase 12 §46/§47 新增 31 用例 + 5 个旧用例契约更新）
- [x] `python -m py_compile $(git ls-files '*.py')` 全过
- [x] 关键改动进 commit（如 git 化）
- [x] UI 无 emoji，沟通全中文
- [x] Phase 11 + Phase 12 Handoff §5/§6.0/§6.1/§6.2/§8/§9/§10 同步（#12 状态从 3 值拍板稿改成 2 值已落地；#8/#9/#10/#11 全部 Phase 12 落地；#11 用户假设反转保留双字段）
