# mcd-ai-content-platform — 决策记录（详）

> **何时读我**：新 session 想了解"为什么 Phase X 这样设计"时，按 Phase 编号搜这里。
> 速查表在 `Handoff.md §6.1`。
> **本文件已压缩**（2026-08-31）：Phase 1-10 早期决策压成 1-2 行 + 1-2 句 why；Phase 11+ 保留详细。删 git commit message 已经有的细节。

---

## 5. 决策记录

### 2026-08-24 · 项目立项 + Phase 1-3.2

- **项目立项**：PRD v2.0 + 3 处补充（§4.0 CTR 三入口 / §13.5 Adapter 策略 / §15.A 工程化配套）。why：单页面 mcd-copy-analyzer 不够用，统一整合到内网工作台
- **端口 8510**：避让 mcd-copy-analyzer 8501
- **setup_and_run.bat 闪退 5 次迭代**：最终 v5 跳过 venv，用系统 Python。why：venv 在 Win11 子系统下不可靠
- **bat 文件必须 CRLF**：cmd 严格要 CRLF，Write 工具默认 LF。why：v5 闪退第 6 次才发现 LF
- **Phase 1**：CTR Adapter 4 模块（baseline/prompt/column/char）+ `PredictionResult` dataclass；verify 82 PASS
- **Phase 2**：抽 copy-analyzer Adapter + 6 模块；verify 152 PASS
- **Phase 3**：6 service + 2 prompt + 1 repository + 2 yaml + 5 页面占位；st.Page("app.py") 自引用递归 bug 修复；verify 230 PASS

### 2026-08-26 · Phase 4 业务页 + CTR Adapter bug

- **Phase 4**：pages/02/03/04 三业务页落地（单条诊断/批量评估/七 Tab 洞察）；01 渠道预览升级到高保真；verify 290 PASS
- **CTR Adapter bug 修复**：`_demo_pred` 在 `_bl_str="未知"` 时 bl*100 抛 TypeError，新增 bl=None 兜底；predict_one 重写不走 Candidate 包装

### 2026-08-26 · Phase 5 CTR 反哺闭环 P0+P1+P2

- **P0 record 指纹**：task_signature SHA1-12（channel/coupon/plan_type/audience/stage/scene + 标题/正文桶）。why：让 records.db ↔ feedback.db 可 join
- **P1 feedback 库**：repositories/feedback_repository（SQLite）+ pages/05_feedback 上传
- **P2 baseline 校准自动化**：calibrate_baseline.py 三段策略（<5 跳过 / 5-20 EMA α=0.3 / ≥20 全量）。why：手动 EMA 容易漂移，自动三段防过拟合
- **GitHub secret scanning**：tools/push_via_api.py 硬编码 token 被扫描阻断，改读环境变量

### 2026-08-26 · Phase 6 P0 业务确认 + 企微 1v1 预览 + LLM 留空

- **业务确认 12 项**（详 docs/architecture.md §五）：Demo 主渠道 APP Push + 企微 1v1；枚举/字数/词表复用 yaml；predictor 走 main 版；内网 LLM 暂留空
- **企微 1v1 聊天气泡**：ui/styles.py 加 `.wechat-bubble-wrap` + 01 替换占位
- **LLM 留空 banner**：config/llm_settings.yaml 4 字段全空 + ui/llm_status.py 检测器 + `.llm-warning` 样式。why：未配置 LLM 时给用户清晰提示
- verify 349 PASS

### 2026-08-26 · Phase 6 P1 灰态 + 进阶弱化 + CTR 免责

- **决策 1（6 维度前端灰态）**：product_benefit/objective 改 disabled=True + label 加「待开发·二期接入」+ help tooltip。why：拍板前不接后端，避免半成品数据污染
- **决策 2（4 附属页面弱化）**：advanced_notice banner + 首页分组卡（核心大/进阶小）。why：避免业务方误以为 02-05 已正式
- **决策 3（CTR 反哺免责）**：04/05 顶部 banner "演示口径·业务确认前不接真实数据"。why：保护合规边界
- **不动**：app.py / 后端反哺 / 任何页面删除
- verify 395 PASS

### 2026-08-26 · Phase 6 P2 CTR 口径固化 v3.1

- **Q1-Q6 拍板**：Q1 去重点击 / Q2 触达成功 / Q3 全周期 / Q4 不跨渠道 / Q5 min_reach≥1000 / Q6 业务确认前不接真实
- **bi_dt 铁律**：12 点前 T-2 兜底，新增 `core/data_window.resolve_bi_dt_window()`
- **6 文件落地**：baseline JSON v3.1 + 5 处注释同步 + docs/ctr-kpi-definition-proposal-v0.2.md 拍板稿
- **关键前提**：导出表口径必须与 Q1-Q6 完全一致，否则"真实值"是另一套定义
- verify 421 PASS

### 2026-08-26 · Phase 6 P3 simplify 清理

- **修 A 手写 yaml → yaml.safe_load**：ui/llm_status.py 30 行 → 1 行（PyYAML 已依赖）
- **修 B 4 处 v3.1 docstring 缩成 1 行**：ground truth 只留 baseline JSON
- **修 C 删 PENDING_FIELDS 死元组**
- **修 D 删 core/data_window.py _to_local aware datetime 死分支**
- **修 E ui/notice.py 抽 render_notice helper**
- 净减 56 行

### 2026-08-26 · Phase 7 业务拍板落地 #3 + #6

- **#3 触发条件**：每周一上午手动跑 calibrate_baseline.py → 新文档 docs/ctr-feedback-schedule.md（**2026-08-31 用户改月度**）
- **#6 反哺影响排序**：rank_candidates_by_ctr 纯函数（pred_ctr 降序 + title 长度兜底）+ 默认 selected_id 改最 CTR 那条
- **顺手清理**：删 phase6_p1/p2_push.py 临时文件

### 2026-08-26 · Phase 8 pytest 迁移 + Phase 6 P4 候选扫除

- **pytest 迁移**：verify.py 加 `_RUNNING_UNDER_PYTEST` 标志 + pytest.ini + 双路一致（CLI 428 + pytest 43）
- **P3 维度权重动态**：config/dimension_weights.yaml + tools/train_dimension_weights.py（v0.1 占位）+ text_analyzer.diagnose_score 加权聚合
- **demo 数据回灌**：feedback_lookup.py（FEEDBACK_READY_MIN_PLANS=50 + lookup_feedback_ctr by signature）。why：让 01 demo mode 在有真实数据时显示真实 CTR 而非 baseline × tm 兜底
- **铁律**：adapter 直接 sqlite3，不 import repository（CLAUDE.md §4.1）

### 2026-08-27 · Phase 9 #1/#2 业务拍板（盲点修正）

- **#1 产品与权益**：单字段 product_benefit → 拆 product_category + benefit_type；10 产品 + 8 权益 +「自定义」兜底；必填 + 参与生成 + jieba 词典与 yaml 枚举解耦并行
- **#2 投放目标**：PRD 6 值 → 4 值（品牌认知/点击驱动/转化促成/用户召回）；**多选**（逗号分隔 max 3，union 合并）；必填 + 参与生成 + 影响 strategy+tone
- **修正 1**：baseline_lookup 实际是 7 维 ≠ Handoff §2 写"7 维含 objective"，objective 是新增维度（7→8，不是 6→4 收敛）
- **修正 2（盲点）**：用户 Q1（新品+大促）+ Q2（召回+新品推荐）都是多目标并存 → 改多选 → baseline 24 → 90 key（2^4-1 × 6，7 级回退）。why：单选会强迫业务方简化信息
- **暂搁**：字典维护 UI pages/06_settings.py（**2026-08-31 用户拍板纳入正式版，跟 UI 重设一起做**）

### 2026-08-27 · Phase 11 #12 工作日 2 值简化

- **用户拍板反转**：原 3 值（法定节假日/非工作日/工作日，需节假日字典）→ 2 值（**只 selectbox 工作日/非工作日**）。why：节假日字典维护成本高，先做最小可用版本
- **实现**：classify_date_type / classify_today_type 纯 weekday 函数（不依赖节假日字典、不处理调休）；baseline JSON 现有 2 值 key 正好对齐
- **后续扩展路径**：要支持节假日时建 data/holidays.yaml + 3 值 baseline key
- verify 491 PASS

### 2026-08-27 · Phase 12 schema 兜底字段 + #8/#9/#10/#11 落地

- **PLAN_TYPES/COUPON_FLAGS 保留"未知"**：schema 兜底（form 不填时 UI 防御），不是数据源枚举（实际只有 2 值）。"未知" ≠ 0 系数（baseline_lookup 跳过该维度分支，走渠道整体兜底）
- **指数平滑衰减已实现**：baseline JSON v3.0+，λ=0.01 半衰期 69.3 天（越靠近 last_updated 权重越高）
- **#11 用户假设反转**：用户原假设"文案带券词影响更大"，CNN0827 数据验证反转 → form "实际是否用券"才是主驱动（企微 1v1 2.56x vs 文案含券 1.32x；APP Push 文案含券反向 0.84x）。**保留 form + 新增 text_has_coupon 双字段**
- **#8 渠道清洗**：删除"无需渠道"(434) + "微信公众号推文"(19)；baseline v3.1.1 删 14 个 key；schema CHANNELS 加"微信小程序订阅消息" + "企微 1v1"连写
- **#9 Plan 命名统一**：PLAN_TYPES 改 ("AARRPlan", "常规Plan", "未知")（连写）；baseline_lookup.py:76 顺手修"普通Plan"→"常规Plan" bug（v3.0 → v3.1 一直存在）
- **#10 SCENES 改选填**：REQUIRED_FIELDS 5 → 4；scene 字段挪到 has-default 区
- verify 522 PASS

### 2026-08-27 · Phase 13 工具定位重定义

- **用户口径**：CTR 评估是辅助决策工具，不是选文案工作流 → 业务方看 3 候选 + CTR 估计 → 自己决定 → 不入库
- **3 按钮全砍**：编辑候选 / 恢复 AI 原文 / 保存当前选择（无人用文案 + records.db 是死数据）
- **records.db 保留但 UI 不调用**：未来 train_dimension_weights.py 可能读 records.db 关联 feedback.db；UI 不暴露"保存"入口，业务方不点击 → 不增长
- **Candidate 字段重构**：删 title_edited/body_edited + effective_title/body/is_edited/reset_edit；引用方 4 文件改 effective_* → title/body
- verify 525 PASS

### 2026-08-27 · Phase 14 + 15 row key 修复 + baseline v3.2

- **用户报告**："选了具体指标 CTR 没变" → 排查发现 2 类根因：
  1. row key 不匹配：_candidate_to_row 输出英文 key，prompt_builder 读中文 key（plan_type/coupon/owner 3 字段读不到）
  2. workday 孤儿字段：TaskInput.planned_send_date 下游 0 消费
- **修复**：_candidate_to_row 中英文 key 双输出 + workday 透传 + prompt_builder.py:101 "普通Plan"→"常规Plan"
- **新增维度**：tools/recalc_text_has_coupon.py 从 cnn_backup_cleaned.xlsx（48307 行）按指数衰减 λ=0.01 聚合 8 keys → baseline v3.2
- **关键发现**：文案含券词对 CTR 渠道差异极大（APP Push 反向 0.84x，企微 1v1 / 微信小程序 / 短信 1.32x / 1.05x / 2.77x）→ 印证 #11 用户假设反转
- verify 557 PASS

### 2026-08-28 · Phase 16-17 代码质量清理

- **Phase 16 calibrate_baseline 扩 2 维度**：text_has_coupon + workday；feedback_repository 加 text_has_coupon 列 + ALTER 兼容老库
- **Phase 16.5 上线声明**：用户拍板"先上线再说"——weekly_calibrate.bat 仅落档不调度；L1 模型升级延期待样本 ≥ 1000
- **Phase 17 多项清理**：02 页面 bug / LLM call LRU cache / weighted_ctr 合并 / 死代码删除 / CSV reader 合并 / rule_engine 重构 / jieba 批量向量化 / Streamlit 页面缓存

### 2026-08-28 · Phase 18 L1 LightGBM PoC

- **用户拍板"先试试看"**：基于 cnn_backup_cleaned.xlsx 4.4 万行训练
- **关键决策**：
  - 剔除微信小程序订阅消息（仅 7 Plan，统一模型被带偏）
  - 特征 14→15 维（5 数值 + 6 类别 one-hot + 1 高效词命中 + 1 计划类型 TE + 1 工作日）
  - 时间衰减权重 half_life=180 天
- **结果**（baseline v3.2 同口径 evaluate_lgbm.py 复现）：L1 MAE 0.395%（vs L0 0.416% 同口径降 5.2%），R² 0.0824（vs L0 0.0659）
- **3 渠道 L1 全胜**：APP Push 0.273% / 企微1v1 0.682% / 短信 0.203%
- **关键发现**：渠道×工作日交叉特征为负向（LightGBM 自己能学，显式加 = 特征冗余）

### 2026-08-28 · Phase 19+20 L1 入生产 + 漂移监控

- **Phase 19 静默双轨**：l1_predictor.py（predict_l1/predict_l1_batch/predict_l1_status）+ sidebar admin checkbox 默认关；模型缺失/渠道不在训练范围时静默降级 unavailable，主流程不受影响
- **Phase 20 l1_model mode 主流程接入**：CTRPredictionAdapter.VALID_MODES 加 "l1_model"（5 态）+ sidebar selectbox（demo/baseline_only/l1_model）+ L1 模型缺失时不可选
- **漂移监控**：tools/monitor_l1_drift.py records.db join feedback.db → MAE vs baseline → 超 1.3 倍红字告警 + drift_log.csv 留档
- **训练责任人**：用户自己（**2026-08-31 拍板**）

### 2026-08-28 · Phase 22 B/C/D 生产闭环

- **B 特征重要性月报脚本**（用户拍板：月报 + 自己看为主）：tools/print_feature_importance.py（217 行）+ humanizer + 月度快照对比 + Top10 涨/跌标。首次跑：正文长度 35.19% / 标题长度 22.92% / 高效词命中 14.59%
- **C 漂移自动回退**（用户拍板：自动切回 L0）：core/active_mode.py 三态 + monitor_l1_drift.py apply_auto_rollback；workflow：drift → 写文件 → 01 启动读 → 黄 banner 提示
- **D 批量预测自动落档 records.db**（用户口径：批量跑的预测一定会投出去）：batch_evaluation_service.save_predictions_to_records + 03 checkbox 默认关按需开启
- 总用例 697 → 794 PASS

### 2026-08-28 · Phase 22 A.1 产品权益维度扩展

- **拆字段**：TaskInput.product_benefit → product_category + benefit_type（启用，**不参与 CTR baseline**——Phase 9 拍板 baseline 数据稀疏 ROI 低；只影响 ① AI prompt 注入 ② 产品词典 jieba 词条扩展）
- **数据源**：config/product_benefit.yaml（10 产品 + 8 权益 + custom_label）+ core/product_benefit.py 加载模块
- **dataclass 字段顺序铁律**：audience/channel/stage/tone → expected_action/.../extra_requirements → product_category/benefit_type（新启）→ objective（灰态）→ text_has_coupon
- **A.2 投放目标暂搁**：用户口径"投放目标可以写待开发，跟 L2 和 UI 坐一桌"
- 总用例 794 → 823 PASS

### 2026-08-28 · Phase 23+24 安全加固 + 全量 sweep

- **Phase 23 Critical-1/2 安全加固**：API key 泄漏（_sanitize_error + _classify_call_error）+ XSS（html.escape）+ page_setup 模块抽取 + monitor_l1_drift 修整
- **Phase 24 全量 sweep**：§61 24 用例覆盖 31 模块 import / SQLite tmp dir / rule_engine 4 边界 / ctr 5 modes 全过 / TaskInput 4 必填 / 空 DB 优雅降级。**首次确认 L1 模型 live**
- 总用例 823 → 854 PASS

### 2026-08-31 · Phase 25 代码清理 + Handoff 压缩

- **L1 runbook**：docs/l1-training-runbook.md 落地（5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报）
- **频率改月度**：docs/ctr-feedback-schedule.md 从"每周一上午"改为"每月 1 号上午手动"（用户拍板）+ §3.5 加 L1 漂移监控步骤
- **死代码清理**：tools/push_*_via_api.py ×9 → tools/_archive/ + ui/plotly_helpers.py axis_rate() 删 + 2 unused import 删
- **L1 CSS 补齐**：ui/styles.py 加 .l1-pill/.l1-label/.l1-value/.l1-meta 4 个类（之前 01 引用但未声明）
- **black 格式化**：ui/styles.py / pages/01/02 三文件
- **Handoff 压缩**：4 文件全整理（Phase 1-10 早期决策压 1-2 行 + why；Phase 11+ 保留）
- verify 854 PASS（无回归）

---

## §5.5 CTR 准确率学习 Roadmap（2026-08-26 · 重要背景）

**完整原文**：`Downloads\CTR准确率学习-Roadmap附录_2026-08-26.md`。**此处给执行摘要**。

**一句话**：把 CTR 从"查找表统计校准"升级到"会自我度量、会重训的回归模型"，让"**预测误差 vs 真实 CTR 曲线**"往下走。

### Phase 16 维度扩展决策（2026-08-27 · 用户拍板）

口径：「**预算owner 不加，工作日类型从 sent_date 推算就行，标题正文是否带券加一下，其他不用**」。

- ✅ 加 `text_has_coupon`（Phase 15 已建维度，Phase 16 接入回流反馈聚合）
- ✅ 加 `工作日类型`（从 `sent_date` 推 `工作日`/`非工作日`，复用 `core/data_window.classify_date_type`）
- ❌ 不加 `预算Owner`（用户拍板"不加"）
- ❌ 不加 `title_len_range`（用户拍板"其他不用"）
- 落地：`tools/calibrate_baseline.py` 覆盖 4 维度（渠道 / 渠道×用券 / 渠道×文案含券词 / 渠道×工作日类型）；`baseline_lookup` 已支持；`feedback_records` 表加 `text_has_coupon TEXT` 列 + ALTER 兼容老库

### 三台阶

| 台阶 | 做法 | 触发 | 状态 |
|---|---|---|---|
| **L0（现状）** | baseline 查找表 + `calibrate_baseline.py` EMA | ✅ 已建（Phase 5 P2） | ✅ 投产 |
| **L1** | LightGBM 回归替查找表（15 维） | ✅ Phase 18-20 落地 | ✅ 投产（runbook 详 5 步流程） |
| **L2** | 增量重训 + 上线前回测门禁 + 误差监控 | L1 稳定后 | ⏳ 待启动 |

### 当前断点

```
①生成 → ②预测 → ③投放 → ④回收真实 CTR
                                ↓
                          ⑤ 重训模型（runbook 详）
```

①②③④ Phase 5 管道已搭（P0 signature + P1 feedback + P2 calibrate），断点在 ⑤（用户手动跑 runbook 流程）。

### 选型铁律 · 为什么是 GBDT 不是深度学习

- 输入是**结构化表格特征** + **中样本** → LightGBM 几乎必然赢神经网络
- GBDT 出**特征重要性**（可解释是刚需）—— 业务要能问"为什么这个 Plan CTR 高"
- 深度 CTR 模型（DeepFM/DIN）要**亿级样本**才回本，本项目喂不饱，别上

### 务实节奏（防过拟合）

- **短期（< 几百条）**：维持 L0 EMA；先把误差曲线搭起来
- **中期（~ 千条）**：切 L1（Phase 18-20 已落地，runbook 详 5 步流程）
- **长期**：L2 增量重训 + 回测门禁（待 L1 稳定）

### 与决策文档联动

CTR 学习 ≠ 复杂模型，但**首先得有"准确率"可量化的指标**——这要先定**口径**（决策文档 #5）。口径不定，**算不出误差** → L1 全免谈。

---

## 已压缩删节（细节查 git log）

- `setup_and_run.bat` 闪退 5 次迭代详细历史（v1-v5 各版）
- 早期 verify.py 用例数 82→152 各 phase 增量明细
- 已知小 bug 修复记录（CTR Adapter bl=None、Candidate.id=A/B/C、CSV bytes literal 等）—— 教训已留 `Handoff-lessons.md`
- 推送脚本演进（force-with-lease / Contents API / GitHub secret scanning）—— 教训已留 `Handoff-lessons.md`
